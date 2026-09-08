from typing import Literal

from pydantic import BaseModel

ViewCode = Literal["HAN_RIVER", "CITY", "PALACE", "FOREST"]


class ViewOption(BaseModel):
    code: ViewCode
    name: str
    emoji: str


class RegionResponseItem(BaseModel):
    code: str
    name: str
    cafeCount: int
