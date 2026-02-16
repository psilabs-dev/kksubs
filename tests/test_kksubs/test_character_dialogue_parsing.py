import pytest
import tempfile
import os
from PIL import Image
from kksubs.core.service.extraction.subtitle import extract_subtitle_groups
from kksubs.core.service.extraction.style import extract_styles
from kksubs.core.data.subtitle.subtitle import CharacterDialogueSubtitle, Subtitle


@pytest.fixture
def temp_image_dir():
    """Create a temporary directory with a test image."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test image
        image = Image.new('RGB', (800, 600), (255, 255, 255))
        image_path = os.path.join(temp_dir, 'test.png')
        image.save(image_path)
        image.close()
        yield temp_dir


def test_parse_character_dialogue_basic(temp_image_dir):
    """Test parsing basic character/dialogue syntax."""
    styles_yaml = [
        {
            'style_id': 'shakespeare',
            'character_dialogue': {
                'enabled': True,
                'character_name': 'Shakespeare',
                'separator': ': ',
                'character': {
                    'text_data': {'color': [255, 215, 0], 'size': 24}
                },
                'dialogue': {
                    'text_data': {'color': [255, 255, 255], 'size': 20}
                }
            },
            'box_data': {
                'grid10': [5, 5],
                'align_h': 'center',
                'align_v': 'center'
            }
        }
    ]
    styles = extract_styles(styles_yaml)

    draft = """
image_id: test.png
shakespeare: to be or not to be
"""

    with tempfile.TemporaryDirectory() as output_dir:
        subtitle_groups = extract_subtitle_groups(
            draft_id='test_draft',
            draft_body=draft,
            styles=styles,
            image_dir=temp_image_dir,
            output_dir=output_dir
        )

        assert 'test.png' in subtitle_groups
        subtitles = subtitle_groups['test.png'][0].subtitles
        assert len(subtitles) == 1
        assert isinstance(subtitles[0], CharacterDialogueSubtitle)
        assert subtitles[0].dialogue_content == ['to be or not to be']
        assert subtitles[0].style.character_dialogue.character_name == 'Shakespeare'


def test_parse_character_dialogue_multiline(temp_image_dir):
    """Test parsing multi-line character/dialogue."""
    styles_yaml = [
        {
            'style_id': 'hamlet',
            'character_dialogue': {
                'enabled': True,
                'character_name': 'Hamlet',
                'character': {'text_data': {'color': [255, 215, 0]}},
                'dialogue': {'text_data': {'color': [255, 255, 255]}}
            }
        }
    ]
    styles = extract_styles(styles_yaml)

    draft = """
image_id: test.png
hamlet: to be or not to be,
that is the question
"""

    with tempfile.TemporaryDirectory() as output_dir:
        subtitle_groups = extract_subtitle_groups(
            draft_id='test_draft',
            draft_body=draft,
            styles=styles,
            image_dir=temp_image_dir,
            output_dir=output_dir
        )

        subtitles = subtitle_groups['test.png'][0].subtitles
        assert len(subtitles) == 1
        assert isinstance(subtitles[0], CharacterDialogueSubtitle)
        assert subtitles[0].dialogue_content == [
            'to be or not to be,',
            'that is the question'
        ]


def test_parse_mixed_regular_and_character_dialogue(temp_image_dir):
    """Test parsing mixed regular and character/dialogue subtitles."""
    styles_yaml = [
        {
            'style_id': 'narrator',
            'text_data': {'color': [200, 200, 200], 'size': 16}
        },
        {
            'style_id': 'romeo',
            'character_dialogue': {
                'enabled': True,
                'character_name': 'Romeo',
                'character': {'text_data': {'color': [255, 0, 0]}},
                'dialogue': {'text_data': {'color': [255, 255, 255]}}
            }
        }
    ]
    styles = extract_styles(styles_yaml)

    draft = """
image_id: test.png
content: A sad tale begins
romeo: wherefore art thou
"""

    with tempfile.TemporaryDirectory() as output_dir:
        subtitle_groups = extract_subtitle_groups(
            draft_id='test_draft',
            draft_body=draft,
            styles=styles,
            image_dir=temp_image_dir,
            output_dir=output_dir
        )

        subtitles = subtitle_groups['test.png'][0].subtitles
        assert len(subtitles) == 2
        # First subtitle is regular
        assert isinstance(subtitles[0], Subtitle)
        assert not isinstance(subtitles[0], CharacterDialogueSubtitle)
        assert subtitles[0].content == ['A sad tale begins']
        # Second subtitle is character/dialogue
        assert isinstance(subtitles[1], CharacterDialogueSubtitle)
        assert subtitles[1].dialogue_content == ['wherefore art thou']


def test_parse_character_dialogue_with_matrix(temp_image_dir):
    """Test parsing character/dialogue with matrix-generated style IDs."""
    # Check existing matrix tests to understand correct syntax
    from kksubs.core.data.subtitle.style_row_enum import STYLE_ROW_ENUM

    # grid10_complete should already be defined in the enum
    assert STYLE_ROW_ENUM.get('grid10_complete') is not None

    styles_yaml = [
        {
            'matrix': [
                {
                    'row': {
                        'row_id': 'grid10_complete'
                    }
                },
                {
                    'row': {
                        'styles': [
                            {
                                'style_id': 'shakespeare',
                                'character_dialogue': {
                                    'enabled': True,
                                    'character_name': 'Shakespeare',
                                }
                            }
                        ]
                    }
                }
            ]
        }
    ]
    styles = extract_styles(styles_yaml)

    # Verify matrix generated styles with grid positions
    # The style IDs use single digits (e.g., '55' not '5-5')
    assert 'shakespeare-55' in styles
    assert 'shakespeare-00' in styles
    assert 'shakespeare-99' in styles

    draft = """
image_id: test.png
shakespeare-55: hello world
"""

    with tempfile.TemporaryDirectory() as output_dir:
        subtitle_groups = extract_subtitle_groups(
            draft_id='test_draft',
            draft_body=draft,
            styles=styles,
            image_dir=temp_image_dir,
            output_dir=output_dir
        )

        subtitles = subtitle_groups['test.png'][0].subtitles
        assert len(subtitles) == 1
        assert isinstance(subtitles[0], CharacterDialogueSubtitle)
        assert subtitles[0].dialogue_content == ['hello world']
        # Check grid position (tuple, not list)
        assert subtitles[0].style.box_data.grid10 == (5, 5)


def test_parse_empty_dialogue(temp_image_dir):
    """Test parsing character/dialogue with empty dialogue."""
    styles_yaml = [
        {
            'style_id': 'juliet',
            'character_dialogue': {
                'enabled': True,
                'character_name': 'Juliet',
            }
        }
    ]
    styles = extract_styles(styles_yaml)

    draft = """
image_id: test.png
juliet:
"""

    with tempfile.TemporaryDirectory() as output_dir:
        subtitle_groups = extract_subtitle_groups(
            draft_id='test_draft',
            draft_body=draft,
            styles=styles,
            image_dir=temp_image_dir,
            output_dir=output_dir
        )

        subtitles = subtitle_groups['test.png'][0].subtitles
        assert len(subtitles) == 1
        assert isinstance(subtitles[0], CharacterDialogueSubtitle)
        # Empty dialogue should result in empty list or list with empty string
        assert subtitles[0].dialogue_content == [] or subtitles[0].dialogue_content == ['']


def test_character_dialogue_style_used_with_content_key(temp_image_dir):
    """Test that using content: key with a character/dialogue style creates regular Subtitle."""
    styles_yaml = [
        {
            'style_id': 'hamlet',
            'character_dialogue': {
                'enabled': True,
                'character_name': 'Hamlet',
            }
        }
    ]
    styles = extract_styles(styles_yaml)

    draft = """
image_id: test.png
content: some text
"""

    with tempfile.TemporaryDirectory() as output_dir:
        subtitle_groups = extract_subtitle_groups(
            draft_id='test_draft',
            draft_body=draft,
            styles=styles,
            image_dir=temp_image_dir,
            output_dir=output_dir
        )

        subtitles = subtitle_groups['test.png'][0].subtitles
        assert len(subtitles) == 1
        # Should be regular Subtitle, not CharacterDialogueSubtitle
        assert isinstance(subtitles[0], Subtitle)
        assert not isinstance(subtitles[0], CharacterDialogueSubtitle)
        assert subtitles[0].content == ['some text']
