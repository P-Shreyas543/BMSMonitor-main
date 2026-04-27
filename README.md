# BMSMonitor

Decibels `BMSMonitor` is a Windows desktop application for live BMS telemetry monitoring and CSV logging over a serial connection.

## Features

- Read live BMS monitor frames over COM port
- Display parsed pack, cell, temperature, status-bit, and calculated values
- Record rolling CSV logs with automatic daily file rotation
- Save live monitoring data to `.csv`
- Branded Windows desktop app with packaged logos and version metadata
- Standalone `.exe` build support with PyInstaller

## Project Structure

```text
BMS_Monitor.py              # Main launcher
bms_monitor/                # Application package
build.py                    # PyInstaller build script
version.json                # App metadata
requirements.txt            # Runtime dependencies
Documentation/              # Reserved project docs folder
logo_sq.ico                 # Windows icon
logo_sq.png                 # Fallback icon
logo_rec.png                # Header logo
SerialLogger.py             # Legacy compatibility launcher
```

## Requirements

- Windows
- Python 3.10+

## Install Dependencies

```bash
pip install -r requirements.txt
```

Build dependency:

```bash
pip install pyinstaller
```

## Run From Source

```bash
python BMS_Monitor.py
```

Legacy launcher also still works:

```bash
python SerialLogger.py
```

## Build Standalone EXE

Default build creates a single standalone executable:

```bash
python build.py
```

Output:

```text
dist/DecibelsBMSMonitor.exe
```

Optional folder-based build:

```bash
python build.py --onedir
```

Clean build artifacts only:

```bash
python build.py --clean-only
```

## Notes

- Tkinter is intentionally used in this version of the project.
- CSV monitor logs are date-suffixed automatically during long monitoring sessions.
- The project structure mirrors the related `BMSConfigurator` repository while preserving the monitor-specific serial protocol and parsing flow.
