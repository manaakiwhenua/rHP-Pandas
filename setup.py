from setuptools import setup, find_packages
from os import path

__version__: str = "0.2.0"

# read the contents of README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="rhppandas",
    version=__version__,
    description="Integration of rHEALPixDGGS and Pandas/GeoPandas",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MWLR",
    url="https://github.com/manaakiwhenua/rHP-Pandas",
    keywords=[
        "python",
        "rHEALPix",
        "rhealpixdggs",
        "geospatial",
        "geopandas",
        "pandas",
        "integration",
    ],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    packages=find_packages(),
    setup_requires=[],
    install_requires=[
        "geopandas",
        "numpy",
        "pandas",
        "shapely",
        "rhealpixdggs",
        "numpy",
        "typing-extensions",
    ],
    python_requires=">=3.11",
    extras_require={
        "test": ["pytest", "pytest-cov"],
        #     "docs": ["sphinx", "numpydoc", "pytest-sphinx-theme", "typing-extensions"],
    },
)
