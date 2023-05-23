

from kksubs.service.studio_project import StudioProjectService
from kksubs.service.sub_project import SubtitleProjectService
from kksubs.watcher.subtitle import SubtitleWatcher


class ProjectWatcher(SubtitleWatcher):
    
    def __init__(self, subtitle_project_service: SubtitleProjectService, studio_project_service: StudioProjectService):
        super().__init__(subtitle_project_service)
        print(studio_project_service.to_game_capture_path())
        self.watch_files([
            studio_project_service.to_game_capture_path()
        ])

        self.sync_func = lambda:None

    def pass_sync(self, sync_func:callable):
        self.sync_func = sync_func

    def event_trigger_action(self):
        self.sync_func()
        return super().event_trigger_action()