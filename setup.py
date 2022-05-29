
from setuptools import find_packages, setup
import os

# Package meta-data.
NAME = 'dronesim'
DESCRIPTION = 'Simulate a drone with visualization, POV streaming and network control'
URL = 'https://github.com/nb-programmer/dronesim'
EMAIL = 'narayanband1356@gmail.com'
AUTHOR = 'nb-programmer'
REQUIRES_PYTHON = '>=3.7.0'
VERSION = '0.1.0'

REQUIRED = [
    'pygame',
    'PyOpenGL',
    'ffmpeg_python',
    'numpy'
]

EXTRAS = {
    "gym": ["gym"]
}

long_desc = DESCRIPTION
try:
    BASEPATH = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(BASEPATH, 'README.md'), encoding='utf-8') as f:
        long_desc = f.read()
except FileNotFoundError:
    pass

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_desc,
    packages=find_packages(),
    url=URL,
    license='MIT',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    install_requires=REQUIRED,
    extras_require=EXTRAS
)
