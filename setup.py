# -*- coding: utf-8 -*-
import os
import sys
import pathlib
import platform
from setuptools import find_packages, setup

PACKAGE_NAME = "extract_version"
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))

# Version of the module
sys.path.append(os.path.abspath(os.path.join(PROJECT_DIR, "src", PACKAGE_NAME)))
from version import VERSION

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text(encoding='utf8')

# Add possible dependencies here
DEPENDENCIES = []

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    author="Yurii Cherkasov",
    author_email="strategarius@protonmail.com",
    description="Python module for extracting version from the string or directory name",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/yuchdev/ExtractVersion",
    project_urls={
        "Bug Tracker": "https://github.com/yuchdev/ExtractVersion/issues",
    },
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate you support Python 3. These classifiers are *not*
        # checked by 'pip install'. See instead 'python_requires' below.
        "Programming Language :: Python :: 3",
        "License :: Commercial",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(where=str(HERE / 'src')),
    package_dir={"": "src"},
    package_data={PACKAGE_NAME: ['defaults/*']},
    python_requires=">=3.8",
    install_requires=DEPENDENCIES,
)
