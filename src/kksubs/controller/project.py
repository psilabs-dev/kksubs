import logging
import os
from typing import Optional
import yaml
from kksubs.exceptions import InvalidProjectException
from kksubs.service.file import FileService
from kksubs.service.studio_project import StudioProjectService

from kksubs.service.sub_project import SubtitleProjectService
from kksubs.watcher.subtitle import SubtitleWatcher
from kksubs.utils.coalesce import coalesce
from kksubs.utils.file import *
from kksubs.utils.decorators import *

METADATA_FILE = 'kksubs.yaml'
GAME_DIRECTORY_KEY = 'game-directory'
LIBRARY_KEY = 'library-directory'
WORKSPACE_KEY = 'workspace-directory'
CURRENT_PROJECT_KEY = 'current-project'

SUBTITLE_SYNC_STATE_KEY = 'subtitle-sync-state'
STUDIO_SYNC_STATE_KEY = 'studio-sync-state'

logger = logging.getLogger(__name__)

class ProjectController:

    def __init__(
            self,
            game_directory:str=None,
            library:str=None,
            metadata_file_path:str=None,
            workspace:str=None,

            subtitle_project_service:SubtitleProjectService=None,
            studio_project_service:StudioProjectService=None,
            current_project:str=None,
    ):
        
        logger.info('Creating project controller...')
        self.metadata_file_path = metadata_file_path
        self.game_directory = game_directory
        self.library = library
        self.workspace = workspace
        self.current_project = current_project

        self.subtitle_sync_state = None
        self.studio_sync_state = None

        self.subtitle_project_service = subtitle_project_service
        self.studio_project_service = studio_project_service

    def _get_metadata_path(self, metadata_file_path:str=None):
        return coalesce(metadata_file_path, self.metadata_file_path)

    def _read_metadata(self, metadata_file_path:str=None) -> Dict:
        metadata_file_path = self._get_metadata_path(metadata_file_path=metadata_file_path)
        if not os.path.exists(metadata_file_path):
            return dict()
        with open(metadata_file_path, 'r') as reader:
            return yaml.safe_load(reader)
        
    def _write_metadata(self, metadata_file_path:str=None):
        if self.workspace is None:
            return
        data = {
            GAME_DIRECTORY_KEY: self.game_directory,
            LIBRARY_KEY: self.library,
            WORKSPACE_KEY: self.workspace,
            CURRENT_PROJECT_KEY: self.current_project,

            SUBTITLE_SYNC_STATE_KEY: self.subtitle_sync_state,
            STUDIO_SYNC_STATE_KEY: self.studio_sync_state,
        }
        metadata_file_path = self._get_metadata_path(metadata_file_path=metadata_file_path)
        with open(metadata_file_path, 'w') as writer:
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
        metadata_path = os.path.join(metadata_directory, METADATA_FILE)
        metadata = self._read_metadata(metadata_path)

        metadata[GAME_DIRECTORY_KEY] = coalesce(game_directory, metadata.get(GAME_DIRECTORY_KEY))
        metadata[LIBRARY_KEY] = coalesce(library, metadata.get(LIBRARY_KEY))
        metadata[WORKSPACE_KEY] = coalesce(workspace, metadata.get(WORKSPACE_KEY))
        metadata[CURRENT_PROJECT_KEY] = metadata.get(CURRENT_PROJECT_KEY)
        metadata[SUBTITLE_SYNC_STATE_KEY] = metadata.get(SUBTITLE_SYNC_STATE_KEY)
        metadata[STUDIO_SYNC_STATE_KEY] = metadata.get(STUDIO_SYNC_STATE_KEY)

        for key in [GAME_DIRECTORY_KEY, LIBRARY_KEY, WORKSPACE_KEY]:
            path = metadata.get(key)
            if path is None:
                raise NotImplementedError(key)
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            metadata[key] = os.path.realpath(path)
        
        self.metadata_file_path = metadata_path
        self.game_directory = metadata.get(GAME_DIRECTORY_KEY)
        self.library = metadata.get(LIBRARY_KEY)
        self.workspace = metadata.get(WORKSPACE_KEY)
        self.current_project = metadata.get(CURRENT_PROJECT_KEY)

        self.subtitle_sync_state = metadata.get(SUBTITLE_SYNC_STATE_KEY)
        self.studio_sync_state = metadata.get(STUDIO_SYNC_STATE_KEY)

        self.subtitle_project_service = SubtitleProjectService(project_directory=workspace)
        self.studio_project_service = StudioProjectService(self.library, self.game_directory, self.workspace)
        self.file_service = FileService()
        self.subtitle_watcher = SubtitleWatcher(self.subtitle_project_service)

    @spacing
    def info(self):
        print(f'--- KKSUBS (working on \"{self.current_project}\") ---\n')
        print(f'Game:                {self.game_directory}')
        print(f'Library:             {self.library}')
        print(f'Workspace:           {self.workspace}')
        self.list_projects(pattern='*', limit=10)

    def activate(self):
        # continuously compose
        self.subtitle_project_service.validate()
        self.subtitle_watcher.watch(
            allow_incremental_updating=True,
            allow_multiprocessing=True
        )

    def clear(self):
        # clear outputs and metadata
        self.subtitle_project_service.clear_subtitles(force=True)

    # 'librarian'-related commands.

    def _unassign(self):
        self.current_project = None
        self.subtitle_project_service.delete_project()

    def _pull_captures(self):
        # just sync captures (library and kksub project)
        capture_path = self.studio_project_service.to_capture_path(self.current_project)
        self.file_service.sync_unidirectional(capture_path, self.subtitle_project_service.images_dir)

    def _pull_to_subtitle_project(self):
        # pull archived subtitle project (if exists) to workspace.
        project_name = self.current_project
        if self.studio_project_service.is_project(project_name):
            # pull contents of the project over.
            studio_project_path = self.studio_project_service.to_project_path(project_name)
            kksubs_project_path = os.path.join(studio_project_path, 'kksubs-project')
            if os.path.exists(kksubs_project_path):
                self.file_service.sync_unidirectional(kksubs_project_path, self.workspace)
        else:
            raise InvalidProjectException(project_name)
        self._pull_captures()

    def _assign(self, project_name:str):
        self.current_project = project_name

    def checkout(self, project_name:str):
        self._unassign()
        self._assign(project_name)
        self._pull_to_subtitle_project()
        self._pull_captures()

    def create(self, project_name:str):
        self.studio_project_service.create_project(project_name)
        self._assign(project_name)
        capture_path = self.studio_project_service.to_capture_path(project_name)
        self.file_service.sync_unidirectional(capture_path, self.subtitle_project_service.images_dir)
        self.subtitle_project_service.create()
        self.sync()

    def list_projects(self, pattern:str, limit:Optional[int]=None):
        logger.info(f"Listing projects with pattern {pattern}.")
        projects = self.studio_project_service.list_projects(pattern=pattern)
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
            for project in projects:
                print(f"- {project}")
        display()

    def delete(self, project_name:str):
        self.studio_project_service.delete_project(project_name, safe=False)
        if project_name == self.current_project:
            self._unassign()
            self.subtitle_project_service.delete_project()

    def _sync_studio(self):
        # just sync studio (game and library)
        previous_state = self.studio_sync_state
        new_sync_state = self.studio_project_service.sync_studio_project(self.current_project, previous_state=previous_state)
        self.studio_sync_state = new_sync_state

    def _sync_workspace(self):
        # sync workspace into library (no need to sync captures)
        previous_state = self.subtitle_sync_state
        new_sync_state = self.studio_project_service.sync_subtitle_project(self.current_project, previous_state=previous_state)
        self.subtitle_sync_state = new_sync_state
        self._pull_captures()

    def sync(self):
        if self.current_project is None:
            logger.error(f'No assigned project to sync with.')
            return
        self._sync_studio()
        self._sync_workspace()
        self._pull_captures()

    def close(self):
        # persist changes to metadata
        self._write_metadata()
        logger.info('Closing project controller...')
