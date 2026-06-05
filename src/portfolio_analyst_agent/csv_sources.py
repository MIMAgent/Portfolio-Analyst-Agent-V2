"""CSV source helpers, including tracked ZIP mirror fallback."""

from __future__ import annotations

from contextlib import contextmanager
import io
from pathlib import Path
from typing import Iterator, TextIO
from zipfile import ZipFile


def csv_zip_mirror_path(csv_path: str | Path) -> Path:
    """Return the conventional ZIP mirror path for a large CSV artifact."""

    path = Path(csv_path)
    return path.with_name(f"{path.name}.zip")


def resolve_existing_csv_source(csv_path: str | Path) -> Path | None:
    """Resolve a CSV path to the raw file or its tracked `.zip` mirror."""

    path = Path(csv_path)
    if path.exists():
        return path

    mirror = csv_zip_mirror_path(path)
    if mirror.exists():
        return mirror

    return None


@contextmanager
def open_csv_text(csv_path: str | Path) -> Iterator[TextIO]:
    """Open a raw CSV, or read the matching CSV member from `<name>.zip`."""

    path = Path(csv_path)
    if path.suffix.lower() == ".zip" and path.exists():
        preferred_name = path.name.removesuffix(".zip")
        with ZipFile(path) as archive:
            member_name = _csv_member_name(archive, preferred_name=preferred_name)
            with archive.open(member_name) as binary_handle:
                text_handle = io.TextIOWrapper(binary_handle, encoding="utf-8", newline="")
                try:
                    yield text_handle
                finally:
                    text_handle.detach()
        return

    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as handle:
            yield handle
        return

    mirror = csv_zip_mirror_path(path)
    if not mirror.exists():
        raise FileNotFoundError(f"CSV source not found: {path} or {mirror}")

    with ZipFile(mirror) as archive:
        member_name = _csv_member_name(archive, preferred_name=path.name)
        with archive.open(member_name) as binary_handle:
            text_handle = io.TextIOWrapper(binary_handle, encoding="utf-8", newline="")
            try:
                yield text_handle
            finally:
                text_handle.detach()


def _csv_member_name(archive: ZipFile, *, preferred_name: str) -> str:
    names = [name for name in archive.namelist() if not name.endswith("/")]
    preferred = [name for name in names if Path(name).name == preferred_name]
    if preferred:
        return preferred[0]

    csv_members = [name for name in names if Path(name).suffix.lower() == ".csv"]
    if len(csv_members) == 1:
        return csv_members[0]
    if not csv_members:
        raise FileNotFoundError("ZIP archive contains no CSV files.")
    raise ValueError(f"ZIP archive contains multiple CSV files and none named {preferred_name!r}.")


__all__ = ["csv_zip_mirror_path", "open_csv_text", "resolve_existing_csv_source"]
