# VS Code Configuration for ACT

This folder contains VS Code workspace settings to improve your development workflow.

## Quick Setup

1. **Install Recommended Extensions**: VS Code will prompt you, or run `Ctrl+Shift+X` and search for "Recommended"

2. **Reload Window**: After installing extensions, reload VS Code (`Ctrl+Shift+P` → "Reload Window")

## Key Features

### Auto-Save & File Watching
- Files auto-save after 1 second of inactivity
- File watcher excludes cache folders for better performance

### Python & Pylance
- Uses Pylance for type checking
- Configured for Python 3.12
- Type checking mode: "basic" (good balance of checks vs performance)

### Git Integration
- Auto-fetch enabled
- Smart commit enabled
- No sync confirmation needed

### Debugging
- Launch configurations for UI and current file
- Python path automatically set

### Tasks
- `Ctrl+Shift+B` to launch UI
- Or use Command Palette (`Ctrl+Shift+P`) → "Tasks: Run Task"

## Troubleshooting

### Files Not Updating
1. **Reload Window**: `Ctrl+Shift+P` → "Developer: Reload Window"
2. **Restart Pylance**: `Ctrl+Shift+P` → "Python: Restart Language Server"
3. **Close and Reopen File**: Sometimes VS Code caches file contents

### Pylance Errors Not Clearing
1. Restart Pylance Language Server
2. Check Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Verify `pyrightconfig.json` settings

### Git Issues
- Check git status in terminal: `git status`
- VS Code git panel should auto-refresh

## Recommended Workflow

1. **Make changes** → Files auto-save
2. **Check errors** → Pylance shows inline
3. **Test** → Use debugger or tasks
4. **Commit** → Use VS Code Source Control panel

## Keyboard Shortcuts

- `Ctrl+Shift+B` - Build/Run default task (Launch UI)
- `F5` - Start debugging
- `Ctrl+Shift+P` - Command Palette
- `Ctrl+` ` - Toggle terminal
- `Ctrl+B` - Toggle sidebar

