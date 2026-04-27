import ctypes
import csv
import datetime
import os
import queue
import struct
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Dict, Optional

import serial
import serial.tools.list_ports
from PIL import Image, ImageTk, UnidentifiedImageError

from .config import (
    APP_NAME,
    APP_PLATFORM,
    APP_PUBLISHER,
    APP_VERSION,
    APP_WEBSITE,
    BAUD_RATES,
    COLORS,
    DEFAULT_BAUD_INDEX,
    EXECUTABLE_NAME,
    FONTS,
    FRAME_CONFIG,
    HEADER_LOGO_PATH,
    HEADER_LOGO_SIZE,
    HEADER_SIZE,
    ICON_ICO_PATH,
    ICON_PNG_PATH,
    MIN_WINDOW_SIZE,
    PROCESS_LOOP_DELAY_MS,
    SYNC_HEADER,
    TX_CMD_START,
    TX_CMD_STOP,
    TX_IDENTIFIER,
    WINDOW_SIZE,
    get_export_dir,
    get_windows_app_id,
)
from .protocol import DataParser, PARSED_HEADERS, PAYLOAD_FMT, TOTAL_SIZE, calculate_crc16


ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


def set_system_awake(enable: bool = True) -> None:
    if os.name != "nt":
        return
    try:
        if enable:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
        else:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    except Exception:
        pass


class CSVLoggerThread(threading.Thread):
    def __init__(self, status_queue=None):
        super().__init__(daemon=True)
        self.queue = queue.Queue()
        self.status_queue = status_queue
        self.running = False
        self.filename = None
        self.file_handle = None
        self.writer = None
        self._date = None

    def start_logging(self, filename: str) -> None:
        self.filename = os.path.splitext(filename)[0]
        self.running = True
        self.start()

    def stop_logging(self) -> None:
        self.running = False
        self.queue.put(None)

    def _rotate(self) -> None:
        if self.file_handle:
            self.file_handle.close()
        current_date = datetime.date.today().isoformat()
        filepath = f"{self.filename}_{current_date}.csv"
        new_file = not os.path.exists(filepath)
        self.file_handle = open(filepath, "a", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file_handle)
        if new_file:
            header = ["Timestamp_Sec", "ISO_Time"] + [item["name"] for item in PARSED_HEADERS]
            self.writer.writerow(header)
        self._date = datetime.date.today()

    def run(self) -> None:
        while self.running or not self.queue.empty():
            try:
                data_packet = self.queue.get(timeout=1)
                if data_packet is None:
                    break

                if datetime.date.today() != self._date or not self.file_handle:
                    self._rotate()

                timestamp, flat, stats = data_packet
                iso_time = datetime.datetime.fromtimestamp(timestamp).isoformat()
                row = [f"{timestamp:.3f}", iso_time]

                flat_index = 0
                for header in PARSED_HEADERS:
                    if header["type"] == "calc":
                        value = stats.get(header["key"], 0)
                    else:
                        value = flat[flat_index]
                        flat_index += 1

                    if header["type"] == "bit":
                        row.append(1 if value else 0)
                    else:
                        row.append(header["fmt"].format(value))

                self.writer.writerow(row)
                self.file_handle.flush()
            except queue.Empty:
                continue
            except Exception as exc:
                self.running = False
                if self.status_queue:
                    self.status_queue.put(("LOGGER_ERROR", str(exc)))
                break

        if self.file_handle:
            self.file_handle.close()


class SerialWorker(threading.Thread):
    def __init__(self, port: str, baud: int, data_queue, status_queue, log_queue):
        super().__init__(daemon=True)
        self.port = port
        self.baud = baud
        self.data_queue = data_queue
        self.status_queue = status_queue
        self.log_queue = log_queue
        self.stop_event = threading.Event()
        self.ser: Optional[serial.Serial] = None

    def stop(self) -> None:
        self.stop_event.set()
        if self.ser and self.ser.is_open:
            try:
                self._send(TX_CMD_STOP, 0)
                self.ser.close()
            except Exception:
                pass

    def _send(self, cmd: int, value: int) -> None:
        if not self.ser:
            return
        try:
            payload = struct.pack("<BB", TX_IDENTIFIER, cmd) + struct.pack("<I", value) + b"\x00" * 4
            crc = calculate_crc16(payload)
            frame = payload + struct.pack("<H", crc)
            self.ser.write(frame)
        except Exception as exc:
            self.log_queue.put(f"TX Error: {exc}")

    def run(self) -> None:
        buffer = bytearray()
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.05)
            self.status_queue.put(("CONNECTED", f"{self.port}|{self.baud}"))
            self.log_queue.put(f"Connected to {self.port} @ {self.baud}bps")
            self._send(TX_CMD_START, 0)

            while not self.stop_event.is_set():
                if not self.ser.is_open:
                    raise serial.SerialException("Port closed unexpectedly")

                if self.ser.in_waiting:
                    buffer.extend(self.ser.read(self.ser.in_waiting))

                while len(buffer) >= TOTAL_SIZE:
                    if buffer[:HEADER_SIZE] == SYNC_HEADER:
                        frame = buffer[HEADER_SIZE:TOTAL_SIZE]
                        try:
                            rx_time = time.time()
                            raw = struct.unpack(PAYLOAD_FMT, frame)
                            processed = DataParser.parse(raw, FRAME_CONFIG)
                            self.data_queue.put((rx_time, processed))
                            del buffer[:TOTAL_SIZE]
                        except struct.error:
                            self.log_queue.put("Corrupt frame. Sync lost.")
                            del buffer[:1]
                    else:
                        del buffer[:1]

                time.sleep(0.005)
        except (OSError, serial.SerialException) as exc:
            if self.ser is None:
                self.status_queue.put(("OPEN_ERROR", f"{self.port}|{self.baud}|{exc}"))
            else:
                self.status_queue.put(("ERROR", str(exc)))
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.log_queue.put("Serial thread exited")


class BMSMonitorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_PUBLISHER} {APP_NAME} v{APP_VERSION}")
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(*MIN_WINDOW_SIZE)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window_icon = None
        self.logo_img = None

        self.gui_log_queue = queue.Queue()
        self.serial_data_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.serial_thread: Optional[SerialWorker] = None
        self.csv_thread: Optional[CSVLoggerThread] = None
        self.is_connected = False
        self.is_connecting = False
        self.entries: Dict[str, tk.Entry] = {}
        self.rx_frame_count = 0
        self.last_packet_time: Optional[float] = None
        self.closing_in_progress = False
        self.process_loop_after_id: Optional[str] = None

        self._configure_window_branding()
        self._configure_styles()
        self.build_ui()
        self.process_incoming_data()

    def _configure_window_branding(self) -> None:
        if ICON_ICO_PATH.exists():
            try:
                self.root.iconbitmap(str(ICON_ICO_PATH))
            except (tk.TclError, OSError):
                pass

        if ICON_PNG_PATH.exists():
            try:
                self.window_icon = tk.PhotoImage(file=str(ICON_PNG_PATH))
                self.root.iconphoto(True, self.window_icon)
            except (tk.TclError, OSError):
                pass

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(get_windows_app_id())
        except (AttributeError, OSError):
            pass

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

    def build_ui(self) -> None:
        header_frame = tk.Frame(self.root, pady=10, bg=COLORS["bg_light"], relief="groove", borderwidth=1)
        header_frame.pack(side=tk.TOP, fill="x")
        self.create_header(header_frame)

        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.create_parameter_area(main_frame)

        log_frame = tk.LabelFrame(self.root, text="System Log", height=120, font=FONTS["header"])
        log_frame.pack(side=tk.BOTTOM, fill="x", padx=10, pady=10)
        self.log_area = scrolledtext.ScrolledText(log_frame, height=6, state="disabled", font=FONTS["mono"])
        self.log_area.pack(fill="both", expand=True)

        self.status_bar = tk.Label(self.root, text="Ready. Select a COM port to begin.", anchor="w", padx=10, pady=6, bg=COLORS["bg_header"], fg=COLORS["text_label"], font=FONTS["normal"])
        self.status_bar.pack(side=tk.BOTTOM, fill="x")

    def create_header(self, parent) -> None:
        left_container = tk.Frame(parent, bg=COLORS["bg_light"])
        left_container.pack(side=tk.LEFT, padx=20)
        self._create_logo_widget(left_container)

        title_block = tk.Frame(left_container, bg=COLORS["bg_light"])
        title_block.pack(side=tk.LEFT)
        tk.Label(title_block, text=APP_NAME.upper(), font=FONTS["title"], fg=COLORS["text_label"], bg=COLORS["bg_light"]).pack(side=tk.LEFT)
        subtitle = f"Version {APP_VERSION}  |  {APP_PLATFORM}"
        tk.Label(title_block, text=subtitle, font=FONTS["normal"], fg=COLORS["text_gray"], bg=COLORS["bg_light"]).pack(side=tk.LEFT, padx=(15, 0))

        right_container = tk.Frame(parent, bg=COLORS["bg_light"])
        right_container.pack(side=tk.RIGHT, padx=20)
        self._create_connection_controls(right_container)

    def _create_logo_widget(self, parent) -> None:
        try:
            image = Image.open(HEADER_LOGO_PATH)
            image.thumbnail(HEADER_LOGO_SIZE, Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(image)
            logo_label = tk.Label(parent, image=self.logo_img, bg=COLORS["bg_light"], cursor="hand2")
            logo_label.pack(side=tk.LEFT, padx=(0, 15))
            logo_label.bind("<Button-1>", lambda _event: webbrowser.open(APP_WEBSITE))
        except (FileNotFoundError, OSError, UnidentifiedImageError):
            tk.Label(parent, text="[DECIBELS]", font=FONTS["label_title"], bg=COLORS["btn_disabled"]).pack(side=tk.LEFT, padx=(0, 15))

    def _create_connection_controls(self, parent) -> None:
        tk.Label(parent, text="COM port:", bg=COLORS["bg_light"], font=FONTS["normal"]).pack(side=tk.LEFT, padx=(0, 5))
        self.port_combo = ttk.Combobox(parent, width=12, font=FONTS["normal"], state="readonly")
        self.port_combo.pack(side=tk.LEFT)

        self.btn_refresh = tk.Button(parent, text="⟳", command=self.update_ports, font=FONTS["button_small"], width=3, bg=COLORS["btn_refresh"])
        self.btn_refresh.pack(side=tk.LEFT, padx=(2, 15))
        self.update_ports()

        tk.Label(parent, text="Baud rate:", bg=COLORS["bg_light"], font=FONTS["normal"]).pack(side=tk.LEFT, padx=(0, 5))
        self.baud_combo = ttk.Combobox(parent, values=BAUD_RATES, width=9, font=FONTS["normal"], state="readonly")
        self.baud_combo.current(DEFAULT_BAUD_INDEX)
        self.baud_combo.pack(side=tk.LEFT, padx=(0, 15))

        self.btn_connect = tk.Button(parent, text="Connect", command=self.toggle_connection, bg=COLORS["btn_connect"], font=FONTS["button"], width=12)
        self.btn_connect.pack(side=tk.LEFT)

        self.connection_badge = tk.Label(parent, text="DISCONNECTED", font=FONTS["button"], bg="#fce8e6", fg=COLORS["status_error"], padx=10, pady=4)
        self.connection_badge.pack(side=tk.LEFT, padx=(12, 0))

    def create_parameter_area(self, parent) -> None:
        btn_frame = tk.Frame(parent, pady=6, bg=COLORS["bg_light"], relief="groove", borderwidth=1)
        btn_frame.pack(fill="x")

        action_group = tk.Frame(btn_frame, bg=COLORS["bg_light"])
        action_group.pack(side=tk.LEFT, padx=6)
        tk.Label(action_group, text="Session Log", bg=COLORS["bg_light"], fg=COLORS["text_gray"], font=FONTS["mono_small"]).pack(side=tk.LEFT, padx=(2, 8))
        self.btn_record = self._create_toolbar_button(action_group, "SAVE LOG", self.toggle_recording, COLORS["btn_record"], 14)

        tk.Frame(btn_frame, width=1, bg="#cccccc").pack(side=tk.LEFT, fill="y", padx=12, pady=5)

        file_group = tk.Frame(btn_frame, bg=COLORS["bg_light"])
        file_group.pack(side=tk.LEFT, padx=6)
        tk.Label(file_group, text="View Tools", bg=COLORS["bg_light"], fg=COLORS["text_gray"], font=FONTS["mono_small"]).pack(side=tk.LEFT, padx=(2, 8))
        self.btn_clear = self._create_toolbar_button(file_group, "CLEAR VIEW", self.clear_all_values, COLORS["btn_neutral"], 12)
        self.btn_ekf = self._create_toolbar_button(file_group, "EKF ANALYZER", self.open_ekf_window, COLORS["btn_neutral"], 14)

        tk.Frame(btn_frame, width=1, bg="#cccccc").pack(side=tk.LEFT, fill="y", padx=12, pady=5)

        status_group = tk.Frame(btn_frame, bg=COLORS["bg_light"])
        status_group.pack(side=tk.LEFT, padx=8)
        self.lbl_stats = tk.Label(status_group, text="Frames: 0  |  Last Packet: --  |  Log Status: IDLE", font=FONTS["mono_small"], fg=COLORS["text_gray"], bg=COLORS["bg_light"])
        self.lbl_stats.pack(anchor="e", pady=2)

        list_frame = tk.Frame(parent)
        list_frame.pack(fill="both", expand=True, pady=(10, 0))
        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        headers = [("Parameter Name", 38), ("Current Value", 16), ("Unit", 10), ("Data Type", 14)]
        for col, (text, width) in enumerate(headers):
            tk.Label(self.scrollable_frame, text=text, font=FONTS["header"], width=width, anchor="w" if col == 0 else "center", bg=COLORS["bg_header"], relief="flat").grid(row=0, column=col, padx=2, pady=2, sticky="ew")

        for index, header in enumerate(PARSED_HEADERS, start=1):
            bg_color = COLORS["bg_bright"] if index % 2 == 0 else COLORS["bg_alt"]
            tk.Label(self.scrollable_frame, text=header["name"], anchor="w", bg=bg_color, font=FONTS["normal"]).grid(row=index, column=0, padx=5, pady=2, sticky="nsew")

            entry_frame = tk.Frame(self.scrollable_frame, bg=bg_color)
            entry_frame.grid(row=index, column=1, padx=2, pady=2, sticky="nsew")
            entry = tk.Entry(entry_frame, width=14, justify="center", font=FONTS["normal"], relief="flat", bg=bg_color)
            entry.insert(0, "--")
            entry.configure(state="readonly")
            entry.pack(pady=2)

            key = header.get("key") or header.get("name")
            self.entries[key] = entry

            tk.Label(self.scrollable_frame, text=header["unit"], fg=COLORS["text_unit"], bg=bg_color, font=FONTS["normal"]).grid(row=index, column=2, padx=2, pady=2, sticky="nsew")
            tk.Label(self.scrollable_frame, text=header.get("source_fmt", "--"), fg=COLORS["text_gray"], bg=bg_color, font=FONTS["mono_small"]).grid(row=index, column=3, padx=2, pady=2, sticky="nsew")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        list_frame.bind("<Enter>", lambda _event: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        list_frame.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))

    def _create_toolbar_button(self, parent, text: str, command, bg_color: str, width: int):
        button = tk.Button(parent, text=text, command=command, bg=bg_color, font=FONTS["button"], width=width)
        button.pack(side=tk.LEFT, padx=4, pady=2)
        return button
        
    def open_ekf_window(self) -> None:
        if hasattr(self, 'ekf_window') and self.ekf_window and self.ekf_window.window.winfo_exists():
            self.ekf_window.window.lift()
            return
        from .ekf_window import EKFAnalyzerWindow
        self.ekf_window = EKFAnalyzerWindow(self.root, FONTS, COLORS)

    def update_ports(self) -> None:
        try:
            ports = sorted(serial.tools.list_ports.comports(), key=lambda port: port.device)
        except Exception as exc:
            self.port_combo["values"] = []
            self.port_combo.set("")
            self._set_status(f"Unable to enumerate COM ports: {exc}", COLORS["status_error"])
            self.log_gui(f"Port scan failed: {exc}")
            return

        port_names = [port.device for port in ports]
        current = self.port_combo.get()
        self.port_combo["values"] = port_names
        if current in port_names:
            self.port_combo.set(current)
        elif port_names:
            self.port_combo.current(0)
        else:
            self.port_combo.set("")

        self._set_status(f"Detected {len(port_names)} serial port(s).", COLORS["text_label"])

    def toggle_connection(self) -> None:
        if self.is_connected or self.is_connecting:
            self.disconnect()
            return

        port = self.port_combo.get().strip()
        baud_text = self.baud_combo.get().strip()

        if not port:
            messagebox.showwarning("Connect Error", "Please select a COM port before connecting.")
            return

        try:
            baud = int(baud_text)
        except ValueError:
            messagebox.showerror("Connect Error", f"Invalid baud rate: {baud_text}")
            return

        try:
            self.serial_thread = SerialWorker(port, baud, self.serial_data_queue, self.status_queue, self.gui_log_queue)
            self.serial_thread.start()
            self.is_connecting = True
            self._set_connection_ui(connecting=True)
            self._set_status(f"Connecting to {port} @ {baud} bps...", COLORS["status_warn"])
            self.log_gui(f"Opening serial connection on {port} @ {baud}bps")
        except Exception as exc:
            self.serial_thread = None
            self.is_connecting = False
            self._set_connection_ui(False)
            self._set_status(f"Connection failed: {exc}", COLORS["status_error"])
            self.log_gui(f"Connection failed: {exc}")
            messagebox.showerror("Connection Error", str(exc))

    def _friendly_open_error(self, port: str, raw_error: str) -> str:
        error_text = raw_error.lower()
        if "access is denied" in error_text or "permissionerror" in error_text:
            return f"Could not open {port}.\n\nThe port is busy, locked, or already in use by another application."
        if "file not found" in error_text or "cannot find the file specified" in error_text:
            return f"Could not open {port}.\n\nThe device is not available anymore. Try refreshing the COM ports list."
        return f"Could not open {port}.\n\n{raw_error}"

    def _set_connection_ui(self, connected: bool = False, connecting: bool = False) -> None:
        if connecting:
            self.btn_connect.config(text="Connecting...", state="disabled", bg="#f4e4c1")
            self.btn_refresh.config(state="disabled")
            self.port_combo.config(state="disabled")
            self.baud_combo.config(state="disabled")
            self.connection_badge.config(text="CONNECTING", bg="#fdf0d5", fg=COLORS["status_warn"])
            return

        if connected:
            self.btn_connect.config(text="Disconnect", state="normal", bg=COLORS["btn_disconnect"])
            self.btn_refresh.config(state="disabled")
            self.port_combo.config(state="disabled")
            self.baud_combo.config(state="disabled")
            self.btn_record.config(state="normal")
            self.connection_badge.config(text="CONNECTED", bg="#dff3e1", fg=COLORS["status_ok"])
        else:
            self.btn_connect.config(text="Connect", state="normal", bg=COLORS["btn_connect"])
            self.btn_refresh.config(state="normal")
            self.port_combo.config(state="readonly")
            self.baud_combo.config(state="readonly")
            self.btn_record.config(state="disabled")
            self.connection_badge.config(text="DISCONNECTED", bg="#fce8e6", fg=COLORS["status_error"])

    def _drain_queue(self, target_queue) -> None:
        while not target_queue.empty():
            try:
                target_queue.get_nowait()
            except queue.Empty:
                break

    def _reset_live_view(self) -> None:
        for entry in self.entries.values():
            entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, "--")
            entry.configure(state="readonly")
        self.rx_frame_count = 0
        self.last_packet_time = None
        self._update_stats_label(log_status=self._current_log_status(), color=self._current_log_status_color())

    def disconnect(self) -> None:
        was_active = self.is_connected or self.is_connecting
        if self.csv_thread:
            self.toggle_recording()
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.join(timeout=1.0)
            self.serial_thread = None

        self.is_connecting = False
        self.is_connected = False
        self._drain_queue(self.serial_data_queue)
        self._set_connection_ui(False)
        self._reset_live_view()
        self._set_status("Disconnected. Select a COM port to reconnect.", COLORS["text_label"])
        if was_active:
            self.log_gui("Disconnected.")

    def toggle_recording(self) -> None:
        if self.csv_thread is None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = filedialog.asksaveasfilename(
                initialdir=str(get_export_dir()),
                initialfile=f"bms_monitor_{timestamp}.csv",
                defaultextension=".csv",
                filetypes=[("CSV Log", "*.csv")],
                title="Save Monitoring Log",
            )
            if not filename:
                return

            try:
                set_system_awake(True)
                self.csv_thread = CSVLoggerThread(self.status_queue)
                self.csv_thread.start_logging(filename)
                self.btn_record.config(text="STOP SAVE", bg=COLORS["btn_stop"])
                self._update_stats_label(log_status=f"RECORDING to {Path(filename).name}", color=COLORS["status_error"])
                self._set_status(f"Recording monitor data to {filename}", COLORS["status_error"])
                self.log_gui(f"Started logging to {filename} (System Sleep Disabled)")
            except Exception as exc:
                set_system_awake(False)
                self.csv_thread = None
                self._set_status(f"Unable to start logging: {exc}", COLORS["status_error"])
                self.log_gui(f"Unable to start logging: {exc}")
                messagebox.showerror("Logging Error", str(exc))
        else:
            self.csv_thread.stop_logging()
            self.csv_thread.join(timeout=1.0)
            self.csv_thread = None
            set_system_awake(False)
            self.btn_record.config(text="SAVE LOG", bg=COLORS["btn_record"])
            self._update_stats_label(log_status="IDLE", color=COLORS["text_gray"])
            self._set_status("Logging stopped. Live monitoring is still active.", COLORS["text_label"])
            self.log_gui("Stopped logging (System Sleep Enabled)")

    def process_incoming_data(self) -> None:
        while not self.gui_log_queue.empty():
            self.log_gui(self.gui_log_queue.get_nowait())

        while not self.status_queue.empty():
            msg_type, msg_val = self.status_queue.get_nowait()
            if msg_type == "CONNECTED":
                self.is_connecting = False
                self.is_connected = True
                self._set_connection_ui(True)
                port, baud = msg_val.split("|", 1)
                self._set_status(f"Connected to {port} @ {baud} bps.", COLORS["status_ok"])
            elif msg_type == "OPEN_ERROR":
                parts = msg_val.split("|", 2)
                port = parts[0] if len(parts) > 0 else "COM port"
                raw_error = parts[2] if len(parts) > 2 else msg_val
                self.is_connecting = False
                self.is_connected = False
                self.serial_thread = None
                self._set_connection_ui(False)
                self._set_status(f"Could not open {port}.", COLORS["status_error"])
                self.log_gui(f"Port open failed on {port}: {raw_error}")
                messagebox.showerror("Port Busy", self._friendly_open_error(port, raw_error))
            elif msg_type == "ERROR":
                self._set_status(f"Connection lost: {msg_val}", COLORS["status_error"])
                self.disconnect()
                messagebox.showerror("Connection Error", f"Lost connection:\n{msg_val}")
            elif msg_type == "LOGGER_ERROR":
                if self.csv_thread:
                    self.csv_thread = None
                self.btn_record.config(text="SAVE LOG", bg=COLORS["btn_record"])
                self._update_stats_label(log_status="ERROR", color=COLORS["status_error"])
                self._set_status(f"CSV logging failed: {msg_val}", COLORS["status_error"])
                set_system_awake(False)
                self.log_gui(f"CSV logging failed: {msg_val}")
                messagebox.showerror("Logging Error", f"CSV logging failed:\n{msg_val}")

        while not self.serial_data_queue.empty():
            rx_time, data = self.serial_data_queue.get_nowait()
            self.rx_frame_count += 1
            self.last_packet_time = rx_time

            if self.csv_thread and self.csv_thread.running:
                self.csv_thread.queue.put((rx_time, data["flat"], data["stats"]))

            if hasattr(self, 'ekf_window') and self.ekf_window and self.ekf_window.window.winfo_exists():
                try:
                    # Based on FRAME_CONFIG: Index 0 is Pack Voltage (V), Index 1 is Pack Current (A)
                    pack_current = data["flat"][1]
                    # Fetch the minimum cell voltage from calculated stats, fallback to pack voltage if missing
                    min_cell_voltage = data["stats"].get("Cells_min", data["flat"][0])
                    self.ekf_window.push_live_data(pack_current, min_cell_voltage, rx_time)
                except (IndexError, TypeError):
                    pass

            self.update_gui(data)
            self._update_stats_label()

        if not self.closing_in_progress:
            self.process_loop_after_id = self.root.after(PROCESS_LOOP_DELAY_MS, self.process_incoming_data)
        else:
            self.process_loop_after_id = None

    def update_gui(self, data: Dict) -> None:
        flat = data["flat"]
        stats = data["stats"]
        flat_index = 0

        for header in PARSED_HEADERS:
            key = header.get("key") or header.get("name")
            entry = self.entries.get(key)
            if not entry:
                continue

            if header["type"] == "calc":
                value = stats.get(header["key"], 0)
            else:
                value = flat[flat_index]
                flat_index += 1

            if header["type"] == "bit":
                display_value = "ON" if value else "OFF"
            else:
                display_value = header["fmt"].format(value)

            entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, display_value)
            entry.configure(state="readonly")

    def _update_stats_label(self, log_status: Optional[str] = None, color: Optional[str] = None) -> None:
        if self.last_packet_time:
            last_packet = datetime.datetime.fromtimestamp(self.last_packet_time).strftime("%H:%M:%S")
        else:
            last_packet = "--"
        status_text = log_status if log_status is not None else self._current_log_status()
        status_color = color if color is not None else self._current_log_status_color()
        self.lbl_stats.config(text=f"Frames: {self.rx_frame_count}  |  Last Packet: {last_packet}  |  Log Status: {status_text}", fg=status_color)

    def _current_log_status(self) -> str:
        if self.csv_thread and self.csv_thread.running:
            return "RECORDING"
        return "IDLE"

    def _current_log_status_color(self) -> str:
        if self.csv_thread and self.csv_thread.running:
            return COLORS["status_error"]
        return COLORS["text_gray"]

    def clear_all_values(self) -> None:
        for entry in self.entries.values():
            entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, "--")
            entry.configure(state="readonly")
        self.rx_frame_count = 0
        self.last_packet_time = None
        self._update_stats_label(log_status=self._current_log_status(), color=self._current_log_status_color())
        self.log_gui("Cleared all displayed monitor values")

    def _set_status(self, message: str, color: str) -> None:
        if hasattr(self, "status_bar"):
            self.status_bar.config(text=message, fg=color)

    def log_gui(self, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    def on_close(self) -> None:
        if self.closing_in_progress:
            return

        if self.csv_thread or self.is_connected or self.is_connecting:
            should_close = messagebox.askyesno("Close Application", "Monitoring is still active.\n\nClose the application and disconnect safely?")
            if not should_close:
                self.log_gui("Shutdown cancelled by user")
                return

        self.closing_in_progress = True
        
        if self.process_loop_after_id:
            try:
                self.root.after_cancel(self.process_loop_after_id)
            except tk.TclError:
                pass
            self.process_loop_after_id = None
            
        try:
            if self.csv_thread:
                self.csv_thread.stop_logging()
                self.csv_thread.join(timeout=1.0)
                self.csv_thread = None
            if self.serial_thread:
                self.serial_thread.stop()
                self.serial_thread.join(timeout=1.0)
                self.serial_thread = None
        finally:
            set_system_awake(False)
            self.root.destroy()
