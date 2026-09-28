"""Publish checked assets; never replace a published historical release."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "dist"
info = json.loads((OUT / "BUILD_INFO.json").read_text())
repo, tag = info["release_repository"], info["tag"]
assert repo == os.environ["GITHUB_REPOSITORY"]
for line in (OUT / "SHA256SUMS.txt").read_text().splitlines():
    expected, filename = line.split("  ", 1)
    assert Path(filename).name == filename
    assert hashlib.sha256((OUT / filename).read_bytes()).hexdigest() == expected
assert hashlib.sha256((OUT / "yt-dlp.exe").read_bytes()).hexdigest() == info["exe_sha256"]


def gh(*args):
    return subprocess.check_output(["gh", *args, "--repo", repo], text=True)


existing = subprocess.run(["gh", "release", "view", tag, "--repo", repo, "--json", "isDraft"], capture_output=True, text=True)
if existing.returncode == 0:
    assert json.loads(existing.stdout)["isDraft"], "Refusing to overwrite a published release"
    # Only an unpublished draft from an interrupted attempt can be replaced.
    gh("release", "delete", tag, "--yes")
notes = OUT.parent / "release-notes.md"
notes.write_text(f"""Windows x64 单文件 SABR 测试核心，版本 `{info['version']}`。\n\n来源：[{info['repository']} / {info['branch']}](https://github.com/{info['repository']}/tree/{info['source_sha']})，PR #13515。\n\n- Source SHA: `{info['source_sha']}`\n- Recipe SHA256: `{info['recipe_sha256']}`\n- EXE SHA256: `{info['exe_sha256']}`\n- 构建时间 UTC: {info['build_time_utc']}\n\n已通过 Windows x64、单 EXE 空 PATH 启动、SABR/protobug 收集检查和上游 SABR 单元测试。在线下载与 FluentYTDL GUI 不属于 CI 已验证项，详见 VALIDATION.json。\n\n`-U` 已禁用，请从本仓库下载新版本。直接替换正式版 FluentYTDL 核心不会阻止应用自身的更新/修复覆盖。FluentYTDL 源码不包含在本仓库。\n\n源代码快照为准确的上游提交；generated-version.py 是构建生成的版本元数据。保留许可证与第三方声明。\n""", encoding="utf-8")
assets = [str(path) for path in sorted(OUT.iterdir())]
gh("release", "create", tag, *assets, "--target", info["controller_sha"], "--draft", "--prerelease", "--title", f"SABR {info['version']} · {info['source_sha'][:12]}", "--notes-file", str(notes))
gh("release", "edit", tag, "--draft=false")
print(gh("release", "view", tag, "--json", "url,assets,isPrerelease"))
