import unittest
from unittest.mock import patch

from security_requirements import pinned_line, secure_lock, verify_installed


class SecurityLockTests(unittest.TestCase):
    def test_old_hashes_are_removed_and_unrelated_requirements_preserved(self):
        other = "requests==2.34.2 --hash=sha256:unrelated\n"
        old = "certifi==2026.7.22 \\\n    --hash=sha256:old1 \\\n    --hash=sha256:old2\n"
        self.assertEqual(secure_lock(old + other), pinned_line("certifi") + other)

    def test_newer_pin_and_hash_are_not_downgraded(self):
        text = "certifi==2026.11.1 --hash=sha256:new\n"
        self.assertEqual(secure_lock(text), text)

    def test_urllib3_streaming_and_proxy_fixes(self):
        self.assertEqual(secure_lock("urllib3==2.7.0 --hash=sha256:old\n"), pinned_line("urllib3"))

    def test_pip_is_upgraded_too(self):
        self.assertEqual(secure_lock("pip==26.2.1 --hash=sha256:old\n"), pinned_line("pip"))

    def test_unsafe_environment_fails_before_packaging(self):
        with patch("importlib.metadata.version", return_value="1.0"):
            with self.assertRaises(RuntimeError):
                verify_installed()


if __name__ == "__main__":
    unittest.main()
