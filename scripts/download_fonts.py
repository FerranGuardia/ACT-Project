"""
Download open-source fonts for ACT application.

This script downloads the required open-source fonts and places them
in the src/ui/fonts directory.

Run this script before packaging the application to ensure all fonts are bundled.
"""

import os
import urllib.request
from pathlib import Path

# Font URLs - using reliable GitHub raw content URLs
FONTS = {
    'Roboto': {
        'regular': 'https://raw.githubusercontent.com/google/fonts/main/apache/roboto/Roboto%5Bwdth%2Cwght%5D.ttf',
        'bold': 'https://raw.githubusercontent.com/google/fonts/main/apache/roboto/Roboto%5Bwdth%2Cwght%5D.ttf',
        'license': 'Apache 2.0',
        'note': 'Variable font - contains all weights'
    },
    'Inter': {
        'regular': 'https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip',
        'bold': 'https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip',
        'license': 'SIL Open Font License 1.1',
        'note': 'Download as ZIP, extract TTF files'
    },
    'SourceSans3': {
        'regular': 'https://raw.githubusercontent.com/adobe-fonts/source-sans/3.052R/OTF/SourceSans3-Regular.otf',
        'bold': 'https://raw.githubusercontent.com/adobe-fonts/source-sans/3.052R/OTF/SourceSans3-Bold.otf',
        'license': 'SIL Open Font License 1.1',
        'note': 'OTF format - Qt supports it'
    }
}

def download_font(url: str, dest_path: Path) -> bool:
    """Download a font file from URL."""
    try:
        print(f"Downloading {dest_path.name}...")
        urllib.request.urlretrieve(url, dest_path)
        print(f"[OK] Downloaded {dest_path.name}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download {dest_path.name}: {e}")
        return False

def main():
    """Download all required fonts."""
    # Get fonts directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    fonts_dir = project_root / "src" / "ui" / "fonts"
    
    # Create fonts directory if it doesn't exist
    fonts_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("ACT Font Downloader")
    print("=" * 60)
    print(f"Fonts directory: {fonts_dir}")
    print()
    
    downloaded = 0
    skipped = 0
    
    for font_name, font_info in FONTS.items():
        print(f"\nProcessing {font_name} ({font_info['license']})...")
        
        # Regular weight
        regular_path = fonts_dir / f"{font_name}-Regular.ttf"
        if regular_path.exists():
            print(f"  [SKIP] {regular_path.name} already exists")
            skipped += 1
        else:
            if download_font(font_info['regular'], regular_path):
                downloaded += 1
        
        # Bold weight
        bold_path = fonts_dir / f"{font_name}-Bold.ttf"
        if bold_path.exists():
            print(f"  [SKIP] {bold_path.name} already exists")
            skipped += 1
        else:
            if download_font(font_info['bold'], bold_path):
                downloaded += 1
    
    print("\n" + "=" * 60)
    print(f"Download complete!")
    print(f"  Downloaded: {downloaded} files")
    print(f"  Skipped: {skipped} files (already exist)")
    print("=" * 60)

if __name__ == "__main__":
    main()

