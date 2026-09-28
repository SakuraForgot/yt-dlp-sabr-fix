"""Resolve the moving upstream branch once, then build its immutable commit."""
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "yt-dlp-sabr-fix"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request("https://api.github.com/" + path, headers=headers), timeout=60) as response:
        return json.load(response)


def recipe_digest():
    digest = hashlib.sha256()
    files = [ROOT / "source.json", *ROOT.glob("scripts/*.py"), *ROOT.glob(".github/workflows/*.yml")]
    for path in sorted(files):
        digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()


def main():
    config = json.loads((ROOT / "source.json").read_text())
    requested = os.environ.get("SOURCE_SHA", "").strip()
    if requested and not re.fullmatch(r"[0-9a-fA-F]{40}", requested):
        raise ValueError("source_sha must be a complete 40-character commit SHA")
    ref = requested or config["branch"]
    commit = api(f"repos/{config['repository']}/commits/{urllib.parse.quote(ref, safe='')}")
    sha = commit["sha"]
    recipe = recipe_digest()
    tag = f"sabr-{sha[:12]}-{recipe[:12]}"
    if os.environ.get("FORCE_REBUILD") == "true":
        tag += f"-r{os.environ['GITHUB_RUN_ID']}-{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}"
    build = True
    try:
        release = api(f"repos/{config['release_repository']}/releases/tags/{tag}")
        build = release.get("draft", False)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    result = {**config, "source_sha": sha, "recipe_sha256": recipe, "tag": tag,
              "controller_sha": os.environ.get("GITHUB_SHA", "local"), "build": build}
    (ROOT / "resolved.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            for key, value in {"sha": sha, "tag": tag, "build": str(build).lower(), "python": config["python"], "repository": config["repository"]}.items():
                output.write(f"{key}={value}\n")


if __name__ == "__main__":
    main()
