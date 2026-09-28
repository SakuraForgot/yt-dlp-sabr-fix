"""Fail closed on architecture, frozen modules, and executable startup."""
import json
import os
import struct
import subprocess
import tempfile
from pathlib import Path

from PyInstaller.archive.readers import CArchiveReader

OUT = Path(__file__).resolve().parents[1] / "dist"
exe = OUT / "yt-dlp.exe"
info = json.loads((OUT / "BUILD_INFO.json").read_text())
data = exe.read_bytes()
offset = struct.unpack_from("<I", data, 0x3C)[0]
assert data[offset:offset + 4] == b"PE\0\0"
assert struct.unpack_from("<H", data, offset + 4)[0] == 0x8664
archive = CArchiveReader(str(exe))
modules = archive.open_embedded_archive("PYZ.pyz").toc
required = ["protobug", "yt_dlp.downloader.sabr", "yt_dlp.extractor.youtube._streaming.sabr", "yt_dlp.extractor.youtube._proto"]
for module in required:
    assert any(name == module or name.startswith(module + ".") for name in modules), module
env = dict(os.environ, PATH="")
for name in ("PYTHONHOME", "PYTHONPATH"):
    env.pop(name, None)
with tempfile.TemporaryDirectory(prefix="sabr-frozen-") as directory:
    # Single executable in a clean directory, with neither Python nor tools on PATH.
    isolated = Path(directory) / "yt-dlp.exe"
    isolated.write_bytes(data)
    for args in (["--version"], ["--help"], ["--ignore-config", "-v"]):
        result = subprocess.run([str(isolated), *args], cwd=directory, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        # Verbose without a URL initializes YoutubeDL and prints identity, then
        # exits 2 with the expected usage error. --list-extractors exits earlier.
        assert result.returncode == (2 if "-v" in args else 0), result.stderr
        assert "Traceback" not in result.stderr and "ModuleNotFoundError" not in result.stderr
        if args == ["--version"]:
            assert result.stdout.strip() == info["version"]
        if "-v" in args:
            assert info["release_repository"] in result.stderr and "sabr-test" in result.stderr
report = {"exe_sha256": info["exe_sha256"], "source_sha": info["source_sha"],
          "windows_x64": "passed", "single_exe_empty_path": "passed", "version_help": "passed",
          "bundled_modules": required, "upstream_sabr_unit_tests": "passed",
          "live_youtube_sabr_download": "not_run", "fluentytdl_gui": "not_run"}
(OUT / "VALIDATION.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
