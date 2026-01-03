# Fonts Directory

This directory contains open-source fonts bundled with the ACT application.

## Fonts Included

### Roboto (Apache 2.0 License)
- **Regular**: `Roboto-Regular.ttf`
- **Bold**: `Roboto-Bold.ttf`
- **Used by**: Material Dark theme
- **License**: Apache License 2.0
- **Source**: https://github.com/googlefonts/roboto

### Inter (SIL Open Font License 1.1)
- **Regular**: `Inter-Regular.ttf`
- **Bold**: `Inter-Bold.ttf`
- **Used by**: Discord Dark theme (replaces Whitney), GitHub Dark theme
- **License**: SIL Open Font License 1.1
- **Source**: https://github.com/rsms/inter

### Source Sans 3 (SIL Open Font License 1.1)
- **Regular**: `SourceSans3-Regular.otf`
- **Bold**: `SourceSans3-Bold.otf`
- **Used by**: Available as alternative option
- **License**: SIL Open Font License 1.1
- **Source**: https://github.com/adobe-fonts/source-sans

### Segoe UI (Microsoft - System Font)
- **Regular**: `segoeui.ttf`
- **Bold**: `segoeuib.ttf`
- **Used by**: Default themes (as fallback)
- **Note**: Segoe UI is a system font on Windows. These files are included for consistency but the application will use the system font if available.

## Downloading Fonts

To download/update fonts, run:

```bash
python scripts/download_fonts_v2.py
```

This script will:
1. Download all required open-source fonts
2. Place them in this directory
3. Ensure fonts are ready for bundling

## Font Loading

Fonts are automatically loaded when the application starts via `QFontDatabase.addApplicationFont()` in `main_window.py`. The application will use these bundled fonts, ensuring consistent appearance across all platforms.

## Licensing

All fonts in this directory are either:
- **Open-source** (Apache 2.0 or SIL OFL) - safe to redistribute
- **System fonts** (Segoe UI) - referenced but not redistributed

You can safely bundle these fonts with your application distribution.




