# Application Launcher (应用启动器) - Claude Context Guide

## Project Overview

This is a **cross-platform application launcher** written in Python with PyQt5, designed to organize and quickly launch applications, files, and websites. The application supports Windows, macOS, and Linux with platform-specific optimizations and features.

## Technology Stack

### Core Technologies
- **Language**: Python 3.6+
- **GUI Framework**: PyQt5
- **Architecture**: Desktop application with system tray integration
- **Platform Support**: Windows, macOS, Linux

### Key Dependencies
- **PyQt5**: Main GUI framework
- **pystray**: System tray icon support
- **keyboard**: Global hotkey functionality
- **requests**: HTTP requests for sync services
- **psutil**: System utilities
- **pyinstaller**: Executable building
- **pyobjc**: macOS-specific features (global hotkeys, app integration)
- **python-xlib**: Linux-specific features

### Additional Tools
- **beautifulsoup4**: Web scraping capabilities
- **selenium**: Web automation
- **customtkinter**: Alternative UI components
- **pillow**: Image processing

## Architecture Overview

### Main Components

1. **Entry Points**:
   - `main.py`: GUI application launcher
   - `cli.py`: Command-line interface
   - `launch_gui.py`: Alternative GUI launcher
   - `launch.sh`: Cross-platform shell launcher script

2. **GUI Package** (`gui/`):
   - `main_window.py`: Primary application window
   - `category_tab.py`: Category-based organization
   - `launch_item.py`: Individual launch items
   - `flow_layout.py`: Custom layout manager
   - `hotkey_manager_*.py`: Platform-specific global hotkey support
   - `*_dialog.py`: Various configuration dialogs

3. **Utilities Package** (`utils/`):
   - `config_manager.py`: Configuration file management
   - `app_launcher.py`: Application launching logic
   - `platform_settings.py`: Platform-specific UI and behavior
   - `gist_manager.py`: GitHub Gist synchronization
   - `webdav_manager.py`: WebDAV synchronization
   - `logger.py`: Logging system
   - `os_utils.py`: Operating system utilities

### Configuration System

- **Main Config**: `config.json` - stores all application settings and launch items
- **Config History**: `config_history/` - automatic configuration backups
- **Sync Support**: Multiple synchronization methods (GitHub Gist, WebDAV, Open Gist)

## Key Features

### Application Organization
- **Categories**: Organize applications into custom categories
- **Launch Items**: Each item can launch multiple applications/URLs simultaneously
- **Search**: Quick search functionality with keyboard navigation
- **Flexible Configuration**: JSON-based configuration with visual editing

### Platform Integration
- **System Tray**: Background operation with tray icon
- **Global Hotkeys**: System-wide keyboard shortcuts (platform-specific)
- **Native Look**: Platform-specific UI styling and behavior
- **Auto-launch**: Automatic startup options

### Synchronization
- **GitHub Gist**: Sync configurations via GitHub Gists
- **WebDAV**: Sync via WebDAV servers (Seafile, Nextcloud, etc.)
- **Open Gist**: Alternative gist service support
- **Auto-sync**: Automatic synchronization on startup/shutdown

### Multi-App Launching
- **Batch Launch**: Launch multiple applications with one click
- **Browser Integration**: Open multiple URLs in different browsers
- **Parameter Support**: Pass command-line arguments to applications
- **Remote Development**: Support for VS Code/Cursor remote development

## File Structure

```
work-stack/
├── main.py                    # Main GUI entry point
├── cli.py                     # CLI interface
├── launch.sh                  # Cross-platform launcher script
├── config.json               # Main configuration file
├── requirements.txt          # Python dependencies
├── build_exe.py             # Executable building script
├── gui/                     # GUI components
│   ├── main_window.py       # Main application window
│   ├── category_tab.py      # Category management
│   ├── launch_item.py       # Launch item widgets
│   ├── hotkey_manager_*.py  # Platform-specific hotkey support
│   └── *_dialog.py         # Configuration dialogs
├── utils/                   # Utility modules
│   ├── config_manager.py    # Configuration management
│   ├── app_launcher.py      # Application launching
│   ├── platform_settings.py # Platform-specific settings
│   ├── gist_manager.py      # GitHub Gist sync
│   ├── webdav_manager.py    # WebDAV sync
│   └── logger.py           # Logging system
├── apps/                    # Predefined launch scripts
├── resources/              # Icons and assets
├── logs/                   # Application logs
└── config_history/         # Configuration backups
```

## Configuration Format

The main configuration (`config.json`) structure:

```json
{
  "programs": [
    {
      "name": "Program Name",
      "description": "Optional description",
      "category": "Category Name",
      "launch_items": [
        {
          "app": "application_name_or_path",
          "params": ["param1", "param2"]
        }
      ]
    }
  ],
  "categories": ["Category1", "Category2"],
  "auto_close_after_launch": true,
  "window_size": {"width": 900, "height": 600},
  "github_sync": { /* GitHub Gist settings */ },
  "webdav_sync": { /* WebDAV settings */ },
  "enable_hotkey": false
}
```

## Development Workflow

### Running the Application
```bash
# GUI mode
python main.py
# or
./launch.sh

# CLI mode
python cli.py
# or
./launch.sh [arguments]
```

### Building Executables
```bash
python build_exe.py
```

### Adding New Features
1. **GUI Components**: Add to `gui/` package
2. **Utilities**: Add to `utils/` package  
3. **Platform Support**: Extend `platform_settings.py`
4. **Configuration**: Update config schema in `config_manager.py`

## Platform-Specific Notes

### macOS
- Requires PyObjC for global hotkeys and native integration
- Uses AppKit for proper window management
- Special Dock and menu bar integration
- Launch script handles Qt layer settings

### Windows
- Uses win32 APIs for global hotkeys
- DPI awareness configuration
- System tray integration with proper context menus
- Executable packaging with PyInstaller

### Linux
- Uses python-xlib for global hotkeys
- System tray support varies by desktop environment
- Cross-distribution compatibility considerations

## Logging and Debugging

- **Log Location**: `logs/app.log`
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Logger Usage**: Import from `utils.logger`
- **Platform Debugging**: Check platform-specific code paths

## Security Considerations

- **API Keys**: Stored in configuration (GitHub tokens, WebDAV credentials)
- **File Permissions**: Launcher can execute arbitrary applications
- **Network Sync**: Transmits configuration data to remote services
- **Local Access**: Full file system access for launching applications

## Common Issues and Solutions

1. **Global Hotkeys Not Working**: Check platform-specific permissions and dependencies
2. **Sync Failures**: Verify network connectivity and credentials
3. **Application Not Launching**: Check file paths and permissions
4. **UI Scaling Issues**: Platform-specific DPI settings in `platform_settings.py`

## Future Enhancement Areas

- Plugin system for custom launchers
- Cloud storage integration beyond WebDAV
- Application usage analytics
- Theme customization
- Multi-language support
- Mobile companion app

This codebase represents a mature, feature-rich application launcher with sophisticated synchronization capabilities and cross-platform support. The modular architecture makes it extensible while maintaining platform-specific optimizations.