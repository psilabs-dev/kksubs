from typing import List
from PIL import Image, ImageFont

from kksubs.data import Subtitle
from kksubs.service.processors import create_text_layer

# TODO: add subtitling logic + image processing logic
def add_subtitle_to_image(image:Image.Image, subtitle:Subtitle, get_box=None) -> Image.Image:
    if get_box is None:
        get_box = False

    # expand subtitle.
    style = subtitle.style
    content = subtitle.content
    # expand details of subtitle profile.
    text_data = style.text_data
    box_data = style.box_data

    # extract image data
    image_width, image_height = image.size

    # extract text data
    font_style = "arial.ttf" if text_data.font == "default" else text_data.font
    font_color = text_data.color
    font_size = text_data.size
    font_stroke_size = text_data.stroke_size
    font_stroke_color = text_data.stroke_color
    align_h = box_data.align_h
    align_v = box_data.align_v
    box_width = box_data.box_width
    coords = box_data.coords

    font = ImageFont.truetype(font_style, font_size)
    
    text_layer = create_text_layer(image, font, content, font_color, font_size, font_stroke_color, font_stroke_size, align_h, align_v, box_width, coords)

    image.paste(text_layer, (0, 0), text_layer)

    if not get_box:
        return image
    
    return image

def add_subtitles_to_image(image:Image.Image, subtitles:List[Subtitle]) -> Image.Image:
    for subtitle in subtitles:
        image = add_subtitle_to_image(image, subtitle)
    return image
