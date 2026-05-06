import csv
import re
from pathlib import Path
from typing import Union

from pages.models import SearchCase


def make_safe_filename(url: str) -> str:
    safe = re.sub(r'[<>:"/\\|?%*]', "_", url)
    return safe.replace("https___", "").replace("http___", "")


def load_search_cases(path: Union[str, Path]) -> list[SearchCase]:
    cases: list[SearchCase] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"query", "max_year", "limit"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"CSV missing required columns: {sorted(missing)}"
            )

        for row_num, row in enumerate(reader, start=2):  # 2 = first data row
            try:
                cases.append(
                    SearchCase(
                        query=row["query"].strip(),
                        max_year=int(row["max_year"]),
                        limit=int(row["limit"]),
                    )
                )
            except (ValueError, KeyError) as exc:
                raise ValueError(
                    f"Bad row {row_num} in {path}: {row} ({exc})"
                ) from exc
    return cases