from enum import Enum


class UpdateReason(Enum):
    """Причины обновления работы"""

    NEW = "new"
    AUTHOR = "author"
    CHAPTER = "chapter"
