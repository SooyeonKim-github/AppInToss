from pydantic import BaseModel
from typing import Literal

Direction = Literal['UP','DOWN']

class AnswerRequest(BaseModel):
    answer: Direction
    userId: str
