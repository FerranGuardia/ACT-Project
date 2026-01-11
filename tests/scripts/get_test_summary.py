"""
Helper script to parse pytest output and display test summary.
Can read from a file or run pytest directly.
"""
import sys
import subprocess
import re
import os
from pathlib import Path

def parse_pytest_output_from_file(file_path):
    """Parse pytest output from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            output = f.read()
    except Exception:
        return None
    
    return parse_output(output)

def parse_output(output):
    """Parse pytest output string to get test counts."""
    # Try to get summary from pytest's final summary line (most reliable)
    # Format: "X passed, Y failed, Z skipped in W.XXs" or variations
    summary_patterns = [
        r'(\d+) passed.*?(\d+) failed.*?(\d+) skipped',
        r'(\d+) passed.*?(\d+) skipped.*?(\d+) failed',
        r'(\d+) passed.*?(\d+) failed',
        r'(\d+) passed.*?(\d+) skipped',
        r'(\d+) passed',
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    error = 0
    
    for pattern in summary_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) >= 1:
                passed = int(groups[0])
            if len(groups) >= 2:
                # Determine which is which based on context
                match_text = match.group(0).lower()
                if 'failed' in match_text:
                    failed = int(groups[1])
                elif 'skipped' in match_text:
                    skipped = int(groups[1])
            if len(groups) >= 3:
                # Three groups - need to figure out order
                match_text = match.group(0).lower()
                if 'failed' in match_text and 'skipped' in match_text:
                    # Find positions
                    failed_idx = match_text.find('failed')
                    skipped_idx = match_text.find('skipped')
                    if failed_idx < skipped_idx:
                        failed = int(groups[1])
                        skipped = int(groups[2])
                    else:
                        skipped = int(groups[1])
                        failed = int(groups[2])
            break
    
    # Fallback: count individual test results if summary not found
    if passed == 0 and failed == 0 and skipped == 0:
        passed = len(re.findall(r' PASSED', output))
        failed = len(re.findall(r' FAILED', output))
        skipped = len(re.findall(r' SKIPPED', output))
        error = len(re.findall(r' ERROR', output))
    
    return passed, failed, skipped, error

if __name__ == '__main__':
    # Check if file path provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = parse_pytest_output_from_file(file_path)
    else:
        # Check for temp file from batch script
        temp_file = os.path.join(os.environ.get('TEMP', ''), 'pytest_output.txt')
        if os.path.exists(temp_file):
            result = parse_pytest_output_from_file(temp_file)
        else:
            # Run pytest directly
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
            pytest_result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/unit/', '-v', '--tb=no', '-q'],
                capture_output=True,
                text=True,
                cwd=str(project_root)
            )
            result = parse_output(pytest_result.stdout + pytest_result.stderr)
    
    if result:
        passed, failed, skipped, error = result
        
        # Display summary
        parts = []
        if passed > 0:
            parts.append(f"{passed} passed")
        if skipped > 0:
            parts.append(f"{skipped} skipped")
        if failed > 0:
            parts.append(f"{failed} failed")
        if error > 0:
            parts.append(f"{error} error(s)")
        
        if parts:
            print(f"\nUnit Tests: {', '.join(parts)}")
        else:
            print("\nUnit Tests: No tests found")
    else:
        print("\nUnit Tests: Could not parse test results")

