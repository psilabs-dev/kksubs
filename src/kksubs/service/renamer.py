
import logging
import os
from typing import List

logger = logging.getLogger(__name__)

def check_file_conflict(old_file_paths:List[str], new_file_paths:List[str]) -> bool:
    # assume the old and new file paths are equal in length.
    # if there is file conflict return True
    # else return False
    for i, new_file_path in enumerate(new_file_paths):
        if new_file_path in old_file_paths[i+1:]:
            return True

    return False

def rename_images(image_paths:List[str], input_image_directory:str, padding_length=None, start_at=None, prefix=None, suffix=None) -> List[str]:

    # ideally, come up with an algorithm that dynamically adds a suffix if there is a file naming conflict,
    # and keep adding suffixes inductively until there is no conflict.
    new_image_paths = []
    for i, image_path in enumerate(image_paths):
        extension = os.path.splitext(image_path)[1]
        image_index = str(i+start_at).rjust(padding_length, "0")
        new_basename = f"{prefix}{image_index}{suffix}{extension}"
        new_image_path = os.path.join(input_image_directory, new_basename)
        new_image_paths.append(new_image_path)

    has_conflict = check_file_conflict(image_paths, new_image_paths)
    suffix_count = 0
    while has_conflict and suffix_count <= 5:
        logger.warning("File conflict detected while performing batch renaming. Attempting to overcome conflict by appending suffix.")
        # do some stuff
        conflict_suffix = "_s" # to resolve file conflict
        for j, new_image_path in enumerate(new_image_paths):
            new_image_path_name, extension = os.path.splitext(new_image_path)
            new_image_path = f"{new_image_path_name}{conflict_suffix}{extension}"
            new_image_paths[j] = new_image_path

        has_conflict = check_file_conflict(image_paths, new_image_paths)
        suffix_count += 1

    for i, image_path in enumerate(image_paths):
        os.rename(image_path, new_image_paths[i])
    
    return new_image_paths


def update_images_in_textstring(textstring:str, image_paths:List[str], new_image_paths:List[str]=None) -> str:
    if new_image_paths is None:
        new_image_paths = image_paths

    subtitle_group_textstrings = textstring.split("image_id:")

    # get the image id
    subtitle_body_by_image_id = dict()
    for subtitle_group_text in subtitle_group_textstrings:
        if not subtitle_group_text:
            continue
        if "\n" in subtitle_group_text:
            image_id, subtitle_body = subtitle_group_text.split("\n", 1)
        else:
            image_id = subtitle_group_text.strip()
            subtitle_body = ""
        image_id = image_id.lstrip()
        subtitle_body_by_image_id[image_id] = subtitle_body.strip()

    updated_textstring = ""

    for i, image_path in enumerate(image_paths):
        image_basename = os.path.basename(image_path)
        new_image_basename = os.path.basename(new_image_paths[i])

        # this process will remove subtitles that don't point to images,
        # as well as add new images into the subtitles.
        newline_prepend = ""
        if len(updated_textstring) > 0:
            if updated_textstring[-1] != "\n":
                newline_prepend = "\n\n"
            else:
                newline_prepend = "\n"
        else:
            newline_prepend = ""
            pass

        if image_basename in subtitle_body_by_image_id.keys():
            add_line = newline_prepend + "image_id: "+new_image_basename+"\n"+subtitle_body_by_image_id[image_basename]
        else:
            add_line = f"{newline_prepend}image_id: {new_image_basename}"

        updated_textstring += add_line
    
    if len(updated_textstring) > 0 and updated_textstring[-1] != "\n":
        updated_textstring += "\n"

    return updated_textstring

def update_images_in_textpath(text_path:str, image_paths:List[str], new_image_paths:List[str]=None):
    # updates the image IDs in the draft after renaming each image.

    if not os.path.exists(text_path):
        raise FileNotFoundError(f"text path {text_path} does not exist.")
    with open(text_path, "r", encoding="utf-8") as reader:
        content = reader.read()
    updated_textstring = update_images_in_textstring(content, image_paths, new_image_paths=new_image_paths)
    with open(text_path, "w", encoding="utf-8") as writer:
        writer.write(updated_textstring)