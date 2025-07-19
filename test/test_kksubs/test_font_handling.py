import os
import logging
import pytest
from PIL import Image

from kksubs.data.subtitle.subtitle import Subtitle
from kksubs.data.subtitle.style import Style
from kksubs.data.subtitle.style_attributes import TextData, BoxData
from kksubs.service.subtitle import add_subtitle_to_image


@pytest.fixture(autouse=True)
def setup_logging():
    """Fixture to set up logging configuration for tests."""
    # Suppress warnings for cleaner test output
    logging.getLogger('kksubs.service.subtitle').setLevel(logging.ERROR)


def test_missing_font():
    """Test that missing fonts are handled gracefully."""
    # Create a test image
    test_image = Image.new('RGB', (800, 600), color='blue')
    
    # Create a style with a non-existent font
    text_data = TextData(
        font="/path/to/nonexistent/font.ttf",
        size=48,
        color="white",
        text="Test subtitle"
    )
    
    box_data = BoxData(
        align_h="center",
        align_v="center",
        box_width=30,
        anchor=(0, 0)
    )
    
    style = Style(text_data=text_data, box_data=box_data)
    subtitle = Subtitle(content=["This is a test subtitle"], style=style)
    
    # Test that this doesn't crash
    try:
        result_image = add_subtitle_to_image(test_image, subtitle, os.getcwd())
        # Should return an image of the same size
        assert result_image.size == test_image.size
    except Exception as e:
        pytest.fail(f"Missing font caused crash: {e}")


def test_none_font():
    """Test that None font is handled gracefully."""
    # Create a test image
    test_image = Image.new('RGB', (800, 600), color='green')
    
    # Create a style with None font
    text_data = TextData(
        font=None,
        size=48,
        color="white",
        text="Test subtitle"
    )
    
    box_data = BoxData(
        align_h="center",
        align_v="center",
        box_width=30,
        anchor=(0, 0)
    )
    
    style = Style(text_data=text_data, box_data=box_data)
    subtitle = Subtitle(content=["This is a test subtitle"], style=style)
    
    # Test that this doesn't crash
    try:
        result_image = add_subtitle_to_image(test_image, subtitle, os.getcwd())
        # Should return an image of the same size
        assert result_image.size == test_image.size
    except Exception as e:
        pytest.fail(f"None font caused crash: {e}")


def test_default_font():
    """Test that default font works."""
    # Create a test image
    test_image = Image.new('RGB', (800, 600), color='red')
    
    # Create a style with default font
    text_data = TextData(
        font="default",
        size=48,
        color="white",
        text="Test subtitle"
    )
    
    box_data = BoxData(
        align_h="center",
        align_v="center",
        box_width=30,
        anchor=(0, 0)
    )
    
    style = Style(text_data=text_data, box_data=box_data)
    subtitle = Subtitle(content=["This is a test subtitle"], style=style)
    
    # Test that this works
    try:
        result_image = add_subtitle_to_image(test_image, subtitle, os.getcwd())
        # Should return an image of the same size
        assert result_image.size == test_image.size
    except Exception as e:
        pytest.fail(f"Default font caused crash: {e}") 