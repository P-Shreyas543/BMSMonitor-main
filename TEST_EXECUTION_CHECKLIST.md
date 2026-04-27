# BMS Monitor - Test Execution Checklist

Use this checklist to track test execution. Mark each test with:
- ✅ PASS - Test passed as expected
- ❌ FAIL - Test did not pass; add notes
- ⊘ SKIP - Test skipped; add reason
- 🔄 IN PROGRESS - Currently testing

---

## SMOKE TEST (Quick Validation - 10 min)

Test Date: __________ | Tester: ________________

### Startup & Basic UI
- [ ] ✅ App launches without errors
- [ ] ✅ Main window appears with correct title and size
- [ ] ✅ Header with [DECIBELS] logo/text visible
- [ ] ✅ Connection controls visible and enabled
- [ ] ✅ Parameter list visible (scrollable)
- [ ] ✅ System log panel visible
- [ ] ✅ Status bar shows "Ready..." message

### Port Detection
- [ ] ✅ "Refresh" button works - re-scans COM ports
- [ ] ✅ At least one COM port detected or message shown
- [ ] ✅ Baud rate dropdown populated (14 rates)
- [ ] ✅ Default baud rate is 115200

### Basic Connection (if BMS available)
- [ ] ✅ Can select COM port from dropdown
- [ ] ✅ "Connect" button clickable
- [ ] ✅ Status updates while connecting
- [ ] ✅ Connection succeeds or shows error dialog

### No Crashes
- [ ] ✅ No exceptions in console
- [ ] ✅ No frozen/unresponsive UI
- [ ] ✅ Window can be resized
- [ ] ✅ Window can be closed gracefully

**Smoke Test Result:** ☐ PASS ☐ FAIL ☐ PARTIAL

Notes: ________________________________________________________________

---

## SERIAL CONNECTION TESTS

### Test: Q1.1.1 - Connect to Valid COM Port

Precondition: BMS device connected via serial/USB, device is powered

- [ ] COM port appears in dropdown after refresh
- [ ] Select COM port from dropdown
- [ ] Baud rate set to 115200 (or BMS configured rate)
- [ ] Click "Connect" button
- [ ] Connection badge changes to "CONNECTED" (green)
- [ ] Status bar shows "Connected to {PORT} @ {BAUD} bps"
- [ ] "Connect" button text changes to "Disconnect"
- [ ] Port and baud dropdowns are now disabled (grayed)
- [ ] "SAVE LOG" button becomes enabled
- [ ] Log shows: "Connected to {PORT} @ {BAUD}bps"

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Actual Connection Time: __________ | BMS Device: ________________

Notes: ________________________________________________________________

---

### Test: Q1.1.2 - Graceful Disconnection Handling

Precondition: Connected to active BMS device

- [ ] Unplug USB/serial cable from device
- [ ] Wait 2-5 seconds for timeout detection
- [ ] Error dialog appears: "Connection Error"
- [ ] Status bar shows "Connection lost: ..."
- [ ] Connection badge changes to "DISCONNECTED" (red)
- [ ] All data fields reset to "--"
- [ ] Frame counter resets to 0
- [ ] "Connect" button re-enables
- [ ] Port/baud dropdowns re-enabled
- [ ] "SAVE LOG" button disabled
- [ ] App does NOT crash or freeze

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Time to Detect Disconnection: __________ sec

Notes: ________________________________________________________________

---

### Test: Q1.1.3 - Invalid/Busy COM Port Error Handling

Precondition: COM port exists but is busy (open in another app)

- [ ] Open second serial application (e.g., PuTTY) on COM3
- [ ] Try to connect to COM3 from BMS Monitor
- [ ] Connection fails immediately
- [ ] Friendly error dialog appears describing the issue
- [ ] Error mentions port is busy/in use
- [ ] App remains responsive
- [ ] Can retry connection after closing conflicting app

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Error Message Shown: ________________________________________________________

Notes: ________________________________________________________________

---

### Test: Q1.1.4 - Baud Rate Selection

Precondition: BMS device configured for non-default rate

Expected baud rates in dropdown:
- [ ] 300 bps
- [ ] 600 bps
- [ ] 1200 bps
- [ ] 2400 bps
- [ ] 4800 bps
- [ ] 9600 bps
- [ ] 14400 bps
- [ ] 19200 bps
- [ ] 38400 bps
- [ ] 57600 bps
- [ ] 115200 bps (DEFAULT - should be pre-selected)
- [ ] 230400 bps
- [ ] 460800 bps
- [ ] 921600 bps

Actions:
- [ ] Select alternative baud rate (e.g., 9600)
- [ ] Connect with selected rate
- [ ] If BMS supports rate: connection succeeds
- [ ] If BMS doesn't support rate: connection times out or fails appropriately

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Rates Verified: __________________ | BMS Baud Capability: __________

Notes: ________________________________________________________________

---

### Test: Q1.1.5 - Port Refresh Button

Precondition: USB/serial device available

Initial State:
- [ ] Note current COM ports in dropdown: ____________________________

Actions:
- [ ] Plug in new USB-to-serial device
- [ ] Wait 2 seconds for OS to recognize
- [ ] Click "⟳" refresh button
- [ ] New port appears in dropdown
- [ ] Status bar updates: "Detected {N} serial port(s)"

Cleanup:
- [ ] Unplug device
- [ ] Click refresh
- [ ] Port removed from dropdown

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Ports Detected Before: __________ | Ports Detected After: __________

Notes: ________________________________________________________________

---

## DATA RECEPTION TESTS

### Test: Q1.2.1 - All BMS Data Fields Display

Precondition: Connected to BMS with active data stream (≥ 1 frame received)

Field Verification Checklist (scroll through parameter list):

#### Pack/System Values
- [ ] Pack Voltage (V): shows numeric value (e.g., 48.234 V)
- [ ] Pack Current (A): shows numeric value (positive or negative)
- [ ] Get Value Status (Enum): shows numeric value
- [ ] Load Voltage (V): shows numeric value
- [ ] BMS State (Enum): shows numeric value
- [ ] SoC (OCV) (%): shows percentage value
- [ ] SoC (Coulomb) (%): shows percentage value
- [ ] SoH (%): shows percentage value
- [ ] Cycle Count (Cycles): shows numeric value
- [ ] Cumulative Cap (Ah): shows numeric value

#### Cell Voltages (count: 14)
- [ ] Cell Voltage 1-14: ALL show values in V (not "--")

#### Temperatures (count: 8)
- [ ] BCC Temperature: shows °C value
- [ ] Cell Temperature 1-7: ALL show °C values

#### Status Bits
- [ ] Main FET Status: shows 0 or 1
- [ ] Pre Charge FET Status: shows 0 or 1

#### Balancing Status
- [ ] Cell 1 Balancing - Cell 14 Balancing: ALL show 0 or 1

#### Fault Bits (11 bits)
- [ ] Cell OV: 0 or 1
- [ ] Cell UV: 0 or 1
- [ ] Pack OV: 0 or 1
- [ ] Pack UV: 0 or 1
- [ ] V Fault: 0 or 1
- [ ] OC: 0 or 1
- [ ] OT: 0 or 1
- [ ] UT: 0 or 1
- [ ] OverChg: 0 or 1
- [ ] OverDsg: 0 or 1
- [ ] StatusFault: 0 or 1

#### Other Temperatures
- [ ] Bal. Resistor Temp 1-3: ALL show °C values
- [ ] Pre-Charge Res. Temp: shows °C value
- [ ] MOSFET Temp 1-2: ALL show °C values
- [ ] Ambient Temp: shows °C value

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Total Fields Verified: __________/70+ | Missing Fields: _________________

Notes: ________________________________________________________________

---

### Test: Q1.2.2 - Calculated Statistics Accuracy

Precondition: Connected to BMS with stable cell voltages

Procedure:
1. Note displayed Cell voltages (all 14):
   - Cell 1: _________ V
   - Cell 2: _________ V
   - Cell 3: _________ V
   - ... (list individually)

2. Manual Calculation:
   - [ ] Cell Min = _________ V
   - [ ] Cell Max = _________ V
   - [ ] Cell Diff (Max - Min) = _________ V
   - [ ] Cell Sum (total) = _________ V
   - [ ] Cell Avg (Sum / 14) = _________ V

3. Compare with Display:
   - [ ] Cells Min: App shows _________ V | Manual: _________ V | MATCH ☐
   - [ ] Cells Max: App shows _________ V | Manual: _________ V | MATCH ☐
   - [ ] Cells Diff: App shows _________ V | Manual: _________ V | MATCH ☐
   - [ ] Cells Sum: App shows _________ V | Manual: _________ V | MATCH ☐
   - [ ] Cells Avg: App shows _________ V | Manual: _________ V | MATCH ☐

4. Temperature Stats:
   - [ ] Temps Max: App shows _________ °C | Highest sensor: _________ °C | MATCH ☐
   - [ ] Temps Avg: App shows _________ °C | Manual avg: _________ °C | MATCH ☐

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Calculation Accuracy: ☐ All match ☐ Rounding acceptable ☐ Significant error

Notes: ________________________________________________________________

---

### Test: Q1.2.3 - Frame Counter Accuracy

Precondition: Connected to BMS with active data stream

Procedure:
1. Observe initial frame counter: Frames: __________
2. Wait exactly 10 seconds
3. Note counter after 10 sec: Frames: __________
4. Wait another 10 seconds
5. Note counter after 20 sec: Frames: __________

Verification:
- [ ] Counter increased from step 1 to step 3
- [ ] Counter increased from step 3 to step 5
- [ ] Increment appears consistent (typical BMS transmits ~10 Hz)
- [ ] No frame skips/gaps observed
- [ ] Counter never decreases

Calculations:
- [ ] Frame rate: (Counter_20sec - Counter_0sec) / 20 = _________ Hz
- [ ] Expected rate (typical): ~10 Hz
- [ ] Actual rate within ±2 Hz of expected: ☐ YES ☐ NO

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Frame Transmission Rate: _________ Hz | Expected: ~10 Hz

Notes: ________________________________________________________________

---

### Test: Q1.2.4 - Corrupt Frame Handling

Precondition: Serial monitoring tool available (e.g., COM port sniffer)

Procedure:
1. Connect to active BMS
2. Use serial sniffer to inject corrupted frame with:
   - Bad CRC
   - Wrong sync header
   - Truncated payload
3. Observe application behavior

Expected Behavior:
- [ ] App detects corrupt frame
- [ ] Log shows: "Corrupt frame. Sync lost."
- [ ] App resyncs to next valid frame
- [ ] Valid data continues to display
- [ ] No crash or freeze
- [ ] Next valid frame displays correctly

**Result:** ☐ PASS ☐ FAIL ☐ SKIP (requires special equipment)

Frames Injected: __________ | Frames Recovered: __________ | Recovery Time: __________ sec

Notes: ________________________________________________________________

---

### Test: Q1.2.5 - Last Packet Timestamp

Precondition: Connected to BMS

Procedure:
1. Note current system time: __________
2. Check "Last Packet: {TIME}" shown in stats
3. Compare displayed time vs system time

Verification:
- [ ] Timestamp shows recent time (within 1 second of system clock)
- [ ] Timestamp updates with each new frame
- [ ] Time never goes backward (monotonically increasing)
- [ ] Format is readable and accurate

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

System Clock: __________ | App Display: __________ | Difference: __________ sec

Notes: ________________________________________________________________

---

## CSV LOGGING TESTS

### Test: Q1.3.1 - Save CSV Log File

Precondition: Connected to BMS with active data transmission

Procedure:
1. Click "SAVE LOG" button
2. [ ] File dialog opens with default directory
3. [ ] Default filename: bms_monitor_{DATE}_{TIME}.csv
4. [ ] Accept dialog (save to default location or custom location)
5. [ ] Note filename: ______________________________________________________________
6. [ ] Wait 10 seconds and observe data recording
7. [ ] Button text changes to "STOP SAVE"
8. [ ] Button background color changes to red
9. [ ] Stats label shows: "RECORDING to {FILENAME}"
10. [ ] Status bar shows: "Recording monitor data to {FILENAME}"
11. [ ] Log shows connection message about recording

Actions - Stop Recording:
12. [ ] Click "STOP SAVE" button
13. [ ] Button resets to "SAVE LOG" (blue background)
14. [ ] Stats label shows: "Log Status: IDLE"

File Verification:
15. [ ] File exists at saved location: ✓ YES ✓ NO
16. [ ] File size > 0 bytes: __________ bytes
17. [ ] File is valid CSV (can be opened): ✓ YES ✓ NO
18. [ ] File has data rows (not empty): ✓ YES ✓ NO

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

CSV File Path: ________________________________________________________________

CSV File Size: __________ bytes | Duration Recorded: __________ sec | Rows: __________

Notes: ________________________________________________________________

---

### Test: Q1.3.2 - CSV Header Format

Precondition: CSV file created in Q1.3.1

Procedure:
1. Open CSV file in text editor (Notepad, VS Code)
2. Examine first row (header row)

Expected Header Format:
```
Timestamp_Sec,ISO_Time,Pack Voltage,Pack Current,...[all 70+ fields]
```

Field Verification:
- [ ] First column: "Timestamp_Sec"
- [ ] Second column: "ISO_Time"
- [ ] Next columns: field names match GUI display
- [ ] Total columns ≥ 72 (2 timestamp + 70+ data fields)
- [ ] No blank columns
- [ ] No duplicate column names

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Total Header Columns: __________ | Format Correct: ☐ YES ☐ NO

Notes: ________________________________________________________________

---

### Test: Q1.3.3 - CSV Data Values Accuracy

Precondition: CSV file with data from Q1.3.1

Procedure:
1. While recording, note a specific value on screen:
   - Field: ____________________
   - Displayed value: __________________
   - Displayed unit: __________

2. Open CSV file
3. Find corresponding data row (check timestamp)
4. Find column for that field
5. Note CSV value: __________________

Verification:
- [ ] CSV value matches displayed value (accounting for formatting)
- [ ] Value format is numeric (no errors)
- [ ] All rows have values (no empty cells)
- [ ] Timestamp column increases monotonically

Additional Checks (spot 5 fields):
- [ ] Field 1: Display __________ | CSV __________ | MATCH ☐
- [ ] Field 2: Display __________ | CSV __________ | MATCH ☐
- [ ] Field 3: Display __________ | CSV __________ | MATCH ☐
- [ ] Field 4: Display __________ | CSV __________ | MATCH ☐
- [ ] Field 5: Display __________ | CSV __________ | MATCH ☐

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Fields Verified: __________ / 5 | Accuracy: ___________% 

Notes: ________________________________________________________________

---

### Test: Q1.3.4 - Daily Log Rotation

Precondition: System time can be adjusted OR natural midnight crossing is feasible

Procedure:
1. Start recording: bms_monitor_2024-12-31.csv
2. Set system time to 23:58:00 on Dec 31
3. Continue recording
4. When timer reaches 00:05 on Jan 1:
   - [ ] New file created: bms_monitor_2025-01-01.csv
   - [ ] Logging continues without interruption
   - [ ] First file properly closed and finalized
5. Stop recording

Verification:
- [ ] Both files created: ☐ YES ☐ NO
- [ ] First file: __________ rows, __________ bytes
- [ ] Second file: __________ rows, __________ bytes
- [ ] No data loss during rotation
- [ ] Each file has correct headers
- [ ] Timestamps continuous across files

**Result:** ☐ PASS ☐ FAIL ☐ SKIP (requires time adjustment)

Date Before: __________ | Date After: __________ | Files Created: __________

Notes: ________________________________________________________________

---

### Test: Q1.3.5 - Stop and Restart Logging

Precondition: Connected to BMS with data stream

Procedure:
1. Click "SAVE LOG" → save as "log_session1.csv"
2. Record for 5 seconds
3. Click "STOP SAVE"
4. Click "SAVE LOG" → save as "log_session2.csv"  
5. Record for 5 seconds
6. Click "STOP SAVE"

Verification:
- [ ] First file created and closed properly
- [ ] Second file created as separate file
- [ ] Both files contain valid data
- [ ] log_session1.csv size > 0: __________ bytes
- [ ] log_session2.csv size > 0: __________ bytes
- [ ] Both files have headers
- [ ] No data overlap between files

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

File 1 Rows: __________ | File 2 Rows: __________ | Total Data Loss: __________

Notes: ________________________________________________________________

---

## UI/DISPLAY TESTS

### Test: Q1.4.1 - All Parameters Displayed

Precondition: Connected to BMS

Procedure:
1. [ ] Scroll through entire parameter list
2. [ ] Count visible parameter rows
3. [ ] Verify no fields are cut off or hidden

Expected: 70+ rows visible with scrolling

- [ ] Header row visible: "Parameter Name | Current Value | Unit | Data Type"
- [ ] Alternating row colors visible (white/gray) for readability
- [ ] Vertical scrollbar appears on right
- [ ] Scrollbar functional (can scroll up/down)
- [ ] All 70+ parameters fit on screen with scrolling

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Total Rows Visible: __________ | Scrollbar Present: ☐ YES ☐ NO

Notes: ________________________________________________________________

---

### Test: Q1.4.2 - Unit Display

Precondition: Connected to BMS with data

Procedure:
1. Scroll through parameter list
2. Verify each field's unit column

Spot-check units:
- [ ] Pack Voltage → "V" ✓
- [ ] Pack Current → "A" ✓
- [ ] Cell Voltages → "V" ✓
- [ ] Temperatures → "Deg C" ✓
- [ ] FET Status bits → "Bit" ✓
- [ ] SoC → "%" ✓
- [ ] Cycle Count → "Cycles" ✓

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Units Correct: ________ / 7 fields verif

ied

Notes: ________________________________________________________________

---

### Test: Q1.4.3 - Window Resizing

Precondition: App running

Procedure:
1. [ ] Resize window to minimum size (1120 x 680)
   - Window allows/enforces minimum size
   - No elements overlap or cut off
2. [ ] Resize window to larger (e.g., 1600 x 900)
   - Parameter list expands appropriately
   - Scrollbar adjusts
   - All text remains readable
3. [ ] Resize to very small then very large
   - Elements reflow correctly
   - No permanent layout issues

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Minimum Size Enforced: ☐ YES ☐ NO | Layout Responsive: ☐ YES ☐ NO

Notes: ________________________________________________________________

---

### Test: Q1.4.4 - Status Badge Colors

Precondition: App running

Procedure:
1. **Disconnected State:**
   - [ ] Badge shows "DISCONNECTED"
   - [ ] Background color: RED/LIGHT RED (#fce8e6)
   - [ ] Text color: RED/DARK RED

2. **Connecting State** (if device connection is slow):
   - [ ] Badge shows "CONNECTING..."
   - [ ] Background color: ORANGE/LIGHT ORANGE (#fdf0d5)
   - [ ] Text color: ORANGE

3. **Connected State:**
   - Click Connect (if BMS available)
   - [ ] Badge shows "CONNECTED"
   - [ ] Background color: GREEN/LIGHT GREEN (#dff3e1)
   - [ ] Text color: GREEN

4. **Recording State:**
   - Click "SAVE LOG"
   - [ ] "SAVE LOG" button background: LIGHT BLUE (#e6f7ff)
   - [ ] "SAVE LOG" button text: "STOP SAVE"
   - [ ] "SAVE LOG" button background: RED/LIGHT RED (#ffe6e6)

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Badge Colors Correct: ☐ YES ☐ NO | Button Colors Correct: ☐ YES ☐ NO

Notes: ________________________________________________________________

---

### Test: Q1.4.5 - System Log Display

Precondition: App running, will perform actions

Procedure:
1. Perform various actions (connect, disconnect, record, etc.)
2. Observe "System Log" area at bottom

Verification:
- [ ] Log shows messages for key events
- [ ] Messages include timestamps or are sequenced
- [ ] New messages appear at bottom
- [ ] Log is scrollable if many messages
- [ ] Log is read-only (cannot edit text)
- [ ] Old messages don't disappear abruptly
- [ ] Messages are clear and informative

Example messages should include:
- [ ] "Opening serial connection on COM{X} @ {BAUD}bps"
- [ ] "Connected to COM{X} @ {BAUD}bps"
- [ ] "Started logging to {PATH}"
- [ ] "Stopped logging"
- [ ] "Disconnected"

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Sample Messages Seen: _________________________________________________________

Notes: ________________________________________________________________

---

## CONTROL BUTTON TESTS

### Test: Q1.5.1 - Clear View Button

Precondition: Connected to BMS with data streaming and frame counter > 0

Procedure:
1. Note current state:
   - Frame count: __________
   - Last packet time: __________
   - Data fields populated: ☐ YES
2. Click "CLEAR VIEW" button
3. Observe immediate effect

Verification:
- [ ] All data value fields reset to "--"
- [ ] Frame counter resets to "Frames: 0"
- [ ] Last packet time resets to "--"
- [ ] Stats label shows "Log Status: IDLE"
- [ ] Connection remains CONNECTED
- [ ] Serial thread still running
- [ ] New data starts populating again after click

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

State Before Clear: Frames=__________ | State After Clear: Frames=__________

Notes: ________________________________________________________________

---

### Test: Q1.5.2 - Button Enable/Disable States

Precondition: App running

Procedure:

**Disconnected State:**
- [ ] "Connect" button: ENABLED (normal color)
- [ ] "⟳" Refresh button: ENABLED
- [ ] COM port dropdown: ENABLED (readable)
- [ ] Baud dropdown: ENABLED (readable)
- [ ] "SAVE LOG" button: DISABLED (grayed out)
- [ ] "CLEAR VIEW" button: ENABLED

**Connecting State** (observe briefly during connection):
- [ ] "Connect" button: DISABLED, text "Connecting..."
- [ ] "⟳" Refresh button: DISABLED
- [ ] COM port dropdown: DISABLED (locked)
- [ ] Baud dropdown: DISABLED (locked)
- [ ] "SAVE LOG" button: DISABLED

**Connected State** (if BMS available):
- [ ] "Connect" button: ENABLED, text "Disconnect"
- [ ] "⟳" Refresh button: DISABLED
- [ ] COM port dropdown: DISABLED (locked)
- [ ] Baud dropdown: DISABLED (locked)
- [ ] "SAVE LOG" button: ENABLED

**Recording State:**
- [ ] "SAVE LOG" button: text changed to "STOP SAVE"
- [ ] Connection controls: remain disabled

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

States Verified: __________ / 5 | Button States Correct: ☐ YES ☐ NO

Notes: ________________________________________________________________

---

## PERFORMANCE TESTS

### Test: Q3.1 - High-Frequency Data Stream

Precondition: BMS can transmit at high rates

Procedure:
1. Connect to BMS configured for high frame rate (50-100 Hz if possible)
2. Monitor system resources for 5-10 minutes:
   - [ ] Open Windows Task Manager
   - [ ] Note CPU usage: initial __________%, peak __________%, avg __________%
   - [ ] Note memory usage: initial __________ MB, peak __________ MB
   - [ ] Check UI responsiveness: ☐ Smooth ☐ Responsive ☐ Some lag ☐ Frozen
3. Watch for any errors or dropped frames

Verification:
- [ ] CPU < 15% continuously
- [ ] Memory stable (max increase < 50 MB)
- [ ] UI remains responsive
- [ ] Frame counter continuous (no skips)
- [ ] All data values display correctly
- [ ] No crashes after 5+ minutes

**Result:** ☐ PASS ☐ FAIL ☐ SKIP (high-rate device required)

CPU Usage: Avg __________% | Peak __________% | Memory: Avg __________ MB | Peak __________ MB

Notes: ________________________________________________________________

---

### Test: Q3.2 - Large CSV File Handling

Precondition: Recording to CSV for 1+ hours

Procedure:
1. Record continuously for ≥ 1 hour
2. Note resulting file size: __________ MB / __________ KB
3. Note row count: __________ rows
4. Stop recording
5. Open CSV file in Excel or text editor

Verification:
- [ ] File opens without error
- [ ] File is readable and not corrupted
- [ ] Can scroll through all rows
- [ ] Formulas/calculations (if any) work
- [ ] File can be saved in Excel format
- [ ] Memory usage reasonable when file open

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

File Size: __________ MB | Row Count: __________ | Open Time: __________ sec

Notes: ________________________________________________________________

---

### Test: Q3.3 - Memory Leak Detection

Precondition: System with task manager available

Procedure:
1. Start BMS Monitor
2. Connect to BMS
3. Receive data continuously for 4+ hours
4. Take memory measurements every 30 minutes

Time | Memory Usage | Change from Start
-----|--------------|------------------
T=0min | __________ MB | 0 MB (baseline)
T=30min | __________ MB | __________ MB
T=60min | __________ MB | __________ MB
T=90min | __________ MB | __________ MB
T=120min | __________ MB | __________ MB
... (continue up to 4+ hours)

Verification:
- [ ] Memory increases < 100 MB total over 4 hours
- [ ] No continuous growth pattern
- [ ] Memory remains stable after 1 hour
- [ ] After disconnect: memory returns to near baseline
- [ ] No obvious memory leak detected

**Result:** ☐ PASS ☐ FAIL ☐ SKIP (requires 4+ hours)

Initial Memory: __________ MB | Final Memory: __________ MB | Total Growth: __________ MB

Memory Leak Assessment: ☐ NONE ☐ MINOR (< 50 MB/hour) ☐ SIGNIFICANT

Notes: ________________________________________________________________

---

## COMPATIBILITY & BUILD TESTS

### Test: Q4.1 - Windows Compatibility

Device: _________________ | OS Version: _________________

Procedure:
1. Install latest Windows updates
2. Verify Python 3.10+ installed
3. Install dependencies: `pip install -r requirements.txt`
4. Run `python BMS_Monitor.py`

Verification:
- [ ] App launches without errors
- [ ] All features work (connect, data display, logging)
- [ ] No OS-specific errors
- [ ] Window displays correctly

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

OS: _________________ | Python Version: __________ | Issues: _________________

Notes: ________________________________________________________________

---

### Test: Q4.2 - Dependencies Installation

Procedure:
1. Fresh Python environment (venv or conda)
2. Run: `pip install -r requirements.txt`
3. Check installation success

Expected Packages:
- [ ] pyserial: installed, version __________
- [ ] pillow: installed, version __________
- [ ] tkinter: (included with Python)

Verification:
- [ ] All dependencies installed successfully
- [ ] No conflicts or errors reported
- [ ] Can import all modules in Python REPL:
  - [ ] `import serial` → OK
  - [ ] `import PIL` → OK
  - [ ] `import tkinter` → OK

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Install Time: __________ sec | Errors: ___________________

Notes: ________________________________________________________________

---

### Test: Q4.3 - Standalone .exe Build

Procedure:
1. Run: `python build.py`
2. Wait for build to complete
3. Verify dist\DecibelsBMSMonitor.exe exists
4. Run .exe on clean machine (no Python)

Verification:
- [ ] Build completes without errors
- [ ] Build time: __________ minutes
- [ ] .exe file size: __________ MB
- [ ] .exe runs on clean machine without Python installed
- [ ] All features work identically to source version
- [ ] Can connect to BMS
- [ ] Can record CSV logs
- [ ] Window icon displays

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Build Time: __________ min | .exe Size: __________ MB | Functionality: 100% ☐ Yes ☐ No

Notes: ________________________________________________________________

---

## SECURITY & EDGE CASES

### Test: Q2.1 - Data Transmission Timeout

Precondition: Connected to BMS, can stop transmission

Procedure:
1. Connect and receiving data normally
2. Stop BMS transmission (or use device with power control)
3. Observe app behavior after data stops

Verification:
- [ ] App detects loss after __________ seconds
- [ ] Status updates appropriately
- [ ] User can manually disconnect if needed
- [ ] App remains responsive
- [ ] No crash or hang

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Time to Detect Loss: __________ sec | User Action Required: ☐ None ☐ Manual disconnect

Notes: ________________________________________________________________

---

### Test: Q2.2 - Rapid Connect/Disconnect

Procedure:
1. Connected to BMS (or dummy port)
2. Rapidly click Connect → Disconnect → Connect → Disconnect (5 times fast)

Verification:
- [ ] No crashes or exceptions
- [ ] UI remains responsive throughout
- [ ] No threads left hanging
- [ ] App stable after rapid toggling
- [ ] Final state correct (disconnected or connected)

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Cycles Completed: __________ | Failures: __________

Notes: ________________________________________________________________

---

### Test: Q2.3 - CSV Permission Denied

Procedure:
1. Start recording to C:\Users\{User}\Documents\
2. While recording, change directory permissions (remove write access)
3. Observe error handling

Verification:
- [ ] Error detected within __________ seconds
- [ ] Error dialog: "CSV logging failed"
- [ ] Specific error message shown
- [ ] Recording stops gracefully
- [ ] App recovers (can resume operations)

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Error Detected In: __________ sec | Recovery: ☐ Automatic ☐ User restart required

Notes: ________________________________________________________________

---

### Test: Q2.4 - Missing Logo/Icon Files

Procedure:
1. Rename or delete: logo_sq.ico, logo_sq.png, logo_rec.png
2. Run BMS Monitor

Verification:
- [ ] App starts without crashing
- [ ] Fallback [DECIBELS] text appears instead of logo
- [ ] Window title bar icon uses default/fallback
- [ ] All features work normally
- [ ] No errors in log

**Result:** ☐ PASS ☐ FAIL ☐ SKIP

Fallback Display: ☐ Text label ☐ System icon ☐ Blank space

Notes: ________________________________________________________________

---

## FINAL SIGN-OUT

### Overall Test Summary

| Category | Tests | Passed | Failed | Skipped | Pass Rate |
|----------|-------|--------|--------|---------|-----------|
| Smoke | 10 | ___ | ___ | ___ | ___% |
| Serial Connection | 5 | ___ | ___ | ___ | ___% |
| Data Reception | 5 | ___ | ___ | ___ | ___% |
| CSV Logging | 5 | ___ | ___ | ___ | ___% |
| UI/Display | 5 | ___ | ___ | ___ | ___% |
| Controls | 2 | ___ | ___ | ___ | ___% |
| Performance | 3 | ___ | ___ | ___ | ___% |
| Compatibility | 3 | ___ | ___ | ___ | ___% |
| Edge Cases | 4 | ___ | ___ | ___ | ___% |
| **TOTAL** | **42** | **___** | **___** | **___** | **_%** |

### Test Execution Summary

**Total Test Cases:** 42
**Test Date:** __________
**Tester Name:** __________________________________________
**Tester Email:** __________________________________________

**Critical Issues Found:** _____ | **Major Issues:** _____ | **Minor Issues:** _____

### Go/No-Go Decision

- [ ] **GO** - Application is ready for production/release (≥95% tests passing, no critical failures)
- [ ] **GO with exceptions** - Release with known limitations documented
- [ ] **NO-GO** - Critical failures must be resolved before release

### Sign-Off

**QA Lead:** _________________________________ | Date: __________

**Developer:** _______________________________ | Date: __________

**Product Manager:** ________________________ | Date: __________

---

## APPENDIX: Issue Tracking

### Critical Issues Found

| ID | Description | Severity | Status | Comments |
|----|-------------|----------|--------|----------|
| 1 | | CRITICAL | ☐ Open ☐ Fixed | |
| 2 | | CRITICAL | ☐ Open ☐ Fixed | |

### Major Issues Found

| ID | Description | Severity | Status | Comments |
|----|-------------|----------|--------|----------|
| 1 | | MAJOR | ☐ Open ☐ Fixed | |
| 2 | | MAJOR | ☐ Open ☐ Fixed | |

### Minor Issues Found

| ID | Description | Severity | Status | Comments |
|----|-------------|----------|--------|----------|
| 1 | | MINOR | ☐ Open ☐ Fixed | |
| 2 | | MINOR | ☐ Open ☐ Fixed | |

---

**END OF TEST CHECKLIST**
