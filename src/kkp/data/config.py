from abc import ABC
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

class KKPSettings(RepresentableData):
    name = 'settings'
    
    def __init__(
            self,
            export_settings:ExportSettings=None,
    ):
        self.export = export_settings

    @classmethod
    def deserialize(self, settings_data:Dict):
        if settings_data is None:
            return KKPSettings(export_settings=ExportSettings())
        
        return KKPSettings(
            export_settings=ExportSettings.deserialize(settings_data.get(ExportSettings.name))
        )