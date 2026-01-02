# Theme System Implementation

## Overview

A modular theme system has been implemented for the ACT UI. Each theme is stored in its own file, making it easy to add, remove, or modify themes.

## Structure

```
src/ui/themes/
├── __init__.py          # Theme loader and manager
├── README.md            # Documentation for theme files
├── dark_default.py      # Default dark theme
├── dark_material.py     # Material Design theme
├── dark_discord.py      # Discord-inspired theme
├── dark_github.py      # GitHub dark theme
├── dark_blue.py        # Blue dark theme
└── light_default.py    # Light theme (experimental)
```

## Features

✅ **Modular Design** - Each theme in its own file  
✅ **Easy Management** - Add/remove themes by adding/deleting files  
✅ **Live Preview** - See changes immediately  
✅ **Non-Modal Dialog** - Keep dialog open while testing  
✅ **Auto-Discovery** - Themes are automatically discovered  
✅ **Hot Reload** - Reload themes without restarting app  

## Usage

### Accessing Theme Menu

1. Launch the application
2. Click **View** → **🎨 Themes...**
3. Theme dialog opens

### Selecting a Theme

1. Click on a theme in the list to preview it
2. Changes apply immediately to the UI
3. Double-click or click "Apply Theme" to make it permanent
4. Click "Reset to Default" to restore default theme

### Adding a New Theme

1. Create a new file: `src/ui/themes/your_theme_name.py`
2. Copy structure from `dark_default.py`
3. Modify colors
4. Theme appears automatically in the selector!

### Removing a Theme

Simply delete the theme file. It will no longer appear.

### Modifying a Theme

Edit the theme file, then click "Reload Themes" in the dialog.

## Implementation Details

### Theme Files

Each theme file exports a `THEME` dictionary:

```python
THEME = {
    'name': 'Display Name',
    'description': 'Description',
    'author': 'Author (optional)',
    'bg_dark': 'rgb(...)',
    # ... all color values
}
```

### Theme Loader (`__init__.py`)

- Discovers all `.py` files in themes directory
- Dynamically imports theme modules
- Caches themes for performance
- Provides API for theme management

### Style System (`styles.py`)

- `COLORS` is now a dynamic dict that reads from current theme
- All style functions automatically use current theme colors
- No code changes needed in existing widgets

### Theme Dialog (`dialogs/theme_selection_dialog.py`)

- Lists all available themes
- Shows theme preview
- Allows live preview
- Applies themes immediately

### Main Window Integration

- Menu bar: View → Themes...
- Theme changes propagate to all widgets
- Dialog stays open for easy testing

## Current Themes

1. **Dark Default** - Original theme (default)
2. **Material Dark** - Google Material Design
3. **Discord Dark** - Discord-inspired
4. **GitHub Dark** - GitHub dark theme
5. **Dark Blue** - Deep blue theme
6. **Light Mode** - Light theme (experimental)

## Testing

To test the theme system:

```bash
# Run the application
python launch_ui.py

# Or from src directory
python -m src.main
```

Then:
1. Go to View → Themes...
2. Try different themes
3. See changes apply immediately
4. Test adding a new theme file

## Future Enhancements

- [ ] Save selected theme to config file
- [ ] Theme persistence across sessions
- [ ] Custom theme editor
- [ ] Export/import themes
- [ ] Theme preview screenshots

## Notes

- Themes are loaded dynamically, so you can add/remove them without code changes
- The `COLORS` dict in `styles.py` is now dynamic and always reflects the current theme
- All existing widgets automatically use the current theme colors
- Theme changes apply immediately without restarting the application


