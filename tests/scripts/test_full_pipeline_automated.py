"""
Automated Full Pipeline Test

Tests the complete workflow: URL → Scraping → TTS → Audio Files
with multiple URLs automatically.

Usage:
    python test_full_pipeline_automated.py
    python test_full_pipeline_automated.py --quick  # Test only first 2 chapters
    python test_full_pipeline_automated.py --url "https://..."  # Test specific URL
"""

import sys
import os
import argparse
import time
from pathlib import Path
from typing import List, Dict, Optional

# Add ACT project to path
# Script is at: ACT REFERENCES/TESTS/TEST_SCRIPTS/test_full_pipeline_automated.py
# ACT project is at: Desktop/ACT/src (src/ is the root for imports)
script_dir = Path(__file__).parent.absolute()
# Go up: TEST_SCRIPTS -> TESTS -> ACT REFERENCES -> Desktop -> ACT
act_path = script_dir.parent.parent.parent.parent / "ACT"
act_src_path = act_path / "src"

# Also try direct path
if not act_path.exists():
    act_path = Path.home() / "Desktop" / "ACT"
    act_src_path = act_path / "src"

print(f"Looking for ACT project at: {act_path}")
print(f"Looking for ACT src directory at: {act_src_path}")

if act_src_path.exists():
    # Add src/ directory to path (this is where all imports are relative to)
    sys.path.insert(0, str(act_src_path))
    print(f"✓ Added ACT src directory to path: {act_src_path}")
else:
    print(f"✗ ACT src directory not found at: {act_src_path}")
    print(f"Please ensure ACT project is at: {Path.home() / 'Desktop' / 'ACT'}")
    print(f"Expected structure: {act_src_path} should exist")

try:
    from src.processor.pipeline import ProcessingPipeline  # type: ignore
    from src.processor.progress_tracker import ProcessingStatus  # type: ignore
    from src.core.logger import get_logger  # type: ignore
    print("✓ Successfully imported ACT modules")
except ImportError as e:
    print(f"\n✗ Error importing ACT modules: {e}")
    print(f"Make sure ACT project is at: {act_path}")
    print(f"Current Python path: {sys.path[:3]}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")
    sys.exit(1)

logger = get_logger("test.full_pipeline")


# Test URLs with expected chapter counts
TEST_URLS = [
    {
        "url": "https://novelfull.net/bringing-culture-to-a-different-world.html",
        "title": "Bringing culture to a different world",
        "expected_chapters": 1098,
        "voice": "en-US-AndrewNeural",  # Use reliable voice for testing
        "test_chapters": 5  # Only test first 5 chapters for speed
    },
    {
        "url": "https://novelfull.net/overgeared.html",
        "title": "Overgeared",
        "expected_chapters": 2059,
        "voice": "en-US-AndrewNeural",
        "test_chapters": 3
    },
    {
        "url": "https://novelfull.net/the-second-coming-of-gluttony.html",
        "title": "The Second Coming of Gluttony",
        "expected_chapters": 500,
        "voice": "en-US-AndrewNeural",
        "test_chapters": 3
    }
]


class PipelineTestResult:
    """Stores test results for a single URL."""
    
    def __init__(self, url: str, title: str):
        self.url = url
        self.title = title
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


class FullPipelineTester:
    """Automated tester for full pipeline workflow."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path.home() / "Desktop" / "ACT_TEST_OUTPUT"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[PipelineTestResult] = []
        
    def test_url(
        self,
        url: str,
        title: str,
        voice: str = "en-US-AndrewNeural",
        max_chapters: Optional[int] = None,
        quick_mode: bool = False
    ) -> PipelineTestResult:
        """
        Test full pipeline for a single URL.
        
        Args:
            url: Novel URL to test
            title: Novel title
            voice: Voice to use for TTS
            max_chapters: Maximum chapters to process (None = all)
            quick_mode: If True, only test first 2 chapters
            
        Returns:
            PipelineTestResult with test results
        """
        result = PipelineTestResult(url, title)
        start_time = time.time()
        
        # Create project name from title
        project_name = title.lower().replace(" ", "_").replace("-", "_")
        project_name = "".join(c for c in project_name if c.isalnum() or c == "_")
        
        print(f"\n{'='*80}")
        print(f"Testing: {title}")
        print(f"URL: {url}")
        print(f"Voice: {voice}")
        print(f"{'='*80}\n")
        
        try:
            # Create pipeline
            pipeline = ProcessingPipeline(
                project_name=project_name,
                base_output_dir=self.output_dir,
                voice=voice,
                novel_title=title
            )
            
            # Track progress
            chapter_statuses = {}
            
            def on_chapter_update(chapter_num: int, status_str: str, message: str):
                # Convert string status back to enum for comparison
                try:
                    status = ProcessingStatus(status_str)
                except ValueError:
                    status = ProcessingStatus.PENDING
                
                chapter_statuses[chapter_num] = (status, message)
                if status == ProcessingStatus.SCRAPED:
                    result.chapters_scraped += 1
                elif status == ProcessingStatus.COMPLETED:
                    result.chapters_converted += 1
                elif status == ProcessingStatus.FAILED:
                    result.chapters_failed += 1
                    result.errors.append(f"Chapter {chapter_num}: {message}")
            
            pipeline.on_chapter_update = on_chapter_update  # type: ignore[assignment]
            
            # Run full pipeline
            print(f"Starting pipeline for {title}...")
            pipeline_result = pipeline.run_full_pipeline(
                toc_url=url,
                novel_title=title
            )
            
            if not pipeline_result.get("success"):
                result.errors.append(f"Pipeline failed: {pipeline_result.get('error', 'Unknown error')}")
                result.duration = time.time() - start_time
                return result
            
            # Get chapter count
            chapter_manager = pipeline.project_manager.get_chapter_manager()
            if chapter_manager is None:
                result.errors.append("Chapter manager is None")
                result.duration = time.time() - start_time
                return result
            all_chapters = chapter_manager.get_all_chapters()
            result.chapters_found = len(all_chapters)
            
            print(f"✓ Found {result.chapters_found} chapters")
            
            # Determine which chapters to process
            if quick_mode:
                chapters_to_process = all_chapters[:2]
                print(f"Quick mode: Processing only first 2 chapters")
            elif max_chapters:
                chapters_to_process = all_chapters[:max_chapters]
                print(f"Processing first {max_chapters} chapters")
            else:
                chapters_to_process = all_chapters
                print(f"Processing all {len(chapters_to_process)} chapters")
            
            # Process chapters
            print(f"\nProcessing {len(chapters_to_process)} chapters...")
            processed = 0
            for chapter in chapters_to_process:
                if pipeline._check_should_stop():
                    break
                    
                print(f"Processing chapter {chapter.number}...", end=" ", flush=True)
                success = pipeline.process_chapter(chapter, skip_if_exists=False)
                
                if success:
                    processed += 1
                    print("✓")
                else:
                    print("✗")
                    result.errors.append(f"Chapter {chapter.number} failed")
            
            # Count files created
            file_manager = pipeline.file_manager
            text_dir = file_manager.get_text_dir()
            audio_dir = file_manager.get_audio_dir()
            
            if text_dir.exists():
                result.text_files_created = len(list(text_dir.glob("*.txt")))
            if audio_dir.exists():
                result.audio_files_created = len(list(audio_dir.glob("*.mp3")))
            
            # Check results
            if result.chapters_converted > 0:
                result.success = True
                print(f"\n✓ Successfully converted {result.chapters_converted} chapters to audio")
            else:
                result.warnings.append("No chapters were successfully converted to audio")
            
            result.duration = time.time() - start_time
            
            # Cleanup - clear project data
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
        
        return result
    
    def run_all_tests(self, quick_mode: bool = False) -> List[PipelineTestResult]:
        """Run tests for all URLs."""
        print(f"\n{'='*80}")
        print(f"FULL PIPELINE AUTOMATED TEST")
        print(f"Output directory: {self.output_dir}")
        print(f"Quick mode: {quick_mode}")
        print(f"{'='*80}\n")
        
        for test_config in TEST_URLS:
            result = self.test_url(
                url=test_config["url"],
                title=test_config["title"],
                voice=test_config["voice"],
                max_chapters=test_config.get("test_chapters"),
                quick_mode=quick_mode
            )
            self.results.append(result)
            
            # Small delay between tests
            time.sleep(2)
        
        return self.results
    
    def print_summary(self):
        """Print test summary."""
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
            print(f"{i}. {result.title} - {status}")
            print(f"   URL: {result.url}")
            print(f"   Chapters found: {result.chapters_found}")
            print(f"   Chapters scraped: {result.chapters_scraped}")
            print(f"   Chapters converted: {result.chapters_converted}")
            print(f"   Chapters failed: {result.chapters_failed}")
            print(f"   Text files: {result.text_files_created}")
            print(f"   Audio files: {result.audio_files_created}")
            print(f"   Duration: {result.duration:.1f}s")
            
            if result.errors:
                print(f"   Errors:")
                for error in result.errors[:5]:  # Show first 5 errors
                    print(f"     - {error}")
                if len(result.errors) > 5:
                    print(f"     ... and {len(result.errors) - 5} more errors")
            
            if result.warnings:
                print(f"   Warnings:")
                for warning in result.warnings:
                    print(f"     - {warning}")
            
            print()
        
        print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Automated full pipeline test")
    parser.add_argument("--quick", action="store_true", help="Quick mode: test only 2 chapters per URL")
    parser.add_argument("--url", type=str, help="Test specific URL (overrides default URLs)")
    parser.add_argument("--title", type=str, help="Title for custom URL")
    parser.add_argument("--voice", type=str, default="en-US-AndrewNeural", help="Voice to use")
    parser.add_argument("--output", type=str, help="Output directory for test files")
    parser.add_argument("--chapters", type=int, help="Maximum chapters to process")
    
    args = parser.parse_args()
    
    tester = FullPipelineTester(
        output_dir=Path(args.output) if args.output else None
    )
    
    if args.url:
        # Test single URL
        result = tester.test_url(
            url=args.url,
            title=args.title or "Test Novel",
            voice=args.voice,
            max_chapters=args.chapters,
            quick_mode=args.quick
        )
        tester.results.append(result)
    else:
        # Test all URLs
        tester.run_all_tests(quick_mode=args.quick)
    
    tester.print_summary()
    
    # Exit with error code if any tests failed
    if any(not r.success for r in tester.results):
        sys.exit(1)


if __name__ == "__main__":
    main()




