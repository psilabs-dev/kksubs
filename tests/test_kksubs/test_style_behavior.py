"""
Tests for style attribute behavior and functionality.

These tests verify correct behavior for style data structures,
coalescing logic, and deserialization patterns.
"""
import tempfile
import os
from PIL import Image

from kksubs.core.data.subtitle.style_attributes import (
    BoxData, Mask, Background, TextData, CharacterDialogueConfig
)
from kksubs.core.data.subtitle.style import Style
from kksubs.core.data.subtitle.subtitle import CharacterDialogueSubtitle
from kksubs.core.service.subtitle import _render_character_dialogue_subtitle
from kksubs.core.service.extraction.subtitle import extract_subtitle_groups
from kksubs.core.service.extraction.style import extract_styles


def test_boxdata_coalesce_independence():
    """
    BoxData.coalesce() should create independent copies of coordinate lists
    to prevent shared references between different BoxData objects.
    """
    box1 = BoxData()
    box2 = BoxData(anchor=[100, 200], grid4=[2, 3], grid10=[5, 5])

    box1.coalesce(box2)

    assert box1.anchor is not None
    assert box1.grid4 is not None
    assert box1.grid10 is not None

    box1.anchor[0] = 999
    assert box2.anchor[0] == 100, \
        "Modifying box1.anchor should not affect box2.anchor"

    box1.grid4[0] = 888
    assert box2.grid4[0] == 2, \
        "Modifying box1.grid4 should not affect box2.grid4"

    box1.grid10[1] = 777
    assert box2.grid10[1] == 5, \
        "Modifying box1.grid10 should not affect box2.grid10"


def test_textdata_coalesce_independence():
    """
    TextData.coalesce() should create independent copies of color lists
    to prevent shared references between different TextData objects.
    """
    text1 = TextData()
    text2 = TextData(color=[255, 0, 0], stroke_color=[0, 0, 0])

    text1.coalesce(text2)

    assert text1.color is not None
    assert text1.stroke_color is not None

    text1.color[0] = 100
    assert text2.color[0] == 255, \
        "Modifying text1.color should not affect text2.color"

    text1.stroke_color[1] = 200
    assert text2.stroke_color[1] == 0, \
        "Modifying text1.stroke_color should not affect text2.stroke_color"


def test_mask_deserialize_string_path():
    """
    Mask.deserialize() should accept a string path in addition to dict format,
    since YAML can represent paths as strings.
    """
    mask = Mask.deserialize(path="mask.png")

    assert mask is not None
    assert mask.path == "mask.png"


def test_mask_deserialize_dict():
    """
    Mask.deserialize() should accept dict format for backward compatibility.
    """
    mask = Mask.deserialize(path={"path": "mask.png"})

    assert mask is not None
    assert mask.path == "mask.png"


def test_background_deserialize_string_path():
    """
    Background.deserialize() should accept a string path in addition to dict format,
    since YAML can represent paths as strings.
    """
    bg = Background.deserialize(path="bg.png")

    assert bg is not None
    assert bg.path == "bg.png"


def test_background_deserialize_dict():
    """
    Background.deserialize() should accept dict format for backward compatibility.
    """
    bg = Background.deserialize(path={"path": "bg.png"})

    assert bg is not None
    assert bg.path == "bg.png"


def test_character_dialogue_rendering_color_formats():
    """
    Character/dialogue rendering should handle color values as lists (from YAML)
    and convert them to tuples for PIL compatibility.
    """
    image = Image.new('RGBA', (800, 600), (255, 255, 255, 255))

    char_style = Style.deserialize({
        'text_data': {
            'color': [255, 0, 0],
            'size': 24,
        }
    })

    dialogue_style = Style.deserialize({
        'text_data': {
            'color': [255, 255, 255],
            'size': 20,
        }
    })

    config = CharacterDialogueConfig(
        enabled=True,
        character_name="Test",
        separator=": ",
        spacing=0,
        character=char_style,
        dialogue=dialogue_style,
    )

    style = Style.deserialize({
        'box_data': {
            'grid10': [5, 5],
            'align_h': 'center',
            'align_v': 'center',
        }
    })
    style.character_dialogue = config

    subtitle = CharacterDialogueSubtitle(
        dialogue_content=["Hello world"],
        style=style,
    )

    result = _render_character_dialogue_subtitle(image, subtitle, ".")

    assert result is not None
    assert result.size == image.size


def test_character_dialogue_subtitle_independence():
    """
    Multiple character/dialogue subtitles should have independent styles
    after extraction and coalescing.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        image = Image.new('RGB', (800, 600), (255, 255, 255))
        image_path = os.path.join(temp_dir, 'test.png')
        image.save(image_path)
        image.close()

        styles_yaml = [
            {
                'style_id': 'speaker',
                'character_dialogue': {
                    'enabled': True,
                    'character_name': 'Speaker',
                    'character': {
                        'text_data': {'color': [255, 215, 0], 'size': 24}
                    },
                    'dialogue': {
                        'text_data': {'color': [255, 255, 255], 'size': 20}
                    }
                }
            }
        ]
        styles = extract_styles(styles_yaml)

        draft = """
image_id: test.png
speaker: First line
speaker: Second line
speaker: Third line
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

            for subtitle in subtitles:
                assert isinstance(subtitle, CharacterDialogueSubtitle)

            assert subtitles[0].style.character_dialogue is not subtitles[1].style.character_dialogue, \
                "Subtitle 0 and 1 should have independent character_dialogue configs"
            assert subtitles[1].style.character_dialogue is not subtitles[2].style.character_dialogue, \
                "Subtitle 1 and 2 should have independent character_dialogue configs"

            assert subtitles[0].style.character_dialogue.character is not \
                   subtitles[1].style.character_dialogue.character, \
                "Character styles should be independent"

            subtitles[0].style.character_dialogue.character.text_data.color = (0, 255, 0)

            assert subtitles[1].style.character_dialogue.character.text_data.color != (0, 255, 0), \
                "Modifying subtitle 0 should not affect subtitle 1"
            assert subtitles[2].style.character_dialogue.character.text_data.color != (0, 255, 0), \
                "Modifying subtitle 0 should not affect subtitle 2"


def test_character_dialogue_config_coalesce_independence():
    """
    CharacterDialogueConfig.coalesce() should create independent copies
    of nested character and dialogue styles.
    """
    char_style1 = Style(text_data=TextData(color=[255, 0, 0], size=24))
    dialogue_style1 = Style(text_data=TextData(color=[255, 255, 255], size=20))

    config1 = CharacterDialogueConfig(
        enabled=True,
        character_name="Speaker1",
        character=char_style1,
        dialogue=dialogue_style1
    )

    config2 = CharacterDialogueConfig()
    config2.coalesce(config1)

    assert config2.character is not None
    assert config2.dialogue is not None

    assert config2.character is not config1.character, \
        "Coalesced character style should be independent"
    assert config2.dialogue is not config1.dialogue, \
        "Coalesced dialogue style should be independent"

    assert config2.character.text_data is not config1.character.text_data, \
        "Coalesced character text_data should be independent"

    config2.character.text_data.color[0] = 100

    assert config1.character.text_data.color[0] == 255, \
        "Modifying config2 should not affect config1"