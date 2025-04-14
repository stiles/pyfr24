from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='pyfr24',
    version='0.1.4',
    description='A Python client for the Flightradar24 API with CLI support',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Matt Stiles',
    author_email='mattstiles@gmail.com',
    url='https://github.com/mstiles/pyfr24',
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
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.8',
    keywords='flightradar24, flight, tracking, aviation, api, cli',
)
