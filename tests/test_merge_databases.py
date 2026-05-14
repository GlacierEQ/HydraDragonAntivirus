from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # noqa: E402

import pytest  # noqa: E402
from database.merge_databases import merge_databases  # noqa: E402


@pytest.fixture()
def tmp_db_dir(tmp_path: Path) -> Path:
    dir_path = tmp_path / "db"
    dir_path.mkdir()
    (dir_path / "one.ndb").write_text("sig1\nsig2\n")
    (dir_path / "two.ldb").write_text("sig2\nsig3\n")
    return dir_path


def test_merge(tmp_db_dir: Path, tmp_path: Path) -> None:
    output = tmp_path / "combined.db"
    merge_databases([tmp_db_dir], output)
    result = output.read_text().splitlines()
    assert result == ["sig1", "sig2", "sig3"]


def test_merge_recursive_and_comments(tmp_path: Path) -> None:
    base = tmp_path / "db"
    base.mkdir()
    sub = base / "nested"
    sub.mkdir()
    # Include comments and blank lines
    (base / "one.ndb").write_text("#comment\n\nsig1\n")
    (sub / "two.ldb").write_text("sig1\nsig2\n")
    output = tmp_path / "combined.db"
    merge_databases([base], output, recursive=True)
    result = output.read_text().splitlines()
    assert result == ["sig1", "sig2"]


def test_merge_multiple_dirs(tmp_path: Path) -> None:
    first = tmp_path / "first"
    first.mkdir()
    second = tmp_path / "second"
    second.mkdir()
    (first / "a.ndb").write_text("x1\nx2\n")
    (second / "b.ldb").write_text("x2\nx3\n")
    output = tmp_path / "out.db"
    merge_databases([first, second], output)
    assert output.read_text().splitlines() == ["x1", "x2", "x3"]


def test_merge_with_workers(tmp_path: Path) -> None:
    dir_path = tmp_path / "db"
    dir_path.mkdir()
    (dir_path / "one.ndb").write_text("a\nb\n")
    (dir_path / "two.ndb").write_text("b\nc\n")
    out_file = tmp_path / "combo.db"
    merge_databases([dir_path], out_file, workers=1)
    assert out_file.read_text().splitlines() == ["a", "b", "c"]
