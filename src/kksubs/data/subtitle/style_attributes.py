from copy import deepcopy

import kksubs.data.subtitle.style
from kksubs.data.abstract import BaseData
from common.utils.coalesce import coalesce
from kksubs.utils.sanitizers import to_float, to_integer, to_rgb_color, to_string, to_validated_value, to_xy_coords

class TextData(BaseData):
    field_name = "text_data"

    def __init__(
            self, 
            font=None, 
            size=None, color=None, 
            stroke_size=None, stroke_color=None,
            text=None,
            alpha=None,
    ):
        self.font = font
        self.size = size
        self.color = color
        self.stroke_size = stroke_size
        self.stroke_color = stroke_color
        self.text = text
        self.alpha = alpha
        pass

    @classmethod
    def get_default(cls):
        return TextData(
            font="default", 
            size=60, color="white",
            stroke_size=0, stroke_color=(0, 0, 0),
            text="",
            alpha=1,
        )

    @classmethod
    def deserialize(cls, text_style_dict=None):
        if text_style_dict is None:
            return TextData()
        return TextData(**text_style_dict)
    
    def coalesce(self, other:"TextData"):
        if other is None:
            return
        self.font = coalesce(self.font, other.font)
        self.size = coalesce(self.size, other.size)
        self.color = deepcopy(self.color) if self.color is not None else deepcopy(other.color)
        self.stroke_size = coalesce(self.stroke_size, other.stroke_size)
        self.stroke_color = deepcopy(self.stroke_color) if self.stroke_color is not None else deepcopy(other.stroke_color)
        self.alpha = coalesce(self.alpha, other.alpha)
        self.text = coalesce(self.text, other.text)

    def correct_values(self):
        if self.font is not None:
            assert(isinstance(self.font, str))

        self.size = to_integer(self.size)
        self.color = to_rgb_color(self.color)
        self.stroke_size = to_integer(self.stroke_size)
        self.stroke_color = to_rgb_color(self.stroke_color)
        self.alpha = to_float(self.alpha)
        self.text = to_string(self.text)

    pass

class OutlineData(BaseData):
    field_name = "outline_data"

    def __init__(
            self,
            color=None, size=None, blur=None, alpha=None,
    ):
        self.color = color
        self.size = size
        self.blur = blur
        self.alpha = alpha
        pass

    @classmethod
    def get_default(cls):
        return OutlineData(
            color="yellow",
            size=5,
            blur=0,
            alpha=1,
        )
    
    @classmethod
    def deserialize(cls, outline_dict=None):
        if outline_dict is None:
            return None
        return OutlineData(**outline_dict)
    
    def coalesce(self, other:"OutlineData"):
        if other is None:
            return
        self.color = coalesce(self.color, other.color)
        self.size = coalesce(self.size, other.size)
        self.blur = coalesce(self.blur, other.blur)
        self.alpha = coalesce(self.alpha, other.alpha)

    def correct_values(self):
        self.color = to_rgb_color(self.color)
        self.size = to_integer(self.size)
        self.blur = to_integer(self.blur)
        self.alpha = to_float(self.alpha)

class OutlineData1(OutlineData):
    field_name = "outline_data_1"

class BoxData(BaseData):
    field_name = "box_data"

    def __init__(
            self, 
            align_h=None, align_v=None, 
            box_width=None, 
            anchor=None,
            grid4=None,
            grid10=None,
            nudge=None,
            rotate=None,
    ):
        self.align_h = align_h
        self.align_v = align_v
        self.box_width = box_width
        self.anchor = anchor
        self.grid4 = grid4
        self.grid10 = grid10
        self.nudge = nudge
        self.rotate = rotate
        pass

    @classmethod
    def get_default(cls):
        return BoxData(
            align_h="center", align_v="center",
            box_width=30,
            anchor=(0, 0),
        )

    @classmethod
    def deserialize(cls, box_style_dict=None):
        if box_style_dict is None:
            return BoxData()
        return BoxData(**box_style_dict)
    
    def coalesce(self, other:"BoxData"):
        if other is None:
            return
        self.align_h = coalesce(self.align_h, other.align_h)
        self.align_v = coalesce(self.align_v, other.align_v)
        self.box_width = coalesce(self.box_width, other.box_width)

        if self.anchor is None and self.grid4 is None and self.grid10 is None:
            self.anchor = deepcopy(other.anchor) if other.anchor is not None else None
            self.grid4 = deepcopy(other.grid4) if other.grid4 is not None else None
            self.grid10 = deepcopy(other.grid10) if other.grid10 is not None else None

        self.nudge = coalesce(self.nudge, other.nudge)
        self.rotate = coalesce(self.rotate, other.rotate)

    def correct_values(self):
        self.align_h = to_validated_value(self.align_h, {"left", "right", "center"})
        self.align_v = to_validated_value(self.align_v, {"bottom", "top", "center"})
        self.box_width = to_integer(self.box_width)
        self.anchor = to_xy_coords(self.anchor)
        self.grid4 = to_xy_coords(self.grid4)
        self.grid10 = to_xy_coords(self.grid10)
        self.nudge = to_xy_coords(self.nudge)
        self.rotate = to_integer(self.rotate)

class Asset(BaseData):
    field_name = 'asset'

    def __init__(
            self,
            path:str=None,
            rotate:int=None,
            scale:float=None,
            alpha:int=None,
    ):
        self.path = path
        self.rotate = rotate
        self.scale = scale
        self.alpha = alpha

    @classmethod
    def get_default(cls):
        return Asset()
    
    @classmethod
    def deserialize(cls, data=None):
        if data is None:
            return None
        return Asset(**data)
    
    def coalesce(self, other:"Asset"):
        if other is None:
            return
        self.path = coalesce(self.path, other.path)
        self.rotate = coalesce(self.rotate, other.rotate)
        self.scale = coalesce(self.scale, other.scale)
        self.alpha = coalesce(self.alpha, other.alpha)

    def correct_values(self):
        self.path = to_string(self.path)
        self.rotate = to_integer(self.rotate)
        self.scale = to_float(self.scale)
        self.alpha = to_float(self.alpha)

class Brightness(BaseData):
    field_name = "brightness"

    def __init__(
            self,
            value=None,
    ):
        self.value = value
        pass

    @classmethod
    def get_default(cls):
        return Brightness(
            value=1.0
        )
    
    @classmethod
    def deserialize(cls, values=None):
        if values is None:
            return None
        return Brightness(**values)
    
    def coalesce(self, other:"Brightness"):
        if other is None:
            return
        self.value = coalesce(self.value, other.value)

    def correct_values(self):
        self.value = to_float(self.value)

    pass

class Gaussian(BaseData):
    field_name = "gaussian"

    def __init__(
            self,
            value=None, # radius
    ):
        self.value = value
        pass

    @classmethod
    def get_default(cls):
        return Gaussian(
            value=0
        )
    
    @classmethod
    def deserialize(cls, values=None):
        if values is None:
            return None
        return Gaussian(**values)
    
    def coalesce(self, other:"Gaussian"):
        if other is None:
            return
        self.value = coalesce(self.value, other.value)

    def correct_values(self):
        self.value = to_integer(self.value)

    pass

class Motion(BaseData):
    field_name = "motion"

    def __init__(
            self,
            value=None, # kernel size
            angle=None, # value between 0 and 360
    ):
        self.value = value
        self.angle = angle
        pass

    @classmethod
    def get_default(cls):
        return Motion(
            value=0,
            angle=0,
        )
    
    @classmethod
    def deserialize(cls, values=None):
        if values is None:
            return None
        return Motion(**values)
    
    def coalesce(self, other:"Motion"):
        if other is None:
            return
        self.value = coalesce(self.value, other.value)
        self.angle = coalesce(self.angle, other.angle)

    def correct_values(self):
        self.value = to_integer(self.value)
        self.angle = to_integer(self.angle)

    pass

class Mask(BaseData):
    field_name = "mask"

    def __init__(
            self,
            path=None,
    ):
        self.path = path
        pass

    @classmethod
    def get_default(cls):
        return Mask(
        )
    
    @classmethod
    def deserialize(cls, path=None):
        if path is None:
            return None
        if isinstance(path, str):
            return Mask(path=path)
        return Mask(**path)
    
    def coalesce(self, other:"Mask"):
        if other is None:
            return
        self.path = coalesce(self.path, other.path)

    def correct_values(self):
        return

    pass

class Background(BaseData):
    field_name = "background"

    def __init__(
            self,
            path=None,
    ):
        self.path = path
        pass

    @classmethod
    def get_default(cls):
        return Background(
        )

    @classmethod
    def deserialize(cls, path=None):
        if path is None:
            return None
        if isinstance(path, str):
            return Background(path=path)
        return Background(**path)

    def coalesce(self, other:"Background"):
        if other is None:
            return
        self.path = coalesce(self.path, other.path)

    def correct_values(self):
        return

    pass

class CharacterDialogueConfig(BaseData):
    field_name = "character_dialogue"

    def __init__(
            self,
            enabled=None,
            character_name=None,
            separator=None,
            spacing=None,
            character=None,
            dialogue=None,
    ):
        self.enabled = enabled
        self.character_name = character_name
        self.separator = separator
        self.spacing = spacing
        self.character = character
        self.dialogue = dialogue
        pass

    @classmethod
    def get_default(cls):
        return CharacterDialogueConfig(
            enabled=False,
            character_name="",
            separator=": ",
            spacing=0,
            character=None,
            dialogue=None,
        )

    @classmethod
    def deserialize(cls, data=None):
        if data is None:
            return None

        enabled = data.get('enabled', False)
        character_name = data.get('character_name', "")
        separator = data.get('separator', ": ")
        spacing = data.get('spacing', 0)

        character_data = data.get('character')
        dialogue_data = data.get('dialogue')

        character = kksubs.data.subtitle.style.Style.deserialize(character_data) if character_data is not None else None
        dialogue = kksubs.data.subtitle.style.Style.deserialize(dialogue_data) if dialogue_data is not None else None

        return CharacterDialogueConfig(
            enabled=enabled,
            character_name=character_name,
            separator=separator,
            spacing=spacing,
            character=character,
            dialogue=dialogue,
        )

    def coalesce(self, other:"CharacterDialogueConfig"):
        if other is None:
            return

        self.enabled = coalesce(self.enabled, other.enabled)
        self.character_name = coalesce(self.character_name, other.character_name)
        self.separator = coalesce(self.separator, other.separator)
        self.spacing = coalesce(self.spacing, other.spacing)

        if self.character is None:
            self.character = deepcopy(other.character) if other.character is not None else None
        elif other.character is not None:
            self.character.coalesce(other.character)

        if self.dialogue is None:
            self.dialogue = deepcopy(other.dialogue) if other.dialogue is not None else None
        elif other.dialogue is not None:
            self.dialogue.coalesce(other.dialogue)

    def correct_values(self):
        if self.enabled is not None:
            assert isinstance(self.enabled, bool)

        if self.character_name is not None:
            self.character_name = to_string(self.character_name)

        if self.separator is not None:
            self.separator = to_string(self.separator)

        self.spacing = to_integer(self.spacing)

        if self.enabled and not self.character_name:
            raise ValueError("character_name is required when character_dialogue is enabled")

        if self.character is not None:
            self.character.correct_values()

        if self.dialogue is not None:
            self.dialogue.correct_values()

    pass
