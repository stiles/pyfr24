"""
Test that the version is defined in exactly one place.

Version 0.2.0 shipped reporting itself as 1.0.0 because setup.py and
__init__.py each carried their own literal and the bump only updated one.
"""

import importlib.util
import os
import re
import subprocess
import sys
import unittest

import pyfr24

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAS_SETUPTOOLS = importlib.util.find_spec('setuptools') is not None

def read(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return f.read()

class TestVersion(unittest.TestCase):
    """Test version consistency across packaging files."""

    def test_init_literal_matches_the_imported_package(self):
        """The literal in __init__.py is what pyfr24.__version__ reports."""
        match = re.search(
            r'^__version__ = ["\']([^"\']+)["\']',
            read(os.path.join('pyfr24', '__init__.py')),
            re.MULTILINE,
        )

        self.assertIsNotNone(match, "no __version__ literal in pyfr24/__init__.py")
        self.assertEqual(match.group(1), pyfr24.__version__)

    def test_setup_py_does_not_hardcode_a_version(self):
        """A literal in setup.py reintroduces the number that drifted."""
        self.assertIsNone(
            re.search(r'''version\s*=\s*['"]\d''', read('setup.py')),
            "setup.py hardcodes a version; it should call read_version() instead",
        )

    @unittest.skipUnless(HAS_SETUPTOOLS, "setuptools is not installed")
    def test_setup_py_reports_the_package_version(self):
        """Building the distribution picks up the same number.

        Python 3.12 dropped setuptools from the default environment, so this
        skips where it isn't installed. The checks above still hold there.
        """
        result = subprocess.run(
            [sys.executable, 'setup.py', '--version'],
            cwd=ROOT, capture_output=True, text=True,
        )

        self.assertEqual(result.returncode, 0, f"setup.py failed: {result.stderr}")
        self.assertEqual(result.stdout.strip(), pyfr24.__version__)

    def test_version_looks_like_a_release(self):
        """Guard against a mangled __version__ line."""
        self.assertRegex(pyfr24.__version__, r'^\d+\.\d+\.\d+$')

if __name__ == '__main__':
    unittest.main()
