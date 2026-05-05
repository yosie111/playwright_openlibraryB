from dataclasses import dataclass
from typing import Optional


@dataclass()
class BookInfo:

    url: str
    year: Optional[int] = None
    activated: Optional[bool] = None