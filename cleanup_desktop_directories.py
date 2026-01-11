#!/usr/bin/env python3
"""
Desktop Directory Cleanup Script

Moves ACT project directories from Desktop to proper locations.
This script helps clean up directories that were created on the desktop
due to the previous default output directory configuration.
"""

import shutil
import sys
from pathlib import Path

def main():
    """Main cleanup function."""
    print("🧹 ACT Desktop Directory Cleanup Tool")
    print("=" * 50)

    # Get paths
    desktop = Path.home() / "Desktop"
    act_output = Path.home() / "Documents" / "ACT" / "output"

    print(f"📂 Desktop: {desktop}")
    print(f"📂 ACT Output: {act_output}")
    print()

    # Create ACT output directory if it doesn't exist
    act_output.mkdir(parents=True, exist_ok=True)

    # Find potential ACT project directories on desktop
    # These typically have patterns like: project_name/, project_name_scraps/, project_name_audio/
    desktop_items = list(desktop.iterdir()) if desktop.exists() else []

    potential_act_dirs = []
    for item in desktop_items:
        if item.is_dir():
            # Check if it looks like an ACT project directory
            name = item.name.lower()
            if any(keyword in name for keyword in ['scraps', 'audio', 'chapter', 'novel', 'book']):
                potential_act_dirs.append(item)
            # Also check for directories that might be project names
            elif not name.startswith('.') and len(name) > 3:
                # Check if it contains typical ACT files
                if any((item / sub).exists() for sub in ['scraps', 'audio', 'chapters']):
                    potential_act_dirs.append(item)

    if not potential_act_dirs:
        print("✅ No ACT project directories found on desktop.")
        return

    print(f"📋 Found {len(potential_act_dirs)} potential ACT project directories:")
    for i, dir_path in enumerate(potential_act_dirs, 1):
        print(f"  {i}. {dir_path.name}/")
    print()

    # Ask for confirmation
    response = input("🤔 Move these directories to Documents/ACT/output/? (y/N): ").strip().lower()

    if response not in ('y', 'yes'):
        print("❌ Operation cancelled.")
        return

    # Move directories
    moved_count = 0
    for dir_path in potential_act_dirs:
        try:
            dest_path = act_output / dir_path.name
            if dest_path.exists():
                print(f"⚠️  Destination already exists: {dest_path.name}")
                overwrite = input(f"   Overwrite {dest_path.name}? (y/N): ").strip().lower()
                if overwrite not in ('y', 'yes'):
                    continue
                shutil.rmtree(dest_path)

            print(f"📦 Moving: {dir_path.name}")
            shutil.move(str(dir_path), str(act_output))
            moved_count += 1

        except Exception as e:
            print(f"❌ Error moving {dir_path.name}: {e}")

    print()
    if moved_count > 0:
        print(f"✅ Successfully moved {moved_count} directories to {act_output}")
        print("🧹 Desktop cleanup complete!")
    else:
        print("❌ No directories were moved.")

    print()
    print("💡 Future projects will be created in:")
    print(f"   {act_output}")
    print()
    print("📝 You can change this location in the UI or config if needed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)