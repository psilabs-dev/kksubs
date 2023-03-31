from typing import List
from PIL import Image, ImageFont, ImageFilter

from kksubs.data import Subtitle
from kksubs.service.processors import create_text_layer

def add_subtitle_to_image(image:Image.Image, subtitle:Subtitle) -> Image.Image:

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
    
    outline_data = style.outline_data

    if outline_data is not None:
        outline_color = outline_data.color
        outline_size = outline_data.size
        outline_blur = outline_data.blur
        outline_layer = create_text_layer(image, font, content, outline_color, font_size, outline_color, outline_size, align_h, align_v, box_width, coords)
        outline_base = outline_layer
        if outline_blur is not None and isinstance(outline_blur, int) and outline_blur > 0:
            outline_base = image.copy()
            outline_base.paste(outline_layer, (0, 0), outline_layer)
            outline_base = outline_base.filter(ImageFilter.GaussianBlur(radius=outline_blur))
            outline_layer = outline_layer.filter(ImageFilter.GaussianBlur(radius=outline_blur)).convert("RGBA")
            pass
        # outline_layer.show()
        image.paste(outline_base, (0, 0), outline_layer)
        pass

    image.paste(text_layer, (0, 0), text_layer)
    
    return image

def add_subtitles_to_image(image:Image.Image, subtitles:List[Subtitle]) -> Image.Image:
    for subtitle in subtitles:
        image = add_subtitle_to_image(image, subtitle)
    return image
