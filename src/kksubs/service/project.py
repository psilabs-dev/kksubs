import os
import logging
from PIL import Image
from typing import Dict, List
import yaml
from kksubs.data import Style, Subtitle

from kksubs.service.extractors import extract_styles, extract_subtitles
from kksubs.service.renamer import rename_images, update_images_in_textpath
from kksubs.service.subtitle import add_subtitles_to_image

logger = logging.getLogger(__name__)

# project preparation layer.
# folder/file logic, obtain read data, deserialization

class Project:
    def __init__(self, project_directory:str=None):
        if project_directory is None:
            project_directory = "."

        self.project_directory = project_directory
        self.images_dir = os.path.realpath(os.path.join(project_directory, "images"))
        self.drafts_dir = os.path.realpath(os.path.join(project_directory, "drafts"))
        self.outputs_dir = os.path.realpath(os.path.join(project_directory, "output"))
        self.styles_path = os.path.realpath(os.path.join(self.project_directory, "styles.yml"))
        if not (os.path.exists(self.images_dir) and os.path.exists(self.drafts_dir)):
            raise FileNotFoundError
        
    def get_draft_paths(self):
        return list(map(lambda draft_id: os.path.join(self.drafts_dir, draft_id), self.get_draft_ids()))

    def get_draft_ids(self):
        return list(filter(lambda draft:os.path.splitext(draft)[1] in {".txt"}, os.listdir(self.drafts_dir)))

    def get_image_paths(self):
        return list(map(lambda image: os.path.join(self.images_dir, image), filter(lambda file: os.path.isfile(os.path.join(self.images_dir, file)) and os.path.splitext(file)[1] in {".png"} ,os.listdir(self.images_dir))))

    def rename_images(self, padding_length=None, start_at=None, prefix=None, suffix=None):
        # Perform image renaming so it is structured and in alphabetical order.

        image_paths = self.get_image_paths()
        image_paths.sort()
        text_paths = self.get_draft_paths()

        n = len(image_paths)
        input_image_directory = self.images_dir

        if padding_length is None:
            padding_length = len(str(n))
        if start_at is None:
            start_at = 0

        new_image_paths = rename_images(image_paths, input_image_directory, padding_length=padding_length, start_at=start_at, prefix=prefix, suffix=suffix)
        logger.info(f"Renamed {n} images in directory {input_image_directory}.")

        for text_path in text_paths:
            text_id = os.path.basename(text_path)
            extension = os.path.splitext(text_path)[1]
            if extension != ".txt":
                logger.warning("File type not supported, skipping.")
                # raise TypeError(f"File must be text file, not {extension}.")
                continue
            
            text_path = os.path.join(self.drafts_dir, text_id)
            update_images_in_textpath(text_path, image_paths, new_image_paths=new_image_paths)

    pass

    def add_subtitles(self, drafts:Dict[str, List[int]]=None):

        if drafts is None:
            draft_ids = self.get_draft_ids()
            drafts = {draft:None for draft in draft_ids}

        if not os.path.exists(self.outputs_dir):
            logger.info(f"Output directory for project {self.project_directory} not found, making one.")
            os.makedirs(self.outputs_dir, exist_ok=True)

        # get image paths.
        image_paths:List[str] = self.get_image_paths()
        logger.info(f"Got images (basename): {list(map(os.path.basename, image_paths))}")

        # extract subtitle styles (if any)
        if not os.path.exists(self.styles_path):
            logger.warning("No styles configured: will use default styles or ones found in draft.")
            styles_contents = list()
        else:
            with open(self.styles_path, "r", encoding="utf-8") as yaml_reader:
                styles_contents = yaml.safe_load(yaml_reader)

        styles:Dict[str, Style] = extract_styles(styles_contents)
        logger.info(f"Obtained styles: {styles}")

        for draft in drafts:
            # get draft by draft id
            draft_path = os.path.join(self.drafts_dir, draft)
            image_filters = drafts.get(draft)

            if not os.path.exists(draft_path):
                raise FileNotFoundError(draft_path)
            with open(draft_path, "r", encoding="utf-8") as reader:
                draft_body = reader.read()

            # extract draft data
            draft_name = os.path.splitext(draft)[0]

            draft_output_dir = os.path.join(self.outputs_dir, draft_name)
            if not os.path.exists(draft_output_dir):
                logger.info(f"Output directory for draft {draft_name} not found, making one.")
                os.makedirs(draft_output_dir, exist_ok=True)

            # extract styles and subtitles.
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

            logger.info(f"Finished adding subtitles to {num_of_images} images for draft {draft}")

        return 0