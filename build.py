import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
ENTRYPOINT = PROJECT_ROOT / "BMS_Monitor.py"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
VERSION_FILE = PROJECT_ROOT / "version.json"

DATA_FILES = [
    "version.json",
    "logo_sq.ico",
    "logo_sq.png",
    "logo_rec.png",
]


def load_version_data() -> dict:
    if VERSION_FILE.exists():
        with VERSION_FILE.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
    return {"executable_name": "DecibelsBMSMonitor.exe"}


APP_NAME = load_version_data().get("executable_name", "DecibelsBMSMonitor.exe").replace(".exe", "")


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def build_command(onefile: bool = True) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
    ]

    command.append("--onefile" if onefile else "--onedir")

    icon_path = PROJECT_ROOT / "logo_sq.ico"
    if icon_path.exists():
        command.extend(["--icon", str(icon_path)])

    for filename in DATA_FILES:
        filepath = PROJECT_ROOT / filename
        if filepath.exists():
            command.extend(["--add-data", f"{filepath};."])

    command.append(str(ENTRYPOINT))
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the BMS Monitor executable with PyInstaller.")
    parser.add_argument("--clean-only", action="store_true", help="Remove build and dist folders, then exit.")
    parser.add_argument("--onedir", action="store_true", help="Build a folder-based distribution instead of a single standalone executable.")
    args = parser.parse_args()

    if args.clean_only:
        remove_path(BUILD_DIR)
        remove_path(DIST_DIR)
        print("Cleaned build and dist folders.")
        return 0

    if not ENTRYPOINT.exists():
        print(f"Entrypoint not found: {ENTRYPOINT}")
        return 1

    command = build_command(onefile=not args.onedir)
    print("Running build command:")
    print(" ".join(f'"{part}"' if " " in part else part for part in command))

    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode != 0:
        print("Build failed.")
        return completed.returncode

    if args.onedir:
        print(f"Build completed successfully. Output: {DIST_DIR / APP_NAME}")
    else:
        print(f"Build completed successfully. Output: {DIST_DIR / f'{APP_NAME}.exe'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
