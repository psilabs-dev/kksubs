import logging
import os
from typing import Optional
import yaml
from kksubs.controller.file import FileController

from kksubs.service.project import ProjectService
from kksubs.service.watcher import ProjectWatcher
from kksubs.utils.coalesce import coalesce

METADATA_FILE = 'kksubs.yaml'
GAME_DIRECTORY_KEY = 'game-directory'
LIBRARY_KEY = 'library-directory'
WORKSPACE_KEY = 'workspace-directory'

logger = logging.getLogger(__name__)

class ProjectController:

    def __init__(
            self,
            game_directory:str=None,
            library:str=None,
            workspace:str=None,
            project_service:ProjectService=None,
            file_controller:FileController=None,
    ):
        self.game_directory = game_directory
        self.library = library
        self.workspace = workspace
        self.project_service = project_service
        self.file_controller = file_controller

    def _get_metadata_path(self, workspace):
        return os.path.join(workspace, METADATA_FILE)

    def _read_metadata(self, workspace:Optional[str]):
        metadata_file_path = self._get_metadata_path(workspace)
        if not os.path.exists(metadata_file_path):
            return dict()
        with open(metadata_file_path, 'r') as reader:
            return yaml.safe_load(reader)
        
    def _write_metadata(self):
        if self.workspace is None:
            return
        data = {
            GAME_DIRECTORY_KEY: self.game_directory,
            LIBRARY_KEY: self.library,
            WORKSPACE_KEY: self.workspace,
        }
        metadata_file_path = self._get_metadata_path(self.workspace)
        with open(metadata_file_path, 'w') as writer:
            return yaml.safe_dump(data, writer)

    def configure(self, game_directory:Optional[str], library:Optional[str], workspace:Optional[str]):
        # configures controller.
        # retrieve metadata.
        metadata = self._read_metadata(workspace)

        metadata[GAME_DIRECTORY_KEY] = coalesce(game_directory, metadata.get(GAME_DIRECTORY_KEY))
        metadata[LIBRARY_KEY] = coalesce(library, metadata.get(LIBRARY_KEY))
        metadata[WORKSPACE_KEY] = coalesce(workspace, metadata.get(WORKSPACE_KEY))

        for key in [GAME_DIRECTORY_KEY, LIBRARY_KEY, WORKSPACE_KEY]:
            path = metadata.get(key)
            if path is None:
                raise NotImplementedError(key)
            if not os.path.exists(path):
                raise FileNotFoundError(path)
            metadata[key] = os.path.realpath(path)
        
        self.game_directory = metadata.get(GAME_DIRECTORY_KEY)
        self.library = metadata.get(LIBRARY_KEY)
        self.workspace = metadata.get(WORKSPACE_KEY)

        self.project_service = ProjectService(project_directory=workspace)
        self.project_watcher = ProjectWatcher(self.project_service)
        self.file_controller = FileController(self.game_directory, self.library, self.workspace)

    def info(self):
        # TODO: get info
        ...

    def activate(self):
        # continuously compose
        self.project_service.validate()
        self.project_watcher.watch(
            allow_incremental_updating=True,
            allow_multiprocessing=True
        )

    def clear(self):
        # clear outputs and metadata
        self.project_service.clear_subtitles(force=True)

    # 'librarian'-related commands.

    def checkout(self, project_name:str):
        # TODO: checkout project with project name
        self.file_controller.checkout(project_name)
        ...

    def create(self, project_name:str):
        # TODO: create project with project name
        self.file_controller.create(project_name)
        ...

    def list_projects(self, pattern:str):
        self.file_controller.list(pattern)
        ...

    def delete(self, project_name:str):
        # TODO: delete project with name
        self.file_controller.delete(project_name)
        ...

    def sync(self):
        # TODO: sync project with library and subtitle workspace
        self.file_controller.sync()
        ...

    def close(self):
        # persist changes to metadata
        self._write_metadata()
        logger.info('Closing project controller...')
