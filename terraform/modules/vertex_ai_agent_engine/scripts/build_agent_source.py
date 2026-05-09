from __future__ import annotations

import base64
import gzip
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path


def _add_file(tar: tarfile.TarFile, root: Path, path: Path) -> None:
    data = path.read_bytes()
    info = tarfile.TarInfo(str(path.relative_to(root)))
    info.size = len(data)
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mode = 0o644
    tar.addfile(info, io.BytesIO(data))


def main() -> None:
    query = json.load(sys.stdin)
    root = Path(query["ruta_codigo_fuente"]).resolve()
    requirements = root / query["requirements_file"]

    files = sorted((root / "agent").rglob("*.py"))
    files.append(requirements)

    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as gzip_file:
        with tarfile.open(fileobj=gzip_file, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for path in files:
                if not path.is_file():
                    raise FileNotFoundError(path)
                _add_file(tar, root, path)

    payload = buffer.getvalue()
    json.dump(
        {
            "source_archive": base64.b64encode(payload).decode("ascii"),
            "source_sha256": hashlib.sha256(payload).hexdigest(),
        },
        sys.stdout,
    )


if __name__ == "__main__":
    main()
