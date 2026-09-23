from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field

class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

ID = Annotated[str, Field(min_length=1)]
Level = Annotated[int, Field(ge=0, le=5)]
Grade = Literal["Junior", "Middle", "Senior", "Lead"]
GRADES = ("Junior", "Middle", "Senior", "Lead")
