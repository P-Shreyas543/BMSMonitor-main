# BMS Monitor - Quick QA Reference Guide

## Project Summary

**Application:** Decibels BMS Monitor v1.0.0  
**Platform:** Windows Desktop (Tkinter)  
**Purpose:** Live BMS telemetry monitoring and CSV logging  
**Key Technologies:** Python 3.10+, PySerial, PIL, Tkinter

---

## Critical Test Paths (Priority Order)

### 1. Connectivity (5 minutes)
```
✓ Can connect to COM port
✓ Receives data frames  
✓ Graceful disconnection
✓ Error handling (busy port, invalid port)
✓ Port refresh works
```

### 2. Data Accuracy (5 minutes)
```
✓ All 70+ fields display
✓ Calculations correct (min/max/avg/diff/sum)
✓ Timestamp accuracy
✓ Frame counter increments
✓ No data corruption
```

### 3. CSV Logging (5 minutes)
```
✓ Can save to CSV
✓ Headers correct
✓ Data values match display
✓ Daily rotation (if applicable)
✓ Can stop/restart logging
```

### 4. Performance (5 minutes)
```
✓ CPU < 15% at 10 Hz data rate
✓ Memory stable (no leaks)
✓ Responsive UI
✓ No dropped frames
✓ Handles large CSV files
```

---

## File Structure for Testing

```
BMSMonitor-main/
├── BMS_Monitor.py               # Entry point
├── SerialLogger.py              # Legacy launcher
├── build.py                     # PyInstaller build
├── requirements.txt             # Dependencies
├── version.json                 # App metadata
│
├── bms_monitor/
│   ├── __init__.py
│   ├── app.py                   # Main UI/logic
│   ├── config.py                # Constants & settings
│   └── protocol.py              # Data parsing & CRC
│
├── TESTING_QA_PLAN.md           # Comprehensive test plan (40 test cases)
├── UNIT_TESTS.md                # Unit test templates (pytest)
├── TEST_EXECUTION_CHECKLIST.md  # Manual test tracking checklist
└── Documentation/
```

---

## Core Components Tested

### 1. Serial Communication (`SerialWorker` Thread)
- **Responsibility:** Connect/disconnect, send/receive data, handle errors
- **Key Tests:** Q1.1.1-1.1.5, Q2.1-2.2
- **Critical Error Handling:**
  - Port busy/locked
  - Serial exceptions
  - Connection loss
  - Frame corruption

### 2. Data Parsing (`DataParser` Module)
- **Responsibility:** Convert raw serial bytes to structured data
- **Key Tests:** Q1.2.1-1.2.5
- **Data Points:** 70+ fields from BMS protocol
- **Calculations:** Min/Max/Avg/Sum/Diff for cell and temp groups
- **Error Cases:** Corrupt frames, sync loss

### 3. CSV Logging (`CSVLoggerThread` Thread)
- **Responsibility:** Write to CSV, handle daily rotation
- **Key Tests:** Q1.3.1-1.3.5
- **Critical:** No data loss during day rollover at midnight
- **File Handling:** Path validation, permission errors

### 4. User Interface (`BMSMonitorApp` Class)
- **Responsibility:** Display data, handle user interactions
- **Key Tests:** Q1.4.1-1.4.5, Q1.5.1-1.5.2
- **UI Elements:**
  - COM port dropdown
  - Baud rate selector
  - Connect/Disconnect buttons
  - Parameter display table
  - Status badges
  - System log area

---

## Key Test Scenarios

### Scenario 1: Normal Operations (15 min)
1. Start app
2. Detect COM ports
3. Connect to BMS @ 115200 baud
4. Verify all data fields populate
5. Record to CSV for 30 seconds
6. Verify CSV data accuracy
7. Disconnect
8. Verify clean shutdown

**Expected Result:** All steps completed successfully

---

### Scenario 2: Error Recovery (10 min)
1. Try to connect to busy COM port → Error dialog
2. Try with invalid baud rate → Connection timeout
3. Disconnect device mid-session → Error recovery
4. Rapid connect/disconnect → No crash
5. Loss of write permissions → Logging error

**Expected Result:** Graceful error handling, clear messages

---

### Scenario 3: Data Integrity (10 min)
1. Receive 100+ frames
2. Manually verify 5 fields against BMS
3. Verify calculations (cell min/max/avg)
4. Export to CSV
5. Compare CSV values vs display values

**Expected Result:** 100% data accuracy

---

### Scenario 4: Long Duration (1+ hours)
1. Connect to BMS
2. Record for 1+ hour continuously
3. Monitor CPU, memory, responsiveness
4. Trigger midnight log rotation (if any)
5. Verify file integrity

**Expected Result:** Stable performance, no leaks

---

## Quick Fixes Guide

| Issue | Check | Fix |
|-------|-------|-----|
| "Port not found" | Device connected? Device drivers installed? | Reinstall USB drivers |
| "Port busy" | Another app open on same port? | Close competing app (PuTTY, etc.) |
| Data shows "--" | Connected? BMS powered on? | Verify BMS transmitting |
| CSV won't save | Directory exists? Write permissions? | Check directory permissions |
| App frozen | High CPU usage? Large CSV file? | Reduce frame rate or restart |
| Memory grows | Recording for 8+ hours? | Restart app periodically |

---

## Performance Baselines

| Metric | Expected | Limit | Test |
|--------|----------|-------|------|
| Connect time | < 1 sec | 5 sec | Q1.1.1 |
| Frame latency | < 100 ms | 500 ms | Q1.2.5 |
| CPU usage | 5-8% | < 15% | Q3.1 |
| Memory usage | 80-120 MB | < 200 MB | Q3.3 |
| CSV write latency | < 50 ms | 200 ms | Q1.3.1 |
| UI responsiveness | Smooth | Visible lag | Q3.1 |
| CSV file size (1 hr) | ~2-3 MB | > 10 MB = problem | Q3.2 |

---

## Common Data Ranges

| Parameter | Typical Value | Range | Unit |
|-----------|---------------|----- -|------|
| Pack Voltage | 48.0 - 58.0 | 0-100+ | V |
| Pack Current | -50 to +300 | -1000 to +1000 | A |
| Cell Voltage | 2.5 - 4.2 | 0-5 | V |
| Temperature | 15 - 45 | -20 to +80 | °C |
| SoC | 0 - 100 | 0-100 | % |
| Cycle Count | 0 - 10000 | 0-65535 | Cycles |
| Cumulative Cap | 0 - 1000000 | 0-max uint32 | Ah |

---

## Testing Checklist - 30 Min Quick Test

**Time: 30 minutes | Tester: ____________| Date: __________**

### Startup (2 min)
- [ ] App launches ✓
- [ ] COM ports visible ✓
- [ ] No errors in console ✓

### Connection (5 min)
- [ ] Select COM port ✓
- [ ] Connect button works ✓
- [ ] Status badge → CONNECTED ✓
- [ ] Data appears within 2 sec ✓

### Data Display (8 min)
- [ ] All fields populate ✓
- [ ] Values change (not static) ✓
- [ ] Frame counter increments ✓
- [ ] Calculations present ✓
- [ ] Units display correctly ✓

### CSV Logging (10 min)
- [ ] Can click "SAVE LOG" ✓
- [ ] File dialog opens ✓
- [ ] File created ✓
- [ ] "STOP SAVE" works ✓
- [ ] CSV file has data ✓

### Cleanup (5 min)
- [ ] "Disconnect" works ✓
- [ ] Status → DISCONNECTED ✓
- [ ] Can close app without errors ✓
- [ ] No crash on exit ✓

**30-Min Test Result:** ☐ PASS ☐ FAIL

---

## Known Limitations

- Single COM port only (no multi-device)
- Windows only (no Linux/Mac)
- No real-time graphs/charts
- No data export except CSV
- No dark mode (but readable)
- No unit conversion

---

## Tools & Resources

### Required
- Windows 10/11 PC
- USB-to-Serial device or BMS with serial output
- Python 3.10+
- Text editor (for CSV verification)

### Optional
- Excel (for CSV viewing)
- Serial port monitor (for protocol debugging)
- Task Manager (for performance monitoring)
- Pytest (for unit test execution)

---

## Testing Environment Setup

```bash
# 1. Install Python 3.10+
# Verify: python --version

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run app from source
python BMS_Monitor.py

# 5. (Optional) Run unit tests
pip install pytest
pytest tests/ -v

# 6. (Optional) Build standalone .exe
pip install pyinstaller
python build.py
# Output: dist\DecibelsBMSMonitor.exe
```

---

## Common Test Data

### Test Case: Normal Frame Reception
```
Connect to COM3 @ 115200 baud
After 1 second:
- Frame counter = 10 (10 Hz typical rate)
- Pack Voltage = 48.5 V
- Pack Current = 25.3 A
- Cell 1-14 voltages = 3.5-3.6 V each
- All temperatures = 25 ± 5 °C
- SoC = 85-95%
```

### Test Case: CSV Row (sample)
```
Timestamp_Sec,ISO_Time,Pack Voltage,Pack Current,Cell Voltage 1,... 
1234567890.123,2025-04-01T12:00:00.123,48.500,25.300,3.600,...
```

---

## Troubleshooting Quick Guide

### Test Won't Run
- [ ] Python installed? `python --version`
- [ ] Dependencies installed? `pip install -r requirements.txt`
- [ ] Serial port available? Check Device Manager
- [ ] BMS powered on and transmitting?

### App Won't Connect
- [ ] Wrong COM port selected?
- [ ] Wrong baud rate?
- [ ] Another app using port? Close it
- [ ] Bad USB cable?

### Data Looks Wrong
- [ ] Check BMS is actually transmitting
- [ ] Verify protocol matches FRAME_CONFIG
- [ ] Check for sync/CRC errors in log
- [ ] Try different baud rate

### CSV File Issues
- [ ] File location not accessible?
- [ ] Permissions denied?
- [ ] Disk full?
- [ ] Try different directory

---

## Communication Template

**For reporting issues:**
- What were you testing? (test case ID)
- What did you expect? (expected result)
- What happened? (actual result)
- When did it happen? (steps to reproduce)
- Screenshots/logs? (attach if possible)

**Example:**
```
TEST: Q1.1.1 - Connect to COM Port
EXPECTED: Connection established in < 1 second
ACTUAL: Connection timeout after 5 seconds, error: "Port timeout"
STEPS: COM3 @ 9600 baud, BMS powered at address 0x40
DEVICE: Windows 10, Python 3.11, PySerial 3.5
```

---

## Sign-Off Criteria

### Release Ready (100% PASS)
- ✅ All critical tests pass
- ✅ No unresolved bugs
- ✅ Performance acceptable
- ✅ Documentation complete

### Release with Caution (90%+ PASS)
- ✅ All critical tests pass
- ⚠️ Minor issues documented
- ✅ Performance acceptable
- ✅ Workarounds provided

### Do Not Release (< 90% PASS)
- ❌ Critical test failures
- ❌ Data integrity issues
- ❌ Performance problems
- ❌ Blocking bugs

---

## Contact & Support

**Questions about testing?**
- Review TESTING_QA_PLAN.md (detailed)
- Check TEST_EXECUTION_CHECKLIST.md (trackable)
- Review UNIT_TESTS.md (automated)

**Issues found?**
- Document with issue template above
- Note test case ID (Q#.#.#)
- Provide reproduction steps

---

**Last Updated:** 2025-04-01  
**Version:** 1.0  
**Status:** Active
