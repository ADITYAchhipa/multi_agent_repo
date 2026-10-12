import re
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True, frozen=True)


def timestamp(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", value):
        raise ValueError("expected UTC millisecond timestamp")
    datetime.fromisoformat(value)
    return value


def decimal_string(value: str) -> str:
    if not re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?", value):
        raise ValueError("expected normalized nonnegative decimal string")
    return value


Id = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")]
Text = Annotated[str, Field(min_length=1, max_length=2000)]
Timestamp = Annotated[str, AfterValidator(timestamp)]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Quantity = Annotated[str, Field(max_length=80), AfterValidator(decimal_string)]
SafeInt = Annotated[int, Field(ge=0, le=9007199254740991)]
