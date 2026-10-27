import zipfile
import pytest
from scripts.prepare_data import prepare, sha256, NAME


def test_extraction_is_safe_idempotent_and_preserves_zip(tmp_path):
    archive = tmp_path / "source.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../../" + NAME, "Date;Time;Global_active_power\n")
        zf.writestr("../unexpected.txt", "do not extract")
    before = sha256(archive)
    target = prepare(archive, tmp_path / "data")
    assert target.parent == tmp_path / "data"
    assert target.read_text() == "Date;Time;Global_active_power\n"
    assert not (tmp_path / "unexpected.txt").exists()
    assert prepare(archive, tmp_path / "data") == target
    assert sha256(archive) == before
    target.write_text("existing different data", encoding="utf-8")
    with pytest.raises(FileExistsError):
        prepare(archive, tmp_path / "data")
    assert target.read_text() == "existing different data"
