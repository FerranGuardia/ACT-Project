"""
Robustness Test Suite for Full Pipeline

Tests the complete workflow: URL → Scraping → TTS → Audio Files
with multiple URLs from different websites to test robustness.

Usage:
    python run_tests.py
    python run_tests.py --config test_config.json
"""

import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add ACT project to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent
src_path = project_root / "src"

if src_path.exists():
    sys.path.insert(0, str(src_path))
else:
    print(f"✗ ACT src directory not found at: {src_path}")
    print(f"Please ensure ACT project structure is correct")
    input("\nPress Enter to exit...")
    sys.exit(1)

try:
    from processor.pipeline import ProcessingPipeline
    from processor.progress_tracker import ProcessingStatus
    from core.logger import get_logger
except ImportError as e:
    print(f"\n✗ Error importing ACT modules: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")
    sys.exit(1)

logger = get_logger("test.robustness")


class PipelineTestResult:
    """Stores test results for a single URL."""
    
    def __init__(self, url: str, title: str, website: str):
        self.url = url
        self.title = title
        self.website = website
        self.success = False
        self.chapters_found = 0
        self.chapters_scraped = 0
        self.chapters_converted = 0
        self.chapters_failed = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.duration = 0.0
        self.text_files_created = 0
        self.audio_files_created = 0
        
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "title": self.title,
            "website": self.website,
            "success": self.success,
            "chapters_found": self.chapters_found,
            "chapters_scraped": self.chapters_scraped,
            "chapters_converted": self.chapters_converted,
            "chapters_failed": self.chapters_failed,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration": self.duration,
            "text_files_created": self.text_files_created,
            "audio_files_created": self.audio_files_created
        }


class RobustnessTestSuite:
    """Robustness test suite for full pipeline workflow."""
    
    def __init__(self, config_path: Path, base_output_dir: Optional[Path] = None):
        """
        Initialize test suite.
        
        Args:
            config_path: Path to test_config.json
            base_output_dir: Base directory for test outputs (defaults to robustness_tests/output)
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Set up output directories
        if base_output_dir:
            self.base_output_dir = base_output_dir
        else:
            self.base_output_dir = config_path.parent / self.config["settings"]["output_dir"]
        
        self.summary_dir = config_path.parent / self.config["settings"]["summary_dir"]
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.summary_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: List[PipelineTestResult] = []
        
    def _load_config(self) -> Dict:
        """Load test configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def _sanitize_title(self, title: str) -> str:
        """Sanitize title for use in file/directory names."""
        sanitized = title.lower().replace(" ", "_").replace("-", "_")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
        return sanitized[:50]  # Limit length
    
    def test_url(
        self,
        test_config: Dict,
        continue_on_error: bool = True
    ) -> PipelineTestResult:
        """
        Test full pipeline for a single URL.
        
        Args:
            test_config: Test configuration dict with url, title, website, chapters, etc.
            continue_on_error: If True, continue even if errors occur
            
        Returns:
            PipelineTestResult with test results
        """
        url = test_config["url"]
        title = test_config["title"]
        website = test_config.get("website", "unknown")
        max_chapters = test_config.get("chapters", 2)
        voice = test_config.get("voice", "en-US-AndrewNeural")
        provider = test_config.get("provider", "edge_tts")
        
        result = PipelineTestResult(url, title, website)
        start_time = time.time()
        
        # Create project name from title
        project_name = self._sanitize_title(title)
        
        # Create isolated output directory for this test
        test_output_dir = self.base_output_dir / project_name
        test_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*80}")
        print(f"Testing: {title}")
        print(f"Website: {website}")
        print(f"URL: {url}")
        print(f"Voice: {voice}")
        print(f"Chapters to test: {max_chapters}")
        print(f"{'='*80}\n")
        
        try:
            # Create pipeline
            pipeline = ProcessingPipeline(
                project_name=project_name,
                base_output_dir=test_output_dir,
                voice=voice,
                provider=provider,
                novel_title=title
            )
            
            # Track progress
            chapter_statuses = {}
            
            def on_chapter_update(chapter_num: int, status: ProcessingStatus, message: str):
                chapter_statuses[chapter_num] = (status, message)
                if status == ProcessingStatus.SCRAPED:
                    result.chapters_scraped += 1
                elif status == ProcessingStatus.COMPLETED:
                    result.chapters_converted += 1
                elif status == ProcessingStatus.FAILED:
                    result.chapters_failed += 1
                    result.errors.append(f"Chapter {chapter_num}: {message}")
            
            pipeline.on_chapter_update = on_chapter_update
            
            # Run full pipeline
            print(f"Starting pipeline for {title}...")
            pipeline_result = pipeline.run_full_pipeline(
                toc_url=url,
                novel_url=url,
                novel_title=title,
                max_chapters=max_chapters
            )
            
            if not pipeline_result.get("success"):
                error_msg = pipeline_result.get('error', 'Unknown error')
                result.errors.append(f"Pipeline failed: {error_msg}")
                result.duration = time.time() - start_time
                if not continue_on_error:
                    return result
            
            # Get chapter count
            chapter_manager = pipeline.project_manager.get_chapter_manager()
            if chapter_manager:
                all_chapters = chapter_manager.get_all_chapters()
                result.chapters_found = len(all_chapters)
                print(f"✓ Found {result.chapters_found} chapters")
            else:
                result.warnings.append("Chapter manager not available")
            
            # Count files created
            file_manager = pipeline.file_manager
            text_dir = file_manager.get_text_dir()
            audio_dir = file_manager.get_audio_dir()
            
            if text_dir.exists():
                result.text_files_created = len(list(text_dir.glob("chapter_*.txt")))
            if audio_dir.exists():
                result.audio_files_created = len(list(audio_dir.glob("chapter_*.mp3")))
            
            # Check results
            if result.chapters_converted > 0:
                result.success = True
                print(f"\n✓ Successfully converted {result.chapters_converted} chapters to audio")
            else:
                result.warnings.append("No chapters were successfully converted to audio")
            
            result.duration = time.time() - start_time
            
            # Cleanup - clear project data if configured
            if self.config["settings"].get("clear_project_data_after_test", True):
                try:
                    pipeline.clear_project_data()
                    print("✓ Cleared test project data")
                except Exception as e:
                    result.warnings.append(f"Failed to clear project data: {e}")
            
        except Exception as e:
            result.errors.append(f"Exception during testing: {str(e)}")
            result.duration = time.time() - start_time
            import traceback
            logger.error(f"Error testing {url}: {traceback.format_exc()}")
            if not continue_on_error:
                raise
        
        return result
    
    def run_all_tests(self) -> List[PipelineTestResult]:
        """Run tests for all URLs in config."""
        print(f"\n{'='*80}")
        print(f"ROBUSTNESS TEST SUITE - FULL PIPELINE")
        print(f"Output directory: {self.base_output_dir}")
        print(f"Summary directory: {self.summary_dir}")
        print(f"Total tests: {len(self.config['tests'])}")
        print(f"{'='*80}\n")
        
        continue_on_error = self.config["settings"].get("continue_on_error", True)
        
        for i, test_config in enumerate(self.config["tests"], 1):
            print(f"\n[{i}/{len(self.config['tests'])}] Running test...")
            result = self.test_url(test_config, continue_on_error=continue_on_error)
            self.results.append(result)
            
            # Small delay between tests
            if i < len(self.config["tests"]):
                time.sleep(2)
        
        return self.results
    
    def generate_summary(self) -> Path:
        """Generate markdown summary report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = self.summary_dir / f"test_summary_{timestamp}.md"
        
        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total_tests - successful
        
        # Calculate statistics
        total_chapters_found = sum(r.chapters_found for r in self.results)
        total_chapters_converted = sum(r.chapters_converted for r in self.results)
        total_duration = sum(r.duration for r in self.results)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# Robustness Test Suite - Summary Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Overall Statistics
            f.write("## Overall Statistics\n\n")
            f.write(f"- **Total Tests:** {total_tests}\n")
            f.write(f"- **Successful:** {successful} ✓\n")
            f.write(f"- **Failed:** {failed} ✗\n")
            f.write(f"- **Success Rate:** {(successful/total_tests*100):.1f}%\n")
            f.write(f"- **Total Chapters Found:** {total_chapters_found}\n")
            f.write(f"- **Total Chapters Converted:** {total_chapters_converted}\n")
            f.write(f"- **Total Duration:** {total_duration:.1f}s ({total_duration/60:.1f} minutes)\n\n")
            f.write("---\n\n")
            
            # What Worked
            f.write("## ✅ What Worked\n\n")
            working_tests = [r for r in self.results if r.success]
            if working_tests:
                f.write("| Website | Novel | Chapters Found | Chapters Converted | Duration |\n")
                f.write("|---------|-------|----------------|-------------------|----------|\n")
                for result in working_tests:
                    f.write(f"| {result.website} | {result.title} | {result.chapters_found} | {result.chapters_converted} | {result.duration:.1f}s |\n")
            else:
                f.write("No tests passed successfully.\n")
            f.write("\n---\n\n")
            
            # What Didn't Work
            f.write("## ❌ What Didn't Work\n\n")
            failed_tests = [r for r in self.results if not r.success]
            if failed_tests:
                f.write("| Website | Novel | Error Summary |\n")
                f.write("|---------|-------|---------------|\n")
                for result in failed_tests:
                    error_summary = result.errors[0][:100] if result.errors else "Unknown error"
                    f.write(f"| {result.website} | {result.title} | {error_summary} |\n")
            else:
                f.write("All tests passed successfully! ✓\n")
            f.write("\n---\n\n")
            
            # Detailed Results
            f.write("## Detailed Results\n\n")
            for i, result in enumerate(self.results, 1):
                status_icon = "✅" if result.success else "❌"
                f.write(f"### {i}. {status_icon} {result.title}\n\n")
                f.write(f"- **Website:** {result.website}\n")
                f.write(f"- **URL:** {result.url}\n")
                f.write(f"- **Status:** {'PASS' if result.success else 'FAIL'}\n")
                f.write(f"- **Chapters Found:** {result.chapters_found}\n")
                f.write(f"- **Chapters Scraped:** {result.chapters_scraped}\n")
                f.write(f"- **Chapters Converted:** {result.chapters_converted}\n")
                f.write(f"- **Chapters Failed:** {result.chapters_failed}\n")
                f.write(f"- **Text Files Created:** {result.text_files_created}\n")
                f.write(f"- **Audio Files Created:** {result.audio_files_created}\n")
                f.write(f"- **Duration:** {result.duration:.1f}s\n\n")
                
                if result.errors:
                    f.write("**Errors:**\n")
                    for error in result.errors:
                        f.write(f"- {error}\n")
                    f.write("\n")
                
                if result.warnings:
                    f.write("**Warnings:**\n")
                    for warning in result.warnings:
                        f.write(f"- {warning}\n")
                    f.write("\n")
                
                f.write("---\n\n")
        
        print(f"\n✓ Summary report generated: {summary_path}")
        return summary_path
    
    def print_summary(self):
        """Print test summary to console."""
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}\n")
        
        total_tests = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total_tests - successful
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful} ✓")
        print(f"Failed: {failed} ✗")
        print(f"\n{'='*80}\n")
        
        for i, result in enumerate(self.results, 1):
            status = "✓ PASS" if result.success else "✗ FAIL"
            print(f"{i}. [{result.website}] {result.title} - {status}")
            print(f"   Chapters found: {result.chapters_found}")
            print(f"   Chapters converted: {result.chapters_converted}")
            print(f"   Duration: {result.duration:.1f}s")
            
            if result.errors:
                print(f"   Errors: {len(result.errors)}")
                for error in result.errors[:3]:  # Show first 3 errors
                    print(f"     - {error[:80]}")
                if len(result.errors) > 3:
                    print(f"     ... and {len(result.errors) - 3} more errors")
            
            print()
        
        print(f"{'='*80}\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Robustness test suite for full pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="test_config.json",
        help="Path to test configuration JSON file"
    )
    
    args = parser.parse_args()
    
    # Get config path
    config_path = Path(__file__).parent / args.config
    if not config_path.exists():
        print(f"✗ Config file not found: {config_path}")
        sys.exit(1)
    
    # Run tests
    suite = RobustnessTestSuite(config_path)
    suite.run_all_tests()
    
    # Generate summary
    summary_path = suite.generate_summary()
    
    # Print summary
    suite.print_summary()
    
    print(f"\n✓ Test suite completed!")
    print(f"✓ Summary report: {summary_path}")
    
    # Exit with error code if any tests failed
    if any(not r.success for r in suite.results):
        sys.exit(1)


if __name__ == "__main__":
    main()



