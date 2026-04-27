"""Unit tests for BMS Monitor protocol module."""

import pytest
from bms_monitor.protocol import (
    DataParser, 
    calculate_crc16, 
    PAYLOAD_FMT, 
    PARSED_HEADERS,
    FRAME_CONFIG,
    get_precision_fmt
)
import struct


class TestCRC16:
    """CRC16 calculation tests"""
    
    def test_crc16_empty_data(self):
        """CRC of empty data should be 0xFFFF"""
        result = calculate_crc16(b'')
        assert result == 0xFFFF
    
    def test_crc16_known_values(self):
        """Test CRC16 with known pattern"""
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
        
        # Should have Cells stats
        cell_calcs = [h for h in calc_headers if 'Cells' in h['name']]
        assert len(cell_calcs) >= 5
    
    def test_parse_returns_dict_with_flat_and_stats(self):
        """Parse should return dict with 'flat' and 'stats' keys"""
        # Create minimal test data
        test_raw = tuple([0] * 50)  # Pad with zeros
        
        result = DataParser.parse(test_raw, FRAME_CONFIG)
        assert isinstance(result, dict)
        assert 'flat' in result
        assert 'stats' in result
        assert isinstance(result['flat'], list)
        assert isinstance(result['stats'], dict)
    
    def test_parse_calculates_stats(self):
        """Parse should calculate group statistics"""
        test_raw = tuple([0] * 50)
        result = DataParser.parse(test_raw, FRAME_CONFIG)
        assert len(result['stats']) > 0


class TestPrecisionFormatting:
    """Verify number formatting precision based on factors"""
    
    def test_format_with_factor_001(self):
        """0.001 factor should format to 3 decimals"""
        fmt = get_precision_fmt(0.001)
        assert '.3f' in fmt
    
    def test_format_with_factor_01(self):
        """0.1 factor should format to 1 decimal"""
        fmt = get_precision_fmt(0.1)
        assert '.1f' in fmt
    
    def test_format_with_no_factor(self):
        """No factor should format as integer"""
        fmt = get_precision_fmt(1)
        assert '.0f' in fmt
    
    def test_format_returns_valid_string(self):
        """Format should return valid format string"""
        fmt = get_precision_fmt(0.01)
        assert isinstance(fmt, str)
        assert '{' in fmt and '}' in fmt


class TestFrameConfig:
    """Test frame configuration"""
    
    def test_frame_config_exists(self):
        """FRAME_CONFIG should exist and be non-empty"""
        assert isinstance(FRAME_CONFIG, list)
        assert len(FRAME_CONFIG) > 0
    
    def test_all_frame_config_entries_have_required_fields(self):
        """All FRAME_CONFIG entries should have name and fmt"""
        for field in FRAME_CONFIG:
            assert 'name' in field
            assert 'fmt' in field
            assert field['fmt'] in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float']
    
    def test_parsed_headers_match_config(self):
        """PARSED_HEADERS should be generated from FRAME_CONFIG"""
        assert isinstance(PARSED_HEADERS, list)
        assert len(PARSED_HEADERS) > len(FRAME_CONFIG)  # More headers due to bit expansion


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
