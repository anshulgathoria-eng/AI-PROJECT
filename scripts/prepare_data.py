"""Safely extract only the expected dataset; never change the source archive."""
import argparse
import hashlib
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "household_power_consumption.txt"


def sha256(path):
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def prepare(archive, destination=ROOT / "data"):
    archive, destination = Path(archive).resolve(), Path(destination).resolve()
    before = sha256(archive)
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / NAME
    with zipfile.ZipFile(archive) as zf:
        matches = [i for i in zf.infolist() if Path(i.filename.replace("\\", "/")).name == NAME and not i.is_dir()]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {NAME}; found {len(matches)}.")
        entry = matches[0]
        print(f"ZIP member: {entry.filename} ({entry.file_size:,} bytes)")
        # Copy to a fixed filename: member paths cannot escape destination.
        if target.exists():
            with zf.open(entry) as src:
                expected = hashlib.file_digest(src, "sha256").hexdigest()
            if sha256(target) != expected:
                raise FileExistsError(f"Different file exists at {target}; preserve or move it before retrying.")
        else:
            with zf.open(entry) as src, target.open("xb") as out:
                shutil.copyfileobj(src, out)
    if sha256(archive) != before:
        raise RuntimeError("Source ZIP hash unexpectedly changed.")
    print(f"Dataset: {target}\nOriginal ZIP unchanged; SHA256: {before}")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", type=Path)
    args = parser.parse_args()
    archives = list(ROOT.glob("*.zip")) if args.archive is None else [args.archive]
    if len(archives) != 1:
        parser.error("Specify the dataset ZIP path explicitly.")
    prepare(archives[0])
