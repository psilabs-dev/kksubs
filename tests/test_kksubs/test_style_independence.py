"""
Tests for style object independence during coalescing operations.

Verifies that each subtitle maintains independent style objects after coalescing,
ensuring modifications to one style do not affect other styles or the original
style dictionary.
"""
import tempfile
import os
from copy import deepcopy
from PIL import Image

from kksubs.data.subtitle.style import Style
from kksubs.data.subtitle.style_attributes import TextData, BoxData, CharacterDialogueConfig
from kksubs.service.extraction.subtitle import extract_subtitle_groups
from kksubs.service.extraction.style import extract_styles


def test_coalesce_creates_independent_objects():
    """
    When coalescing styles, each style should get independent copies of
    nested objects, not shared references.
    """
    # Create a default style with text_data
    default_style = Style(text_data=TextData(color=(255, 255, 255), size=20))

    # Create two subtitles with empty styles
    sub1_style = Style()
    sub2_style = Style()

    # Coalesce both with the default style
    sub1_style.coalesce(default_style)
    sub2_style.coalesce(default_style)

    # All three should have text_data
    assert sub1_style.text_data is not None
    assert sub2_style.text_data is not None
    assert default_style.text_data is not None

    # Each should have independent text_data objects
    assert sub1_style.text_data is not default_style.text_data, \
        "sub1 should have independent text_data, not share with default"
    assert sub2_style.text_data is not default_style.text_data, \
        "sub2 should have independent text_data, not share with default"
    assert sub1_style.text_data is not sub2_style.text_data, \
        "sub1 and sub2 should have independent text_data objects"

    # Mutating one should not affect the others
    sub1_style.text_data.color = (255, 0, 0)  # Change to RED

    assert default_style.text_data.color == (255, 255, 255), \
        "Mutating sub1 should not affect default style"
    assert sub2_style.text_data.color == (255, 255, 255), \
        "Mutating sub1 should not affect sub2"


def test_correct_values_does_not_mutate_shared_objects():
    """
    When correct_values() converts types, it should only affect the specific
    style instance, not any styles it was coalesced from.
    """
    # Create default style with string values (as they come from YAML)
    default_style = Style(
        text_data=TextData(color="white", size="60"),  # String values from YAML
        box_data=BoxData(box_width="30")
    )

    # Create subtitle style and coalesce
    sub_style = Style()
    sub_style.coalesce(default_style)

    # Call correct_values to convert types
    sub_style.correct_values()

    # After correct_values, subtitle style should have converted types
    assert sub_style.text_data.color == (255, 255, 255)
    assert sub_style.text_data.size == 60
    assert isinstance(sub_style.text_data.size, int)

    # Original default style should remain unchanged
    assert default_style.text_data.color == "white", \
        "Default style should still have original string value"
    assert default_style.text_data.size == "60", \
        "Default style should still have original string value"


def test_character_dialogue_config_coalesce_independence():
    """
    CharacterDialogueConfig.coalesce() should create independent nested style objects.
    """
    # Create two configs with nested styles
    char_style = Style(text_data=TextData(color=(255, 215, 0), size=24))
    dialogue_style = Style(text_data=TextData(color=(255, 255, 255), size=20))

    config1 = CharacterDialogueConfig(
        enabled=True,
        character_name="Romeo",
        character=char_style,
        dialogue=dialogue_style
    )

    config2 = CharacterDialogueConfig()

    # Coalesce config2 with config1
    config2.coalesce(config1)

    # Config2 should have the styles
    assert config2.character is not None
    assert config2.dialogue is not None

    # But they should be independent objects
    assert config2.character is not config1.character, \
        "config2.character should be independent of config1.character"
    assert config2.dialogue is not config1.dialogue, \
        "config2.dialogue should be independent of config1.dialogue"

    # Mutating config2 should not affect config1
    config2.character.text_data.color = (0, 255, 0)  # GREEN

    assert config1.character.text_data.color == (255, 215, 0), \
        "Mutating config2 should not affect config1"


def test_multiple_subtitles_have_independent_styles():
    """
    Multiple subtitles extracted in the same operation should each have
    independent style objects.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test image
        image = Image.new('RGB', (800, 600), (255, 255, 255))
        image_path = os.path.join(temp_dir, 'test.png')
        image.save(image_path)
        image.close()

        # Create styles with string values (as from YAML)
        styles_yaml = [
            {
                'style_id': 'default',
                'text_data': {
                    'color': 'white',  # String value
                    'size': '60'       # String value
                }
            }
        ]
        styles = extract_styles(styles_yaml)

        # Store original default style color for comparison
        original_default_color = styles['default'].text_data.color
        assert original_default_color == 'white'

        # Create draft with multiple subtitles
        draft = """
image_id: test.png
content: First subtitle
content: Second subtitle
content: Third subtitle
"""

        with tempfile.TemporaryDirectory() as output_dir:
            subtitle_groups = extract_subtitle_groups(
                draft_id='test_draft',
                draft_body=draft,
                styles=styles,
                image_dir=temp_dir,
                output_dir=output_dir
            )

            subtitles = subtitle_groups['test.png'][0].subtitles
            assert len(subtitles) == 3

            # Each subtitle should have independent text_data objects
            assert subtitles[0].style.text_data is not subtitles[1].style.text_data, \
                "Subtitle 0 and 1 should have independent text_data"
            assert subtitles[1].style.text_data is not subtitles[2].style.text_data, \
                "Subtitle 1 and 2 should have independent text_data"
            assert subtitles[0].style.text_data is not styles['default'].text_data, \
                "Subtitle should not share text_data with default style"

            # Mutating one subtitle should not affect others
            subtitles[0].style.text_data.color = (255, 0, 0)  # RED

            assert subtitles[1].style.text_data.color == (255, 255, 255), \
                "Mutating subtitle 0 should not affect subtitle 1"
            assert subtitles[2].style.text_data.color == (255, 255, 255), \
                "Mutating subtitle 0 should not affect subtitle 2"


def test_styles_dictionary_unchanged_across_extractions():
    """
    The styles dictionary should remain unchanged when used across multiple
    subtitle extraction operations.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test image
        image = Image.new('RGB', (800, 600), (255, 255, 255))
        image_path = os.path.join(temp_dir, 'test.png')
        image.save(image_path)
        image.close()

        # Create styles dictionary (loaded once and reused)
        styles_yaml = [
            {
                'style_id': 'default',
                'text_data': {
                    'color': 'white',
                    'size': '60'
                }
            }
        ]
        styles = extract_styles(styles_yaml)

        # Store the original values
        original_text_data = styles['default'].text_data
        original_color = deepcopy(styles['default'].text_data.color)

        draft = """
image_id: test.png
content: Test subtitle
"""

        with tempfile.TemporaryDirectory() as output_dir:
            # First extraction
            extract_subtitle_groups(
                draft_id='draft1',
                draft_body=draft,
                styles=styles,
                image_dir=temp_dir,
                output_dir=output_dir
            )

            # Second extraction with same styles dictionary
            extract_subtitle_groups(
                draft_id='draft2',
                draft_body=draft,
                styles=styles,
                image_dir=temp_dir,
                output_dir=output_dir
            )

            # The styles dictionary should be unchanged
            assert styles['default'].text_data.color == original_color, \
                "Styles dictionary should not be mutated by extraction"

            # The text_data object reference should be the same
            assert styles['default'].text_data is original_text_data, \
                "Style dictionary should maintain same object references"


def test_nested_child_styles_are_independent():
    """
    When a parent style has child styles, correct_values() should ensure
    all child styles have independent copies of inherited attributes.
    """
    # Create parent style with sub-styles
    parent = Style(
        style_id='parent',
        text_data=TextData(color='white', size='60'),
        styles=[
            Style(style_id='child1', text_data=TextData(color='red')),
            Style(style_id='child2', text_data=TextData(color='blue'))
        ]
    )

    # Call correct_values - children should inherit but remain independent
    parent.correct_values()

    # Child styles should have their own text_data objects
    assert parent.styles[0].text_data is not parent.text_data, \
        "Child1 should not share text_data with parent"
    assert parent.styles[1].text_data is not parent.text_data, \
        "Child2 should not share text_data with parent"
    assert parent.styles[0].text_data is not parent.styles[1].text_data, \
        "Child1 and child2 should not share text_data"

    # Mutating child should not affect parent or siblings
    parent.styles[0].text_data.size = 100

    assert parent.text_data.size == 60, \
        "Mutating child should not affect parent"
    assert parent.styles[1].text_data.size == 60, \
        "Mutating child1 should not affect child2"
