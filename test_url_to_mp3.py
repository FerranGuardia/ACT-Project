#!/usr/bin/env python
"""Test URL TO MP3 card icon loading."""
import sys
from pathlib import Path

sys.path.insert(0, 'src')

from ui.landing_page_components import CardIcon
from ui.landing_page_modes import MODES_CONFIG
from PySide6.QtWidgets import QApplication

app = QApplication([])

# Check landing page config
print("\n" + "="*60)
print("Checking Landing Page Modes")
print("="*60)
for mode in MODES_CONFIG:
    print(f"ID: {mode.id:12} | Title: {mode.title:20} | Icon: {mode.icon}")

# Test URL TO MP3 icon loading
print("\n" + "="*60)
print("Testing URL TO MP3 Card Icon")
print("="*60)

icon = CardIcon('⚡')
images_path = Path('src/ui/images')
print(f"\nImages folder: {images_path.absolute()}")
print(f"Files in folder:")
for img in sorted(images_path.glob("*.png")):
    print(f"  - {img.name}")

# Manual check
url_to_mp3_path = images_path / "url to mp3.png"
print(f"\nDirect path check: {url_to_mp3_path.absolute()}")
print(f"Exists: {url_to_mp3_path.exists()}")

# Check CardIcon result
has_image = icon.pixmap() is not None and not icon.pixmap().isNull()
print(f"\nCardIcon result:")
print(f"✓ Image loaded" if has_image else "~ Using emoji fallback")

if has_image:
    print(f"✓ URL TO MP3 card is now displaying the graphic!")
else:
    print(f"Note: Still using emoji, checking why...")
    # Debug the find_image_path method
    found_path = icon._find_image_path()
    print(f"Found path: {found_path}")
