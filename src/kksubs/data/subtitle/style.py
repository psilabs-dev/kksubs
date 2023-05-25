from copy import deepcopy
from typing import List

from kksubs.data.subtitle.style_attributes import *

class Style(BaseData):
    field_name = "style"

    def __init__(
            self, 
            style_id:str=None, 
            text_data:TextData=None,
            outline_data:OutlineData=None,
            outline_data_1:OutlineData1=None,
            box_data:BoxData=None,
            brightness:Brightness=None,
            gaussian:Gaussian=None,
            motion:Motion=None,
            background:Background=None,
            mask:Mask=None,
            styles:List["Style"]=None,
    ):
        self.style_id = style_id
        self.text_data = text_data
        self.outline_data = outline_data
        self.outline_data_1 = outline_data_1
        self.box_data = box_data
        self.brightness = brightness
        self.gaussian = gaussian
        self.motion = motion
        self.background = background
        self.mask = mask
        self.styles = styles
        pass

    @classmethod
    def get_default(cls):
        return Style(
            style_id="",
            text_data=TextData.get_default(),
            # stroke_data=StrokeData.get_default(),
            box_data=BoxData.get_default(),
            # styles=[]
        )

    @classmethod
    def from_dict(cls, style_dict:dict=None):
        if style_dict is None:
            return Style()
        return Style(
            style_id=style_dict.get("style_id"),
            text_data=TextData.from_dict(text_style_dict=style_dict.get(TextData.field_name)),
            outline_data=OutlineData.from_dict(outline_dict=style_dict.get(OutlineData.field_name)),
            outline_data_1=OutlineData1.from_dict(outline_dict=style_dict.get(OutlineData1.field_name)),
            box_data=BoxData.from_dict(box_style_dict=style_dict.get(BoxData.field_name)),
            brightness=Brightness.from_dict(values=style_dict.get(Brightness.field_name)),
            gaussian=Gaussian.from_dict(values=style_dict.get(Gaussian.field_name)),
            motion=Motion.from_dict(values=style_dict.get(Motion.field_name)),
            background=Background.from_dict(path=style_dict.get(Background.field_name)),
            mask=Background.from_dict(path=style_dict.get(Mask.field_name)),
            styles=[Style.from_dict(style_dict=sub_style_dict) for sub_style_dict in style_dict.get("styles")] if "styles" in style_dict.keys() else None,
        )
    
    def coalesce(self, other:"Style", essential=False):
        if other is None:
            return
        self.style_id = coalesce(self.style_id, other.style_id)
        if self.text_data is None:
            self.text_data = other.text_data
        else:
            self.text_data.coalesce(other.text_data)
        if self.outline_data is None:
            self.outline_data = other.outline_data
        else:
            self.outline_data.coalesce(other.outline_data)
        if self.outline_data_1 is None:
            self.outline_data_1 = other.outline_data_1
        else:
            self.outline_data_1.coalesce(other.outline_data_1)
        if self.box_data is None:
            self.box_data = other.box_data
        else:
            self.box_data.coalesce(other.box_data)
        if essential:
            return
        
        if self.brightness is None:
            self.brightness = other.brightness
        else:
            self.brightness.coalesce(other.brightness)
        if self.gaussian is None:
            self.gaussian = other.gaussian
        else:
            self.gaussian.coalesce(other.gaussian)
        if self.motion is None:
            self.motion = other.motion
        else:
            self.motion.coalesce(other.motion)
        if self.background is None:
            self.background = other.background
        else:
            self.background.coalesce(other.background)
        if self.mask is None:
            self.mask = other.mask
        else:
            self.mask.coalesce(other.mask)
        if not self.styles:
            self.styles = other.styles

    def inherit(self, style:"Style"):
        # inherit from other styles.
        self.coalesce(style)

    def correct_values(self):
        self.text_data.correct_values()
        if self.outline_data is not None:
            self.outline_data.coalesce(OutlineData.get_default())
            self.outline_data.correct_values()
        if self.outline_data_1 is not None:
            self.outline_data_1.coalesce(OutlineData1.get_default())
            self.outline_data_1.correct_values()
        self.box_data.correct_values()
        if self.brightness is not None:
            self.brightness.coalesce(Brightness.get_default())
            self.brightness.correct_values()
        if self.gaussian is not None:
            self.gaussian.coalesce(Gaussian.get_default())
            self.gaussian.correct_values()
        if self.motion is not None:
            self.motion.coalesce(Motion.get_default())
            self.motion.correct_values()
        if self.background is not None:
            self.background.coalesce(Background.get_default())
            self.background.correct_values()
        if self.mask is not None:
            self.mask.coalesce(Mask.get_default())
            self.mask.correct_values()
        if self.styles is not None:
            for style in self.styles:
                style.correct_values()
                style.coalesce(self, essential=True)

    pass

class Layer(RepresentableData, ABC):
    # an abstract indexed element of a matrix.
    ...

class ContextLayer(Layer):

    def __init__(
            self,
            delimiter:str=None,
    ):
        if delimiter is None:
            delimiter = '-'
        self.delimiter = delimiter

    @classmethod
    def from_dict(cls, context_dict):
        return ContextLayer(**context_dict)

    def project(self, projector:Style, style:Style):
        projected_style = deepcopy(style)
        projected_style_id = projected_style.style_id
        projected_style.inherit(projector)
        projected_style.style_id = f'{projected_style_id}{self.delimiter}{projector.style_id}'
        return projected_style

class StyleRow(Layer):

    def __init__(self, styles:List[Style]=None):
        if styles is None:
            styles = list()
        
        self.styles = styles
        self.context = ContextLayer()

    def add_context(self, context:ContextLayer):
        self.context = context

    def action(self, style_row:"StyleRow"=None) -> "StyleRow":
        # self act on other based on some "context".
        if style_row is None:
            return self

        projection_list = style_row.styles
        row = StyleRow(styles=style_row.styles + self.styles)

        for style in self.styles:
            for projector in projection_list:
                row.styles.append(style_row.context.project(projector, style))
        
        return row

class StyleMatrix(RepresentableData):
    def __init__(self, rows:List[StyleRow]=None):
        if rows is None:
            rows = list()
        self.rows = rows

    def add_row(self, row:StyleRow):
        self.rows.append(row)

    def add_context(self, context:ContextLayer):
        if self.rows:
            self.rows[-1].add_context(context)

    def out(self, delimiter=None) -> List[Style]:
        if delimiter is None:
            delimiter = '-'

        output_row:StyleRow = None
        for row in self.rows:
            if isinstance(row, StyleRow):
                output_row = row.action(output_row)

        return output_row.styles