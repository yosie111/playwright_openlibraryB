import re


def make_safe_filename(url: str) -> str:
    safe = re.sub(r'[<>:"/\\|?%*]', "_", url)
    return safe.replace("https___", "").replace("http___", "")
