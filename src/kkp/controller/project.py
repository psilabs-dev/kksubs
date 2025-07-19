import logging
import os
from pathlib import Path
from typing import List, Optional
import yaml
from common.exceptions import InvalidProjectException
import subprocess
from packaging import version

from common.import_utils import get_kksubs_version
from kkp.data.config import KKPSettings
from kksubs.service.file import FileService
from kkp.service.studio_project import StudioProjectService

from kksubs.service.sub_project import SubtitleProjectService
from kkp.view.project import ProjectView
from kkp.watcher.project import ProjectWatcher
from common.utils.coalesce import coalesce
from common.utils.file import *
from common.utils.decorators import *
from common.utils.application import *
from common.exceptions import NotConfiguredException

# config information
CONFIG_FILE_NAME = 'config.yaml'
GAME_DIRECTORY_KEY = 'game-directory'
LIBRARY_KEY = 'library-directory'
WORKSPACE_KEY = 'workspace-directory'
SETTINGS_KEY = 'settings'

# data information
DATA_FILE_NAME = 'data.yaml'
CURRENT_PROJECT_KEY = 'current-project'
SYNC_TIME_KEY = 'last-synced-time'
SUBTITLE_SYNC_STATE_KEY = 'subtitle-sync-state'
STUDIO_SYNC_STATE_KEY = 'studio-sync-state'
QUICK_ACCESS_KEY = 'quick-access'
LIST_PROJECT_HISTORY_KEY = 'list-project-history'
RECENT_PROJECTS_KEY = 'recent-projects'
VERSION_KEY = 'version'

logger = logging.getLogger(__name__)

def format_project_name(project_name:str):
    if project_name is None:
        return project_name
    return project_name.replace('/', os.path.sep)

class ProjectController:

    def __init__(
            self,
            game_directory:Optional[str | Path]=None,
            library:Optional[str | Path]=None,
            config_file_path:Optional[str | Path]=None,
            workspace:Optional[str | Path]=None,

            data_file_path:Optional[str | Path]=None,
            subtitle_project_service:Optional[SubtitleProjectService]=None,
            studio_project_service:Optional[StudioProjectService]=None,
            project_view:Optional[ProjectView]=None,

            current_project:Optional[str]=None,
    ):
        
        logger.info('Creating project controller...')

        if game_directory:
            if isinstance(game_directory, str):
                _game_directory = Path(game_directory)
            else:
                _game_directory = game_directory
        else:
            _game_directory = None
        if library:
            if isinstance(library, str):
                _library = Path(library)
            else:
                _library = library
        else:
            _library = None
        if config_file_path:
            if isinstance(config_file_path, str):
                _config_file_path = Path(config_file_path)
            else:
                _config_file_path = config_file_path
        else:
            _config_file_path = None
        if workspace:
            if isinstance(workspace, str):
                _workspace = Path(workspace)
            else:
                _workspace = workspace
        else:
            _workspace = None
        if data_file_path:
            if isinstance(data_file_path, str):
                _data_file_path = Path(data_file_path)
            else:
                _data_file_path = data_file_path
        else:
            _data_file_path = None

        self.config_file_path: Optional[Path] = _config_file_path
        self.game_directory: Optional[Path] = _game_directory
        self.library: Optional[Path] = _library
        self.workspace: Optional[Path] = _workspace
        self.settings:Optional[KKPSettings] = None

        self.current_project: Optional[str] = current_project

        self.data_file_path: Optional[Path] = _data_file_path
        self.subtitle_sync_state = None
        self.studio_sync_state = None
        self.last_sync_time = None

        self.subtitle_project_service = subtitle_project_service
        self.studio_project_service = studio_project_service
        # self.subtitle_watcher = None
        self.project_watcher = None
        self.project_view = project_view

        self.quick_access:Optional[List[str]] = None
        self.list_project_history:Optional[List[str]] = None
        self.list_project_limit:int = 10
        self.recent_projects:Optional[List[str]] = None
        self.recent_projects_limit:int = 5

        self.export_map = {
            'UserData/cap': 'cap',
            'kksubs-project/output': 'output',
        }
        self.merge_targets = {
            str(Path('UserData') / 'bg'),
            # str(Path('UserData') / 'cap'),
            str(Path('UserData') / 'cardframe'),
            str(Path('UserData') / 'chara'),
            # str(Path('UserData') / 'config'),
            str(Path('UserData') / 'coordinate'),
            # str(Path('UserData') / 'LauncherEN'),
            str(Path('UserData') / 'MaterialEditor'),
            str(Path('UserData') / 'Overlays'),
            # str(Path('UserData') / 'pattern'),
            # str(Path('UserData') / 'pattern_thumb'),
            # str(Path('UserData') / 'save'),
            str(Path('UserData') / 'studio'),
        }

    def _get_config_file_path(self, config_path:Optional[str | Path]=None) -> Optional[Path]:
        result = coalesce(config_path, self.config_file_path)
        if isinstance(result, Path):
            return result
        if isinstance(result, str):
            return Path(result)
        if result is None:
            return None
        raise TypeError(f"Invalid config path: {result}")

    def _get_data_file_path(self, data_file_path:Optional[str | Path]=None) -> Optional[Path]:
        result = coalesce(data_file_path, self.data_file_path)
        if isinstance(result, Path):
            return result
        if isinstance(result, str):
            return Path(result)
        if result is None:
            return None
        raise TypeError(f"Invalid data file path: {result}")

    def _read_config(self, config_file_path:Optional[str | Path]=None) -> Dict:
        config_file_path = self._get_config_file_path(config_path=config_file_path)
        if config_file_path is None or not config_file_path.exists():
            return dict()
        with open(config_file_path, 'r', encoding='utf-8') as reader:
            result = yaml.safe_load(reader)
            if result is None:
                return dict()
            return result
        
    def _write_config(self, config_path:Optional[str | Path]=None):
        if self.workspace is None:
            return
        if self.settings:
            settings = self.settings.serialize()
        else:
            settings = None
        config = {
            GAME_DIRECTORY_KEY: self.game_directory,
            LIBRARY_KEY: self.library,
            WORKSPACE_KEY: self.workspace,
            SETTINGS_KEY: settings,
        }
        config_path = self._get_config_file_path(config_path=config_path)
        if config_path:
            with open(config_path, 'w') as writer:
                return yaml.safe_dump(config, writer)
        else:
            raise ValueError("Config path is None")

    def _read_data(self, data_path:Optional[str | Path]=None) -> Dict:
        data_file_path = self._get_data_file_path(data_file_path=data_path)
        if data_file_path:
            if data_file_path.exists():
                with open(data_file_path, 'r', encoding='utf-8') as reader:
                    result = yaml.safe_load(reader)
                    if result is None:
                        return dict()
                    return result
        return dict()

    def _write_data(self, data_path:Optional[str | Path]=None):
        if self.workspace is None:
            return
        data = {
            CURRENT_PROJECT_KEY: self.current_project,
            SUBTITLE_SYNC_STATE_KEY: self.subtitle_sync_state,
            STUDIO_SYNC_STATE_KEY: self.studio_sync_state,
            QUICK_ACCESS_KEY: self.quick_access,
            LIST_PROJECT_HISTORY_KEY: self.list_project_history,
            RECENT_PROJECTS_KEY: self.recent_projects,
            VERSION_KEY: get_kksubs_version(),
        }
        data_path = self._get_data_file_path(data_file_path=data_path)
        if data_path:
            with open(data_path, 'w', encoding='utf-8') as writer:
                return yaml.safe_dump(data, writer)
        else:
            raise ValueError("Data path is None")

    def configure_v2(
            self, 
    ):
        # configure_controller.

        # application data is now located in the dotfolder ~/.kksubs.
        if (config_path := get_config_path()) and config_path.exists() and (application_root := get_application_root()) and application_root.exists():
            # read from config
            with open(config_path, "r", encoding="utf-8") as reader:
                application_config = yaml.safe_load(reader)
                library = application_config[LIBRARY_KEY]
                game_directory = application_config[GAME_DIRECTORY_KEY]
                workspace = application_config[WORKSPACE_KEY]
            metadata_directory = application_root / 'metadata'
            metadata_directory.mkdir(exist_ok=True)
        else:
            raise NotConfiguredException()
        
        # retrieve metadata.
        config_path = get_config_path()
        data_path = metadata_directory / DATA_FILE_NAME

        config_info = self._read_config(config_path)
        data_info = self._read_data(data_path)

        config_info[GAME_DIRECTORY_KEY] = coalesce(game_directory, config_info.get(GAME_DIRECTORY_KEY))
        config_info[LIBRARY_KEY] = coalesce(library, config_info.get(LIBRARY_KEY))
        config_info[WORKSPACE_KEY] = coalesce(workspace, config_info.get(WORKSPACE_KEY))
        config_info[SETTINGS_KEY] = config_info.get(SETTINGS_KEY)

        data_info[CURRENT_PROJECT_KEY] = data_info.get(CURRENT_PROJECT_KEY)
        data_info[SUBTITLE_SYNC_STATE_KEY] = data_info.get(SUBTITLE_SYNC_STATE_KEY)
        data_info[STUDIO_SYNC_STATE_KEY] = data_info.get(STUDIO_SYNC_STATE_KEY)
        data_info[SYNC_TIME_KEY] = data_info.get(SYNC_TIME_KEY)
        data_info[QUICK_ACCESS_KEY] = data_info.get(QUICK_ACCESS_KEY)
        data_info[LIST_PROJECT_HISTORY_KEY] = data_info.get(LIST_PROJECT_HISTORY_KEY)
        data_info[RECENT_PROJECTS_KEY] = data_info.get(RECENT_PROJECTS_KEY)
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

                    for data_key in [
                        CURRENT_PROJECT_KEY, 
                        SUBTITLE_SYNC_STATE_KEY, 
                        STUDIO_SYNC_STATE_KEY, 
                        SYNC_TIME_KEY, 
                        QUICK_ACCESS_KEY,
                        LIST_PROJECT_HISTORY_KEY,
                        RECENT_PROJECTS_KEY,
                    ]:
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
        self.settings = KKPSettings.deserialize(config_info.get(SETTINGS_KEY))

        # # load settings
        # if self.settings.log is not None:
        #     level = self.settings.log.get_log_level()
        #     if level is None:
        #         pass
        #     else:
        #         logger.setLevel(level=level)

        self.current_project = data_info.get(CURRENT_PROJECT_KEY)
        self.subtitle_sync_state = data_info.get(SUBTITLE_SYNC_STATE_KEY)
        self.studio_sync_state = data_info.get(STUDIO_SYNC_STATE_KEY)
        self.last_sync_time = data_info.get(SYNC_TIME_KEY)
        self.quick_access = data_info.get(QUICK_ACCESS_KEY)
        self.list_project_history = data_info.get(LIST_PROJECT_HISTORY_KEY)
        self.recent_projects = data_info.get(RECENT_PROJECTS_KEY)

        self.subtitle_project_service = SubtitleProjectService(workspace_directory=self.workspace)
        self.studio_project_service = StudioProjectService(self.library, self.game_directory, self.workspace)
        self.project_view = ProjectView()

        self.file_service = FileService()
        # self.subtitle_watcher = SubtitleWatcher(self.subtitle_project_service)
        self.project_watcher = ProjectWatcher(self.subtitle_project_service, self.studio_project_service)
        self.project_watcher.load_watch_arguments(
            allow_incremental_updating=True,
            allow_multiprocessing=True,
        )

    @deprecated
    def configure(
            self, 
            metadata_directory:Optional[str], 
            game_directory:Optional[str], 
            library:Optional[str], 
            workspace:Optional[str]
    ):
        # configures controller.
        # retrieve metadata.
        if metadata_directory is None:
            raise ValueError("Metadata directory is None")

        config_path = Path(metadata_directory) / CONFIG_FILE_NAME
        data_path = Path(metadata_directory) / DATA_FILE_NAME

        config_info = self._read_config(config_path)
        data_info = self._read_data(data_path)

        config_info[GAME_DIRECTORY_KEY] = coalesce(game_directory, config_info.get(GAME_DIRECTORY_KEY))
        config_info[LIBRARY_KEY] = coalesce(library, config_info.get(LIBRARY_KEY))
        config_info[WORKSPACE_KEY] = coalesce(workspace, config_info.get(WORKSPACE_KEY))
        config_info[SETTINGS_KEY] = config_info.get(SETTINGS_KEY)

        data_info[CURRENT_PROJECT_KEY] = data_info.get(CURRENT_PROJECT_KEY)
        data_info[SUBTITLE_SYNC_STATE_KEY] = data_info.get(SUBTITLE_SYNC_STATE_KEY)
        data_info[STUDIO_SYNC_STATE_KEY] = data_info.get(STUDIO_SYNC_STATE_KEY)
        data_info[SYNC_TIME_KEY] = data_info.get(SYNC_TIME_KEY)
        data_info[QUICK_ACCESS_KEY] = data_info.get(QUICK_ACCESS_KEY)
        data_info[LIST_PROJECT_HISTORY_KEY] = data_info.get(LIST_PROJECT_HISTORY_KEY)
        data_info[RECENT_PROJECTS_KEY] = data_info.get(RECENT_PROJECTS_KEY)
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

                    for data_key in [
                        CURRENT_PROJECT_KEY, 
                        SUBTITLE_SYNC_STATE_KEY, 
                        STUDIO_SYNC_STATE_KEY, 
                        SYNC_TIME_KEY, 
                        QUICK_ACCESS_KEY,
                        LIST_PROJECT_HISTORY_KEY,
                        RECENT_PROJECTS_KEY,
                    ]:
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
        self.settings = KKPSettings.deserialize(config_info.get(SETTINGS_KEY))

        # load settings
        if self.settings.log is not None:
            level = self.settings.log.get_log_level()
            if level is None:
                pass
            else:
                logger.setLevel(level=level)

        self.current_project = data_info.get(CURRENT_PROJECT_KEY)
        self.subtitle_sync_state = data_info.get(SUBTITLE_SYNC_STATE_KEY)
        self.studio_sync_state = data_info.get(STUDIO_SYNC_STATE_KEY)
        self.last_sync_time = data_info.get(SYNC_TIME_KEY)
        self.quick_access = data_info.get(QUICK_ACCESS_KEY)
        self.list_project_history = data_info.get(LIST_PROJECT_HISTORY_KEY)
        self.recent_projects = data_info.get(RECENT_PROJECTS_KEY)

        self.subtitle_project_service = SubtitleProjectService(workspace_directory=self.workspace)
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
    def info(self, show_recent_projects:bool=False):

        print(f'Game:                {self.game_directory}')
        print(f'Library:             {self.library}')
        print(f'Workspace:           {self.workspace}')

        projects = self.list_projects(pattern='*', limit=self.list_project_limit, update_quick_access=False)
        if show_recent_projects:
            recent_projects = self.list_recent_projects(limit=self.recent_projects_limit, start_index=len(projects), update_quick_access=False)
        else:
            recent_projects = list()
        try:
            self.set_quick_access(projects+recent_projects)
        except:
            raise Exception((projects, recent_projects))

        current_project = self.current_project
        if current_project is not None and self.studio_project_service.is_project(current_project):
            print(f'---- KKSUBS v-{get_kksubs_version()} (working on \"{self.current_project}\") ----')
        else:
            self._unassign(delete_project=False)
            print(f'---- KKSUBS v-{get_kksubs_version()} (no project assigned) ----')

    def compose(self, incremental_update:bool=True):
        if self.subtitle_project_service is None:
            raise ValueError("Subtitle project service is None")
        self.subtitle_project_service.validate()
        self.subtitle_project_service.add_subtitles(allow_incremental_updating=incremental_update, update_drafts=True)

    def activate(self):
        # continuously compose
        def sync_func():
            self.sync(compose=False)
        if self.project_watcher is None:
            raise ValueError("Project watcher is None")
        self.project_watcher.pass_sync(sync_func)
        self.project_watcher.watch()

    def clear(self):
        # clear outputs and metadata
        if self.subtitle_project_service is None:
            raise ValueError("Subtitle project service is None")
        self.subtitle_project_service.clear_subtitles(force=True)

    def _unassign(self, delete_project:bool=True):
        self.current_project = None
        if delete_project:
            if self.subtitle_project_service is None:
                raise ValueError("Subtitle project service is None")
            self.subtitle_project_service.delete_project()

    def _clean_userdata_directory(self):
        """
        Clean up the UserData directory in the game directory to prevent 
        directory structure conflicts during checkout.
        """
        if self.game_directory is None:
            raise ValueError("Game directory is None")
        
        userdata_path = os.path.join(self.game_directory, 'UserData')
        if os.path.exists(userdata_path):
            import shutil
            logger.info(f"Cleaning up UserData directory: {userdata_path}")
            shutil.rmtree(userdata_path)
            logger.info("UserData directory cleaned up successfully")

    def _pull_captures(self):
        # just sync captures (library and kksub project)
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        if self.subtitle_project_service is None:
            raise ValueError("Subtitle project service is None")
        if self.current_project is None:
            raise ValueError("Current project is None")
        capture_path = self.studio_project_service.to_project_capture_path(self.current_project)
        self.file_service.sync_unidirectional(capture_path, self.subtitle_project_service.images_dir)

    def _pull_to_subtitle_project(self):
        # pull archived subtitle project (if exists) to workspace.
        project_name = self.current_project
        if project_name is None:
            raise ValueError("Current project is None")
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
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

    def _update_recent_projects(self, project_name:str):
        # updates recent project list with project name.
        project_name = format_project_name(project_name)
        recent_projects = self.get_recent_projects()
        if recent_projects is None:
            recent_projects = list()
        if project_name in recent_projects:
            recent_projects.remove(project_name)
        recent_projects.insert(0, project_name)
        self.set_recent_projects(recent_projects)

    def _remove_from_recent_projects(self, project_name):
        if project_name in self.get_recent_projects():
            self.get_recent_projects().remove(project_name)

    def _assign(self, project_name:str):
        self.current_project = project_name
        self._update_recent_projects(project_name)

    def _get_project_from_quick_access(self, project_name:str):
        # check if project refers to a quick access integer.
        previous_projects = self.quick_access
        if previous_projects is not None:
            if project_name.isdigit() and int(project_name) < len(previous_projects):
                project_name = previous_projects[int(project_name)]
        return project_name
    
    def get_output_directory(self) -> str:
        if self.subtitle_project_service is None:
            raise ValueError("Subtitle project service is None")
        return self.subtitle_project_service.get_output_directory()

    def checkout(self, project_name:str, new_branch:bool=False, compose:bool=True) -> bool:
        """
        Checkout existing or new archive. Return True if successful checkout, else False.
        """
        if self.current_project is None:
            raise ValueError("Current project is None")
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        if self.project_view is None:
            raise ValueError("Project view is None")
        if self.subtitle_project_service is None:
            raise ValueError("Subtitle project service is None")


        project_name = format_project_name(project_name)
        if new_branch:
            # for creating new branch.
            if self.current_project is None:
                print('Cannot checkout from empty project. Please create a project first.')
                return False
            
            parent_dir = os.path.dirname(self.current_project)
            project_name = os.path.join(parent_dir, project_name)
            confirm = self.project_view.confirm_project_checkout(self.current_project, project_name)
            if not confirm:
                print('Checkout cancelled.')
                return False
            
            # save changes before creating new branch.
            print(f'Saving project {self.current_project}.')
            self.sync(compose=False)
            print(f'Creating new project {project_name}.')
            self._create(project_name, compose=True)
            print(f'Successfully created {project_name}')
        
        else:
            if self.current_project is None:
                raise ValueError("Current project is None")
            project_name = self._get_project_from_quick_access(project_name)
            project_list = self.studio_project_service.list_projects(project_name)
            # if existing branch, search for eligible branches.
            if len(project_list) == 0:
                print(f"Cannot find existing project that matches pattern \"{project_name}\"; checkout cancelled.")
                return False
            if len(project_list) == 1:
                project_name = project_list[0]
            elif len(project_list) > 1:
                project_name = self.project_view.select_project_from_list(self.current_project, project_list)
                if project_name is None:
                    print("Checkout cancelled.")
                    return False

            confirm = self.project_view.confirm_project_checkout(self.current_project, project_name)
            if not confirm:
                print("Checkout cancelled.")
                return False
            if project_name == format_project_name(self.current_project):
                print(f'Current workspace is already assigned to {project_name}.')
                return False

            if self.current_project is not None and self.studio_project_service.is_project(self.current_project):
                print(f'Saving project {self.current_project}.')
                self.save_current_project()
            
            print(f'Checking out {project_name}.')
            self._unassign(delete_project=True)
            self._clean_userdata_directory()
            self._assign(project_name)
            self._pull_to_subtitle_project()

            self.subtitle_project_service.clear_subtitles(force=True)
            self.subtitle_project_service.create()

            print(f'Loading project {project_name}')
            self.sync(compose=compose)
            self.studio_project_service.correct_scene_order()
            print(f'Checkout successful.')
            return True

    def _create(self, project_name:str, compose:bool=True):
        # create project.
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        if self.subtitle_project_service is None:
            raise ValueError("Subtitle project service is None")
        if self.file_service is None:
            raise ValueError("File service is None")
        self.studio_project_service.create_project(project_name)
        self._assign(project_name)
        capture_path = self.studio_project_service.to_project_capture_path(project_name)
        self.file_service.sync_unidirectional(capture_path, self.subtitle_project_service.images_dir)
        self.subtitle_project_service.create()
        self.sync(compose=False)
        if compose:
            self.compose()

    def create(self, project_name:str, compose:bool=True):
        project_name = format_project_name(project_name)
        confirm = input(f'Create project {project_name} from {self.current_project}? (Y) ') == 'Y'
        if not confirm:
            return
        
        logger.info(f'Saving project {self.current_project}')
        self.sync(compose=False)
        logger.info(f'Creating project {project_name}')
        self._create(project_name, compose=False)
        if compose:
            logger.info('Applying subtitles...')
            self.compose()

    def get_recent_projects(self) -> List[str]:
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        if self.recent_projects is None:
            return list()
        
        for recent_project in self.recent_projects:
            if not self.studio_project_service.is_project(recent_project):
                # logger.error(f'Project {recent_project} is invalid.')
                self.recent_projects.remove(recent_project)
        
        while len(self.recent_projects) > self.recent_projects_limit:
            self.recent_projects.pop()

        return self.recent_projects

    def set_recent_projects(self, recent_projects:List[str]):
        self.recent_projects = recent_projects

    def set_quick_access(self, project_list:List[str]):
        self.quick_access = project_list

    def list_recent_projects(self, limit:Optional[int]=None, start_index:Optional[int]=None, update_quick_access:bool=True) -> List[str]:
        logger.info(f'Listing recent projects.')
        if start_index is None:
            start_index = 0

        recent_projects = self.get_recent_projects()
        if not recent_projects:
            print(f'No recent projects found.')
            return list()
        num_projects = len(recent_projects)
        
        if limit is None:
            pass
        elif isinstance(limit, int):
            recent_projects = recent_projects[:limit]
        else:
            raise TypeError(type(limit))

        @spacing
        def display():
            print('Recent projects:\n')
            for i, project in enumerate(recent_projects):
                print(f"[{i+start_index}] {project}")
            if limit is not None and limit < num_projects:
                print('   ...')
        display()
        
        if update_quick_access:
            self.set_quick_access(recent_projects)

        return recent_projects

    def list_projects(self, pattern:str, limit:Optional[int]=None, start_index:Optional[int]=None, update_quick_access:bool=True, is_display=True) -> List[str]:
        """
        Display a list of Projects whose ID fit a specific regex pattern.
        """
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        logger.info(f"Listing projects with pattern {pattern}.")
        if start_index is None:
            start_index = 0
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
            logger.info("No projects found in library.")
            return list()

        @spacing
        def display_project_list(reverse=False):
            print('List of Projects:\n')

            if not reverse:
                for i, project in enumerate(projects):
                    print(f"[{i+start_index}] {project}" + ("    <-- current" if self.current_project==project else ""))
            else:
                for i, project in reversed(list(enumerate(projects))):
                    print(f"[{i+start_index}] {project}" + ("    <-- current" if self.current_project==project else ""))

            if limit is not None and limit < num_projects:
                print('   ...')

        if is_display:
            display_project_list()

        self.list_project_history = projects

        if update_quick_access:
            self.set_quick_access(projects)

        return projects

    def rename(self, new_project_id: str):
        """
        Rename current project to a new project ID, provided the new project does not lie in an existing project.
        """
        if self.current_project is None:
            raise ValueError("Current project is None")
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        is_renamed = self.studio_project_service.rename_project(self.current_project, new_project_id)
        if is_renamed:
            self.current_project = new_project_id
            print(f"Successfully renamed project {self.current_project} to {new_project_id}.")
            return
        else:
            print(f"Failed to rename project.")

    def delete(self, project_name:str, safe:bool=True):
        """
        Deletes an project from the library by project ID.
        """
        project_name = self._get_project_from_quick_access(project_name)

        # project to delete cannot be current project.
        if project_name == self.current_project:
            print("Cannot delete current project from library!")
            # self._unassign()
            # self.subtitle_project_service.delete_project()
            return
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        is_deleted = self.studio_project_service.delete_project(project_name, safe=safe)
        if is_deleted:
            print(f"Deleted project {project_name}.")

    def _sync_studio(self):
        # just sync studio (game and library)
        if self.current_project is None:
            raise ValueError("Current project is None")
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        previous_state: Optional[Dict] = self.studio_sync_state
        new_sync_state = self.studio_project_service.sync_studio_project(self.current_project, previous_state=previous_state, last_sync_time=self.last_sync_time)
        self.studio_sync_state = new_sync_state

    def _sync_workspace(self):
        # sync workspace into library (no need to sync captures)
        if self.current_project is None:
            raise ValueError("Current project is None")
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        previous_state: Optional[Dict] = self.subtitle_sync_state
        new_sync_state = self.studio_project_service.sync_subtitle_project(self.current_project, previous_state=previous_state, last_sync_time=self.last_sync_time)
        self.subtitle_sync_state = new_sync_state

    def sync(self, compose:bool=True):
        if self.current_project is None:
            logger.error(f'No assigned project to sync with.')
            return
        self._sync_studio()
        logger.info(f'Synced studio.')
        self._sync_workspace()
        logger.info(f'Synced subtitle project.')
        self._pull_captures()
        logger.info(f'Retrieved captures.')
        if compose:
            logger.info(f'Applying subtitles...')
            self.compose(incremental_update=True)
            logger.info(f'Applied subtitles.')

    def save_current_project(self):
        self.sync(compose=True)

    def _find_executable(self, base_name: str) -> Optional[str]:
        """Find executable with cross-platform support."""
        import platform
        
        if self.game_directory is None:
            return None
            
        # Try different executable extensions based on platform
        if platform.system() == "Windows":
            extensions = ['.exe']
        else:
            # On Linux/Mac, try no extension first, then .exe (for Wine)
            extensions = ['', '.exe']
        
        for ext in extensions:
            exe_path = os.path.join(self.game_directory, f'{base_name}{ext}')
            if os.path.exists(exe_path):
                return exe_path
        
        return None

    def open_studio(self):
        if self.game_directory is None:
            raise ValueError("Game directory is None")
        
        studio_exe_path = self._find_executable('CharaStudio')
        if studio_exe_path is None:
            raise FileNotFoundError("CharaStudio executable not found")
        
        print(f'Launching Studio; please wait...')
        subprocess.Popen(studio_exe_path)
        return

    def open_game(self):
        if self.game_directory is None:
            raise ValueError("Game directory is None")
        
        game_exe_path = self._find_executable('Koikatsu Party')
        if game_exe_path is None:
            raise FileNotFoundError("Koikatsu Party executable not found")
        
        print(f'Launching Koikatsu Party; please wait...')
        subprocess.Popen(game_exe_path)
        return
    
    def open_library_directory(self):
        if self.library is None:
            raise ValueError("Library is None")
        if not self.library.exists():
            raise FileNotFoundError(self.library)
        from common.utils.file import open_directory
        open_directory(self.library)
    
    def open_output_folders(self, drafts:Optional[str]=None):
        """
        Open the subtitled output images in file explorer.
        """
        output_dir = self.get_output_directory()
        from common.utils.file import open_directory
        
        if drafts is not None and not drafts:
            for draft in drafts:
                draft_folder = os.path.join(output_dir, draft)
                if os.path.exists(draft_folder):
                    open_directory(draft_folder)
                else:
                    raise FileNotFoundError(draft_folder)
                return
        
        folders = os.listdir(output_dir)
        for folder in folders:
            folder = os.path.join(output_dir, folder)
            open_directory(folder)

    def export_gallery(
            self, 
            destination:Optional[str]=None, 
            pattern:Optional[str]=None, 
            clean:bool=False, 
            show_destination:bool=False, 
            force:bool=False
    ):
        if self.settings is None:
            raise ValueError("Settings is None")
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        # export library outputs to destination.
        try:
            settings_destination = self.settings.export.destination
            destination = coalesce(destination, settings_destination)
        except AttributeError:
            pass
        
        if destination is None:
            raise TypeError('Destination is None.')

        if not os.path.exists(destination):
            raise FileNotFoundError(destination)
        
        destination = os.path.realpath(destination)
        if not os.path.isdir(destination):
            raise TypeError(f'Destination {destination} is not a directory.')

        if not force:
            confirm = input(f'Export output to {destination}? (Y) ') == 'Y'
            if not confirm:
                return
        
        if clean:
            shutil.rmtree(destination)
            os.makedirs(destination, exist_ok=True)

        projects = self.studio_project_service.export_gallery(destination, pattern=pattern)
        print(f'Finished exporting {len(projects)} projects.')

        if show_destination:
            from common.utils.file import open_directory
            open_directory(destination)

    def _merge_project(self, project_name:str):
        # merge project into current project.
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        if self.game_directory is None:
            raise ValueError("Game directory is None")
        if self.file_service is None:
            raise ValueError("File service is None")
        for merge_target in self.merge_targets:
            source = os.path.join(self.studio_project_service.to_project_path(project_name), merge_target)
            destination = os.path.join(self.game_directory, merge_target)
            self.file_service.transfer(source, destination)
        return

    def merge_project(self, project_name:str):
        # transfer items from project-name to current project.
        # note: if the file exists with same name, it will be overridden.
        if self.studio_project_service is None:
            raise ValueError("Studio project service is None")
        if self.project_view is None:
            raise ValueError("Project view is None")
        project_name = format_project_name(project_name)
        project_name = self._get_project_from_quick_access(project_name)
        project_names = self.studio_project_service.list_projects(pattern=project_name)
        
        if not project_names:
            print(f'No projects found.')
            return

        if len(project_names) == 1:
            project_name = project_names[0]
            confirm = input(f'Merge from {project_name} into current game? (Y) ') == 'Y'
            pass
        if len(project_names) > 1:
            project_names = self.project_view.select_projects_from_list(self.current_project, project_names)
            if not project_names:
                return
            for p in project_names:
                print(f'- {p}')
            print('You are about to merge the above projects into your current project. Files of the same name will be overridden.')
            confirm = input(f'Proceed? (Y) ') == 'Y'

        if not confirm:
            return
        
        for p in project_names:
            self._merge_project(p)
            logger.info(f'Finished merging project {p}.')
        return

    def close(self):
        # persist changes to metadata
        self._write_config()
        self._write_data()
        logger.info('Closing project controller...')