# Theme System

Modular theme system for ACT UI. Each theme is defined in its own Python file for easy management.

## Structure

Each theme file (`*.py`) in this directory should define a `THEME` dictionary with the following structure:

```python
THEME = {
    'name': 'Theme Display Name',
    'description': 'Brief description of the theme',
    'author': 'Author name (optional)',
    # Font settings
    'font_family': 'Segoe UI',              # Font family (comma-separated for fallbacks)
    'font_size_base': '10pt',              # Base font size
    'font_size_large': '12pt',              # Large font size (headings, group boxes)
    'font_size_small': '9pt',              # Small font size
    # Colors
    'bg_dark': 'rgb(27, 29, 35)',           # Main background
    'bg_medium': 'rgb(39, 44, 54)',         # Secondary background
    'bg_light': 'rgb(44, 49, 60)',          # Light background
    'bg_lighter': 'rgb(52, 59, 72)',        # Lighter background
    'bg_hover': 'rgb(33, 37, 43)',          # Hover state background
    'bg_content': 'rgb(40, 44, 52)',        # Content area background
    'text_primary': 'rgb(210, 210, 210)',   # Primary text color
    'text_secondary': 'rgb(98, 103, 111)',  # Secondary text color
    'accent': 'rgb(85, 170, 255)',          # Accent color
    'accent_hover': 'rgb(105, 180, 255)',   # Accent hover color
    'accent_pressed': 'rgb(65, 130, 195)',  # Accent pressed color
    'border': 'rgb(64, 71, 88)',            # Border color
    'border_focus': 'rgb(91, 101, 124)',    # Focused border color
}
```

## Adding a New Theme

1. Create a new file: `your_theme_name.py`
2. Copy the structure from an existing theme (e.g., `dark_default.py`)
3. Modify the color values
4. Update the `name` and `description` fields
5. The theme will automatically appear in the theme selector!

Example:
```python
# src/ui/themes/my_custom_theme.py
THEME = {
    'name': 'My Custom Theme',
    'description': 'A custom theme I created',
    'author': 'Your Name',
    'bg_dark': 'rgb(20, 20, 20)',
    # ... rest of colors
}
```

## Removing a Theme

Simply delete the theme file. The theme will no longer appear in the selector.

## Modifying a Theme

Edit the theme file directly. Changes will take effect after:
- Closing and reopening the theme dialog, OR
- Clicking "Reload Themes" in the theme dialog

## Current Themes

- **dark_default** - Original dark theme (default)
- **dark_material** - Google Material Design dark theme
- **dark_discord** - Discord-inspired dark theme
- **dark_github** - GitHub dark theme
- **dark_blue** - Deep blue dark theme
- **light_default** - Light theme (experimental)

## Font Settings

Each theme can define its own font settings:

- **font_family**: Font family name(s). Use comma-separated list for fallbacks (e.g., `'Roboto, Segoe UI'`)
- **font_size_base**: Base font size for most UI elements (default: `'10pt'`)
- **font_size_large**: Larger font size for headings, group boxes (default: `'12pt'`)
- **font_size_small**: Smaller font size for secondary text (default: `'9pt'`)

### Font Family Examples

- `'Segoe UI'` - Windows default
- `'Roboto, Segoe UI'` - Material Design font with fallback
- `'Whitney, Segoe UI'` - Discord font with fallback
- `'-apple-system, BlinkMacSystemFont, Segoe UI'` - System fonts

## Color Guidelines

### Background Colors
- `bg_dark`: Main window background (darkest)
- `bg_medium`: Secondary surfaces (cards, panels)
- `bg_light`: Elevated surfaces
- `bg_lighter`: Hover states, highlights
- `bg_hover`: Hover background
- `bg_content`: Content area background

### Text Colors
- `text_primary`: Main text (high contrast)
- `text_secondary`: Secondary text (lower contrast)

### Accent Colors
- `accent`: Primary accent color (buttons, links)
- `accent_hover`: Accent hover state
- `accent_pressed`: Accent pressed state

### Border Colors
- `border`: Standard borders
- `border_focus`: Focused input borders

## Tips

1. **Contrast**: Ensure text colors have sufficient contrast against backgrounds
2. **Consistency**: Keep accent colors consistent across states
3. **Testing**: Test themes in the theme dialog before finalizing
4. **Accessibility**: Consider colorblind users when choosing colors
5. **RGB Format**: Always use `rgb(r, g, b)` format for colors

## Theme File Naming

Theme files should use lowercase with underscores:
- ✅ `dark_default.py`
- ✅ `my_custom_theme.py`
- ❌ `DarkDefault.py` (will work but inconsistent)
- ❌ `my-theme.py` (hyphens not recommended)

The filename (without `.py`) becomes the theme ID used internally.

