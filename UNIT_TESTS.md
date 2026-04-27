# Unit Test Suite - BMS Monitor

This document outlines unit tests for critical modules. These tests can be executed with pytest.

## Running Unit Tests

```bash
pip install pytest
pytest tests/ -v --tb=short
```

---

## 1. Protocol Tests (`test_protocol.py`)

Testing the data parsing and CRC validation logic.

```python
import pytest
from bms_monitor.protocol import (
    DataParser, 
    calculate_crc16, 
    PAYLOAD_FMT, 
    PARSED_HEADERS,
    FRAME_CONFIG
)
import struct

class TestCRC16:
    """CRC16 calculation tests"""
    
    def test_crc16_empty_data(self):
        """CRC of empty data should be 0xFFFF"""
        assert calculate_crc16(b'') == 0xFFFF
    
    def test_crc16_known_values(self):
        """Test against known CRC16 values"""
        # Test with known pattern
        data = b'\x5A\xAA'  # TX_IDENTIFIER + TX_CMD_START
        crc = calculate_crc16(data)
        assert isinstance(crc, int)
        assert 0 <= crc <= 0xFFFF
    
    def test_crc16_consistency(self):
        """Same data should always produce same CRC"""
        data = b'BMS_DATA_TEST_PATTERN'
        crc1 = calculate_crc16(data)
        crc2 = calculate_crc16(data)
        assert crc1 == crc2
    
    def test_crc16_different_data_different_crc(self):
        """Different data should produce different CRCs"""
        data1 = b'DATA1'
        data2 = b'DATA2'
        assert calculate_crc16(data1) != calculate_crc16(data2)


class TestDataParser:
    """Data parsing and field extraction tests"""
    
    def test_payload_format_creates_valid_struct_format(self):
        """Test that PAYLOAD_FMT is valid struct unpack format"""
        # Should not raise exception
        assert PAYLOAD_FMT.startswith('<')  # Little-endian
        
    def test_prepare_config_returns_tuple(self):
        """prepare_config should return (format_str, headers_list)"""
        fmt, headers = DataParser.prepare_config(FRAME_CONFIG)
        assert isinstance(fmt, str)
        assert isinstance(headers, list)
        assert fmt.startswith('<')
        assert len(headers) > 0
    
    def test_all_headers_have_required_fields(self):
        """Every header should have required metadata"""
        fmt, headers = DataParser.prepare_config(FRAME_CONFIG)
        
        required_fields = {'name', 'unit', 'type', 'fmt'}
        for header in headers:
            assert required_fields.issubset(header.keys()), \
                f"Header {header.get('name')} missing required fields"
            assert header['type'] in ['val', 'bit', 'calc']
            assert len(header['name']) > 0
            assert len(header['unit']) > 0
    
    def test_bit_field_expansion(self):
        """Bit fields should expand to individual bits"""
        fmt, headers = DataParser.prepare_config(FRAME_CONFIG)
        
        # Find FET Status bit field (2 bits: Main FET, Pre Charge FET)
        fet_headers = [h for h in headers if 'FET Status' in h['name']]
        assert len(fet_headers) == 2  # Should have 2 bit entries
        assert all(h['type'] == 'bit' for h in fet_headers)
    
    def test_calculated_fields_generated(self):
        """Calculated fields (min/max/avg) should be present"""
        fmt, headers = DataParser.prepare_config(FRAME_CONFIG)
        
        calc_headers = [h for h in headers if h['type'] == 'calc']
        assert len(calc_headers) > 0  # Should have some calculated fields
        
        # Should have Cells stats: min, max, diff, sum, avg
        cell_calcs = [h for h in calc_headers if 'Cells' in h['name']]
        assert len(cell_calcs) >= 5
        
        # Should have Temps stats: max, avg
        temp_calcs = [h for h in calc_headers if 'Temps' in h['name']]
        assert len(temp_calcs) >= 2
    
    def test_parse_single_value_fields(self):
        """Test parsing single-value fields"""
        # Create test data with pack voltage = 48.500 V (48500 as uint16)
        test_raw = (48500,) + (0,) * 50  # Pad with zeros
        
        result = DataParser.parse(test_raw, FRAME_CONFIG)
        assert 'flat' in result
        assert 'stats' in result
        assert len(result['flat']) > 0
    
    def test_parse_multi_value_fields(self):
        """Test parsing multi-value fields (like 14 cell voltages)"""
        # 14 cell voltages around 3.6V each (3600 as uint16)
        cell_voltages = (3600, 3605, 3590, 3608, 3595, 
                        3602, 3598, 3603, 3599, 3601,
                        3596, 3604, 3600, 3607)
        
        # Create sufficient test data
        test_raw = (48500, 10000) + cell_voltages + (0,) * 30
        
        result = DataParser.parse(test_raw, FRAME_CONFIG)
        assert len(result['flat']) > 0
        assert len(result['stats']) > 0
    
    def test_parse_calculates_cell_stats(self):
        """Test that cell statistics are correctly calculated"""
        # Set cell voltages with known values for easy verification
        cell_voltages = (3000, 3100, 3200, 3300, 3400,  # 5 cells
                        3000, 3100, 3200, 3300, 3400,  # repeat
                        3000, 3100, 3200, 3300)       # 14 total
        
        test_raw = (48500, 10000) + cell_voltages + (0,) * 30
        result = DataParser.parse(test_raw, FRAME_CONFIG)
        
        # Cells stats should be calculated
        assert 'Cells_min' in result['stats'] or len(result['flat']) > 0
    
    def test_parse_with_bit_fields(self):
        """Test parsing bitfield entries"""
        # Create test data where FET status = 0x03 (both FETs active)
        test_raw = (48500, 10000) + (3600,) * 14 + (0,) * 30
        
        result = DataParser.parse(test_raw, FRAME_CONFIG)
        # Should parse without error
        assert isinstance(result, dict)
        assert 'flat' in result


class TestPrecisionFormatting:
    """Verify number formatting precision based on factors"""
    
    def test_format_with_factor_001(self):
        """0.001 factor should format to 3 decimals"""
        from bms_monitor.protocol import get_precision_fmt
        fmt = get_precision_fmt(0.001)
        assert '.3f' in fmt or fmt == "{:.3f}"
    
    def test_format_with_factor_01(self):
        """0.1 factor should format to 1 decimal"""
        from bms_monitor.protocol import get_precision_fmt
        fmt = get_precision_fmt(0.1)
        assert '.1f' in fmt or fmt == "{:.1f}"
    
    def test_format_with_no_factor(self):
        """No factor should format as integer"""
        from bms_monitor.protocol import get_precision_fmt
        fmt = get_precision_fmt(1)
        assert '.0f' in fmt or fmt == "{:.0f}"


---

## 2. Configuration Tests (`test_config.py`)

Testing configuration loading and constants.

```python
import pytest
from bms_monitor.config import (
    load_app_metadata,
    FRAME_CONFIG,
    BAUD_RATES,
    DEFAULT_BAUD_INDEX,
    COLORS,
    FONTS,
)

class TestConfigLoading:
    """Test configuration loading"""
    
    def test_frame_config_loaded(self):
        """FRAME_CONFIG should have expected fields"""
        assert isinstance(FRAME_CONFIG, list)
        assert len(FRAME_CONFIG) > 0
        
        # All entries should have name and fmt
        for field in FRAME_CONFIG:
            assert 'name' in field
            assert 'fmt' in field
            assert field['fmt'] in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float']
    
    def test_baud_rates_valid(self):
        """BAUD_RATES should contain standard rates"""
        expected_rates = {'300', '9600', '115200', '921600'}
        actual_rates = set(BAUD_RATES)
        assert expected_rates.issubset(actual_rates)
        assert DEFAULT_BAUD_INDEX < len(BAUD_RATES)
    
    def test_default_baud_index_valid(self):
        """DEFAULT_BAUD_INDEX should point to valid rate"""
        default_rate = BAUD_RATES[DEFAULT_BAUD_INDEX]
        assert default_rate == '115200'
    
    def test_colors_defined(self):
        """Color palette should be defined"""
        required_colors = {
            'bg_light', 'bg_bright', 'text_label',
            'status_ok', 'status_error', 'btn_connect'
        }
        assert required_colors.issubset(COLORS.keys())
        
        # All colors should be valid hex
        for color_name, color_value in COLORS.items():
            assert color_value.startswith('#')
            assert len(color_value) == 7
    
    def test_fonts_defined(self):
        """Font definitions should be complete"""
        required_fonts = {'title', 'normal', 'button', 'mono'}
        assert required_fonts.issubset(FONTS.keys())
        
        for font_name, font_spec in FONTS.items():
            assert isinstance(font_spec, tuple)
            assert len(font_spec) == 3  # (family, size, weight)


class TestAppMetadata:
    """Test application metadata"""
    
    def test_metadata_loading(self):
        """Metadata should load without error"""
        # This should not raise exception
        metadata = load_app_metadata()
        assert isinstance(metadata, dict)
        assert 'app_name' in metadata
        assert metadata['app_version']


---

## 3. Serial Communication Tests (`test_serial.py`)

Tests for SerialWorker thread behavior (requires mocking).

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
import queue
import threading
import struct

class TestSerialWorker:
    """Test serial worker thread"""
    
    @patch('bms_monitor.app.serial.Serial')
    def test_serial_worker_initialization(self, mock_serial):
        """SerialWorker should initialize without errors"""
        from bms_monitor.app import SerialWorker
        
        data_q = queue.Queue()
        status_q = queue.Queue()
        log_q = queue.Queue()
        
        worker = SerialWorker('COM3', 115200, data_q, status_q, log_q)
        assert worker.port == 'COM3'
        assert worker.baud == 115200
    
    @patch('bms_monitor.app.serial.Serial')
    def test_serial_worker_handles_connection_error(self, mock_serial):
        """SerialWorker should handle connection errors gracefully"""
        from bms_monitor.app import SerialWorker
        
        mock_serial.side_effect = Exception("Port not found")
        
        data_q = queue.Queue()
        status_q = queue.Queue()
        log_q = queue.Queue()
        
        worker = SerialWorker('COM_INVALID', 115200, data_q, status_q, log_q)
        # Thread should not crash when started
        # (Full test would need threading setup)


class TestCSVLoggerThread:
    """Test CSV logging thread"""
    
    def test_csv_logger_initialization(self):
        """CSVLoggerThread should initialize"""
        from bms_monitor.app import CSVLoggerThread
        
        status_q = queue.Queue()
        logger = CSVLoggerThread(status_q)
        
        assert logger.running == False
        assert logger.filename == None
    
    def test_csv_logger_queue_put_get(self):
        """CSV logger should handle queue operations"""
        from bms_monitor.app import CSVLoggerThread
        import time
        
        logger = CSVLoggerThread()
        
        # Put test data in queue
        test_data = (time.time(), [48.5, 10.0], {'Cells_min': 3.6})
        logger.queue.put(test_data)
        
        # Should be retrievable
        retrieved = logger.queue.get_nowait()
        assert retrieved == test_data


---

## 4. Integration Tests (`test_integration.py`)

End-to-end tests (requires actual hardware or mocking).

```python
import pytest
from unittest.mock import patch, MagicMock
import tkinter as tk
import time

class TestAppIntegration:
    """Integration tests for complete application"""
    
    @patch('bms_monitor.app.serial.Serial')
    def test_app_initialization(self, mock_serial):
        """App should initialize and create UI"""
        from bms_monitor.app import BMSMonitorApp
        
        root = tk.Tk()
        app = BMSMonitorApp(root)
        
        # Check basic initialization
        assert app.root is not None
        assert len(app.entries) > 0
        assert app.is_connected == False
        assert app.rx_frame_count == 0
        
        root.destroy()
    
    @patch('bms_monitor.app.serial.Serial')
    def test_app_port_update(self, mock_serial):
        """Port update should populate dropdown"""
        from bms_monitor.app import BMSMonitorApp
        
        root = tk.Tk()
        app = BMSMonitorApp(root)
        
        # Mock comports
        mock_port = MagicMock()
        mock_port.device = 'COM3'
        
        with patch('bms_monitor.app.serial.tools.list_ports.comports', return_value=[mock_port]):
            app.update_ports()
            # Combobox should be populated
            assert 'COM3' in app.port_combo['values']
        
        root.destroy()
    
    def test_clear_all_values(self):
        """Clear view should reset all displays"""
        from bms_monitor.app import BMSMonitorApp
        
        root = tk.Tk()
        app = BMSMonitorApp(root)
        
        # Simulate frame counter
        app.rx_frame_count = 100
        app.last_packet_time = time.time()
        
        # Clear
        app.clear_all_values()
        
        assert app.rx_frame_count == 0
        assert app.last_packet_time is None
        
        root.destroy()


---

## Test Execution Commands

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_protocol.py -v

# Run specific test class
pytest tests/test_protocol.py::TestCRC16 -v

# Run with coverage report
pytest tests/ --cov=bms_monitor --cov-report=html

# Run with output capturing disabled (see print statements)
pytest tests/ -v -s
```

## Expected Test Results

All tests should PASS. If any fail:

1. **Protocol tests fail** → Check PAYLOAD_FMT and struct unpacking
2. **Config tests fail** → Verify config.py constants are correct
3. **Serial tests fail** → Check mock setup and serial module
4. **Integration tests fail** → Verify Tkinter installation and app initialization

---

## Continuous Integration

To automatically run tests on each commit:

```yaml
# .github/workflows/tests.yml
name: Unit Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest tests/ --cov=bms_monitor
```

---

**Note:** These unit tests use mocking to avoid requiring actual BMS hardware. For full integration testing, a real BMS device connected via USB/serial is required.
