import logging
from pathlib import Path
from typing import List, Optional, Dict, Set
import os
import re
import shutil
import fnmatch
import tempfile
from natsort import natsorted

from common.data.file import Bucket
from common.exceptions import InvalidProjectException
from kksubs.service.file import FileService

logger = logging.getLogger(__name__)

STUDIO_PROJECT_FILENAME = ".studio_project"

class StudioProjectService:

    def __init__(
            self, 
            library:str, 
            game_directory:str,
            workspace:str,
            studio_file_names:List[str]=None,
            subtitle_file_names:List[str]=None,
    ):
        if studio_file_names is None:
            studio_file_names = ['UserData']
        if subtitle_file_names is None:
            subtitle_file_names = ['drafts', 'output', 'styles.yml']

        self.library = library
        self.game_directory = game_directory
        self.workspace = workspace
        self.studio_file_names = studio_file_names
        self.subtitle_file_names = subtitle_file_names
        self.file_service = FileService()

    def get_sync_state(self, project_path) -> Dict:
        sync_state = dict()
        for file in self.studio_file_names:
            file_path = os.path.join(project_path, file)
            if not os.path.exists(file_path):
                continue
            if os.path.isfile(file_path):
                sync_state[file_path] = os.path.getmtime(file_path)
            if os.path.isdir(file_path):
                sync_state[file_path] = Bucket(file_path).state()
        return sync_state

    def to_project_path(self, project_name:str) -> str:
        """
        Convert project ID to path to the Project. Note that this Project may not yet exist, hence no abspath or realpath.
        """
        return os.path.join(self.library, project_name)

    def is_project(self, project_name:str) -> bool:
        # check if project name corresponds to a valid project in the library.
        return project_name is not None and (
            os.path.exists(os.path.join(self.library, project_name, STUDIO_PROJECT_FILENAME))
            or project_name == self.game_directory
        )
    
    def copy_files(self, source, destination):
        # copy contents from files. (replace destination if exist)
        for file in self.studio_file_names:
            source_file_path = os.path.join(source, file)
            destination_file_path = os.path.join(destination, file)
            self.file_service.sync_unidirectional(source_file_path, destination_file_path)

            # # clear existing files
            # if os.path.exists(destination_file_path):
            #     if os.path.isfile(destination_file_path):
            #         os.remove(destination_file_path)
            #     if os.path.isdir(destination_file_path):
            #         shutil.rmtree(destination_file_path)

            # if not os.path.exists(source_file_path):
            #     continue

            # if os.path.isfile(source_file_path):
            #     shutil.copy(source_file_path, destination_file_path)
            # if os.path.isdir(source_file_path):
            #     shutil.copytree(source_file_path, destination_file_path)

    def directory_in_another_project(self, project_name: str) -> bool:
        """
        Return True if the directory given by the Project name is inside another Project.
        """
        target_dir = self.library
        for level in re.split(r'[\/\\]', project_name):
            if not os.path.exists(target_dir):
                pass
            if os.path.exists(os.path.join(target_dir, STUDIO_PROJECT_FILENAME)):
                return True
            target_dir = os.path.join(target_dir, level)
        return False

    # CRUD operations.
    # create
    def create_project(self, project_name:str, source_project_path=None):
        if source_project_path is None:
            source_project_path = self.game_directory

        # create project to library from workspace.
        logger.info(f"Creating project {project_name}.")
        
        # create project path if necessary (within the library)
        project_path = self.to_project_path(project_name)

        # check if super directory is a project (if so, raise error).
        if self.directory_in_another_project(project_name):
            raise FileExistsError("Project is being created in another directory.")

        metadata_path = os.path.join(project_path, STUDIO_PROJECT_FILENAME)
        # check if metadata exists.
        if os.path.exists(metadata_path):
            raise FileExistsError(f"Project {project_name} exists.")

        os.makedirs(project_path, exist_ok=True)
        # add metadata
        with open(metadata_path, "w") as writer:
            writer.write("")

        # copy contents from files.
        self.copy_files(source_project_path, project_path)

    def copy_project(self, source_project_name, destination_project_name:str=None) -> Optional[str]:
        if source_project_name == destination_project_name:
            raise KeyError("Destination of copy cannot be source.")

        if not self.is_project(source_project_name):
            raise InvalidProjectException(source_project_name)

        if destination_project_name is None:
            destination_project_name = source_project_name + "-copy"
            while self.is_project(destination_project_name):
                destination_project_name += "-copy"

        source_project_path = self.to_project_path(source_project_name)

        if self.is_project(destination_project_name):
            confirmation = input("A project already exists with this name. Override? (y/n): ")
            if confirmation != "y":
                return None
            destination_project_path = self.to_project_path(destination_project_name)
            self.copy_files(source_project_path, destination_project_path)
            return destination_project_name
        else:
            self.create_project(destination_project_name, source_project_path=source_project_path)
            return destination_project_name

    # get
    def list_projects(self, pattern=None) -> List[str]:
        # list projects in library (that fit optional pattern argument).
        library_path = self.library
        projects = list()
        for dirpath, dirnames, filenames in os.walk(library_path):
            if STUDIO_PROJECT_FILENAME in filenames:
                rel_path = os.path.relpath(dirpath, library_path)
                if pattern is None or fnmatch.fnmatch(rel_path, pattern):
                    projects.append(os.path.relpath(dirpath, self.library))
        return projects
    
    def transfer(self, source:str, destinations:Set[str], folders:Set[str]):
        source_path = self.to_project_path(source)
        destination_paths = list(map(self.to_project_path, destinations))
        for folder in folders:
            folder_from_source = os.path.join(source_path, folder)
            if not os.path.exists(folder_from_source):
                logger.info(f"Skipping folder {folder_from_source} which does not exist.")
                continue
            if not os.path.isdir(folder_from_source):
                logger.error(f'target {folder_from_source} is not directory.')
                continue
            for dest_path in destination_paths:
                folder_from_dest = os.path.join(dest_path, folder)
                if os.path.exists(folder_from_dest) and not os.path.isdir(folder_from_dest):
                    logger.warning(f'Target {folder_from_dest} exists but is not a directory: skipping.')
                    continue
                os.makedirs(folder_from_dest, exist_ok=True)
                shutil.copytree(folder_from_source, folder_from_dest, dirs_exist_ok=True)
        return

    # update
    def pull_project(self, from_project_name):
        # pull changes from library to workspace (aka. load project).
        logger.info(f"Pulling from project {from_project_name}.")
        if not self.is_project(from_project_name):
            raise InvalidProjectException(from_project_name)
        project_path = self.to_project_path(from_project_name)
        self.copy_files(project_path, self.game_directory)

    def push_project(self, to_project_name):
        # push changes from workspace to library.
        logger.info(f"Pushing project {to_project_name}.")
        if not self.is_project(to_project_name):
            raise InvalidProjectException(to_project_name)
        project_path = self.to_project_path(to_project_name)
        self.copy_files(self.game_directory, project_path)

    def get_sync_state(self):
        new_state = dict()
        for file in self.studio_file_names:
            workspace_file_path = os.path.join(self.game_directory, file)
            if os.path.isdir(workspace_file_path):
                new_state[file] = Bucket(path=workspace_file_path).files
        return new_state

    def sync_studio_project(self, project_name, previous_state:Optional[Dict]=None, last_sync_time:Optional[int]=None) -> Dict:
        # sync between library and workspace and returns the final state as output.
        new_state = dict()
        
        for file in self.studio_file_names:
            if previous_state is None:
                relevant_state = None
            else:
                relevant_state = previous_state.get(file)

            workspace_file_path = os.path.join(self.game_directory, file)
            library_file_path = os.path.join(self.library, project_name, file)
            output_bucket = self.file_service.sync_bidirectional(workspace_file_path, library_file_path, previous_state=relevant_state, last_sync_time=last_sync_time)
            if output_bucket is None:
                new_state[file] = None
            else:
                new_state[file] = output_bucket.state()

        return new_state
    
    def sync_subtitle_project(self, project_name, previous_state:Optional[Dict]=None, last_sync_time:Optional[int]=None) -> Dict:
        new_state = dict()

        for file in self.subtitle_file_names:
            if previous_state is None:
                relevant_state = None
            else:
                relevant_state = previous_state.get(file)
            workspace_file_path = os.path.join(self.workspace, file)
            library_file_path = os.path.join(self.library, project_name, 'kksubs-project', file)
            output = self.file_service.sync_bidirectional(workspace_file_path, library_file_path, previous_state=relevant_state, last_sync_time=last_sync_time)

            if output is None:
                new_state[file] = None
            elif isinstance(output, int) or isinstance(output, float):
                new_state[file] = output
            elif isinstance(output, Bucket):
                new_state[file] = output.state()
            else:
                raise TypeError(f'Unexpected type occurred: {type(output)}')

        return new_state

    # rename project
    def rename_project(self, current_project_id: str, new_project_id: str, safe=True) -> bool:
        """
        Renames the current Project, provided the new project name is not a subset of another Project.
        Return True if successfully renamed, else False.
        """

        # validate current project ID
        if not self.is_project(current_project_id):
            logger.error(f"Cannot rename project {new_project_id}: cannot verify current project {current_project_id}.")
            return False

        # validate new project name.
        if self.is_project(new_project_id) or self.directory_in_another_project(new_project_id):
            logger.error(f"Cannot rename project {new_project_id}: Project cannot be contained in another project.")
            return False
        
        new_project_path = self.to_project_path(new_project_id)
        if os.path.exists(new_project_path):
            logger.error(f"Cannot rename project {new_project_id}: A directory already exists here.")
            return False
        
        # move old project to new project.
        curr_project_path = self.to_project_path(current_project_id)
        if safe:
            confirmation = input(f"Move project {current_project_id} to {new_project_id}? (Y): ")
            if confirmation != "Y":
                print("cancelled")
                return False

        shutil.move(curr_project_path, new_project_path)
        return True

    # delete
    def delete_project(self, project_name, safe=True) -> bool:
        # delete project from library.
        logger.info(f"Deleting project {project_name}.")
        if not self.is_project(project_name):
            raise InvalidProjectException(project_name)
        if safe:
            confirmation = input(f"Delete project {project_name}? (Y): ")
            if confirmation != "Y":
                return False
        shutil.rmtree(os.path.join(self.library, project_name))
        return True

    # delete multiple projects
    def delete_projects(self, project_names, safe=True) -> bool:
        # check if all the projects are valid.
        for name in project_names:
            if not self.is_project(name):
                raise InvalidProjectException(name)
        
        if safe:
            print("Delete the following projects?\n-----")
            for name in project_names:
                print(f"- {name}")
            print("-----")
            confirmation = input(f"Confirm (y/n): ")
            if confirmation!= "y":
                return False
        
        for name in project_names:
            self.delete_project(name, safe=False)
        return True
    
    def to_game_capture_path(self) -> str:
        capture_path = os.path.join(self.game_directory, 'UserData/cap')
        return capture_path

    def to_project_capture_path(self, project_name:str) -> str:
        if not self.is_project(project_name):
            raise InvalidProjectException(project_name)
        project_path = self.to_project_path(project_name)
        capture_path = os.path.join(project_path, 'UserData/cap')
        return capture_path
    
    def export_project_to_gallery(self, project_name, destination):
        cap_source = os.path.join(self.to_project_capture_path(project_name))
        cap_target = os.path.join(destination, project_name, 'cap')
        output_source = os.path.join(self.to_project_path(project_name), str(Path('kksubs-project') / 'output'))
        output_target = os.path.join(destination, project_name, 'output')

        # print(f'{cap_source}\n{cap_target}\n{output_source}\n{output_target}\n')
        self.file_service.sync_unidirectional(cap_source, cap_target)
        self.file_service.sync_unidirectional(output_source, output_target)
        return
    
    def export_gallery(self, destination:str, pattern:Optional[str]=None):
        projects = self.list_projects(pattern=pattern)
        for project_name in projects:
            self.export_project_to_gallery(project_name, destination)
            logger.info(f'Exported project \"{project_name}\".')
        
        return projects

    def correct_scene_order(self) -> bool:
        """
        Correct order of scene files when sorted by modified/created time, which is how CharaStudio orders scenes. Return True if successful, else False.
        """
        scene_directory = os.path.join(self.game_directory, 'UserData', 'studio', 'scene')
        if not os.path.exists(scene_directory):
            logger.error(f"Scene directory {scene_directory} not found.")
            return False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get a list of all .png files in the original directory
            png_files = [file for file in os.listdir(scene_directory) if file.endswith('.png')]
            png_files = natsorted(png_files)  # Sort files using natural sorting

            # Move original images to the temporary directory
            for png_file in png_files:
                src_path = os.path.join(scene_directory, png_file)
                dst_path = os.path.join(temp_dir, png_file)
                shutil.move(src_path, dst_path)

            # Copy images from the temporary directory back to the original directory
            temp_files = os.listdir(temp_dir)
            for temp_file in temp_files:
                src_path = os.path.join(temp_dir, temp_file)
                dst_path = os.path.join(scene_directory, temp_file)
                shutil.copy(src_path, dst_path)
        
        return True