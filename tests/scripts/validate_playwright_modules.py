"""
Simple validation script to verify Playwright modules load correctly.

This script checks that:
1. All module files exist
2. Files can be read and contain expected functions
3. Module dependencies are satisfied
"""

import sys
from pathlib import Path

def validate_modules():
    """Validate that all Playwright modules exist and can be loaded."""
    project_root = Path(__file__).parent.parent.parent
    script_dir = project_root / "src" / "scraper" / "playwright_scripts"
    
    required_modules = [
        "chapter_detector.js",
        "link_counter.js",
        "load_more_handler.js",
        "container_finder.js",
        "scroll_operations.js",
        "scroll_loop.js",
        "main.js",
    ]
    
    print("Validating Playwright modules...")
    print(f"Script directory: {script_dir}\n")
    
    # Check all modules exist
    missing_modules = []
    for module in required_modules:
        module_path = script_dir / module
        if module_path.exists():
            line_count = len(module_path.read_text(encoding="utf-8").splitlines())
            print(f"[OK] {module}: {line_count} lines")
        else:
            print(f"[FAIL] {module}: MISSING")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n[ERROR] Missing modules: {', '.join(missing_modules)}")
        return False
    
    # Validate module contents
    print("\nValidating module contents...")
    
    # Check for key functions in each module
    module_checks = {
        "chapter_detector.js": ["isChapterLink"],
        "link_counter.js": ["countChapterLinks", "getChapterLinks"],
        "load_more_handler.js": ["tryClickLoadMore", "matchesLoadMoreText"],
        "container_finder.js": ["findChapterContainer"],
        "scroll_operations.js": ["scrollContainer", "scrollContainerToBottom", "scrollToLastChapter", "scrollPastLastChapter"],
        "scroll_loop.js": ["performScrollLoop", "SCROLL_CONFIG"],
        "main.js": ["scrollAndCountChapters"],
    }
    
    all_functions_found = True
    for module, functions in module_checks.items():
        module_path = script_dir / module
        content = module_path.read_text(encoding="utf-8")
        
        for func in functions:
            if func in content:
                print(f"[OK] {module}: Function '{func}' found")
            else:
                print(f"[FAIL] {module}: Function '{func}' MISSING")
                all_functions_found = False
    
    if not all_functions_found:
        print("\n[ERROR] Some required functions are missing")
        return False
    
    # Try to simulate bundling (read all files)
    print("\nSimulating module bundling...")
    try:
        bundled_parts = []
        for module in required_modules:
            module_path = script_dir / module
            content = module_path.read_text(encoding="utf-8")
            bundled_parts.append(content)
        
        bundled_script = "\n\n".join(bundled_parts)
        script_length = len(bundled_script.splitlines())
        print(f"[OK] Bundled script would be: {script_length} lines")
        
        # Check that main entry point exists
        if "scrollAndCountChapters" in bundled_script:
            print("[OK] Main entry point 'scrollAndCountChapters' found")
        else:
            print("[FAIL] Main entry point 'scrollAndCountChapters' MISSING")
            return False
        
        print("\n[SUCCESS] All validations passed!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error bundling modules: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_modules()
    sys.exit(0 if success else 1)

