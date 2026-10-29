from enum import Enum

from pydantic import BaseModel


class Mode(str, Enum):
    NATIVE = "native"
    NON_NATIVE = "non_native"


MODE_LABELS: dict[Mode, str] = {
    Mode.NATIVE: "Native speaker",
    Mode.NON_NATIVE: "Non-native speaker",
}


class ModeOption(BaseModel):
    id: Mode
    label: str
