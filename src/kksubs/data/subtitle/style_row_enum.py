from enum import Enum
from typing import List

from kksubs.data.subtitle.style import *

grid4_complete:List[Style] = list()
for i in range(4):
    for j in range(4):
        grid4_complete.append(Style(style_id=f"{i}{j}", box_data=BoxData(grid4=[i, j])))

grid10_complete:List[Style] = list()
for i in range(10):
    for j in range(10):
        grid10_complete.append(Style(style_id=f"{i}{j}", box_data=BoxData(grid10=[i, j])))

# list of rows
class STYLE_ROW_ENUM(Enum):

    id = StyleRow()
    grid4_complete = StyleRow(styles=grid4_complete)
    grid10_complete = StyleRow(styles=grid10_complete)

    @classmethod
    def get(cls, row_name) -> StyleRow:
        for r_enum in cls:
            if row_name == r_enum.name:
                return r_enum.value
        return None