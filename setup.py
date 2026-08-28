import re
from pathlib import Path

from setuptools import setup, find_packages

HERE = Path(__file__).parent

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


def read_version():
    """Read __version__ from the package, the one place it's defined.

    Parsed rather than imported so building doesn't need the dependencies
    installed, and so there's no second copy of the number to drift.
    """
    source = (HERE / "pyfr24" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__ = ["\']([^"\']+)["\']', source, re.MULTILINE)
    if not match:
        raise RuntimeError("Could not find __version__ in pyfr24/__init__.py")
    return match.group(1)


setup(
    name='pyfr24',
    version=read_version(),
    description='A Python client for the Flightradar24 API with CLI support',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Matt Stiles',
    author_email='mattstiles@gmail.com',
    url='https://github.com/stiles/pyfr24',
    packages=find_packages(),
    install_requires=[
        'requests',
        'matplotlib',
        'geopandas',
        'contextily',
        'shapely',
        'pandas',
    ],
    entry_points={
        'console_scripts': [
            'pyfr24=pyfr24.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    # zoneinfo, used for timezone conversion, is stdlib only from 3.9.
    python_requires='>=3.9',
    keywords='flightradar24, flight, tracking, aviation, api, cli',
)
