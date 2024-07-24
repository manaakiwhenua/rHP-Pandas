from setuptools import setup, find_packages
from os import path

from rhppandas import __version__

# read the contents of README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="rhppandas",
    version=__version__,
    # cmdclass=versioneer.get_cmdclass(),
    # license="MIT",
    description="Integration of rHEALPixDGGS and GeoPandas",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MWLR",
    # url="https://github.com/manaakiwhenua/rHP-Pandas",
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
        "Development Status :: 3 - Alpha",
        # "License :: OSI Approved :: MIT License",
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
