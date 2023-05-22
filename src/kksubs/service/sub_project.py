import os
import logging
import shutil
from PIL import Image
from typing import Dict, List
import yaml
import multiprocessing
import time

import pickle

from kksubs.data.subtitle import Style, Subtitle, SubtitleGroup
from kksubs.exceptions import InvalidProjectException

from kksubs.service.extractors import extract_styles, extract_subtitles
from kksubs.service.subtitle import add_subtitles_to_image
from kksubs.utils.renamer import rename_images, update_images_in_textpath

logger = logging.getLogger(__name__)

def add_subtitle_process(
        i, 
        image_path, 
        project_directory,
        subtitles_by_image_id, 
        draft_output_dir, 
        prefix, 
        num_of_images
):
    image_id = os.path.basename(image_path)
    image = Image.open(image_path)
    # print(image_id)

    if image_id in subtitles_by_image_id.keys():
        subtitles = subtitles_by_image_id[image_id]
        subtitled_image = add_subtitles_to_image(image, subtitles, project_directory)
    else:
        subtitled_image = image

    save_path = os.path.join(draft_output_dir, prefix+image_id)
    subtitled_image.save(save_path)
    logger.info(f"Added subtitles to image {i+1}/{num_of_images}.")
    # print(f"Added subtitles to image {i+1}/{num_of_images}.")

# project preparation layer.
# folder/file logic, obtain read data, deserialization

class SubtitleProjectService:
    def __init__(
            self, project_directory:str=None, create=None,
            metadata_directory:str=None,
            state_directory:str=None,
            images_dir:str=None,
            drafts_dir:str=None,
            outputs_dir:str=None,
            styles_path:str=None,
    ):
        if project_directory is None:
            project_directory = "."
        # if create is None:
        #     create = False

        project_directory = os.path.realpath(project_directory)
        if metadata_directory is None:
            metadata_directory = os.path.join(project_directory, ".kksubs")
        if state_directory is None:
            state_directory = os.path.join(metadata_directory, 'state')
        if images_dir is None:
            images_dir = os.path.realpath(os.path.join(project_directory, "images"))
        if drafts_dir is None:
            drafts_dir = os.path.realpath(os.path.join(project_directory, "drafts"))
        if outputs_dir is None:
            outputs_dir = os.path.realpath(os.path.join(project_directory, "output"))
        if styles_path is None:
            styles_path = os.path.realpath(os.path.join(project_directory, "styles.yml"))

        self.project_directory = project_directory
        self.metadata_directory = metadata_directory
        self.state_directory = state_directory
        self.images_dir = images_dir
        self.drafts_dir = drafts_dir
        self.outputs_dir = outputs_dir
        self.styles_path = styles_path

        # if create:
        #     self.create()

    def validate(self):
        if not (os.path.exists(self.images_dir) and os.path.exists(self.drafts_dir)):
            raise InvalidProjectException(self.project_directory)
        
    def create(self):
        # creates the necessary objects that constitute a kksubs project.
        if not os.path.exists(self.project_directory):
            raise FileNotFoundError
        changes_made = False

        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
            changes_made = True
            logger.info("Created new images directory.")
        else:
            logger.info("Image directory already exists.")
        if not os.path.exists(self.drafts_dir):
            os.makedirs(self.drafts_dir)
            changes_made = True
            logger.info("Created new drafts directory.")
            with open(os.path.join(self.drafts_dir, "draft.txt"), "w") as writer:
                writer.write("")
            logger.info("Created an empty draft.")
            # self.rename_images()
            sorted_image_paths = sorted(self.get_image_paths())
            self.update_drafts(sorted_image_paths, sorted_image_paths)
        else:
            logger.info("Drafts directory already exists.")
        if not os.path.exists(self.outputs_dir):
            os.makedirs(self.outputs_dir)
            changes_made = True
            logger.info("Created new outputs directory.")
        else:
            logger.info("Outputs directory already exists.")
        if not os.path.exists(self.styles_path):
            # create a template styles file. TODO: create template online and make download request.
            with open(self.styles_path, "w") as writer:
                writer.write("")
            changes_made = True
            logger.info("Created a styles file.")
        else:
            logger.info("Styles file already exists.")
        
        if changes_made:
            logger.info("Successfully created a project directory.")
        else:
            logger.info("No changes were made to the project.")

    def get_state_path(self, draft_name:str):
        # draft name without extension.
        return os.path.join(self.state_directory, draft_name)

    def get_draft_paths(self):
        return list(map(lambda draft_id: os.path.join(self.drafts_dir, draft_id), self.get_draft_ids()))

    def get_draft_ids(self):
        return list(filter(lambda draft:os.path.splitext(draft)[1] in {".txt"}, os.listdir(self.drafts_dir)))

    def get_image_paths(self):
        return list(map(lambda image: os.path.join(self.images_dir, image), filter(lambda file: os.path.isfile(os.path.join(self.images_dir, file)) and os.path.splitext(file)[1] in {".png"} ,os.listdir(self.images_dir))))

    def update_drafts(self, image_paths, new_image_paths):
        # replaces old image paths with new image paths for all drafts.
        # to get an empty draft with image paths, use same image paths for both arguments.

        text_paths = self.get_draft_paths()
        for text_path in text_paths:
            text_id = os.path.basename(text_path)
            extension = os.path.splitext(text_path)[1]
            if extension != ".txt":
                logger.warning(f"File type for {text_id} not supported, skipping.")
                # raise TypeError(f"File must be text file, not {extension}.")
                continue
            
            text_path = os.path.join(self.drafts_dir, text_id)
            update_images_in_textpath(text_path, image_paths, new_image_paths=new_image_paths)

    def rename_images(self, padding_length=None, start_at=None, prefix=None, suffix=None):
        # Perform image renaming so it is structured and in alphabetical order.
        if prefix is None:
            prefix = ""
        if suffix is None:
            suffix = ""

        image_paths = self.get_image_paths()
        image_paths.sort()
        # text_paths = self.get_draft_paths()

        n = len(image_paths)
        input_image_directory = self.images_dir

        if padding_length is None:
            padding_length = len(str(n))
        if start_at is None:
            start_at = 0

        new_image_paths = rename_images(image_paths, input_image_directory, padding_length=padding_length, start_at=start_at, prefix=prefix, suffix=suffix)
        logger.info(f"Renamed {n} images in directory {input_image_directory}.")

        self.update_drafts(image_paths, new_image_paths)
        # for text_path in text_paths:
        #     text_id = os.path.basename(text_path)
        #     extension = os.path.splitext(text_path)[1]
        #     if extension != ".txt":
        #         logger.warning(f"File type for {text_id} not supported, skipping.")
        #         # raise TypeError(f"File must be text file, not {extension}.")
        #         continue
            
        #     text_path = os.path.join(self.drafts_dir, text_id)
        #     update_images_in_textpath(text_path, image_paths, new_image_paths=new_image_paths)

    pass

    def add_subtitles(self, drafts:Dict[str, List[int]]=None, prefix:str=None, allow_multiprocessing=True, allow_incremental_updating=False, update_drafts=False):
        if allow_multiprocessing is None:
            allow_multiprocessing = True
        if allow_incremental_updating is None:
            # incremental updating saves/pickles your previous subtitle into a .kksubs directory, 
            # so that future calls only look for changes in the input data,
            # this will speed up the subtitling process by only subtitling images that are actually updated.
            allow_incremental_updating = False

        if prefix is None:
            prefix = ""

        if drafts is None:
            draft_ids = self.get_draft_ids()
            drafts = {draft:None for draft in draft_ids}

        # log info.
        if allow_multiprocessing:
            logger.info("Multiprocessing is enabled.")
        if allow_incremental_updating:
            logger.info("Incremental updating is enabled.")

        if not os.path.exists(self.outputs_dir):
            logger.info(f"Output directory for project {self.project_directory} not found, making one.")
            os.makedirs(self.outputs_dir, exist_ok=True)

        # get image paths.
        image_paths:List[str] = self.get_image_paths()
        logger.debug(f"Got images (basename): {list(map(os.path.basename, image_paths))}")

        # extract subtitle styles (if any)
        if not os.path.exists(self.styles_path):
            logger.warning("No styles configured: will use default styles or ones found in draft.")
            styles_contents = list()
        else:
            with open(self.styles_path, "r", encoding="utf-8") as yaml_reader:
                styles_contents = yaml.safe_load(yaml_reader)

        styles:Dict[str, Style] = extract_styles(styles_contents)
        logger.debug(f"Obtained styles: {styles}")

        for draft in drafts:
            # get draft by draft id
            draft_path = os.path.join(self.drafts_dir, draft)
            if update_drafts:
                update_images_in_textpath(draft_path, image_paths, new_image_paths=image_paths)

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
            
            # remove images in output that are not in input.
            images_to_remove_from_output = list(set(os.listdir(draft_output_dir)).difference(set(list(map(os.path.basename, image_paths)))))
            for image_to_remove in images_to_remove_from_output:
                os.remove(os.path.join(draft_output_dir, image_to_remove))

            # extract styles and subtitles.
            subtitles_by_image_id:Dict[str, List[Subtitle]] = extract_subtitles(draft_body, styles)

            
            for image_id in list(subtitles_by_image_id):
                # validate image paths for each subtitle.
                image_path = os.path.join(self.images_dir, image_id)
                if not os.path.exists(image_path):
                    logger.warning(f"Image ID {image_id} does not exist but is being referenced by subtitle. This subtitle will be ignored.")
                    del subtitles_by_image_id[image_id]
                    continue

                # TODO: project directory burden switched to subtitles, delete this.
                # validate subtitle font
                subtitles = subtitles_by_image_id.get(image_id)
                for subtitle in subtitles:
                    try:
                        font = subtitle.style.text_data.font
                        if font != "default" and not os.path.exists(font):
                            subtitle.style.text_data.font = os.path.join(
                                self.project_directory, font
                            )
                    except AttributeError: # font does not exist.
                        continue

            # apply subtitles to image with filter.
            if image_filters is None:
                filtered_image_paths = image_paths
            else:
                filtered_image_paths = list(map(lambda j:image_paths[j], filter(lambda i:i < len(image_paths), image_filters)))
            logger.debug(f"Got filtered image paths (basename): {list(map(os.path.basename, filtered_image_paths))}")

            # incremental updating
            if allow_incremental_updating:
                filtered_updated_paths = list()
                subtitle_group_state_path = self.get_state_path(draft_name)

                if not os.path.exists(self.metadata_directory):
                    logger.info(f"Creating additional data directory.")
                    os.mkdir(self.metadata_directory)
                if not os.path.exists(self.state_directory):
                    logger.info(f"Creating states directory.")
                    os.mkdir(self.state_directory)
                if not os.path.exists(subtitle_group_state_path):
                    logger.info("No previous state for this draft is found.")
                    previous_draft_state:Dict[str, SubtitleGroup] = dict()
                else:
                    with open(subtitle_group_state_path, "rb") as reader:
                        logger.info(f"Reading previous state from {subtitle_group_state_path}")
                        previous_draft_state:Dict[str, SubtitleGroup] = pickle.load(reader)

                # save subtitles as image.
                current_draft_state:Dict[str, SubtitleGroup] = {
                    image_id:SubtitleGroup(
                        input_image_path=os.path.join(self.images_dir, image_id),
                        image_modified_time=os.path.getmtime(os.path.join(self.images_dir, image_id)), 
                        output_image_path=os.path.join(draft_output_dir, image_id),
                        subtitles=subtitles_by_image_id[image_id],
                    ) for image_id in subtitles_by_image_id
                }

                # check image deltas
                curr_draft_image_ids = set(current_draft_state.keys())
                previous_draft_image_ids = set(previous_draft_state.keys())

                curr_draft_new_images = curr_draft_image_ids.difference(previous_draft_image_ids)
                curr_draft_deleted_images = previous_draft_image_ids.difference(curr_draft_image_ids)
                curr_draft_indeterminate = curr_draft_image_ids.intersection(previous_draft_image_ids)
                # add subtitles to new images and delete subtitles from deleted images

                for image_path in filtered_image_paths:
                    image_id = os.path.basename(image_path)
                    if image_id not in os.listdir(draft_output_dir):
                        logger.info(f"Found image {image_id} not in output, adding.")
                        filtered_updated_paths.append(image_path)
                        continue
                    if image_id in curr_draft_new_images:
                        logger.info(f"New image detected, adding to subtitle queue: {image_id}")
                        filtered_updated_paths.append(image_path)
                        continue
                    if image_id in curr_draft_deleted_images:
                        # delete output image logic here here.
                        if os.path.exists(os.path.join(draft_output_dir, image_id)):
                            logger.info(f"Removing image {image_id}")
                            os.remove(os.path.join(draft_output_dir, image_id))
                        continue
                    if image_id in curr_draft_indeterminate:
                        previous_image_state:SubtitleGroup = previous_draft_state.get(image_id)
                        current_image_state:SubtitleGroup = current_draft_state.get(image_id)
                        if previous_image_state != current_image_state:
                            logger.info(f"Changes detected for image {image_id}")
                            filtered_updated_paths.append(image_path)
                            continue
                        else:
                            logger.debug(f"No updates to image {image_id}: skipping.")
                            continue
                    if image_id not in curr_draft_image_ids:
                        logger.error(f"Image ID {image_id} not found in the draft.")
                        filtered_updated_paths.append(image_path)
                        continue
                    else:
                        logger.error("An unexpected situation occurred.")
                
                filtered_image_paths = filtered_updated_paths

                with open(subtitle_group_state_path, "wb") as writer:
                    logger.info(f"Saving current subtitle state to {subtitle_group_state_path}")
                    pickle.dump(current_draft_state, writer)

            logger.debug(f"Obtained subtitles: {subtitles_by_image_id}")

            num_of_images = len(filtered_image_paths)
            logger.info(f"Will begin subtitling {num_of_images} images: {list(map(os.path.basename, filtered_image_paths))}")

            # subtitle images.
            start_time = time.time()
            if allow_multiprocessing:
                pool = multiprocessing.Pool()
                pool.starmap(add_subtitle_process, [(i, image_path, self.project_directory, subtitles_by_image_id, draft_output_dir, prefix, num_of_images) for i, image_path in enumerate(filtered_image_paths)])
            else:
                for i, image_path in enumerate(filtered_image_paths):
                    add_subtitle_process(i, image_path, self.project_directory, subtitles_by_image_id, draft_output_dir, prefix, num_of_images)
            runtime = time.time() - start_time

            logger.info(f"Finished subtitling {num_of_images} images for draft {draft} ({runtime}s)")

        return 0
    
    # Delete folders in output directory.
    def clear_subtitles(self, drafts:Dict[str, List[int]]=None, force=False):
        # remove outputs corresponding to a draft.
        # if drafts is None, remove all folders in the output directory.

        if drafts is None:
            folders = list(filter(lambda dir:os.path.isdir(os.path.join(self.outputs_dir, dir)), os.listdir(self.outputs_dir)))
            if not folders:
                logger.warning("Output directory has no folders to delete.")

            # print(folders)
            if not force:
                print(f"Clear these output folders and contents? {folders}")

            confirmation = "y" if force else input("Enter y to confirm: ")
            if confirmation == "y":

                for folder in folders:
                    shutil.rmtree(os.path.join(self.outputs_dir, folder))
                    logger.info(f"Removed folder {folder}")
                
                if os.path.exists(self.metadata_directory):
                    logger.info("Removing additional project data directory.")
                    shutil.rmtree(self.metadata_directory)

                return 0

            return 0

        for draft in drafts:
            draft_name = os.path.splitext(draft)[0]
            draft_output_dir = os.path.join(self.outputs_dir, draft_name)
            if os.path.exists(draft_output_dir):
                shutil.rmtree(draft_output_dir)

            # search for metadata related to the draft.
            draft_state = self.get_state_path(draft_name)
            print(draft_state)
            if os.path.exists(draft_state):
                logger.info("Deleting previous draft states from .kksubs file.")
                os.remove(draft_state)
        return 0
    
    def delete_project(self):
        for path in [self.images_dir, self.outputs_dir, self.drafts_dir, self.metadata_directory, self.styles_path]:
            if not os.path.exists(path):
                continue
            if os.path.isdir(path):
                shutil.rmtree(path)
            if os.path.isfile(path):
                os.remove(path)