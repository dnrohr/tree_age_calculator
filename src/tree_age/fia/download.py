from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from urllib.request import Request, urlopen
import zipfile

from . import NEW_ENGLAND_STATES

URL_TEMPLATE = "https://apps.fs.usda.gov/fia/datamart/Databases/SQLite_FIADB_{state}.zip"


def download_state(state: str, destination: Path, force: bool = False) -> Path:
    state = state.upper()
    if state not in NEW_ENGLAND_STATES:
        raise ValueError(f"Unsupported state {state!r}; expected one of {', '.join(NEW_ENGLAND_STATES)}")
    destination.mkdir(parents=True, exist_ok=True)
    database = destination / state / f"SQLite_FIADB_{state}.db"
    if database.exists() and not force:
        return database

    url = URL_TEMPLATE.format(state=state)
    archive = destination / f"SQLite_FIADB_{state}.zip"
    temporary = archive.with_suffix(".zip.part")
    request = Request(url, headers={"User-Agent": "tree-age-estimator/0.4"})
    with urlopen(request, timeout=120) as response, temporary.open("wb") as output:
        shutil.copyfileobj(response, output)
    temporary.replace(archive)
    if not zipfile.is_zipfile(archive):
        raise RuntimeError(f"Downloaded file for {state} is not a valid ZIP archive")
    extract_dir = destination / state
    extract_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(extract_dir)
    if not database.exists():
        matches = list(extract_dir.glob("*.db"))
        if len(matches) != 1:
            raise RuntimeError(f"Expected one SQLite database for {state}, found {len(matches)}")
        database = matches[0]

    manifest = {
        "state": state,
        "source_url": url,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_bytes": archive.stat().st_size,
        "database_file": database.name,
    }
    (extract_dir / "download_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return database


def download_states(states: tuple[str, ...], destination: Path, force: bool = False) -> list[Path]:
    return [download_state(state, destination, force) for state in states]

