
from setuptools import find_packages, setup
import os

# Package meta-data.
NAME = 'dronesim'
DESCRIPTION = 'Simulate a UAV for AI applications in 3D environments'
URL = 'https://github.com/nb-programmer/dronesim'
EMAIL = 'narayanband1356@gmail.com'
AUTHOR = 'nb-programmer'
REQUIRES_PYTHON = '>=3.7.0'
VERSION = '0.5.2'
LICENSE = 'MIT'

REQUIRED = [
    'Panda3D',              # The 3D game engine that does all the heavy lifting of rendering
    'panda3d-gltf',         # Model export format support for gltf/glb models
    'panda3d-simplepbr',    # Physically Based Rendering (PBR) model support (Blender-exported models)
    'pyee',                 # Event interface for state change in the simulator
    'numpy',                # Number manipulation and some math functions
    'PyGLM',                # Matrix and vector math
    'simple-pid',           # PID controller for physics engines
    'matplotlib'            # To plot target vs actual to tune PID coefficients
]

EXTRAS = {
    "gym": ["gym"],         #Optional Gym environment support
    "cv": ["opencv-python"] #For some objectives
}

PACKAGE_DATA = {
    #Include models, scenes and textures with the package when installing
    NAME: [
        'assets/**',
        'assets/models/**',
        'assets/scenes/**',
        'assets/textures/**'
    ]
}

PACKAGE_ENTRY_SCRIPTS = [ 'dronesim = dronesim.__main__:main' ]

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
    package_data=PACKAGE_DATA,
    entry_points={'console_scripts': PACKAGE_ENTRY_SCRIPTS},
    url=URL,
    license=LICENSE,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    install_requires=REQUIRED,
    extras_require=EXTRAS
)
