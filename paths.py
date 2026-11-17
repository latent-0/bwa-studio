"""Where the studio keeps its files. Locally that is this folder. On Vercel the deployed folder is read-only, so a writable copy of the seed
files (assets, before images, scripts, brand defaults) is made under /tmp and runtime changes are mirrored to the database by persist.py."""
import os
import shutil
from pathlib import Path

SRC = Path(__file__).parent
SERVERLESS = bool(os.environ.get("VERCEL"))
ROOT = Path(os.environ.get("STUDIO_ROOT") or ("/tmp/studio" if SERVERLESS else SRC))

SEED_DIRS = ("assets", "before", "sites")
SEED_DATA = ("final_scripts.txt",)
SEED_FILES = ("brands.csv",)


def prepare():
    """On a fresh serverless instance, copy the read-only seed files into the writable root. Safe to call repeatedly."""
    if ROOT == SRC or (ROOT / ".ready").exists():
        return
    ROOT.mkdir(parents=True, exist_ok=True)
    for d in SEED_DIRS:
        if (SRC / d).exists():
            shutil.copytree(SRC / d, ROOT / d, dirs_exist_ok=True)
    (ROOT / "data").mkdir(exist_ok=True)
    for f in SEED_DATA:
        if (SRC / "data" / f).exists():
            shutil.copyfile(SRC / "data" / f, ROOT / "data" / f)
    if (SRC / "data" / "pitch").exists():
        shutil.copytree(SRC / "data" / "pitch", ROOT / "data" / "pitch", dirs_exist_ok=True)
    for f in SEED_FILES:
        if (SRC / f).exists():
            shutil.copyfile(SRC / f, ROOT / f)
    (ROOT / ".ready").write_text("1")


prepare()
