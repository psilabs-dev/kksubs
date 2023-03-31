import os
import logging
from PIL import Image
from typing import Dict, List
import yaml
from kksubs.data import Style, Subtitle

from kksubs.service.extractors import extract_styles, extract_subtitles
from kksubs.service.subtitle import add_subtitles_to_image

logger = logging.getLogger(__name__)

# project preparation layer.
# folder/file logic, obtain read data, deserialization

def add_subtitles(project_directory:str, draft:str, image_filters:List[int]=None):

    # validate project directory.
    images_dir = os.path.realpath(os.path.join(project_directory, "images"))
    drafts_dir = os.path.realpath(os.path.join(project_directory, "drafts"))
    outputs_dir = os.path.realpath(os.path.join(project_directory, "output"))
    if not (os.path.exists(images_dir) and os.path.exists(drafts_dir)):
        raise FileNotFoundError
    if not os.path.exists(outputs_dir):
        logger.info(f"Output directory for project {project_directory} not found, making one.")
        os.makedirs(outputs_dir, exist_ok=True)

    # get image paths.
    image_paths:List[str] = list(map(lambda image: os.path.join(images_dir, image), filter(lambda file: os.path.isfile(os.path.join(images_dir, file)) and os.path.splitext(file)[1] in {".png"} ,os.listdir(images_dir))))
    logger.info(f"Got images (basename): {list(map(os.path.basename, image_paths))}")
    
    # get draft by draft id
    draft_path = os.path.join(drafts_dir, draft)
    if not os.path.exists(draft_path):
        raise FileNotFoundError(draft_path)
    with open(draft_path, "r", encoding="utf-8") as reader:
        draft_body = reader.read()
    
    # extract draft data
    draft_name = os.path.splitext(draft)[0]
    draft_output_dir = os.path.join(outputs_dir, draft_name)
    if not os.path.exists(draft_output_dir):
        logger.info(f"Output directory for draft {draft_name} not found, making one.")
        os.makedirs(draft_output_dir, exist_ok=True)

    # extract subtitle styles (if any)
    styles_path = os.path.realpath(os.path.join(project_directory, "styles.yml"))
    if not os.path.exists(styles_path):
        logger.warning("No styles configured: will use default styles or ones found in draft.")
        styles_contents = list()
    else:
        with open(styles_path, "r", encoding="utf-8") as yaml_reader:
            styles_contents = yaml.safe_load(yaml_reader)

    # extract styles and subtitles.
    styles:Dict[str, Style] = extract_styles(styles_contents)
    logger.info(f"Obtained styles: {styles}")
    subtitles_by_image_id:Dict[str, List[Subtitle]] = extract_subtitles(draft_body, styles)
    logger.info(f"Obtained subtitles: {subtitles_by_image_id}")

    # apply subtitles to image with filter.
    if image_filters is None:
        filtered_image_paths = image_paths
    else:
        filtered_image_paths = list(map(lambda j:image_paths[j], filter(lambda i:i < len(image_paths), image_filters)))
    logger.info(f"Got filtered image paths (basename): {list(map(os.path.basename, filtered_image_paths))}")

    num_of_images = len(filtered_image_paths)
    # subtitle the images
    for i, image_path in enumerate(filtered_image_paths):
        image_id = os.path.basename(image_path)
        image = Image.open(image_path)

        if image_id in subtitles_by_image_id.keys():
            subtitles = subtitles_by_image_id[image_id]
            subtitled_image = add_subtitles_to_image(image, subtitles)
        else:
            subtitled_image = image
            
        save_path = os.path.join(draft_output_dir, image_id)
        subtitled_image.save(save_path)
        logger.info(f"Added subtitles to image {i+1}/{num_of_images}.")

    logger.info(f"Finished adding subtitles to {num_of_images} images.")
    return 0