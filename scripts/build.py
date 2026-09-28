"""Use upstream's locked Windows dependencies and official PyInstaller entry point."""
import datetime
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "upstream"
OUT = ROOT / "dist"


def run(*args):
    subprocess.run([sys.executable, *args], cwd=SOURCE, check=True)


def main():
    info = json.loads((ROOT / "resolved.json").read_text())
    assert sys.platform == "win32" and platform.machine().lower() in {"amd64", "x86_64"}
    assert platform.python_version() == info["python"]
    actual_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip()
    assert actual_sha == info["source_sha"], (actual_sha, info["source_sha"])
    # Never pass a publishing credential to upstream code.
    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        os.environ.pop(key, None)
    for lock in ("pip", "win-x64-pyinstaller", "curl-cffi"):
        run("-m", "pip", "install", "--require-hashes", "-r", f"bundle/requirements/{lock}.txt")
    # Test-only dependency; excluded from the packaged runtime by upstream's hooks.
    run("devscripts/install_deps.py", "--omit-default", "--include-group", "test")
    run("-m", "pytest", "test/test_sabr", "-q")
    built = datetime.datetime.now(datetime.timezone.utc)
    version = built.strftime("%Y.%m.%d")
    run("devscripts/update-version.py", "-c", info["release_repository"], "-r", info["release_repository"], version)
    run("devscripts/set-variant.py", "sabr-test", "-M", "SABR test core: in-place updates are disabled. Download a new build from https://github.com/SakuraForgot/yt-dlp-sabr-fix/releases")
    run("devscripts/make_lazy_extractors.py")
    run("-m", "bundle.pyinstaller", "--clean")
    OUT.mkdir(exist_ok=True)
    exe = OUT / "yt-dlp.exe"
    shutil.copy2(SOURCE / "dist/yt-dlp.exe", exe)
    info.update(build_time_utc=built.isoformat(), version=version, architecture="Windows x64", variant="sabr-test",
                exe_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
                workflow_run=f"https://github.com/{info['release_repository']}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}")
    info["dependencies"] = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True).splitlines()
    (OUT / "BUILD_INFO.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["git", "archive", "--format=tar.gz", f"--output={OUT / 'upstream-source.tar.gz'}", "HEAD"], cwd=SOURCE, check=True)
    shutil.copy2(SOURCE / "yt_dlp/version.py", OUT / "generated-version.py")
    for name in ("LICENSE", "THIRD_PARTY_LICENSES.txt"):
        shutil.copy2(SOURCE / name, OUT / name)
    subprocess.run([sys.executable, str(ROOT / "scripts/verify.py")], check=True)
    with (OUT / "SHA256SUMS.txt").open("w", encoding="utf-8", newline="\n") as sums:
        for path in sorted(OUT.iterdir()):
            if path.name != "SHA256SUMS.txt":
                sums.write(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")


if __name__ == "__main__":
    main()
