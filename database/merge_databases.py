"""Merge ClamAV database files into a single combined file.

This utility deduplicates signatures across multiple rule files. It can
optionally recurse into subdirectories and ignore comment lines starting with
``#``. The default behaviour processes only the files in ``source_dir``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, Sequence, Set


DEFAULT_EXTENSIONS = {".ldb", ".ndb", ".db", ".ign2"}


def read_signatures(file_path: Path) -> Iterable[str]:
    """Yield non-empty, non-comment signatures from a file."""
    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                yield stripped


def merge_databases(
    source_dirs: Sequence[Path],
    output_file: Path,
    *,
    extensions: Sequence[str] = tuple(DEFAULT_EXTENSIONS),
    recursive: bool = False,
    workers: int = 4,
) -> None:
    """Merge rule files under ``source_dirs`` into ``output_file``.

    Parameters
    ----------
    source_dirs : Sequence[Path]
        Directories containing database files.
    output_file : Path
        File to write the merged database.
    extensions : Sequence[str], optional
        File extensions to include. Defaults to ``DEFAULT_EXTENSIONS``.
    recursive : bool, optional
        If ``True``, process files in subdirectories as well.
    workers : int, optional
        Number of threads to use when reading files.
    """

    valid_ext = {ext.lower() for ext in extensions}
    signatures: Set[str] = set()
    files = []
    for directory in source_dirs:
        iterator = directory.rglob("*") if recursive else directory.iterdir()
        for path in iterator:
            if path.suffix.lower() in valid_ext and path.is_file():
                files.append(path)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for sigs in executor.map(read_signatures, files):
            signatures.update(sigs)

    combined = "\n".join(sorted(signatures)) + "\n"
    output_file.write_text(combined, encoding="utf-8")


def parse_args() -> argparse.Namespace:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Merge ClamAV database files")
    parser.add_argument(
        "source_dirs",
        type=Path,
        nargs="+",
        help="Directories containing database files",
    )
    parser.add_argument(
        "output_file",
        type=Path,
        help="Path to write merged database",
    )
    parser.add_argument(
        "--extensions",
        type=str,
        default=",".join(sorted(DEFAULT_EXTENSIONS)),
        help=(
            "Comma-separated list of file extensions to include. "
            f"Defaults to {','.join(sorted(DEFAULT_EXTENSIONS))}."
        ),
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories when searching for databases",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of threads to use when reading files",
    )
    return parser.parse_args()


def main() -> None:  # pragma: no cover
    args = parse_args()
    for directory in args.source_dirs:
        if not directory.is_dir():
            raise SystemExit(f"{directory} is not a directory")
    ext_list = [e.strip() for e in args.extensions.split(",") if e.strip()]
    merge_databases(
        args.source_dirs,
        args.output_file,
        extensions=ext_list,
        recursive=args.recursive,
        workers=args.workers,
    )
    print(f"Merged databases saved to {args.output_file}")


if __name__ == "__main__":  # pragma: no cover
    main()
