from setuptools import setup, find_packages

setup(
    name='pyfr24',
    version='0.1.0',
    description='A Python client for the Flightradar24 API',
    author='Your Name',
    author_email='mattstiles@gmail.com',
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
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
