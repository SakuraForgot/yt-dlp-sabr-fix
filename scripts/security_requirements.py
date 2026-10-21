"""Hash-pinned security remediation for upstream dependency locks."""
import importlib.metadata
import re

# PyPI wheel SHA-256; pip hash also published in the Python security announcement:
# https://discuss.python.org/t/109576
SECURITY_PINS = {
    "urllib3": ("2.8.0", "0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3"),
    "pip": ("26.2.2", "fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70"),
    "certifi": ("2026.10.19", "42d35340cc5b9ba78e818ddbff0c5b1c2b779de448a340fd1b989f5fa8670e1b"),
}


def version_tuple(value):
    if not re.fullmatch(r"\d+(?:\.\d+)*", value):
        raise ValueError(f"Review non-stable security dependency version: {value}")
    return tuple(map(int, value.split(".")))


def pinned_line(name):
    version, digest = SECURITY_PINS[name]
    return f"{name}=={version} --hash=sha256:{digest}\n"


def secure_lock(text):
    """Replace only outdated security pins; preserve other hashes and newer pins."""
    lines = iter(text.splitlines(keepends=True))
    result = []
    for line in lines:
        match = re.match(r"^(pip|certifi|urllib3)==([^\s;]+)", line)
        if match and version_tuple(match[2]) < version_tuple(SECURITY_PINS[match[1]][0]):
            # Consume the complete logical requirement, including its old hashes.
            while line.rstrip().endswith("\\"):
                line = next(lines)
            result.append(pinned_line(match[1]))
        else:
            result.append(line)
    return "".join(result)


def verify_installed():
    for name, (minimum, _) in SECURITY_PINS.items():
        actual = importlib.metadata.version(name)
        if version_tuple(actual) < version_tuple(minimum):
            raise RuntimeError(f"Unsafe build dependency: {name} {actual}; require >= {minimum}")
