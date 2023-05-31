import logging
import os
from typing import List, Optional
import yaml
from common.exceptions import InvalidProjectException
import subprocess
from packaging import version
import time

from common.import_utils import get_kksubs_version
from kksubs.service.file import FileService
from kkp.service.studio_project import StudioProjectService

from kksubs.service.sub_project import SubtitleProjectService
from kkp.view.project import ProjectView
from kkp.watcher.project import ProjectWatcher
from common.utils.coalesce import coalesce
from common.utils.file import *
from common.utils.decorators import *

# config information
CONFIG_FILE_NAME = 'config.yaml'
GAME_DIRECTORY_KEY = 'game-directory'
LIBRARY_KEY = 'library-directory'
WORKSPACE_KEY = 'workspace-directory'

# data information
DATA_FILE_NAME = 'data.yaml'
CURRENT_PROJECT_KEY = 'current-project'
SYNC_TIME_KEY = 'last-synced-time'
SUBTITLE_SYNC_STATE_KEY = 'subtitle-sync-state'
STUDIO_SYNC_STATE_KEY = 'studio-sync-state'
LIST_PROJECT_HISTORY_KEY = 'list-project-history'
VERSION_KEY = 'version'

logger = logging.getLogger(__name__)

class ProjectController:

    def __init__(
            self,
            game_directory:str=None,
            library:str=None,
            config_file_path:str=None,
            workspace:str=None,

            data_file_path:str=None,
            subtitle_project_service:SubtitleProjectService=None,
            studio_project_service:StudioProjectService=None,
            project_view:ProjectView=None,

            current_project:str=None,
    ):
        
        logger.info('Creating project controller...')
        self.config_file_path = config_file_path
        self.game_directory = game_directory
        self.library = library
        self.workspace = workspace
        self.current_project = current_project

        self.data_file_path = data_file_path
        self.subtitle_sync_state = None
        self.studio_sync_state = None
        self.last_sync_time = None

        self.subtitle_project_service = subtitle_project_service
        self.studio_project_service = studio_project_service
        # self.subtitle_watcher = None
        self.project_watcher = None
        self.project_view = project_view

        self.list_project_history:List[str] = None

    def _get_config_file_path(self, config_path:str=None):
        return coalesce(config_path, self.config_file_path)

    def _get_data_file_path(self, data_file_path:str=None):
        return coalesce(data_file_path, self.data_file_path)

    def _read_config(self, config_file_path:str=None) -> Dict:
        config_file_path = self._get_config_file_path(config_path=config_file_path)
        if not os.path.exists(config_file_path):
            return dict()
        with open(config_file_path, 'r') as reader:
            return coalesce(yaml.safe_load(reader), dict())
        
    def _write_config(self, config_path:str=None):
        if self.workspace is None:
            return
        config = {
            GAME_DIRECTORY_KEY: self.game_directory,
            LIBRARY_KEY: self.library,
            WORKSPACE_KEY: self.workspace,
        }
        config_path = self._get_config_file_path(config_path=config_path)
        with open(config_path, 'w') as writer:
            return yaml.safe_dump(config, writer)

    def _read_data(self, data_path:str=None) -> Dict:
        data_file_path = self._get_data_file_path(data_file_path=data_path)
        if not os.path.exists(data_file_path):
            return dict()
        with open(data_file_path, 'r') as reader:
            return coalesce(yaml.safe_load(reader), dict())

    def _write_data(self, data_path:str=None):
        if self.workspace is None:
            return
        data = {
            CURRENT_PROJECT_KEY: self.current_project,
            SUBTITLE_SYNC_STATE_KEY: self.subtitle_sync_state,
            STUDIO_SYNC_STATE_KEY: self.studio_sync_state,
            LIST_PROJECT_HISTORY_KEY: self.list_project_history,
            VERSION_KEY: get_kksubs_version(),
        }
        data_path = self._get_data_file_path(data_file_path=data_path)
        with open(data_path, 'w') as writer:
            return yaml.safe_dump(data, writer)

    def configure(
            self, 
            metadata_directory:Optional[str], 
            game_directory:Optional[str], 
            library:Optional[str], 
            workspace:Optional[str]
    ):
        # configures controller.
        # retrieve metadata.
        config_path = os.path.join(metadata_directory, CONFIG_FILE_NAME)
        data_path = os.path.join(metadata_directory, DATA_FILE_NAME)

        config_info = self._read_config(config_path)
        data_info = self._read_data(data_path)

        config_info[GAME_DIRECTORY_KEY] = coalesce(game_directory, config_info.get(GAME_DIRECTORY_KEY))
        config_info[LIBRARY_KEY] = coalesce(library, config_info.get(LIBRARY_KEY))
        config_info[WORKSPACE_KEY] = coalesce(workspace, config_info.get(WORKSPACE_KEY))

        data_info[CURRENT_PROJECT_KEY] = data_info.get(CURRENT_PROJECT_KEY)
        data_info[SUBTITLE_SYNC_STATE_KEY] = data_info.get(SUBTITLE_SYNC_STATE_KEY)
        data_info[STUDIO_SYNC_STATE_KEY] = data_info.get(STUDIO_SYNC_STATE_KEY)
        data_info[SYNC_TIME_KEY] = data_info.get(SYNC_TIME_KEY)
        data_info[LIST_PROJECT_HISTORY_KEY] = data_info.get(LIST_PROJECT_HISTORY_KEY)
        data_info[VERSION_KEY] = data_info.get(VERSION_KEY)

        # version comparison
        version_from_data = data_info.get(VERSION_KEY)
        current_version = get_kksubs_version()
        if version_from_data is None or version.parse(version_from_data) < version.parse(current_version):
            print(f'A different version {version_from_data} is detected (current version {current_version}).')

            # check for, import, and remove old data files.
            kks_data_file = os.path.join(metadata_directory, 'kksubs.yaml')
            if os.path.exists(kks_data_file):
                confirm = input('A kksubs.yaml file is detected. Import settings from that file? This will delete the kksubs.yaml file and create new config files. (Y) ') == "Y"
                if confirm:
                    previous_data = self._read_data(data_path=kks_data_file)

                    for config_key in [GAME_DIRECTORY_KEY, LIBRARY_KEY, WORKSPACE_KEY]:
                        config_info[config_key] = coalesce(config_info.get(config_key), previous_data.get(config_key))

                    for data_key in [CURRENT_PROJECT_KEY, SUBTITLE_SYNC_STATE_KEY, STUDIO_SYNC_STATE_KEY, SYNC_TIME_KEY, LIST_PROJECT_HISTORY_KEY]:
                        data_info[data_key] = coalesce(data_info.get(data_key), previous_data.get(data_key))
                    logger.info('Deleting old data file.')
                    os.remove(kks_data_file)

        for key in [GAME_DIRECTORY_KEY, LIBRARY_KEY, WORKSPACE_KEY]:
            path = config_info.get(key)
            if path is None:
                raise NotImplementedError(key)
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            config_info[key] = os.path.realpath(path)
        
        self.config_file_path = config_path
        self.data_file_path = data_path

        self.game_directory = config_info.get(GAME_DIRECTORY_KEY)
        self.library = config_info.get(LIBRARY_KEY)
        self.workspace = config_info.get(WORKSPACE_KEY)

        self.current_project = data_info.get(CURRENT_PROJECT_KEY)
        self.subtitle_sync_state = data_info.get(SUBTITLE_SYNC_STATE_KEY)
        self.studio_sync_state = data_info.get(STUDIO_SYNC_STATE_KEY)
        self.last_sync_time = data_info.get(SYNC_TIME_KEY)
        self.list_project_history = data_info.get(LIST_PROJECT_HISTORY_KEY)

        self.subtitle_project_service = SubtitleProjectService(project_directory=self.workspace)
        self.studio_project_service = StudioProjectService(self.library, self.game_directory, self.workspace)
        self.project_view = ProjectView()

        self.file_service = FileService()
        # self.subtitle_watcher = SubtitleWatcher(self.subtitle_project_service)
        self.project_watcher = ProjectWatcher(self.subtitle_project_service, self.studio_project_service)
        self.project_watcher.load_watch_arguments(
            allow_incremental_updating=True,
            allow_multiprocessing=True,
        )

    @spacing
    def info(self):
        print(f'Game:                {self.game_directory}')
        print(f'Library:             {self.library}')
        print(f'Workspace:           {self.workspace}')
        self.list_projects(pattern='*', limit=10)

        current_project = self.current_project
        if self.studio_project_service.is_project(current_project):
            print(f'--- KKSUBS (working on \"{self.current_project}\") ---')
        else:
            self._unassign()
            print('--- KKSUBS (no project assigned) ---')

    def compose(self, incremental_update:bool=None):
        self.subtitle_project_service.validate()
        self.subtitle_project_service.add_subtitles(allow_incremental_updating=incremental_update, update_drafts=True)

    def activate(self):
        # continuously compose
        def sync_func():
            self.sync(compose=False)
        self.project_watcher.pass_sync(sync_func)
        self.project_watcher.watch()

        # self.subtitle_project_service.validate()
        # self.subtitle_watcher.load_watch_arguments(allow_incremental_updating=True, allow_multiprocessing=True)
        # self.subtitle_watcher.watch()

    def clear(self):
        # clear outputs and metadata
        self.subtitle_project_service.clear_subtitles(force=True)

    # 'librarian'-related commands.

    def _unassign(self):
        self.current_project = None
        self.subtitle_project_service.delete_project()

    def _pull_captures(self):
        # just sync captures (library and kksub project)
        capture_path = self.studio_project_service.to_project_capture_path(self.current_project)
        self.file_service.sync_unidirectional(capture_path, self.subtitle_project_service.images_dir)

    def _pull_to_subtitle_project(self):
        # pull archived subtitle project (if exists) to workspace.
        project_name = self.current_project
        if self.studio_project_service.is_project(project_name):
            # pull contents of the project over.
            studio_project_path = self.studio_project_service.to_project_path(project_name)
            kksubs_project_path = os.path.join(studio_project_path, 'kksubs-project')
            if os.path.exists(kksubs_project_path):
                self.file_service.sync_unidirectional(
                    kksubs_project_path, 
                    self.workspace, 
                    filename_filter=['drafts', 'styles.yml', 'styles.yaml', 'output']
                )
        else:
            raise InvalidProjectException(project_name)
        self._pull_captures()

    def _assign(self, project_name:str):
        self.current_project = project_name

    def _get_project_from_history(self, project_name):
        previous_projects = self.list_project_history
        if previous_projects is not None:
            if project_name.isdigit() and int(project_name) < len(previous_projects):
                project_name = previous_projects[int(project_name)]
        return project_name
    
    def get_output_directory(self):
        return self.subtitle_project_service.get_output_directory()

    def checkout(self, project_name:str, new_branch:bool=False):

        if new_branch:
            # for creating new branch.
            if self.current_project is not None:
                parent_dir = os.path.dirname(self.current_project)
                project_name = os.path.join(parent_dir, project_name)
                self.create(project_name)
        
        else:
            project_name = self._get_project_from_history(project_name)
            project_list = self.studio_project_service.list_projects(project_name)
            # if existing branch, search for eligible branches.
            if len(project_list) == 0:
                raise InvalidProjectException(project_name)
            if len(project_list) == 1:
                project_name = project_list[0]
            elif len(project_list) > 1:
                project_name = self.project_view.select_project_from_list(self.current_project, project_list)

            confirm = self.project_view.confirm_project_checkout(self.current_project, project_name)
            if not confirm:
                return
            if project_name == self.current_project:
                print(f'Current workspace is already assigned to {project_name}.')
                return

            if self.current_project is not None and self.studio_project_service.is_project(self.current_project):
                self.sync()
            
            self._unassign()
            self._assign(project_name)
            self._pull_to_subtitle_project()
            self.subtitle_project_service.create()
            self.sync()

    def create(self, project_name:str):            
        self.studio_project_service.create_project(project_name)
        self._assign(project_name)
        capture_path = self.studio_project_service.to_project_capture_path(project_name)
        self.file_service.sync_unidirectional(capture_path, self.subtitle_project_service.images_dir)
        self.subtitle_project_service.create()
        self.sync()
        self.compose()

    def list_projects(self, pattern:str, limit:Optional[int]=None):
        logger.info(f"Listing projects with pattern {pattern}.")
        projects = self.studio_project_service.list_projects(pattern=pattern)
        num_projects = len(projects)

        if limit is None:
            projects = projects[:]
        elif isinstance(limit, int):
            projects = projects[:limit]
        else:
            raise TypeError(type(limit))
        
        projects.sort()
        if not projects:
            print("No projects found in library.")
            return
        
        @spacing
        def display():
            print('List of projects:\n')
            for i, project in enumerate(projects):
                print(f"[{i}] {project}")
            if limit is not None and limit < num_projects:
                print('   ...')
        display()
        self.list_project_history = projects

    def delete(self, project_name:str, safe:bool=True):
        project_name = self._get_project_from_history(project_name)
        self.studio_project_service.delete_project(project_name, safe=safe)
        if project_name == self.current_project:
            self._unassign()
            self.subtitle_project_service.delete_project()

    def _sync_studio(self):
        # just sync studio (game and library)
        previous_state = self.studio_sync_state
        new_sync_state = self.studio_project_service.sync_studio_project(self.current_project, previous_state=previous_state, last_sync_time=self.last_sync_time)
        self.studio_sync_state = new_sync_state

    def _sync_workspace(self):
        # sync workspace into library (no need to sync captures)
        previous_state = self.subtitle_sync_state
        new_sync_state = self.studio_project_service.sync_subtitle_project(self.current_project, previous_state=previous_state, last_sync_time=self.last_sync_time)
        self.subtitle_sync_state = new_sync_state

    def sync(self, compose:bool=True):
        if self.current_project is None:
            logger.error(f'No assigned project to sync with.')
            return
        self._sync_studio()
        self._sync_workspace()
        self._pull_captures()
        if compose:
            self.compose()

    def open_studio(self):
        studio_exe_path = os.path.join(self.game_directory, 'CharaStudio.exe')
        print(f'Launching Studio; please wait...')
        subprocess.Popen(studio_exe_path)
        return

    def open_game(self):
        game_exe_path = os.path.join(self.game_directory, 'Koikatsu Party.exe')
        print(f'Launching Koikatsu Party; please wait...')
        subprocess.Popen(game_exe_path)
        return
    
    def open_output_folders(self, drafts:str=None):
        output_dir = self.get_output_directory()
        if drafts is not None and not drafts:
            for draft in drafts:
                draft_folder = os.path.join(output_dir, draft)
                if os.path.exists(draft_folder):
                    os.startfile(draft_folder)
                else:
                    raise FileNotFoundError(draft_folder)
                return
        
        folders = os.listdir(output_dir)
        for folder in folders:
            folder = os.path.join(output_dir, folder)
            os.startfile(folder)

    def close(self):
        # persist changes to metadata
        self._write_config()
        self._write_data()
        logger.info('Closing project controller...')
