import os
from typing import List
from PIL import Image, ImageFont, ImageFilter, ImageEnhance

from kksubs.data import Subtitle
from kksubs.service.processors import create_text_layer

def get_pil_coordinates(image:Image.Image, anchor, grid4, nudge):
    image_width, image_height = image.size
    if grid4 is not None:
        grid4_x, grid4_y = grid4
        tb_anchor_x = int(image_width//4*grid4_x)
        tb_anchor_y = int(image_height//4*grid4_y)
    else:
        tb_anchor_x, tb_anchor_y = anchor
        tb_anchor_x = image_width/2 + tb_anchor_x
        tb_anchor_y = image_height/2 - tb_anchor_y
    if nudge is not None: # if there is anchor point data, use it to fine-tune.
        x_nudge, y_nudge = nudge
        tb_anchor_x = tb_anchor_x + x_nudge
        tb_anchor_y = tb_anchor_y - y_nudge

    return tb_anchor_x, tb_anchor_y

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
    if text_data.font == "default":
        font_style = "arial.ttf"
    elif os.path.exists(text_data.font):
        font_style = text_data.font
    else:
        raise FileNotFoundError(text_data.font)
    
    font_color = text_data.color
    font_size = text_data.size
    font_stroke_size = text_data.stroke_size
    font_stroke_color = text_data.stroke_color
    align_h = box_data.align_h
    align_v = box_data.align_v
    box_width = box_data.box_width

    anchor = box_data.anchor
    grid4 = box_data.grid4
    nudge = box_data.nudge

    tb_anchor_x, tb_anchor_y = get_pil_coordinates(image, anchor=anchor, grid4=grid4, nudge=nudge)

    font = ImageFont.truetype(font_style, font_size)
    
    text_layer = create_text_layer(image, font, content, font_color, font_size, font_stroke_color, font_stroke_size, align_h, align_v, box_width, tb_anchor_x, tb_anchor_y)
    
    brightness = style.brightness
    if brightness is not None:
        brightness = brightness.value
        if brightness is not None:
            brightness_enhancer = ImageEnhance.Brightness(image)
            image = brightness_enhancer.enhance(brightness)
    
    gaussian = style.gaussian
    if gaussian is not None:
        radius = gaussian.value
        if radius is not None:
            image = image.filter(ImageFilter.GaussianBlur(radius=radius))

    outline_data = style.outline_data

    if outline_data is not None:
        outline_color = outline_data.color
        outline_size = outline_data.size
        outline_blur = outline_data.blur
        outline_layer = create_text_layer(image, font, content, outline_color, font_size, outline_color, outline_size, align_h, align_v, box_width, tb_anchor_x, tb_anchor_y)
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
