"""
Download open-source fonts for ACT application.

This script downloads the required open-source fonts and places them
in the src/ui/fonts directory.

Run this script before packaging the application to ensure all fonts are bundled.
"""

import os
import urllib.request
import zipfile
import tempfile
from pathlib import Path

def download_file(url: str, dest_path: Path) -> bool:
    """Download a file from URL."""
    try:
        print(f"Downloading {dest_path.name}...")
        urllib.request.urlretrieve(url, dest_path)
        print(f"[OK] Downloaded {dest_path.name}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download {dest_path.name}: {e}")
        return False

def download_and_extract_zip(url: str, dest_dir: Path, font_name: str) -> bool:
    """Download a ZIP file and extract specific font files."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / f"{font_name}.zip"
            print(f"Downloading {font_name} ZIP...")
            urllib.request.urlretrieve(url, zip_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract TTF files
                for member in zip_ref.namelist():
                    if member.endswith('.ttf') and ('Regular' in member or 'Bold' in member):
                        # Extract to fonts directory
                        content = zip_ref.read(member)
                        filename = Path(member).name
                        dest_path = dest_dir / filename
                        dest_path.write_bytes(content)
                        print(f"[OK] Extracted {filename}")
            return True
    except Exception as e:
        print(f"[ERROR] Failed to download/extract {font_name}: {e}")
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
    
    # Roboto - use Google Fonts CDN
    print("\nProcessing Roboto (Apache 2.0)...")
    roboto_regular = fonts_dir / "Roboto-Regular.ttf"
    roboto_bold = fonts_dir / "Roboto-Bold.ttf"
    
    if not roboto_regular.exists():
        # Use Google Fonts API
        url = 'https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap'
        # Actually, let's use a direct download from a reliable source
        if download_file('https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf', roboto_regular):
            downloaded += 1
    else:
        print(f"  [SKIP] {roboto_regular.name} already exists")
        skipped += 1
    
    if not roboto_bold.exists():
        if download_file('https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf', roboto_bold):
            downloaded += 1
    else:
        print(f"  [SKIP] {roboto_bold.name} already exists")
        skipped += 1
    
    # Inter - download from releases
    print("\nProcessing Inter (SIL Open Font License 1.1)...")
    inter_regular = fonts_dir / "Inter-Regular.ttf"
    inter_bold = fonts_dir / "Inter-Bold.ttf"
    
    if not inter_regular.exists() or not inter_bold.exists():
        # Download from GitHub releases
        zip_url = 'https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip'
        if download_and_extract_zip(zip_url, fonts_dir, 'Inter'):
            downloaded += 2
    else:
        print(f"  [SKIP] Inter fonts already exist")
        skipped += 2
    
    # Source Sans 3 - already downloaded, just check
    print("\nProcessing Source Sans 3 (SIL Open Font License 1.1)...")
    source_regular = fonts_dir / "SourceSans3-Regular.otf"
    source_bold = fonts_dir / "SourceSans3-Bold.otf"
    
    if source_regular.exists() and source_bold.exists():
        print(f"  [SKIP] Source Sans 3 fonts already exist")
        skipped += 2
    else:
        if not source_regular.exists():
            if download_file('https://raw.githubusercontent.com/adobe-fonts/source-sans/3.052R/OTF/SourceSans3-Regular.otf', source_regular):
                downloaded += 1
        if not source_bold.exists():
            if download_file('https://raw.githubusercontent.com/adobe-fonts/source-sans/3.052R/OTF/SourceSans3-Bold.otf', source_bold):
                downloaded += 1
    
    print("\n" + "=" * 60)
    print(f"Download complete!")
    print(f"  Downloaded: {downloaded} files")
    print(f"  Skipped: {skipped} files (already exist)")
    print("=" * 60)
    print("\nNote: Fonts are now ready to be bundled with your application.")
    print("Qt will load them automatically when the application starts.")

if __name__ == "__main__":
    main()


