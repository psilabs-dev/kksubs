import os
import logging
import shutil
import traceback
from PIL import Image
from typing import Dict, List
import yaml
import multiprocessing
import time

import pickle

from kksubs.data.subtitle.style import Style
from kksubs.data.subtitle.subtitle import SubtitleGroup
from common.exceptions import *

from kksubs.service.extraction.subtitle import extract_subtitle_groups
from kksubs.service.extraction.style import extract_styles
from kksubs.service.subtitle import add_subtitles_to_image
from kksubs.utils.renamer import rename_images, update_images_in_textpath

logger = logging.getLogger(__name__)

def add_subtitle_group_process(
        i,
        subtitle_group:SubtitleGroup,
        project_directory:str,
        num_of_images:int
):
    image_path = subtitle_group.input_image_path
    image = Image.open(image_path)

    subtitles = subtitle_group.subtitles
    if subtitles is not None:
        subtitled_image = add_subtitles_to_image(image, subtitles, project_directory)
    else:
        # probably shouldn't happen.
        subtitled_image = image
    
    save_path = subtitle_group.output_image_path
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    subtitled_image.save(save_path)
    logger.info(f"Added subtitles to image {i+1}/{num_of_images}.")

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
            self, workspace_directory:str=None,
            metadata_directory:str=None,
            state_directory:str=None,
            images_dir:str=None,
            drafts_dir:str=None,
            outputs_dir:str=None,
            styles_path:str=None,
    ):
        if workspace_directory is None:
            raise NotImplementedError("Workspace directory must be implemented.")
        # if create is None:
        #     create = False

        workspace_directory = os.path.realpath(workspace_directory)

        if metadata_directory is None:
            metadata_directory = os.path.join(os.path.expanduser("~"), ".kksubs")

        if state_directory is None:
            state_directory = os.path.join(metadata_directory, 'subtitle_journal')
        if images_dir is None:
            images_dir = os.path.realpath(os.path.join(workspace_directory, "images"))
        if drafts_dir is None:
            drafts_dir = os.path.realpath(os.path.join(workspace_directory, "drafts"))
        if outputs_dir is None:
            outputs_dir = os.path.realpath(os.path.join(workspace_directory, "output"))
        if styles_path is None:
            styles_path = os.path.realpath(os.path.join(workspace_directory, "styles.yml"))

        self.workspace_dir = workspace_directory
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
            raise InvalidProjectException(self.workspace_dir)
        
    def create(self):
        # creates the necessary objects that constitute a kksubs project.
        if not os.path.exists(self.workspace_dir):
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
    
    def get_state_path_v2(self, draft_name:str):
        # draft state as yaml file.
        return os.path.join(self.state_directory, draft_name) + '.yaml'

    def get_draft_paths(self):
        return list(map(lambda draft_id: os.path.join(self.drafts_dir, draft_id), self.get_draft_ids()))

    def get_draft_ids(self):
        return list(filter(lambda draft:os.path.splitext(draft)[1] in {".txt"}, os.listdir(self.drafts_dir)))

    def filter_images(self, file_list):
        return list(map(lambda image: os.path.join(file_list, image), filter(lambda file: os.path.isfile(os.path.join(file_list, file)) and os.path.splitext(file)[1] in {".png"} ,os.listdir(file_list))))

    def get_image_paths(self):
        return self.filter_images(self.images_dir)
    
    def get_output_directory(self):
        return self.outputs_dir

    def get_output_paths(self, draft_id:str):
        return self.filter_images(os.path.join(self.outputs_dir, draft_id))

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

    def read_previous_state(self, state_path:str) -> Dict[str, SubtitleGroup]:
        with open(state_path, "rb") as reader:
            logger.info(f"Reading previous state from {state_path}")
            try:
                previous_draft_state:Dict[str, SubtitleGroup] = pickle.load(reader)
                return previous_draft_state
            except AttributeError:
                logger.error(f"""
An attribute error occurred while reading previous state path.
This usually indicates that the state path is written by an outdated program.
The program will now delete the previous state and try again...

Original error message: {traceback.format_exc()} 
                """)
                previous_draft_state = dict()
                os.remove(state_path)
                raise RetryWatcherPrompt
            
    def save_current_state(self, state_path, current_state:Dict[str, SubtitleGroup]):
        with open(state_path, "wb") as writer:
            logger.info(f"Saving current subtitle state to {state_path}")
            pickle.dump(current_state, writer)
            
    # def read_previous_state_v2(self, state_path_v2:str) -> Dict[str, SubtitleGroup]:
    #     # extract subtitle groups from yaml file.
    #     previous_state = dict()
    #     with open(state_path_v2, 'r') as yaml_reader:
    #         state_data:Dict = yaml.safe_load(yaml_reader)
    #         for image_id, subtitle_group_data in state_data.items():
    #             previous_state[image_id] = SubtitleGroup.deserialize(subtitle_group_data)
    #     return previous_state
    
    # def save_current_state_v2(self, state_path, current_state:Dict[str, SubtitleGroup]):
    #     with open(state_path, 'w') as yaml_writer:
    #         data = {key:value.serialize() for key, value in current_state.items()}
    #         yaml.safe_dump(data, yaml_writer)

    def incremental_update(self, draft_name:str, subtitle_group_by_image_id:Dict[str, SubtitleGroup]) -> Dict[str, SubtitleGroup]:
        # filter subgroup dict by incremental update
        draft_output_dir = os.path.join(self.outputs_dir, draft_name)
        draft_id = os.path.splitext(draft_name)[0]
        # print(draft_output_dir)

        filtered_subtitle_group_by_image_id:Dict[str, SubtitleGroup] = dict()
        state_path = self.get_state_path(draft_name)
        # state_path_v2 = self.get_state_path_v2(draft_name)

        if not os.path.exists(self.metadata_directory):
            logger.info(f"Creating additional data directory.")
            os.mkdir(self.metadata_directory)
        if not os.path.exists(self.state_directory):
            logger.info(f"Creating states directory.")
            os.mkdir(self.state_directory)

        if not os.path.exists(state_path):
            logger.info("No previous state for this draft is found.")
            previous_draft_state:Dict[str, SubtitleGroup] = dict()
        else:
            previous_draft_state = self.read_previous_state(state_path)

        # if not os.path.exists(state_path_v2):
        #     logger.info('No previous state v2 for this draft is found.')
        #     previous_draft_state:Dict[str, SubtitleGroup] = dict()
        # else:
        #     previous_draft_state = self.read_previous_state_v2(state_path_v2)

        # check image deltas
        # for indeterminate sets, check for two things:
        # 1) if curr subtitle group != previous subtitle group.
        # 2) if image is updated i.e. image.mtime > previous.mtime.

        curr_image_ids = set(subtitle_group_by_image_id.keys())
        prev_image_ids = set(previous_draft_state.keys())
        out_image_ids = set(map(os.path.basename, self.get_output_paths(draft_id)))

        d1 = curr_image_ids.intersection(prev_image_ids).intersection(out_image_ids) # indeterminate (1, 2)
        
        d2 = curr_image_ids.intersection(prev_image_ids).difference(out_image_ids) # add subtitle.
        d3 = curr_image_ids.intersection(out_image_ids).difference(prev_image_ids) # indeterminate (1)
        d4 = prev_image_ids.intersection(out_image_ids).difference(curr_image_ids) # delete output image.

        d5 = curr_image_ids.difference(prev_image_ids).difference(out_image_ids) # add subtitle.
        d6 = prev_image_ids.difference(curr_image_ids).difference(out_image_ids) # do nothing.
        d7 = out_image_ids.difference(curr_image_ids).difference(prev_image_ids) # delete output image.

        # print(d1, d2, d3, d4, d5, d6, d7)

        for image_id in d1:
            subtitle_group = subtitle_group_by_image_id[image_id]
            previous_subtitle_group = previous_draft_state[image_id]
            if subtitle_group != previous_subtitle_group:
                filtered_subtitle_group_by_image_id[image_id] = subtitle_group_by_image_id[image_id]
                continue
            image_mtime = subtitle_group.image_modified_time
            output_mtime = os.path.getmtime(subtitle_group.output_image_path)
            if image_mtime > output_mtime:
                filtered_subtitle_group_by_image_id[image_id] = subtitle_group_by_image_id[image_id]

        for image_id in d3:
            subtitle_group = subtitle_group_by_image_id[image_id]
            image_mtime = subtitle_group.image_modified_time
            output_mtime = os.path.getmtime(subtitle_group.output_image_path)
            if image_mtime > output_mtime:
                filtered_subtitle_group_by_image_id[image_id] = subtitle_group_by_image_id[image_id]

        for image_id in d4.union(d7):
            output_image_path = os.path.join(draft_output_dir, image_id)
            if os.path.exists(output_image_path):
                os.remove(output_image_path)

        for image_id in d2.union(d5):
            filtered_subtitle_group_by_image_id[image_id] = subtitle_group_by_image_id[image_id]

        self.save_current_state(state_path, subtitle_group_by_image_id)
        # self.save_current_state_v2(state_path_v2, subtitle_group_by_image_id)

        return filtered_subtitle_group_by_image_id

    def add_subtitles_to_draft(
            self, 
            draft:str, # draft filename
            drafts:Dict[str, List[int]], # list of draft filenames and corresponding filtered image indices
            image_paths, 
            styles, 
            update_drafts:bool, prefix,
            allow_incremental_updating:bool, 
            allow_multiprocessing:bool
    ):
        # get draft by draft id
        draft_id = os.path.splitext(draft)[0]
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

        # extract styles and subtitles.
        # subtitles_by_image_id:Dict[str, List[Subtitle]] = extract_subtitles(draft_body, styles)
        subtitle_groups_by_image_id_dict:Dict[str, List[SubtitleGroup]] = extract_subtitle_groups(draft_id, draft_body, styles, self.images_dir, self.outputs_dir, prefix=prefix)

        for image_path in list(subtitle_groups_by_image_id_dict):
            # validate image paths for each subtitle group.
            input_image_path = os.path.join(self.images_dir, image_path)
            if not os.path.exists(input_image_path):
                logger.warning(f"Image ID {image_path} does not exist but is being referenced. These subtitles will be ignored.")
                del subtitle_groups_by_image_id_dict[image_path]
                continue

            subtitle_groups_by_image_id = subtitle_groups_by_image_id_dict.get(image_path)
            # validate fonts
            for group in subtitle_groups_by_image_id:
                for subtitle in group.subtitles:
                    try:
                        font = subtitle.style.text_data.font
                        if font != "default" and not os.path.exists(font):
                            subtitle.style.text_data.font = os.path.join(
                                self.workspace_dir, font
                            )
                    except AttributeError(f'Font does not exist for a subtitle for {image_path}.'): # font does not exist.
                        continue

        # apply subtitles to image with filter.
        if image_filters is None:
            filtered_image_paths = image_paths
        else:
            filtered_image_paths = list(map(lambda j:image_paths[j], filter(lambda i:i < len(image_paths), image_filters)))
        logger.debug(f"Got filtered image paths (basename): {list(map(os.path.basename, filtered_image_paths))}")

        # flattening
        subtitle_group_by_image_id:Dict[str, SubtitleGroup] = {
            _subtitle_group.image_id:_subtitle_group 
            for _image_id in subtitle_groups_by_image_id_dict 
            for _subtitle_group in subtitle_groups_by_image_id_dict[_image_id]
        }
        
        # remove images from output
        output_images_to_delete = list(set(os.listdir(draft_output_dir)).difference(subtitle_group_by_image_id.keys()))
        if output_images_to_delete:
            for image in output_images_to_delete:
                os.remove(os.path.join(draft_output_dir, image))
            logger.info(f'Removed images {output_images_to_delete}')

        # incremental updating (subtitle group)
        filtered_subtitle_groups_by_image_id = subtitle_group_by_image_id
        if allow_incremental_updating:
            filtered_subtitle_groups_by_image_id = self.incremental_update(draft_name, subtitle_group_by_image_id)

        # logger.debug(f"Obtained subtitles: {subtitles_by_image_id}")
        logger.debug(f'Obtained subtitle groups: {subtitle_groups_by_image_id_dict}')

        subtitle_groups:List[SubtitleGroup] = list()
        for image_id in filtered_subtitle_groups_by_image_id:
            subtitle_groups.append(subtitle_group_by_image_id[image_id])

        num_of_images = len(subtitle_groups)
        output_image_paths = list(map(os.path.basename, map(lambda group:group.output_image_path, subtitle_groups)))
        logger.info(f"Will begin subtitling {num_of_images} images: {list(map(os.path.basename, output_image_paths))}")
        print(f"Will begin subtitling {num_of_images} images: {list(map(os.path.basename, output_image_paths))}")

        start_time = time.time()
        if allow_multiprocessing:
            pool = multiprocessing.Pool()
            pool.starmap(add_subtitle_group_process, [(i, subtitle_group, self.workspace_dir, num_of_images) for i, subtitle_group in enumerate(subtitle_groups)])
            pool.close()
        else:
            for i, subtitle_group in enumerate(subtitle_groups):
                add_subtitle_group_process(i, subtitle_group, self.workspace_dir, num_of_images)
        end_time = time.time()
        logger.info(f'Finished subtitling {num_of_images} images for draft {draft} ({end_time - start_time}s).')
        print(f'Finished subtitling {num_of_images} images for draft {draft} ({end_time - start_time}s).')
        return

    def add_subtitles(self, drafts:Dict[str, List[int]]=None, prefix:str=None, allow_multiprocessing=True, allow_incremental_updating=None, update_drafts=True):
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
            logger.info(f"Output directory for project {self.workspace_dir} not found, making one.")
            os.makedirs(self.outputs_dir, exist_ok=True)

        # get image paths.
        image_paths:List[str] = self.get_image_paths()
        logger.debug(f"Got images (basename): {list(map(os.path.basename, image_paths))}")

        # extract subtitle styles (if any)
        if not os.path.exists(self.styles_path):
            logger.info("No styles configured: will use default styles or ones found in draft.")
            styles_contents = list()
        else:
            with open(self.styles_path, "r", encoding="utf-8") as yaml_reader:
                styles_contents = yaml.safe_load(yaml_reader)

        styles:Dict[str, Style] = extract_styles(styles_contents)
        logger.debug(f"Obtained styles: {styles}")

        for draft in drafts:
            self.add_subtitles_to_draft(
                draft, drafts, image_paths, styles, update_drafts, prefix, allow_incremental_updating, allow_multiprocessing
            )

        return 0
    
    # Delete folders in output directory.
    def clear_subtitles(self, drafts:Dict[str, List[int]]=None, force=False):
        # remove outputs corresponding to a draft.
        # if drafts is None, remove all folders in the output directory.
        if not os.path.exists(self.outputs_dir):
            return
        
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

                return 0

            return 0

        for draft in drafts:
            draft_name = os.path.splitext(draft)[0]
            draft_output_dir = os.path.join(self.outputs_dir, draft_name)
            if os.path.exists(draft_output_dir):
                shutil.rmtree(draft_output_dir)

            # search for metadata related to the draft.
            draft_state = self.get_state_path(draft_name)
            if os.path.exists(draft_state):
                logger.info("Deleting previous draft states from .kksubs file.")
                os.remove(draft_state)
        return 0
    
    def delete_project(self):
        for path in [self.images_dir, self.outputs_dir, self.drafts_dir, self.styles_path]:
            if not os.path.exists(path):
                continue
            if os.path.isdir(path):
                shutil.rmtree(path)
            if os.path.isfile(path):
                os.remove(path)