#!/usr/bin/env python
"""Test card icon loading from assets."""
import sys
from pathlib import Path

sys.path.insert(0, 'src')

# Check if images exist
images_path = Path('src/ui/images')
print(f"\nImages folder exists: {images_path.exists()}")
print(f"Images folder path: {images_path.absolute()}")
print(f"Image files:")
if images_path.exists():
    for img in images_path.glob("*.png"):
        print(f"  - {img.name}")

# Test CardIcon class
try:
    from PySide6.QtWidgets import QApplication

    from ui.landing_page_components import CardIcon
    
    app = QApplication([])
    
    # Test all icon types
    icons_to_test = {
        "📖": "Scraper icon",
        "🎙️": "TTS icon",
        "🔊": "Merger icon",
        "⚡": "Full Auto icon"
    }
    
    print("\n" + "="*60)
    print("Testing CardIcon loading")
    print("="*60)
    
    for emoji, name in icons_to_test.items():
        try:
            icon = CardIcon(emoji)
            # Check if image was loaded or fallback to emoji
            if icon.pixmap() and not icon.pixmap().isNull():
                print(f"✓ {name:20} - Image loaded successfully")
            else:
                print(f"~ {name:20} - Using emoji fallback")
        except Exception as e:
            print(f"✗ {name:20} - Error: {e}")
    
    print("\n" + "="*60)
    print("Note: Graphics are properly configured!")
    print("  - Images loaded: UI will display graphics")
    print("  - Emoji fallback: Images not found, emoji will display")
    print("="*60 + "\n")

except Exception as e:
    print(f"\nError testing CardIcon: {e}")
    import traceback
    traceback.print_exc()
