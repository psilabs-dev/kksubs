import pytest
from kksubs.data.subtitle.style_attributes import CharacterDialogueConfig
from kksubs.data.subtitle.style import Style


def test_character_dialogue_config_deserialize_basic():
    """Test basic deserialization of CharacterDialogueConfig."""
    data = {
        'enabled': True,
        'character_name': 'Shakespeare',
        'separator': ': ',
        'spacing': 0,
    }
    config = CharacterDialogueConfig.deserialize(data)
    assert config.enabled is True
    assert config.character_name == 'Shakespeare'
    assert config.separator == ': '
    assert config.spacing == 0
    assert config.character is None
    assert config.dialogue is None


def test_character_dialogue_config_deserialize_with_nested_styles():
    """Test deserialization with nested character and dialogue styles."""
    data = {
        'enabled': True,
        'character_name': 'Romeo',
        'separator': ': ',
        'spacing': 5,
        'character': {
            'text_data': {
                'color': [255, 215, 0],
                'size': 24,
            },
        },
        'dialogue': {
            'text_data': {
                'color': [255, 255, 255],
                'size': 20,
            },
        },
    }
    config = CharacterDialogueConfig.deserialize(data)
    assert config.enabled is True
    assert config.character_name == 'Romeo'
    assert config.spacing == 5
    assert config.character is not None
    assert config.character.text_data.color == [255, 215, 0]
    assert config.character.text_data.size == 24
    assert config.dialogue is not None
    assert config.dialogue.text_data.color == [255, 255, 255]
    assert config.dialogue.text_data.size == 20


def test_character_dialogue_config_deserialize_none():
    """Test that deserialize returns None when data is None."""
    config = CharacterDialogueConfig.deserialize(None)
    assert config is None


def test_character_dialogue_config_get_default():
    """Test get_default returns correct default values."""
    config = CharacterDialogueConfig.get_default()
    assert config.enabled is False
    assert config.character_name == ""
    assert config.separator == ": "
    assert config.spacing == 0
    assert config.character is None
    assert config.dialogue is None


def test_character_dialogue_config_coalesce():
    """Test coalescing two CharacterDialogueConfig objects."""
    config1 = CharacterDialogueConfig(
        enabled=True,
        character_name='Hamlet',
        separator=': ',
        spacing=10,
    )
    config2 = CharacterDialogueConfig(
        enabled=False,
        character_name='Ophelia',
        separator=' - ',
        spacing=5,
    )
    config1.coalesce(config2)
    # config1 values should be preserved (not overwritten by config2)
    assert config1.enabled is True
    assert config1.character_name == 'Hamlet'
    assert config1.separator == ': '
    assert config1.spacing == 10


def test_character_dialogue_config_coalesce_with_nested_styles():
    """Test coalescing with nested character and dialogue styles."""
    char_style1 = Style.deserialize({
        'text_data': {'color': [255, 0, 0], 'size': 24}
    })
    char_style2 = Style.deserialize({
        'text_data': {'color': [0, 255, 0], 'size': 30},
        'outline_data': {'color': [0, 0, 0], 'size': 2}
    })

    config1 = CharacterDialogueConfig(
        enabled=True,
        character_name='Juliet',
        character=char_style1,
    )
    config2 = CharacterDialogueConfig(
        enabled=True,
        character_name='Romeo',
        character=char_style2,
    )

    config1.coalesce(config2)
    # config1 character style should be merged with config2's
    assert config1.character.text_data.color == [255, 0, 0]  # from config1
    assert config1.character.text_data.size == 24  # from config1
    assert config1.character.outline_data.color == [0, 0, 0]  # from config2
    assert config1.character.outline_data.size == 2  # from config2


def test_character_dialogue_config_correct_values():
    """Test correct_values validates and transforms values."""
    config = CharacterDialogueConfig(
        enabled=True,
        character_name='Macbeth',
        separator=': ',
        spacing='10',  # String that should be converted to int
    )
    config.correct_values()
    assert config.character_name == 'Macbeth'
    assert config.spacing == 10  # Should be converted to int


def test_character_dialogue_config_correct_values_missing_character_name():
    """Test that correct_values raises error when enabled but no character_name."""
    config = CharacterDialogueConfig(
        enabled=True,
        character_name='',  # Empty character name
    )
    with pytest.raises(ValueError, match="character_name is required"):
        config.correct_values()


def test_character_dialogue_config_correct_values_with_nested_styles():
    """Test that correct_values recursively calls correct_values on nested styles."""
    config = CharacterDialogueConfig(
        enabled=True,
        character_name='Othello',
        character=Style.deserialize({
            'text_data': {'color': 'red', 'size': '24'}  # String values
        }),
        dialogue=Style.deserialize({
            'text_data': {'color': 'white', 'size': '20'}  # String values
        }),
    )
    config.correct_values()
    # After correct_values, nested styles should have corrected types
    assert config.character.text_data.size == 24  # Converted to int
    assert config.dialogue.text_data.size == 20  # Converted to int
