from dataclasses import dataclass
from typing import Optional


# @dataclass()
# class BookInfo:
#     url: str
#     year: Optional[int] = None
#     activated: Optional[bool] = None

# Bookshelf IDs as defined by Open Library
BOOKSHELF_NONE = -1
BOOKSHELF_WANT_TO_READ = 1
BOOKSHELF_CURRENTLY_READING = 2
BOOKSHELF_ALREADY_READ = 3


@dataclass()
class BookInfo:
    url: str
    year: Optional[int] = None
    # -1 = not on any shelf, 1 = Want to Read, 2 = Currently Reading, 3 = Already Read
    bookshelf_id: int = BOOKSHELF_NONE

@dataclass()
class SearchCase:
    query: str
    max_year: int
    limit: int