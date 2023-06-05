from abc import ABC
import logging
from typing import Dict

from common.data.representable import RepresentableData

class Settings(RepresentableData, ABC):
    name:str

    ...

class ExportSettings(Settings):
    name = 'export'

    def __init__(
            self,
            destination:str=None,
    ):
        self.destination = destination

    @classmethod
    def deserialize(self, export_settings_data):
        if export_settings_data is None:
            return ExportSettings()
        return ExportSettings(**export_settings_data)

class LogSettings(Settings):
    name = 'log'

    def __init__(
            self,
            level:str=None,
    ):
        self.level = level

    @classmethod
    def deserialize(self, log_settings_data):
        if log_settings_data is None:
            return LogSettings()
        return LogSettings(**log_settings_data)
    
    def get_log_level(self):
        if self.level is None:
            return None
        try:
            return logging.getLevelName(self.level.upper())
        except ValueError:
            return None

class KKPSettings(RepresentableData):
    name = 'settings'
    
    def __init__(
            self,
            export_settings:ExportSettings=None,
            log_settings:LogSettings=None,
    ):
        self.export = export_settings
        self.log = log_settings

    @classmethod
    def deserialize(self, settings_data:Dict):
        if settings_data is None:
            return KKPSettings(export_settings=ExportSettings())
        
        return KKPSettings(
            export_settings=ExportSettings.deserialize(settings_data.get(ExportSettings.name)),
            log_settings=LogSettings.deserialize(settings_data.get(LogSettings.name)),
        )