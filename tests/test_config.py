"""Unit tests for BMS Monitor configuration module."""

import pytest
from bms_monitor.config import (
    load_app_metadata,
    FRAME_CONFIG,
    BAUD_RATES,
    DEFAULT_BAUD_INDEX,
    COLORS,
    FONTS,
    CALC_GROUPS,
)


class TestFrameConfig:
    """Test frame configuration"""
    
    def test_frame_config_loaded(self):
        """FRAME_CONFIG should have expected fields"""
        assert isinstance(FRAME_CONFIG, list)
        assert len(FRAME_CONFIG) > 0
        
        # All entries should have name and fmt
        for field in FRAME_CONFIG:
            assert 'name' in field
            assert 'fmt' in field
            assert field['fmt'] in ['int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float']
    
    def test_frame_config_has_required_fields(self):
        """Check for key BMS fields"""
        field_names = {f['name'] for f in FRAME_CONFIG}
        assert 'Pack Voltage' in field_names
        assert 'Pack Current' in field_names
        assert 'Cell Voltage' in field_names


class TestCalcGroups:
    """Test calculated group definitions"""
    
    def test_calc_groups_defined(self):
        """CALC_GROUPS should define cell and temp groups"""
        assert 'Cells' in CALC_GROUPS
        assert 'Temps' in CALC_GROUPS
    
    def test_calc_groups_have_required_fields(self):
        """Each group should have unit and stats"""
        for group_name, group_data in CALC_GROUPS.items():
            assert 'unit' in group_data
            assert 'stats' in group_data
            assert len(group_data['stats']) > 0


class TestBaudRates:
    """Test baud rate configuration"""
    
    def test_baud_rates_valid(self):
        """BAUD_RATES should contain standard rates"""
        expected_rates = {'300', '9600', '115200', '921600'}
        actual_rates = set(BAUD_RATES)
        assert expected_rates.issubset(actual_rates)
    
    def test_default_baud_index_valid(self):
        """DEFAULT_BAUD_INDEX should point to valid rate"""
        assert DEFAULT_BAUD_INDEX < len(BAUD_RATES)
        default_rate = BAUD_RATES[DEFAULT_BAUD_INDEX]
        assert default_rate == '115200'
    
    def test_baud_rates_are_strings(self):
        """All baud rates should be strings"""
        for rate in BAUD_RATES:
            assert isinstance(rate, str)
            assert rate.isdigit()


class TestColorPalette:
    """Test color definitions"""
    
    def test_colors_defined(self):
        """Color palette should be defined"""
        required_colors = {
            'bg_light', 'bg_bright', 'text_label',
            'status_ok', 'status_error', 'btn_connect'
        }
        assert required_colors.issubset(COLORS.keys())
    
    def test_all_colors_valid_hex(self):
        """All colors should be valid hex values"""
        for color_name, color_value in COLORS.items():
            assert color_value.startswith('#'), f"{color_name} is not hex"
            assert len(color_value) == 7, f"{color_name} has wrong length"
            # Check if it's valid hex
            try:
                int(color_value[1:], 16)
            except ValueError:
                pytest.fail(f"{color_name} = {color_value} is not valid hex")


class TestFonts:
    """Test font definitions"""
    
    def test_fonts_defined(self):
        """Font definitions should be complete"""
        required_fonts = {'title', 'normal', 'button', 'mono'}
        assert required_fonts.issubset(FONTS.keys())
    
    def test_fonts_have_correct_format(self):
        """Each font should be (family, size, weight) tuple"""
        for font_name, font_spec in FONTS.items():
            assert isinstance(font_spec, tuple), f"{font_name} is not a tuple"
            assert len(font_spec) == 3, f"{font_name} doesn't have 3 elements"
            assert isinstance(font_spec[0], str), f"{font_name} family not string"
            assert isinstance(font_spec[1], int), f"{font_name} size not int"
            assert isinstance(font_spec[2], str), f"{font_name} weight not string"


class TestAppMetadata:
    """Test application metadata loading"""
    
    def test_metadata_loading(self):
        """Metadata should load without error"""
        metadata = load_app_metadata()
        assert isinstance(metadata, dict)
        assert len(metadata) > 0
    
    def test_metadata_has_required_fields(self):
        """Metadata should include key fields"""
        metadata = load_app_metadata()
        required_fields = {'app_name', 'version', 'publisher'}
        # Check at least some required fields exist
        assert any(field in metadata for field in required_fields)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
