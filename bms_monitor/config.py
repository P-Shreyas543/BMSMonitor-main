import json
import sys
from pathlib import Path


FRAME_CONFIG = [
    {"name": "Pack Voltage", "fmt": "uint16", "unit": "V", "factor": 0.001},
    {"name": "Pack Current", "fmt": "int32", "unit": "A", "factor": 0.001},
    {"name": "Cell Voltage", "fmt": "uint16", "unit": "V", "count": 7, "factor": 0.001, "group": "Cells"},
    {"name": "BCC Temperature", "fmt": "int16", "unit": "Deg C", "factor": 0.1},
    {"name": "Cell Temperature", "fmt": "int16", "unit": "Deg C", "count": 7, "factor": 0.1, "group": "Temps"},
    {"name": "Get Value Status", "fmt": "uint8", "unit": "Enum"},
    {"name": "FET Status", "fmt": "uint8", "unit": "Bitfield", "bits": ["Main FET Status", "Pre Charge FET Status"]},
    {"name": "Load Voltage", "fmt": "uint16", "unit": "V", "factor": 0.001},
    {"name": "Bal. Resistor Temp", "fmt": "int16", "unit": "Deg C", "count": 3, "factor": 0.1},
    {"name": "Pre-Charge Res. Temp", "fmt": "int16", "unit": "Deg C", "factor": 0.1},
    {"name": "MOSFET Temp", "fmt": "int16", "unit": "Deg C", "count": 2, "factor": 0.1},
    {"name": "Ambient Temp", "fmt": "int16", "unit": "Deg C", "factor": 0.1},
    {"name": "Balancing Status", "fmt": "uint8", "unit": "Bitfield", "bits": [f"Cell {i + 1} Balancing" for i in range(7)]},
    {"name": "Fault Status", "fmt": "uint16", "unit": "Bitfield", "bits": ["Cell OV", "Cell UV", "Pack OV", "Pack UV", "V Fault", "OC", "OT", "UT", "OverChg", "OverDsg", "Status Fault", "Delta V Fault", "Delta T Fault"]},
    {"name": "BMS State", "fmt": "uint8", "unit": "Enum"},
    {"name": "SoC (OCV)", "fmt": "uint16", "unit": "%", "factor": 0.1},
    {"name": "SoC (Coulomb)", "fmt": "uint16", "unit": "%", "factor": 0.1},
    {"name": "SoH", "fmt": "uint8", "unit": "%"},
    {"name": "Cycle Count", "fmt": "uint16", "unit": "Cycles"},
    {"name": "Cumulative Cap", "fmt": "uint32", "unit": "Ah"},
]

CALC_GROUPS = {
    "Cells": {"unit": "V", "stats": ["min", "max", "diff", "sum", "avg"]},
    "Temps": {"unit": "Deg C", "stats": ["max", "avg"]},
}

TX_IDENTIFIER = 0x5A
TX_CMD_START = 0xAA
TX_CMD_STOP = 0x55
SYNC_HEADER = b"\xAA\x55"
HEADER_SIZE = len(SYNC_HEADER)

BAUD_RATES = ("300", "600", "1200", "2400", "4800", "9600", "14400", "19200", "38400", "57600", "115200", "230400", "460800", "921600")
DEFAULT_BAUD_INDEX = BAUD_RATES.index("115200")
PROCESS_LOOP_DELAY_MS = 50
MIN_WINDOW_SIZE = (1120, 680)
HEADER_LOGO_SIZE = (220, 50)

COLORS = {
    "bg_light": "#f5f5f5",
    "bg_bright": "#ffffff",
    "bg_alt": "#f9f9f9",
    "bg_header": "#e8e8e8",
    "text_label": "#333333",
    "text_unit": "#0066cc",
    "text_gray": "#666666",
    "text_subtle": "gray",
    "btn_disconnect": "#ffcccc",
    "btn_connect": "#dddddd",
    "btn_record": "#e6f7ff",
    "btn_stop": "#ffe6e6",
    "btn_neutral": "#f0f0f0",
    "btn_refresh": "#e0e0e0",
    "btn_disabled": "#dddddd",
    "status_ok": "#1f7a1f",
    "status_warn": "#b26a00",
    "status_error": "#b42318",
}

FONTS = {
    "title": ("PT Sans", 20, "bold"),
    "label_title": ("PT Sans", 16, "bold"),
    "header": ("PT Sans", 10, "bold"),
    "normal": ("PT Sans", 10),
    "button": ("PT Sans", 9, "bold"),
    "button_small": ("Segoe UI", 10, "bold"),
    "mono_small": ("Consolas", 8),
    "mono": ("Consolas", 9),
}


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
VERSION_FILE = BASE_DIR / "version.json"

DEFAULT_APP_METADATA = {
    "app_name": "BMS Monitor",
    "publisher": "Decibels",
    "version": "1.0.0",
    "platform": "Windows (Tkinter)",
    "website": "https://lms.decibelslab.com/",
    "window_size": "1320x760",
    "executable_name": "DecibelsBMSMonitor.exe",
}


def load_app_metadata():
    if VERSION_FILE.exists():
        with VERSION_FILE.open("r", encoding="utf-8") as file_handle:
            raw_data = json.load(file_handle)
        return {**DEFAULT_APP_METADATA, **raw_data}
    return dict(DEFAULT_APP_METADATA)


APP_METADATA = load_app_metadata()
APP_NAME = APP_METADATA["app_name"]
APP_PUBLISHER = APP_METADATA["publisher"]
APP_VERSION = APP_METADATA["version"]
APP_PLATFORM = APP_METADATA["platform"]
APP_WEBSITE = APP_METADATA["website"]
WINDOW_SIZE = APP_METADATA["window_size"]
EXECUTABLE_NAME = APP_METADATA["executable_name"]

ICON_ICO_PATH = BASE_DIR / "logo_sq.ico"
ICON_PNG_PATH = BASE_DIR / "logo_sq.png"
HEADER_LOGO_PATH = BASE_DIR / "logo_rec.png"
DOCUMENTATION_DIR = BASE_DIR / "Documentation"


def get_export_dir() -> Path:
    export_dir = Path.home() / "Documents" / APP_PUBLISHER / APP_NAME
    export_dir.mkdir(parents=True, exist_ok=True)
    DOCUMENTATION_DIR.mkdir(parents=True, exist_ok=True)
    return export_dir


def get_windows_app_id() -> str:
    safe_name = "".join(ch.lower() if ch.isalnum() else "" for ch in APP_NAME)
    safe_version = APP_VERSION.replace(".", "_")
    return f"{APP_PUBLISHER.lower()}.{safe_name}.v{safe_version}"
