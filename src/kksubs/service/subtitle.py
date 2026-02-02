import os
from typing import List
from PIL import Image, ImageFont, ImageFilter, ImageEnhance
import importlib.resources

from common.utils.coalesce import coalesce
from kksubs.data.subtitle.style_attributes import OutlineData
from kksubs.data.subtitle.subtitle import CharacterDialogueSubtitle, Subtitle
from kksubs.data.subtitle.style import Style
# from kksubs.data.subtitle.subtitle import OutlineData, Subtitle
from kksubs.service.processor.motion_blur import apply_motion_blur
from kksubs.service.processor.apply_text import create_text_layer

import logging

logger = logging.getLogger(__name__)

def get_pil_coordinates(image:Image.Image, anchor, grid4, grid10, nudge):
    image_width, image_height = image.size
    if grid4 is not None:
        grid4_x, grid4_y = grid4
        tb_anchor_x = int(image_width//4*grid4_x)
        tb_anchor_y = int(image_height//4*grid4_y)
    elif grid10 is not None:
        grid10_x, grid10_y = grid10
        tb_anchor_x = int(image_width//10*grid10_x)
        tb_anchor_y = int(image_height//10*grid10_y)
    else:
        tb_anchor_x, tb_anchor_y = anchor
        tb_anchor_x = image_width/2 + tb_anchor_x
        tb_anchor_y = image_height/2 - tb_anchor_y
    if nudge is not None: # if there is anchor point data, use it to fine-tune.
        x_nudge, y_nudge = nudge
        tb_anchor_x = tb_anchor_x + x_nudge
        tb_anchor_y = tb_anchor_y - y_nudge

    return tb_anchor_x, tb_anchor_y

def _get_default_font():
    """Get the default font, trying bundled font first, then system default."""
    try:
        # Try to get the bundled font from package resources
        font_files = importlib.resources.files('resources.fonts.roboto')
        font_path = font_files / 'Roboto-Regular.ttf'
        with importlib.resources.as_file(font_path) as font_file:
            return str(font_file)
    except (ImportError, AttributeError, FileNotFoundError):
        # If importlib.resources fails, return None for system default
        return None

def _render_text_with_outlines(
    image: Image.Image,
    content: List[str],
    style,
    font: ImageFont.FreeTypeFont,
    tb_anchor_x: float,
    tb_anchor_y: float,
    tb_center_x: float,
    tb_center_y: float,
) -> Image.Image:
    """
    Helper to render text with outline layers (outline_data_1, outline_data).
    Returns a layer with text and outlines composited.
    """
    text_data = style.text_data
    box_data = style.box_data

    font_color = text_data.color
    font_size = text_data.size
    font_stroke_size = text_data.stroke_size
    font_stroke_color = text_data.stroke_color
    align_h = box_data.align_h
    align_v = box_data.align_v
    box_width = box_data.box_width
    rotate = box_data.rotate if box_data.rotate is not None else 0

    # Create base layer
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))

    # Create text layer
    text_layer = create_text_layer(
        layer, font, content, font_color, font_size,
        font_stroke_color, font_stroke_size, align_h, align_v,
        box_width, tb_anchor_x, tb_anchor_y
    ).rotate(rotate, center=(tb_center_x, tb_center_y))

    # Apply outline layers
    for outline_data in [style.outline_data_1, style.outline_data]:
        if outline_data is not None and isinstance(outline_data, OutlineData):
            outline_color = outline_data.color
            outline_size = outline_data.size
            outline_blur = outline_data.blur
            outline_alpha = outline_data.alpha
            try:
                outline_layer = create_text_layer(
                    layer, font, content, outline_color, font_size,
                    outline_color, outline_size, align_h, align_v,
                    box_width, tb_anchor_x, tb_anchor_y
                ).rotate(rotate, center=(tb_center_x, tb_center_y))
                outline_base = outline_layer
                if outline_blur is not None and isinstance(outline_blur, int) and outline_blur > 0:
                    outline_base = layer.copy()
                    outline_base.paste(outline_layer, (0, 0), outline_layer)
                    outline_base = outline_base.filter(ImageFilter.GaussianBlur(radius=outline_blur))
                    outline_layer = outline_layer.filter(ImageFilter.GaussianBlur(radius=outline_blur)).convert("RGBA")
                    if outline_alpha is not None and outline_alpha < 1:
                        outline_layer = ImageEnhance.Brightness(outline_layer.getchannel('A')).enhance(outline_alpha)
                layer.paste(outline_base, (0, 0), outline_layer)
            except Exception as e:
                logger.warning(f'Failed to process outline: {e}')

    # Apply text layer
    text_mask = text_layer
    if text_data.alpha is not None and text_data.alpha < 1:
        text_mask = ImageEnhance.Brightness(text_mask.getchannel('A')).enhance(text_data.alpha)
    layer.paste(text_layer, (0, 0), text_mask)

    return layer

def _render_character_dialogue_subtitle(
    image: Image.Image,
    subtitle: CharacterDialogueSubtitle,
    project_directory: str
) -> Image.Image:
    """
    Render character/dialogue subtitle as horizontally-arranged container.

    Character and dialogue are rendered as separate elements with independent
    styling, then positioned as a single container unit.
    """
    style = subtitle.style
    config = style.character_dialogue

    if config is None or not config.enabled:
        logger.warning("CharacterDialogueSubtitle has no valid character_dialogue config, rendering as empty.")
        return image

    # Get character name and dialogue
    char_text = config.character_name
    separator_text = config.separator if config.separator is not None else ": "
    spacing = config.spacing if config.spacing is not None else 0
    dialogue_lines = subtitle.dialogue_content if subtitle.dialogue_content else [""]

    # Get default styles if not provided
    char_style = config.character if config.character is not None else style
    dialogue_style = config.dialogue if config.dialogue is not None else style

    # Ensure styles have defaults coalesced
    char_style.coalesce(Style.get_default())
    dialogue_style.coalesce(Style.get_default())

    # Get character font
    char_text_data = char_style.text_data
    if char_text_data.font == "default":
        char_font_path = _get_default_font()
    elif char_text_data.font and os.path.exists(char_text_data.font):
        char_font_path = char_text_data.font
    else:
        logger.warning(f"Cannot find character font {char_text_data.font}, using default.")
        char_font_path = _get_default_font()

    try:
        char_font = ImageFont.truetype(char_font_path, char_text_data.size)
    except Exception as e:
        logger.warning(f"Failed to load character font: {e}")
        return image

    # Get dialogue font
    dialogue_text_data = dialogue_style.text_data
    if dialogue_text_data.font == "default":
        dialogue_font_path = _get_default_font()
    elif dialogue_text_data.font and os.path.exists(dialogue_text_data.font):
        dialogue_font_path = dialogue_text_data.font
    else:
        logger.warning(f"Cannot find dialogue font {dialogue_text_data.font}, using default.")
        dialogue_font_path = _get_default_font()

    try:
        dialogue_font = ImageFont.truetype(dialogue_font_path, dialogue_text_data.size)
    except Exception as e:
        logger.warning(f"Failed to load dialogue font: {e}")
        return image

    # Calculate text dimensions
    char_bbox = char_font.getbbox(char_text)
    char_width = char_bbox[2] - char_bbox[0]
    char_height = char_bbox[3] - char_bbox[1]

    sep_bbox = char_font.getbbox(separator_text)
    sep_width = sep_bbox[2] - sep_bbox[0]
    sep_height = sep_bbox[3] - sep_bbox[1]

    # Calculate dialogue dimensions
    dialogue_text = "\n".join(dialogue_lines)
    dialogue_bbox = dialogue_font.getbbox(dialogue_text)
    dialogue_width = dialogue_bbox[2] - dialogue_bbox[0]
    dialogue_height = dialogue_bbox[3] - dialogue_bbox[1]

    # Calculate container dimensions (horizontal layout)
    container_width = char_width + sep_width + spacing + dialogue_width
    container_height = max(char_height, sep_height, dialogue_height)

    # Get container anchor point
    box_data = style.box_data
    tb_center_x, tb_center_y = get_pil_coordinates(
        image, anchor=box_data.anchor, grid4=box_data.grid4,
        grid10=box_data.grid10, nudge=None
    )
    tb_anchor_x, tb_anchor_y = get_pil_coordinates(
        image, anchor=box_data.anchor, grid4=box_data.grid4,
        grid10=box_data.grid10, nudge=box_data.nudge
    )

    # Calculate container top-left based on alignment
    if box_data.align_h == "center":
        container_x = tb_anchor_x - container_width / 2
    elif box_data.align_h == "left":
        container_x = tb_anchor_x
    else:  # right
        container_x = tb_anchor_x - container_width

    if box_data.align_v == "center":
        container_y = tb_anchor_y - container_height / 2
    elif box_data.align_v == "top":
        container_y = tb_anchor_y
    else:  # bottom
        container_y = tb_anchor_y - container_height

    # Render character portion
    char_layer = _render_text_with_outlines(
        image, [char_text], char_style, char_font,
        container_x, container_y, tb_center_x, tb_center_y
    )

    # Render separator portion (uses character style)
    sep_layer = _render_text_with_outlines(
        image, [separator_text], char_style, char_font,
        container_x + char_width, container_y, tb_center_x, tb_center_y
    )

    # Render dialogue portion
    dialogue_layer = _render_text_with_outlines(
        image, dialogue_lines, dialogue_style, dialogue_font,
        container_x + char_width + sep_width + spacing, container_y,
        tb_center_x, tb_center_y
    )

    # Composite all layers
    image = image.convert("RGBA")
    image = Image.alpha_composite(image, char_layer)
    image = Image.alpha_composite(image, sep_layer)
    image = Image.alpha_composite(image, dialogue_layer)

    return image

def add_subtitle_to_image(image:Image.Image, subtitle:Subtitle, project_directory:str) -> Image.Image:

    # Check if this is a character/dialogue subtitle
    if isinstance(subtitle, CharacterDialogueSubtitle):
        return _render_character_dialogue_subtitle(image, subtitle, project_directory)

    # expand subtitle.
    style = subtitle.style
    content = subtitle.content
    if not content:
        content = [""]
    # expand details of subtitle profile.
    text_data = style.text_data
    box_data = style.box_data

    # extract image data
    image_width, image_height = image.size

    # extract text data
    if text_data.font == "default":
        font_style = _get_default_font()
    elif text_data.font and os.path.exists(text_data.font):
        font_style = text_data.font
    else:
        logger.warning(f"Cannot find font asset {text_data.font}, skipping text rendering for this subtitle.")
        font_style = None
    
    # add default text data
    if text_data.text:
        content[0] = text_data.text + content[0]
    
    font_color = text_data.color
    font_size = text_data.size
    font_stroke_size = text_data.stroke_size
    font_stroke_color = text_data.stroke_color
    align_h = box_data.align_h
    align_v = box_data.align_v
    box_width = box_data.box_width
    rotate = box_data.rotate
    if rotate is None:
        rotate = 0

    anchor = box_data.anchor
    grid4 = box_data.grid4
    grid10 = box_data.grid10
    nudge = box_data.nudge # nudge will not determine center of rotation.

    tb_center_x, tb_center_y = get_pil_coordinates(image, anchor=anchor, grid4=grid4, grid10=grid10, nudge=None) # center of rotation.
    tb_anchor_x, tb_anchor_y = get_pil_coordinates(image, anchor=anchor, grid4=grid4, grid10=grid10, nudge=nudge)

    # asset data
    asset_data = style.asset_data
    if asset_data is not None:
        asset_path = asset_data.path
        asset_rotate = asset_data.rotate
        asset_scale = asset_data.scale
        asset_alpha = asset_data.alpha
        if asset_path is None or not os.path.exists(asset_path):
            logger.warning(f'Asset path {asset_path} does not exist, skipping asset rendering.')
        else:
            try:
                asset = Image.open(asset_path)
                asset_width, asset_height = asset.size
                asset_rotate = coalesce(asset_rotate, rotate, 0)
                asset_scale = coalesce(asset_scale, 1)
                asset_width, asset_height = int(asset_width*asset_scale), int(asset_height*asset_scale)
                asset_position = (int(tb_anchor_x-asset_width//2), int(tb_anchor_y-asset_height//2))
                asset = asset.rotate(
                    asset_rotate
                ).resize(
                    (asset_width, asset_height)
                )
                asset_mask = asset.convert("RGBA")
                if asset_alpha is not None and asset_alpha < 1:
                    asset_mask = ImageEnhance.Brightness(asset_mask.getchannel('A')).enhance(asset_alpha)
                image.paste(asset, asset_position, asset_mask)
            except Exception as e:
                logger.warning(f'Failed to process asset {asset_path}: {e}')

    # add background
    background = style.background
    if background is not None:
        bg_path = background.path
        if bg_path is not None:
            if not os.path.exists(bg_path):
                bg_path = os.path.join(project_directory, bg_path)
            if not os.path.exists(bg_path):
                logger.warning(f"Background image file {bg_path} cannot be found, skipping background.")
            else:
                try:
                    bg_image = Image.open(bg_path)
                    image.paste(bg_image, (0, 0), bg_image)
                except Exception as e:
                    logger.warning(f'Failed to process background image {bg_path}: {e}')

    # apply sub styles
    styles = style.styles
    if styles is not None:
        for sub_style in styles:
            image = add_subtitle_to_image(image, Subtitle(content=[], style=sub_style), project_directory)

    # Create font object - handle missing fonts gracefully
    font = None
    if font_style is not None:
        try:
            font = ImageFont.truetype(font_style, font_size)
        except (OSError, AttributeError, TypeError) as e:
            logger.warning(f"Failed to create font object from {font_style}: {e}. Skipping text rendering.")
            font = None
    else:
        logger.warning("No valid font available, skipping text rendering.")
        
    # Only render text if we have a valid font
    if font is not None and content:
        text_layer = create_text_layer(image, font, content, font_color, font_size, font_stroke_color, font_stroke_size, align_h, align_v, box_width, tb_anchor_x, tb_anchor_y).rotate(rotate, center=(tb_center_x, tb_center_y))
    else:
        # Create empty text layer if no font is available
        text_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))

    # effect processing layer
    mask = style.mask
    has_mask = False
    if mask is not None:
        mask_path = mask.path
        if mask_path is not None:
            if not os.path.exists(mask_path):
                mask_path = os.path.join(project_directory, mask_path)
            if not os.path.exists(mask_path):
                logger.warning(f"Mask file {mask_path} cannot be found, skipping mask effects.")
            else:
                try:
                    mask_image = Image.open(mask_path)
                    has_mask = True
                except Exception as e:
                    logger.warning(f'Failed to process mask image {mask_path}: {e}')

    brightness = style.brightness
    if brightness is not None:
        brightness = brightness.value
        if brightness is not None:
            brightness_enhancer = ImageEnhance.Brightness(image)
            if has_mask:
                image.paste(brightness_enhancer.enhance(brightness), (0, 0), mask_image)
            else:
                image = brightness_enhancer.enhance(brightness)
    
    gaussian = style.gaussian
    if gaussian is not None:
        radius = gaussian.value
        if radius is not None:
            if has_mask:
                image.paste(image.filter(ImageFilter.GaussianBlur(radius=radius)), (0, 0), mask_image)
            else:
                image = image.filter(ImageFilter.GaussianBlur(radius=radius))

    motion = style.motion
    if motion is not None:
        kernel_size = motion.value
        angle = motion.angle
        if kernel_size is not None and angle is not None:
            if has_mask:
                image.paste(apply_motion_blur(image, kernel_size, angle), (0, 0), mask_image)
            else:
                image = apply_motion_blur(image, kernel_size, angle)

    # outline data application - only if we have a valid font
    if font is not None and content:
        for outline_data in [style.outline_data_1, style.outline_data]:
            if outline_data is not None and isinstance(outline_data, OutlineData):
                outline_color = outline_data.color
                outline_size = outline_data.size
                outline_blur = outline_data.blur
                outline_alpha = outline_data.alpha
                try:
                    outline_layer = create_text_layer(image, font, content, outline_color, font_size, outline_color, outline_size, align_h, align_v, box_width, tb_anchor_x, tb_anchor_y).rotate(rotate, center=(tb_center_x, tb_center_y))
                    outline_base = outline_layer
                    if outline_blur is not None and isinstance(outline_blur, int) and outline_blur > 0:
                        outline_base = image.copy()
                        outline_base.paste(outline_layer, (0, 0), outline_layer)
                        outline_base = outline_base.filter(ImageFilter.GaussianBlur(radius=outline_blur))
                        outline_layer = outline_layer.filter(ImageFilter.GaussianBlur(radius=outline_blur)).convert("RGBA")
                        if outline_alpha is not None and outline_alpha < 1:
                            outline_layer = ImageEnhance.Brightness(outline_layer.getchannel('A')).enhance(outline_alpha)
                    # outline_layer.show()
                    image.paste(outline_base, (0, 0), outline_layer)
                except Exception as e:
                    logger.warning(f'Failed to process outline: {e}')

    # Apply text layer
    if font is not None and content:
        text_mask = text_layer
        if text_data.alpha is not None and text_data.alpha < 1:
            text_mask = ImageEnhance.Brightness(text_mask.getchannel('A')).enhance(text_data.alpha)
        image.paste(text_layer, (0, 0), text_mask)
    
    return image

def add_subtitles_to_image(image:Image.Image, subtitles:List[Subtitle], project_directory:str) -> Image.Image:
    for subtitle in subtitles:
        image = add_subtitle_to_image(image, subtitle, project_directory)
    return image
