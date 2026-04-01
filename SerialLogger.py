import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import queue
import time
import struct
import csv
import os
import datetime
import math
import ctypes  # Added for System Sleep Prevention
from typing import List, Dict, Any, Tuple

# ==========================================
#        ASSETS & VISUAL CONFIG
# ==========================================
LOGO_RAW_HEX = [
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x3f, 0xff, 0xff, 0xf0, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xf8, 0x3f, 0xff, 0xff, 0xf0, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xf8, 0x3f, 0xff, 0xff, 0xf0, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xf8, 
  0x3f, 0xff, 0xff, 0xf0, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xf8, 0x3f, 0xff, 0xff, 0xf0, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xf8, 0x3f, 0x80, 0x3f, 0xf0, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xf8, 
  0x3f, 0x80, 0x1f, 0xf0, 0xf8, 0x0f, 0x80, 0x3c, 0x1e, 0x30, 0x0f, 0x00, 
  0x63, 0xff, 0x07, 0xf8, 0x3f, 0xff, 0xff, 0xf0, 0xf8, 0x03, 0x80, 0x18, 
  0x06, 0x30, 0x07, 0x00, 0x23, 0xfc, 0x03, 0xf8, 0x3f, 0x80, 0x07, 0xf0, 
  0xf8, 0x01, 0x80, 0x30, 0x06, 0x30, 0x03, 0x00, 0x63, 0xfc, 0x01, 0xf8, 
  0x3f, 0x80, 0x03, 0xf0, 0xf8, 0xf1, 0x8f, 0xf1, 0xc2, 0x31, 0xe3, 0x1f, 
  0xe3, 0xf8, 0x71, 0xf8, 0x3f, 0xff, 0xff, 0xf0, 0xf8, 0xf1, 0x8f, 0xf1, 
  0xe2, 0x31, 0xe3, 0x1f, 0xe3, 0xf8, 0x71, 0xf8, 0x3f, 0xff, 0xff, 0xf0, 
  0xf8, 0xf1, 0x80, 0xf1, 0xfe, 0x30, 0x03, 0x01, 0xe3, 0xfc, 0x1f, 0xf8, 
  0x3f, 0x80, 0x03, 0xf0, 0xf8, 0xf1, 0x80, 0xf1, 0xfe, 0x30, 0x07, 0x00, 
  0xe3, 0xfe, 0x07, 0xf8, 0x3f, 0x80, 0x03, 0xf0, 0xf8, 0xf1, 0x80, 0xf1, 
  0xfe, 0x30, 0x03, 0x01, 0xe3, 0xff, 0x01, 0xf8, 0x3f, 0xff, 0xff, 0xf0, 
  0xf8, 0xf1, 0x8f, 0xf1, 0xfe, 0x31, 0xe3, 0x1f, 0xe3, 0xff, 0xe1, 0xf8, 
  0x3f, 0x80, 0x07, 0xf0, 0xf8, 0xf1, 0x8f, 0xf1, 0xe3, 0x39, 0xe3, 0x1f, 
  0xe3, 0xfc, 0xf9, 0xf8, 0x3f, 0x80, 0x07, 0xf0, 0xf8, 0xf1, 0x8f, 0xf1, 
  0xc7, 0x31, 0xe3, 0x1f, 0xe3, 0xfc, 0x71, 0xf8, 0x3f, 0xff, 0xff, 0xf0, 
  0xf8, 0x03, 0x80, 0x30, 0x06, 0x30, 0x03, 0x00, 0x60, 0x0c, 0x01, 0xf8, 
  0x3f, 0xff, 0xff, 0xf0, 0xf8, 0x07, 0x80, 0x3c, 0x1e, 0x30, 0x0f, 0x00, 
  0x60, 0x0f, 0x07, 0xf8, 0x3f, 0x80, 0x1f, 0xf0, 0xfc, 0x1f, 0x80, 0x3e, 
  0x3f, 0x38, 0x1f, 0x80, 0x70, 0x0f, 0x8f, 0xf8, 0x3f, 0x80, 0xff, 0xf0, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xf8, 
  0x3f, 0xff, 0xff, 0xf0, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xf8, 0x3f, 0xff, 0xff, 0xf0, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xf8, 0x3f, 0xff, 0xff, 0xf0, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xf8, 
  0x3f, 0xff, 0xff, 0xf0, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xf8, 0x1f, 0xff, 0xff, 0xf0, 0x7f, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xf0, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
]

def generate_corrected_xbm(hex_list):
    """
    Converts raw hex list to XBM string with BIT REVERSAL
    to correct the 'Mirror Image' display issue.
    """
    reverse_bits = lambda n: int('{:08b}'.format(n)[::-1], 2)
    corrected_bytes = [reverse_bits(b) for b in hex_list]
    hex_str = ", ".join([f"0x{b:02x}" for b in corrected_bytes])
    
    return f"""
    #define logo_width 128
    #define logo_height 42
    static unsigned char logo_bits[] = {{
        {hex_str}
    }};
    """

# ==========================================
#        MASTER CONFIGURATION
# ==========================================
# --- PROTOCOL ---
TX_IDENTIFIER = 0x5A 
TX_CMD_START  = 0xAA 
TX_CMD_STOP   = 0x55 
SYNC_HEADER   = b'\xAA\x55'
HEADER_SIZE   = len(SYNC_HEADER)

# --- FRAME DEFINITIONS ---
FRAME_CONFIG = [
    {'name': 'Pack Voltage', 'fmt': 'uint16', 'unit': 'V', 'factor': 0.001},
    {'name': 'Pack Current', 'fmt': 'int32', 'unit': 'A', 'factor': 0.001},
    {'name': 'Cell Voltage', 'fmt': 'uint16', 'unit': 'V', 'count': 14, 'factor': 0.001, 'group': 'Cells'},
    {'name': 'BCC Temperature', 'fmt': 'int16', 'unit': '°C', 'factor': 0.1},
    {'name': 'Cell Temperature', 'fmt': 'int16', 'unit': '°C', 'count': 7, 'factor': 0.1, 'group': 'Temps'},
    {'name': 'Get Value Status', 'fmt': 'uint8', 'unit': 'Enum'},
    {'name': 'FET Status', 'fmt': 'uint8', 'unit': 'Bitfield', 'bits': ["Main FET Status", "Pre Charge FET Status"]},
    {'name': 'Load Voltage', 'fmt': 'uint16', 'unit': 'V', 'factor': 0.001},
    {'name': 'Bal. Resistor Temp', 'fmt': 'int16', 'unit': '°C', 'count':3, 'factor': 0.1},
    {'name': 'Pre-Charge Res. Temp', 'fmt': 'int16', 'unit': '°C', 'factor': 0.1},
    {'name': 'MOSFET Temp', 'fmt': 'int16', 'unit': '°C', 'count':2, 'factor': 0.1},
    {'name': 'Ambient Temp', 'fmt': 'int16', 'unit': '°C', 'factor': 0.1},
    {'name': 'Balancing Status', 'fmt': 'uint16', 'unit': 'Bitfield', 'bits': [f"Cell {i+1} Balancing" for i in range(14)]}, 
    {'name': 'Fault Status', 'fmt': 'uint16', 'unit': 'Bitfield', 'bits': ["Cell OV", "Cell UV", "Pack OV", "Pack UV", "V Fault", "OC", "OT", "UT", "OverChg", "OverDsg", "StatusFault"]},
    {'name': 'BMS State', 'fmt': 'uint8', 'unit': 'Enum'},
    {'name': 'SoC (OCV)', 'fmt': 'uint16', 'unit': '%', 'factor':0.1},
    {'name': 'SoC (Coulomb)', 'fmt': 'uint16', 'unit': '%', 'factor':0.1},
    {'name': 'SoH', 'fmt':'uint8','unit':'%'},
    {'name': 'Cycle Count', 'fmt': 'uint16', 'unit': 'Cycles'},
    {'name': 'Cumulative Cap', 'fmt': 'uint32', 'unit': 'Ah'},
]

# --- CALCULATION GROUPS ---
CALC_GROUPS = {
    'Cells': {'unit': 'V', 'stats': ['min', 'max', 'diff', 'sum', 'avg']},
    'Temps': {'unit': '°C', 'stats': ['max', 'avg']}
}

# ==========================================
#           CORE LOGIC & UTILITIES
# ==========================================
def calculate_crc16(data: bytes) -> int:
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 1) != 0:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

# --- SYSTEM SLEEP PREVENTION (WINDOWS) ---
ES_CONTINUOUS       = 0x80000000
ES_SYSTEM_REQUIRED  = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

def set_system_awake(enable=True):
    """
    Prevents the system from sleeping while logging is active.
    Works on Windows via kernel32.SetThreadExecutionState.
    """
    if os.name == 'nt':
        try:
            if enable:
                ctypes.windll.kernel32.SetThreadExecutionState(
                    ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
                )
            else:
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        except:
            pass

def get_precision_fmt(factor):
    """
    Returns a format string (e.g., "{:.3f}") based on the factor.
    0.001 -> 3 decimals
    0.1   -> 1 decimal
    1.0   -> 0 decimals (int)
    """
    if not factor or factor == 1:
        return "{:.0f}"
    
    # Calculate decimals: -log10(factor)
    try:
        decimals = int(round(-math.log10(factor)))
        if decimals < 0: decimals = 0
        return "{:." + str(decimals) + "f}"
    except:
        return "{:.2f}" # Fallback

class DataParser:
    TYPE_MAP = {'int8':'b', 'uint8':'B', 'int16':'h', 'uint16':'H', 'int32':'i', 'uint32':'I', 'float':'f'}

    @staticmethod
    def prepare_config(config: List[Dict]) -> Tuple[str, List[Dict]]:
        fmt = "<" # Little Endian
        headers = []
        for field in config:
            count = field.get('count', 1)
            fmt += str(count) + DataParser.TYPE_MAP[field['fmt']] if count > 1 else DataParser.TYPE_MAP[field['fmt']]
            
            # Determine format string once based on factor
            f_val = field.get('factor', 1)
            fmt_str = get_precision_fmt(f_val)
            
            # Expand Headers
            if 'bits' in field:
                for b in field['bits']: 
                    headers.append({'name': b, 'unit': 'Bit', 'type': 'bit', 'key': b, 'fmt': "{:.0f}"})
            elif count > 1:
                for i in range(count): 
                    headers.append({'name': f"{field['name']} {i+1}", 'unit': field['unit'], 'type': 'val', 'factor': f_val, 'group': field.get('group'), 'fmt': fmt_str})
            else:
                headers.append({'name': field['name'], 'unit': field['unit'], 'type': 'val', 'factor': f_val, 'group': field.get('group'), 'fmt': fmt_str})

        # Add Calc Headers
        for grp, meta in CALC_GROUPS.items():
            # Find the base factor for this group to determine precision
            base_factor = 1.0
            for field in config:
                if field.get('group') == grp:
                    base_factor = field.get('factor', 1.0)
                    break
            
            grp_fmt = get_precision_fmt(base_factor)
            
            for stat in meta['stats']:
                headers.append({'name': f"{grp} {stat.title()}", 'unit': meta['unit'], 'type': 'calc', 'key': f"{grp}_{stat}", 'fmt': grp_fmt})
        
        return fmt, headers

    @staticmethod
    def parse(raw_data: tuple, config: List[Dict]) -> Dict[str, Any]:
        vals = []
        groups = {k: [] for k in CALC_GROUPS.keys()}
        idx = 0
        
        for field in config:
            count = field.get('count', 1)
            chunk = raw_data[idx : idx+count]
            idx += count
            
            if 'bits' in field:
                val = chunk[0]
                for i in range(len(field['bits'])):
                    vals.append((val >> i) & 1)
            else:
                for item in chunk:
                    val = item * field.get('factor', 1) if field.get('factor') else item
                    vals.append(val)
                    if field.get('group') in groups: groups[field.get('group')].append(val)

        stats = {}
        for grp, values in groups.items():
            if values:
                v_min, v_max = min(values), max(values)
                v_sum = sum(values)
                v_avg = v_sum / len(values)
                
                req_stats = CALC_GROUPS[grp]['stats']
                if 'min' in req_stats: stats[f"{grp}_min"] = v_min
                if 'max' in req_stats: stats[f"{grp}_max"] = v_max
                if 'diff' in req_stats: stats[f"{grp}_diff"] = v_max - v_min
                if 'sum' in req_stats: stats[f"{grp}_sum"] = v_sum
                if 'avg' in req_stats: stats[f"{grp}_avg"] = v_avg
        
        return {'flat': vals, 'stats': stats}

PAYLOAD_FMT, PARSED_HEADERS = DataParser.prepare_config(FRAME_CONFIG)
PAYLOAD_SIZE = struct.calcsize(PAYLOAD_FMT)
TOTAL_SIZE = HEADER_SIZE + PAYLOAD_SIZE

# ==========================================
#           THREADED MODULES
# ==========================================
class CSVLoggerThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.queue = queue.Queue()
        self.running = False
        self.filename = None
        self.file_handle = None
        self.writer = None
        self._date = None

    def start_logging(self, filename):
        self.filename = os.path.splitext(filename)[0]
        self.running = True
        self.start()

    def stop_logging(self):
        self.running = False
        self.queue.put(None)

    def _rotate(self):
        if self.file_handle: self.file_handle.close()
        current_date = datetime.date.today().isoformat()
        fname = f"{self.filename}_{current_date}.csv"
        
        new_file = not os.path.exists(fname)
        self.file_handle = open(fname, 'a', newline='')
        self.writer = csv.writer(self.file_handle)
        
        if new_file:
            header = ["Timestamp_Sec", "ISO_Time"] + [h['name'] for h in PARSED_HEADERS]
            self.writer.writerow(header)
        self._date = datetime.date.today()

    def run(self):
        while self.running or not self.queue.empty():
            try:
                data_packet = self.queue.get(timeout=1)
                if data_packet is None: break 
                
                if datetime.date.today() != self._date: self._rotate()
                elif not self.file_handle: self._rotate()
                
                ts, flat, stats = data_packet
                iso_time = datetime.datetime.fromtimestamp(ts).isoformat()
                
                # Standardize Timestamp to 3 decimal places
                row = [f"{ts:.3f}", iso_time]
                
                flat_idx = 0
                for h in PARSED_HEADERS:
                    val = 0
                    if h['type'] == 'calc':
                        val = stats.get(h['key'], 0)
                    elif h['type'] == 'bit':
                        val = flat[flat_idx]
                        flat_idx += 1
                    else:
                        val = flat[flat_idx]
                        flat_idx += 1
                    
                    # Apply Dynamic Format String
                    if h['type'] == 'bit':
                        row.append(1 if val else 0)
                    else:
                        row.append(h['fmt'].format(val))

                self.writer.writerow(row)
                self.file_handle.flush() 
            except queue.Empty:
                continue
            except Exception as e:
                pass 
        
        if self.file_handle: self.file_handle.close()

class SerialWorker(threading.Thread):
    def __init__(self, port, baud, data_queue, status_queue, log_queue):
        super().__init__(daemon=True)
        self.port = port
        self.baud = baud
        self.data_queue = data_queue
        self.status_queue = status_queue 
        self.log_queue = log_queue
        self.stop_event = threading.Event()
        self.ser = None

    def stop(self):
        self.stop_event.set()
        if self.ser and self.ser.is_open:
            try:
                self._send(TX_CMD_STOP, 0)
                self.ser.close()
            except: pass

    def _send(self, cmd, val):
        if not self.ser: return
        try:
            payload = struct.pack('<BB', TX_IDENTIFIER, cmd) + struct.pack('<I', val) + b'\x00'*4
            crc = calculate_crc16(payload)
            frame = payload + struct.pack('<H', crc)
            self.ser.write(frame)
        except Exception as e:
            self.log_queue.put(f"TX Error: {e}")

    def run(self):
        buffer = bytearray()
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.05)
            self.log_queue.put(f"Connected to {self.port} @ {self.baud}bps")
            self._send(TX_CMD_START, 0) # Handshake

            while not self.stop_event.is_set():
                if not self.ser.is_open:
                    raise serial.SerialException("Port closed unexpectedly")

                if self.ser.in_waiting:
                    buffer.extend(self.ser.read(self.ser.in_waiting))

                while len(buffer) >= TOTAL_SIZE:
                    if buffer[:HEADER_SIZE] == SYNC_HEADER:
                        frame = buffer[HEADER_SIZE:TOTAL_SIZE]
                        try:
                            # 1. Capture Time Immediately on Receipt
                            rx_time = time.time()
                            
                            # 2. Parse
                            raw = struct.unpack(PAYLOAD_FMT, frame)
                            processed = DataParser.parse(raw, FRAME_CONFIG)
                            
                            # 3. Queue (Time, Data)
                            self.data_queue.put((rx_time, processed))
                            
                            del buffer[:TOTAL_SIZE]
                        except struct.error:
                            self.log_queue.put("Corrupt Frame. Sync lost.")
                            del buffer[:1]
                    else:
                        del buffer[:1] 
                
                time.sleep(0.005) 

        except (OSError, serial.SerialException) as e:
            self.status_queue.put(("ERROR", str(e)))
        finally:
            if self.ser: self.ser.close()
            self.log_queue.put("Serial Thread Exited")

# ==========================================
#              GUI APPLICATION
# ==========================================
class BMS_Logger_App:
    def __init__(self, root):
        self.root = root
        self.root.title("Decibels BMS Monitor v1.0")
        self.root.geometry("1280x720")
        
        try:
            self.root.iconbitmap("logo.ico")
        except: pass

        # --- Data & State ---
        self.gui_log_queue = queue.Queue()
        self.serial_data_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.serial_thread = None
        self.csv_thread = None
        self.is_connected = False
        self.entries = {} 

        self.build_ui()
        self.root.after(50, self._system_tick)

    def build_ui(self):
        # 1. Header
        header_frame = tk.Frame(self.root, pady=10, bg="#f5f5f5", relief="groove", borderwidth=1)
        header_frame.pack(side=tk.TOP, fill="x")
        self.create_header(header_frame)

        # 2. Main Area
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.create_parameter_area(main_frame)

        # 3. Log
        log_frame = tk.LabelFrame(self.root, text="System Log", height=120, font=("PT Sans", 10, "bold"))
        log_frame.pack(side=tk.BOTTOM, fill="x", padx=10, pady=10)
        self.log_area = scrolledtext.ScrolledText(log_frame, height=6, state='disabled', font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True)

    def create_header(self, parent):
        left_container = tk.Frame(parent, bg="#f5f5f5")
        left_container.pack(side=tk.LEFT, padx=20)

        try:
            xbm_data = generate_corrected_xbm(LOGO_RAW_HEX)
            self.logo_img = tk.BitmapImage(data=xbm_data, foreground="#0055A6", background="#f5f5f5")
            logo_label = tk.Label(left_container, image=self.logo_img, bg="#f5f5f5")
            logo_label.pack(side=tk.LEFT, padx=(0, 15))
        except Exception as e:
            tk.Label(left_container, text="[DECIBELS]", font=("PT Sans", 16, "bold"), bg="#ddd").pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(left_container, text="BMS MONITOR", font=("PT Sans", 20, "bold"), fg="#333", bg="#f5f5f5").pack(side=tk.LEFT)

        right_container = tk.Frame(parent, bg="#f5f5f5")
        right_container.pack(side=tk.RIGHT, padx=20)

        tk.Label(right_container, text="COM port:", bg="#f5f5f5", font=("PT Sans", 11)).pack(side=tk.LEFT, padx=(0,5))
        self.port_combo = ttk.Combobox(right_container, width=12, font=("PT Sans", 10))
        self.port_combo.pack(side=tk.LEFT)
        
        self.btn_refresh = tk.Button(right_container, text="⟳", command=self._scan_ports, 
                                   font=("Segoe UI", 10, "bold"), width=3, bg="#e0e0e0")
        self.btn_refresh.pack(side=tk.LEFT, padx=(2, 15))
        self._scan_ports()

        tk.Label(right_container, text="Baud rate:", bg="#f5f5f5", font=("PT Sans", 11)).pack(side=tk.LEFT, padx=(0,5))
        self.baud_combo = ttk.Combobox(right_container, values=["9600", "115200", "921600"], width=9, font=("PT Sans", 10))
        self.baud_combo.current(1)
        self.baud_combo.pack(side=tk.LEFT, padx=(0, 15))

        self.btn_connect = tk.Button(right_container, text="Connect", command=self._toggle_connect, 
                                   bg="#dddddd", font=("PT Sans", 10, "bold"), width=12)
        self.btn_connect.pack(side=tk.LEFT)

    def create_parameter_area(self, parent):
        btn_frame = tk.Frame(parent, pady=5)
        btn_frame.pack(fill="x")
        btn_font = ("PT Sans", 9, "bold")
        
        self.btn_record = tk.Button(btn_frame, text="START LOGGING", command=self._toggle_recording, 
                                  bg="#e6f7ff", font=btn_font, width=20, state="disabled")
        self.btn_record.pack(side=tk.LEFT, padx=5)
        
        self.lbl_log_status = tk.Label(btn_frame, text="Log Status: IDLE", font=("PT Sans", 9), fg="gray")
        self.lbl_log_status.pack(side=tk.LEFT, padx=15)

        list_frame = tk.Frame(parent)
        list_frame.pack(fill="both", expand=True, pady=(10,0))
        canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        headers = [("Parameter Name", 40), ("Current Value", 15), ("Unit", 10)]
        header_font = ("PT Sans", 10, "bold")
        for col, (text, width) in enumerate(headers):
            tk.Label(self.scrollable_frame, text=text, font=header_font, width=width, 
                     anchor="w" if col==0 else "center", bg="#e8e8e8", relief="flat").grid(row=0, column=col, padx=2, pady=2, sticky="ew")

        row_font = ("PT Sans", 10)
        mono_font = ("Consolas", 10)
        
        for idx, h in enumerate(PARSED_HEADERS, start=1):
            bg_color = "#ffffff" if idx % 2 == 0 else "#f9f9f9"
            
            tk.Label(self.scrollable_frame, text=h['name'], anchor="w", bg=bg_color, font=row_font).grid(row=idx, column=0, padx=5, pady=2, sticky="nsew")
            
            entry_frame = tk.Frame(self.scrollable_frame, bg=bg_color)
            entry_frame.grid(row=idx, column=1, padx=2, pady=2, sticky="nsew")
            entry = tk.Entry(entry_frame, width=15, justify="center", font=mono_font, relief="flat", bg=bg_color)
            entry.insert(0, "--")
            entry.configure(state="readonly") 
            entry.pack(pady=2)
            
            key = h.get('key') or h.get('calc_key') or h.get('name')
            self.entries[key] = entry 
            
            tk.Label(self.scrollable_frame, text=h['unit'], fg="#0066cc", bg=bg_color, font=row_font).grid(row=idx, column=2, padx=2, pady=2, sticky="nsew")

        def _on_mousewheel(event): canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        list_frame.bind('<Enter>', lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        list_frame.bind('<Leave>', lambda e: canvas.unbind_all("<MouseWheel>"))

    def _scan_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_combo['values'] = [p.device for p in ports]
        if not ports: self.port_combo.set("")
        else: self.port_combo.current(0)

    def _toggle_connect(self):
        if not self.is_connected:
            port = self.port_combo.get()
            baud = self.baud_combo.get()
            if not port: return
            
            try:
                self.serial_thread = SerialWorker(port, int(baud), self.serial_data_queue, self.status_queue, self.gui_log_queue)
                self.serial_thread.start()
                self.is_connected = True
                
                self.btn_connect.config(text="Disconnect", bg="#ffcccc")
                self.port_combo.config(state="disabled")
                self.baud_combo.config(state="disabled")
                self.btn_record.config(state="normal")
            except Exception as e:
                self.log_gui(f"Connection Failed: {e}")
                messagebox.showerror("Error", str(e))
        else:
            self._disconnect()

    def _disconnect(self):
        if self.csv_thread: self._toggle_recording()
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread = None
            
        self.is_connected = False
        self.btn_connect.config(text="Connect", bg="#dddddd")
        self.port_combo.config(state="normal")
        self.baud_combo.config(state="normal")
        self.btn_record.config(state="disabled")
        self.log_gui("Disconnected.")

    def _toggle_recording(self):
        if self.csv_thread is None:
            fname = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Log", "*.csv")], title="Save Log File")
            if fname:
                # 1. Prevent Sleep
                set_system_awake(True)
                
                # 2. Start Logger
                self.csv_thread = CSVLoggerThread()
                self.csv_thread.start_logging(fname)
                self.btn_record.config(text="STOP LOGGING", bg="#ffe6e6")
                self.lbl_log_status.config(text=f"RECORDING to {os.path.basename(fname)}", fg="red")
                self.log_gui(f"Started logging to {fname} (System Sleep Disabled)")
        else:
            # 1. Stop Logger
            self.csv_thread.stop_logging()
            self.csv_thread = None
            
            # 2. Allow Sleep
            set_system_awake(False)
            
            self.btn_record.config(text="START LOGGING", bg="#e6f7ff")
            self.lbl_log_status.config(text="IDLE", fg="gray")
            self.log_gui("Stopped logging (System Sleep Enabled)")

    def _system_tick(self):
        while not self.gui_log_queue.empty():
            msg = self.gui_log_queue.get_nowait()
            self.log_gui(msg, internal=True)

        while not self.status_queue.empty():
            msg_type, msg_val = self.status_queue.get_nowait()
            if msg_type == "ERROR":
                self._disconnect()
                messagebox.showerror("Connection Error", f"Lost Connection:\n{msg_val}")

        while not self.serial_data_queue.empty():
            rx_time, data = self.serial_data_queue.get_nowait()
            
            if self.csv_thread and self.csv_thread.running:
                self.csv_thread.queue.put((rx_time, data['flat'], data['stats']))

            self._update_gui(data)
            
        self.root.after(50, self._system_tick)

    def _update_gui(self, data):
        flat = data['flat']
        stats = data['stats']
        flat_idx = 0
        
        for h in PARSED_HEADERS:
            key = h.get('key') or h.get('calc_key') or h.get('name')
            if key not in self.entries: continue
            
            val = 0
            val_str = "--"
            
            if h['type'] == 'calc':
                val = stats.get(h['key'], 0)
            elif h['type'] == 'bit':
                val = flat[flat_idx]
                flat_idx += 1
            else:
                val = flat[flat_idx]
                flat_idx += 1
            
            # Dynamic Formatting based on Factor
            if h['type'] == 'bit':
                val_str = "ON" if val else "OFF"
            else:
                val_str = h['fmt'].format(val)
            
            entry = self.entries[key]
            entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, val_str)
            entry.configure(state="readonly")

    def log_gui(self, msg, internal=False):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = BMS_Logger_App(root)
    root.mainloop()