# BMS Monitor - Comprehensive Q&A Testing Plan

## Project Overview
**BMS Monitor** is a Windows desktop application for live BMS (Battery Management System) telemetry monitoring and CSV logging over a serial connection. Built with Tkinter, PySerial, and PIL.

**Key Features:**
- Live BMS data reading over COM port
- Display parsed pack voltage, cell voltages, temperatures, status bits, calculated values
- Automatic CSV logging with daily file rotation
- Windows desktop app with branded icons and version metadata
- Standalone `.exe` build support

---

## 1. FUNCTIONAL TESTING

### 1.1 Serial Connection Management

#### Q1.1.1: Can the application successfully connect to a valid COM port?
**Test Steps:**
1. Open BMS Monitor
2. Open Device Manager and note an active COM port (e.g., COM3)
3. Select the COM port from the dropdown
4. Select baud rate (default: 115200)
5. Click "Connect" button

**Expected Results:**
- Connection status badge changes to "CONNECTED" (green)
- Status bar shows "Connected to {PORT} @ {BAUD} bps."
- "Connect" button changes to "Disconnect"
- COM port and baud rate dropdowns are disabled
- "SAVE LOG" button becomes enabled
- Log area shows connection message

**Acceptance Criteria:** ✓ Status badge and UI reflect connection state

---

#### Q1.1.2: Does the application handle COM port disconnection gracefully?
**Test Steps:**
1. Connect to a valid COM port
2. Physically disconnect the USB/serial cable OR unplug the device
3. Observe application behavior

**Expected Results:**
- Connection error is detected within 5 seconds
- Error dialog appears with message "Connection Error"
- Status becomes "DISCONNECTED"
- UI resets to disconnected state
- All live data displays show "--"

**Acceptance Criteria:** ✓ Error handling is graceful, no crash

---

#### Q1.1.3: What happens when connecting to an invalid/busy COM port?
**Test Steps:**
1. Open another serial terminal (e.g., PuTTY) connected to COM3
2. Try to connect to COM3 from BMS Monitor
3. Observe error handling

**Expected Results:**
- Connection fails immediately
- Friendly error message appears: "The port is busy, locked, or already in use"
- Status shows "Could not open {PORT}"
- Application remains responsive

**Acceptance Criteria:** ✓ Appropriate error message displayed

---

#### Q1.1.4: Can the user select different baud rates?
**Test Steps:**
1. Click the baud rate dropdown
2. Verify all expected rates are present: 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 230400, 460800, 921600
3. Select a different rate and connect
4. Verify connection works with new rate

**Expected Results:**
- All 14 standard baud rates are available
- Default selected is 115200
- Can switch rates when disconnected
- Rates disabled when connected

**Acceptance Criteria:** ✓ All baud rates available and selectable

---

#### Q1.1.5: Does the "Refresh" button update COM port list?
**Test Steps:**
1. Note current COM ports in dropdown
2. Plug in a USB-to-serial device
3. Click "⟳" refresh button
4. Verify new port appears in list

**Expected Results:**
- New COM port appears in dropdown
- Status bar updates: "Detected {N} serial port(s)"
- Dropdown shows sorted port list

**Acceptance Criteria:** ✓ Port list updates correctly

---

### 1.2 Data Reception & Parsing

#### Q1.2.1: Are all expected BMS data fields displayed correctly?
**Test Steps:**
1. Connect to BMS with live data stream
2. Wait for first data frame
3. Verify all 70+ fields populate with values

**Expected Results:**
- Pack Voltage: shows value in V
- Pack Current: shows value in A
- Cell Voltages 1-14: all show values in V
- Temperatures (BCC + Cell): show values in °C
- Status bits (FET Status): show 0 or 1
- Balancing Status: 14-bit field shows balancing states
- Fault Status: 11-bit field shows fault states
- No fields show "--" when connected

**Acceptance Criteria:** ✓ All fields populate; no parsing errors

---

#### Q1.2.2: Are calculated values (min/max/avg/sum/diff) correct?
**Test Steps:**
1. Connect to BMS with stable data
2. Monitor cell voltage stats: Min, Max, Diff, Sum, Avg
3. Monitor temperature stats: Max, Avg
4. Manually verify calculations are correct

**Expected Results:**
- Cell Min = minimum of 14 cell voltages ✓
- Cell Max = maximum of 14 cell voltages ✓
- Cell Diff = Max - Min ✓
- Cell Sum = sum of all 14 cells ✓
- Cell Avg = Sum / 14 ✓
- Temps Max = highest of 8 temperature sensors ✓
- Temps Avg = average of 8 temperature sensors ✓

**Acceptance Criteria:** ✓ All calculations verified mathematically correct

---

#### Q1.2.3: Does the frame counter increment correctly?
**Test Steps:**
1. Connect to live BMS
2. Observe "Frames: ##" counter in stats label
3. Wait 10 seconds and note counter value
4. Wait another 10 seconds and note new counter value

**Expected Results:**
- Counter increments with each received frame
- Increment rate matches serial transmission rate (~10 Hz typical)
- Counter does not skip numbers
- Counter progression is smooth and continuous

**Acceptance Criteria:** ✓ Frame counting is accurate

---

#### Q1.2.4: How does the app handle corrupted serial frames?
**Test Steps:**
1. Use hardware to inject corrupted/invalid frames
2. Observe BMS Monitor behavior
3. Check logs for error messages

**Expected Results:**
- App detects "Corrupt frame" and logs: "Corrupt frame. Sync lost."
- App re-syncs to next valid frame
- No crash or freeze
- Valid frames continue to display

**Acceptance Criteria:** ✓ Graceful handling, continues normal operation

---

#### Q1.2.5: Is the last packet timestamp accurate?
**Test Steps:**
1. Connect to BMS
2. Monitor "Last Packet: {TIME}" in stats
3. Compare against system clock

**Expected Results:**
- Timestamp updates with each frame
- Time is accurate to current system time
- Time advances smoothly (no jumps backward)

**Acceptance Criteria:** ✓ Timestamp accurate and monotonically increasing

---

### 1.3 CSV Logging

#### Q1.3.1: Can the user save logs to CSV?
**Test Steps:**
1. Connect to BMS with data streaming
2. Click "SAVE LOG" button
3. Choose save location and filename
4. Record for 10 seconds
5. Click "STOP SAVE"
6. Verify CSV file created

**Expected Results:**
- File dialog opens with default name "bms_monitor_{DATE}_{TIME}.csv"
- Default directory is user export folder
- CSV file is created at chosen location
- Button changes to "STOP SAVE" (red) while recording
- Log status shows "RECORDING to {FILENAME}"
- Status bar shows recording path
- CSV file is valid (can be opened in Excel)

**Acceptance Criteria:** ✓ CSV file created with correct format

---

#### Q1.3.2: Does the CSV contain correct headers?
**Test Steps:**
1. Record data to CSV (see 1.3.1)
2. Open CSV in text editor
3. Examine header row

**Expected Results:**
- First row contains: "Timestamp_Sec", "ISO_Time", followed by all 70+ field names
- Header names match display names exactly
- No duplicate columns
- Header properly formatted

**Acceptance Criteria:** ✓ CSV headers complete and accurate

---

#### Q1.3.3: Are CSV data values correct?
**Test Steps:**
1. Record 30 seconds of BMS data to CSV
2. Note a specific value displayed (e.g., Pack Voltage = 48.234 V)
3. Find corresponding row in CSV
4. Compare value in CSV vs display

**Expected Results:**
- All numeric values in CSV match GUI display (accounting for formatting)
- Timestamp values increase monotonically
- ISO time format is valid (YYYY-MM-DD HH:MM:SS.ffffff)
- No missing or corrupted values
- Bit fields show 0 or 1 (not raw values)

**Acceptance Criteria:** ✓ CSV data matches display; formatting correct

---

#### Q1.3.4: Does daily log file rotation work?
**Test Steps:**
1. Start recording at 11:55 PM (or use system time manipulation)
2. Record until midnight (00:00)
3. Continue recording for another minute
4. Stop recording
5. Check file system for created files

**Expected Results:**
- Two CSV files created with date suffixes:
  - bms_monitor_2025-03-31.csv
  - bms_monitor_2025-04-01.csv
- Logging continues seamlessly across midnight
- Data not lost during rotation
- No duplicate rows or skipped frames

**Acceptance Criteria:** ✓ Daily rotation works; no data loss

---

#### Q1.3.5: Can logging be stopped and restarted?
**Test Steps:**
1. Start logging to CSV
2. Record for 5 seconds
3. Click "STOP SAVE"
4. Click "SAVE LOG" again
5. Record to new file for 5 seconds
6. Stop

**Expected Results:**
- First file created and properly closed
- Second file created as separate CSV
- Both files contain valid data
- No data loss between sessions
- Each file has headers

**Acceptance Criteria:** ✓ Multiple logging sessions work correctly

---

### 1.4 User Interface & Display

#### Q1.4.1: Does the app display all parameter rows?
**Test Steps:**
1. Connect to BMS
2. Scroll through the parameter list
3. Count total rows that display

**Expected Results:**
- All ~70 parameters visible (with scrolling)
- Column headers: "Parameter Name", "Current Value", "Unit", "Data Type"
- Alternating row colors (white/light gray) for readability
- Scrollbar appears if content exceeds window height
- Mousewheel scrolling works

**Acceptance Criteria:** ✓ All fields displayed; scrolling works

---

#### Q1.4.2: Are units displayed correctly?
**Test Steps:**
1. Connect to BMS
2. Examine unit column
3. Verify units match config

**Expected Results:**
- Pack/Cell Voltages: "V"
- Current: "A"
- Temperatures: "Deg C"
- Status bits: "Bit"
- Percentages (SoC): "%"
- Cycle count: "Cycles"
- Cumulative cap: "Ah"

**Acceptance Criteria:** ✓ All units correct and consistent

---

#### Q1.4.3: Does the app window resize properly?
**Test Steps:**
1. Resize window to minimum size
2. Resize window to larger dimensions
3. Verify layout remains intact

**Expected Results:**
- Minimum window size enforced: 1120x680
- Elements reflow correctly when resized
- Data fields remain readable
- Scrollbar adjusts to new size
- No elements cut off or overlapped

**Acceptance Criteria:** ✓ Window resizing works; layout responsive

---

#### Q1.4.4: Are status badges and colors correct?
**Test Steps:**
1. Disconnect state
2. Connect to BMS
3. Start recording
4. Stop recording

**Expected Results:**
- Disconnected badge: RED "DISCONNECTED" (#fce8e6 background)
- Connecting badge: ORANGE "CONNECTING" (#fdf0d5 background)
- Connected badge: GREEN "CONNECTED" (#dff3e1 background)
- Recording status: RED BG when recording, gray when idle

**Acceptance Criteria:** ✓ Status colors match spec

---

#### Q1.4.5: Does the system log display correctly?
**Test Steps:**
1. Observe the "System Log" area at bottom
2. Perform actions: connect, disconnect, record
3. Check log messages

**Expected Results:**
- Log shows timestamped messages for key events
- New messages appear at bottom
- Old messages scroll out of view if needed
- Log is read-only (cannot edit)
- Messages are clear and informative

**Acceptance Criteria:** ✓ Log messages helpful and clear

---

### 1.5 Connection Control Buttons

#### Q1.5.1: Can user clear/reset display values?
**Test Steps:**
1. Connect and receive data
2. Click "CLEAR VIEW" button
3. Observe display

**Expected Results:**
- All value fields reset to "--"
- Frame counter resets to 0
- Last packet time resets to "--"
- Log status resets to "IDLE"
- Serial connection remains active
- New data populates fields again after button click

**Acceptance Criteria:** ✓ Clear button resets display without disconnecting

---

#### Q1.5.2: Do disabled states work correctly?
**Test Steps:**
1. When disconnected: verify "SAVE LOG" button is disabled (grayed out)
2. When connected: verify "SAVE LOG" button is enabled
3. While connecting: verify "Connect" button shows "Connecting..." and is disabled

**Expected Results:**
- "SAVE LOG" only enabled when connected
- "Refresh" button disabled when connected
- Baud rate dropdown disabled when connected
- COM port dropdown disabled when connected
- Proper visual feedback (button color/state changes)

**Acceptance Criteria:** ✓ Button states match connection status

---

## 2. ERROR HANDLING & EDGE CASES

#### Q2.1: What happens if BMS stops sending data?
**Test Steps:**
1. Connect to BMS
2. Stop BMS transmission
3. Observe timeout behavior

**Expected Results:**
- After 1-2 seconds: status shows connection is still active
- After 10+ seconds: connection loss detected OR continues waiting
- User can manually disconnect
- No crash or hung UI

**Acceptance Criteria:** ✓ Timeout handled appropriately

---

#### Q2.2: Can the app handle rapid connect/disconnect?
**Test Steps:**
1. Click Connect
2. Immediately click Disconnect
3. Repeat 5 times rapidly

**Expected Results:**
- No crashes or hangs
- UI remains responsive
- Thread cleanup happens properly
- No resource leaks

**Acceptance Criteria:** ✓ Rapid toggling handled safely

---

#### Q2.3: What if CSV export directory is deleted?
**Test Steps:**
1. Note export directory
2. Start recording to that location
3. Separately, delete the export directory or revoke write permissions
4. Observe behavior

**Expected Results:**
- Error dialog appears: "CSV logging failed: {REASON}"
- Recording stops
- Log button resets to "SAVE LOG"
- User can retry after fixing permissions

**Acceptance Criteria:** ✓ Graceful failure with user notification

---

#### Q2.4: Can the app handle missing icon/logo files?
**Test Steps:**
1. Rename/delete logo_sq.ico and logo_sq.png
2. Run application
3. Observe behavior

**Expected Results:**
- App starts normally
- Header displays "[DECIBELS]" text instead of logo
- Window title bar icon uses fallback or system default
- No crashes

**Acceptance Criteria:** ✓ Graceful degradation without assets

---

## 3. PERFORMANCE & LOAD TESTING

#### Q3.1: Can the app sustain high-frequency data streams?
**Test Steps:**
1. Configure BMS to transmit at 100 Hz (or max rate)
2. Monitor CPU usage, memory, window responsiveness
3. Run for 1 hour

**Expected Results:**
- CPU usage < 10%
- Memory stable (no growth > 50 MB)
- UI remains responsive
- No dropped frames
- All data accurately recorded

**Acceptance Criteria:** ✓ Performance acceptable for continuous operation

---

#### Q3.2: Are large CSV files handled correctly?
**Test Steps:**
1. Record for 24+ hours continuously
2. Check resulting CSV file size
3. Attempt to open in Excel/viewer

**Expected Results:**
- CSV file handles 1000s of rows without corruption
- File rollover works at midnight
- Can be opened in Excel (even if large)
- All data intact

**Acceptance Criteria:** ✓ Large files manageable

---

#### Q3.3: Does memory gradually increase (leak)?
**Test Steps:**
1. Open app, connect, and receive data for 4+ hours
2. Periodically check Windows Task Manager for memory usage
3. Disconnect and check if memory released

**Expected Results:**
- Memory roughly stable throughout
- No gradual increase > 100 MB over 4 hours
- Memory released after disconnecting
- No obvious memory leaks

**Acceptance Criteria:** ✓ No detected memory leaks

---

## 4. COMPATIBILITY & ENVIRONMENT TESTING

#### Q4.1: Does the app run on Windows 10/11?
**Test Steps:**
1. Install on Windows 10 machine
2. Run and perform basic operations
3. Repeat on Windows 11 machine

**Expected Results:**
- App starts without errors on both versions
- All features work correctly
- No OS-specific errors or crashes

**Acceptance Criteria:** ✓ Confirmed working on target Windows versions

---

#### Q4.2: Are all Python dependencies available?
**Test Steps:**
1. Fresh Windows system with Python 3.10+
2. Run: `pip install -r requirements.txt`
3. Run: `python BMS_Monitor.py`

**Expected Results:**
- All dependencies install successfully
- No conflicts between packages
- App starts and runs normally
- All imports resolve correctly

**Acceptance Criteria:** ✓ All dependencies available and compatible

---

#### Q4.3: Does the compiled .exe work standalone?
**Test Steps:**
1. Build with PyInstaller: `python build.py`
2. Copy `dist/DecibelsBMSMonitor.exe` to another machine without Python
3. Run the .exe

**Expected Results:**
- .exe runs without Python installation
- All features work identically to source version
- Window icon/branding appears correctly
- App can connect and log successfully

**Acceptance Criteria:** ✓ Standalone .exe fully functional

---

## 5. PROTOCOL & DATA INTEGRITY

#### Q5.1: Is CRC16 validation working?
**Test Steps:**
1. Examine protocol parsing code
2. Inject frames with bad CRC
3. Verify rejection

**Expected Results:**
- Frames with invalid CRC are rejected
- "Corrupt frame. Sync lost." logged
- App re-syncs to next valid frame
- Valid frames continue to parse

**Acceptance Criteria:** ✓ CRC validation working

---

#### Q5.2: Are frame formats matched correctly?
**Test Steps:**
1. Verify FRAME_CONFIG vs actual data layout
2. Connect to multiple BMS units if available
3. Verify data parse correctly for each

**Expected Results:**
- All fields parse to correct values
- No off-by-one errors in field positions
- Byte order (little-endian) correct
- Field sizes match config (uint16, int16, uint8, etc.)

**Acceptance Criteria:** ✓ Protocol parsing correct for all variants

---

## 6. BUILD & DEPLOYMENT

#### Q6.1: Can the app be built with PyInstaller?
**Test Steps:**
1. Run: `python build.py`
2. Verify build completes without errors
3. Test resulting .exe

**Expected Results:**
- Build completes in < 2 minutes
- `dist/DecibelsBMSMonitor.exe` created
- Executable is ~100-150 MB (typical for PyInstaller)
- .exe can be executed repeatedly without errors

**Acceptance Criteria:** ✓ Build process works reliably

---

#### Q6.2: Does --clean-only flag work?
**Test Steps:**
1. Build normally: `python build.py`
2. Run: `python build.py --clean-only`
3. Verify artifacts removed

**Expected Results:**
- Build artifacts in `build/` and `dist/` are deleted
- Main script files remain
- Source code untouched

**Acceptance Criteria:** ✓ Clean function works correctly

---

## 7. USABILITY & USER EXPERIENCE

#### Q7.1: Is the UI intuitive for first-time users?
**Test Steps:**
1. Give app to user unfamiliar with it
2. Ask them to: connect, receive data, record log, stop
3. Time how long it takes and note confusion points

**Expected Results:**
- User can complete tasks within 2 minutes
- UI elements are self-explanatory
- Status messages guide user correctly
- No unintuitive button placements

**Acceptance Criteria:** ✓ Intuitive UI, minimal learning curve

---

#### Q7.2: Are error messages helpful?
**Test Steps:**
1. Trigger various errors: bad port, no COM ports available, permission denied, etc.
2. Evaluate error message clarity

**Expected Results:**
- Error messages explain what went wrong
- Error messages suggest remediation (e.g., "Try refreshing ports")
- No obscure error codes shown to user
- Friendly error language

**Acceptance Criteria:** ✓ Error messages informative and user-friendly

---

#### Q7.3: Does the app support dark mode?
**Test Steps:**
1. Enable Windows dark mode
2. Run BMS Monitor
3. Observe appearance

**Expected Results:**
- App displays correctly in dark mode OR
- App remains fully readable even if not optimized for dark mode
- No text becomes unreadable
- Colors remain appropriate

**Acceptance Criteria:** ✓ Acceptable appearance in both light and dark modes

---

## 8. SECURITY CONSIDERATIONS

#### Q8.1: Are COM ports safely enumerated?
**Test Tests:**
1. Connect multiple USB devices
2. Verify app correctly lists only serial ports
3. No crashes when accessing port list

**Expected Results:**
- Only valid serial ports shown
- No attempt to access invalid ports
- Safe handling of permission-denied scenarios
- No security vulnerabilities in port enumeration

**Acceptance Criteria:** ✓ Port enumeration safe and reliable

---

#### Q8.2: Is CSV file path validation adequate?
**Test Steps:**
1. Attempt to save to invalid paths (network drive down, special chars, etc.)
2. Verify safe handling

**Expected Results:**
- Invalid paths rejected with clear error
- App doesn't crash
- User can retry with valid path
- No path traversal vulnerabilities

**Acceptance Criteria:** ✓ Path handling secure

---

## 9. REGRESSION TEST SUITE

### Quick Smoke Test (5 minutes)
1. ✓ App launches
2. ✓ COM ports visible
3. ✓ Can connect (if device available)
4. ✓ Can disconnect
5. ✓ No crashes

### Full Functional Test (30 minutes)
1. ✓ Connect to BMS (Q1.1.1)
2. ✓ Verify all data fields display (Q1.2.1)
3. ✓ Verify calculated stats correct (Q1.2.2)
4. ✓ Record and verify CSV (Q1.3.1, Q1.3.3)
5. ✓ Use CLEAR VIEW button (Q1.5.1)
6. ✓ Verify status displays and colors (Q1.4.4)

---

## 10. KNOWN ISSUES & LIMITATIONS

### Current Known Limitations:
- [ ] No multi-device support (single COM port only)
- [ ] Dark mode not explicitly supported
- [ ] No data export formats besides CSV
- [ ] No real-time graphing/charting
- [ ] Windows-only (no Linux/macOS support)
- [ ] No unit conversion (fixed to SI units)

### Test Case Status Tracking:

| Test ID | Title | Status | Notes |
|---------|-------|--------|-------|
| Q1.1.1 | Connect to COM port | ⬜ PENDING | <add results> |
| Q1.1.2 | Handle disconnection | ⬜ PENDING | <add results> |
| Q1.1.3 | Invalid COM port | ⬜ PENDING | <add results> |
| Q1.1.4 | Select baud rates | ⬜ PENDING | <add results> |
| Q1.1.5 | Refresh ports | ⬜ PENDING | <add results> |
| Q1.2.1 | Display data fields | ⬜ PENDING | <add results> |
| Q1.2.2 | Calculate stats | ⬜ PENDING | <add results> |
| Q1.2.3 | Frame counter | ⬜ PENDING | <add results> |
| Q1.2.4 | Handle corrupt frames | ⬜ PENDING | <add results> |
| Q1.2.5 | Timestamp accuracy | ⬜ PENDING | <add results> |
| Q1.3.1 | Save to CSV | ⬜ PENDING | <add results> |
| Q1.3.2 | CSV headers | ⬜ PENDING | <add results> |
| Q1.3.3 | CSV data values | ⬜ PENDING | <add results> |
| Q1.3.4 | Daily log rotation | ⬜ PENDING | <add results> |
| Q1.3.5 | Stop/restart logging | ⬜ PENDING | <add results> |
| Q1.4.1 | Display parameters | ⬜ PENDING | <add results> |
| Q1.4.2 | Display units | ⬜ PENDING | <add results> |
| Q1.4.3 | Window resize | ⬜ PENDING | <add results> |
| Q1.4.4 | Status colors | ⬜ PENDING | <add results> |
| Q1.4.5 | System log | ⬜ PENDING | <add results> |
| Q1.5.1 | Clear view button | ⬜ PENDING | <add results> |
| Q1.5.2 | Button disable states | ⬜ PENDING | <add results> |
| Q2.1 | BMS stops sending | ⬜ PENDING | <add results> |
| Q2.2 | Rapid connect/disconnect | ⬜ PENDING | <add results> |
| Q2.3 | CSV dir permission denied | ⬜ PENDING | <add results> |
| Q2.4 | Missing icon files | ⬜ PENDING | <add results> |
| Q3.1 | High-frequency data stream | ⬜ PENDING | <add results> |
| Q3.2 | Large CSV files | ⬜ PENDING | <add results> |
| Q3.3 | Memory leak test | ⬜ PENDING | <add results> |
| Q4.1 | Windows 10/11 compatibility | ⬜ PENDING | <add results> |
| Q4.2 | Dependency installation | ⬜ PENDING | <add results> |
| Q4.3 | Standalone .exe | ⬜ PENDING | <add results> |
| Q5.1 | CRC validation | ⬜ PENDING | <add results> |
| Q5.2 | Frame format parsing | ⬜ PENDING | <add results> |
| Q6.1 | PyInstaller build | ⬜ PENDING | <add results> |
| Q6.2 | Clean-only flag | ⬜ PENDING | <add results> |
| Q7.1 | UI intuitiveness | ⬜ PENDING | <add results> |
| Q7.2 | Error message clarity | ⬜ PENDING | <add results> |
| Q7.3 | Dark mode support | ⬜ PENDING | <add results> |
| Q8.1 | COM port safety | ⬜ PENDING | <add results> |
| Q8.2 | Path validation | ⬜ PENDING | <add results> |

---

## TESTING RECOMMENDATIONS

### Priority 1 (Must Test - Critical Path)
- Q1.1.1: Connect to COM port
- Q1.2.1: Display data fields correctly
- Q1.3.1: Save CSV logs
- Q1.3.3: CSV data accuracy
- Q3.1: Performance under load

### Priority 2 (Should Test - Important Features)
- Q1.1.2: Disconnection handling
- Q1.2.2: Calculated stats accuracy
- Q1.3.4: Daily log rotation
- Q4.3: Standalone .exe functionality
- Q2.2: Rapid connect/disconnect

### Priority 3 (Nice to Test - Enhanced Quality)
- Q1.4.x: UI/Display quality
- Q7.x: Usability
- Q3.3: Memory leak investigation
- Q4.1: Multi-OS compatibility (if applicable)

---

## TEST ENVIRONMENT SETUP

### Hardware Required:
- Windows 10/11 PC
- BMS device (for serial communication)
- USB-to-Serial adapter (if needed)

### Software Required:
- Python 3.10+
- All packages from requirements.txt
- PyInstaller (for build testing)
- Excel or CSV viewer for log verification

### Tools Recommended:
- Device Manager (port verification)
- Windows Task Manager (performance monitoring)
- Serial port monitor (protocol debugging)

---

## Sign-Off

**Q&A Testing Team:** Comprehensive
**Test Plan Version:** 1.0
**Last Updated:** 2025-04-01
**Status:** Ready for Execution

---

For each test case, record:
- **Status:** PASS ✓ / FAIL ✗ / SKIP ⊘
- **Date Tested:** YYYY-MM-DD
- **Tester:** Name
- **Notes:** Any observations or deviations
