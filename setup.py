import io
import os

from setuptools import find_packages, setup

from src.dymoprint.constants import VERSION

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

with io.open(os.path.join(PROJECT_ROOT, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

setup(
    name="dymoprint",
    version=VERSION,
    description="Linux Software to print with LabelManager PnP from Dymo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/maresb/dymoprint",
    author="Sebastian J. Bronner",
    author_email="waschtl@sbronner.com",
    maintainer="Ben Mares",
    maintainer_email="services-dymoprint@tensorial.com",
    license="Apache License 2.0",
    python_requires=">=3.7,<4",
    install_requires=[
        "appdirs",
        "Pillow>=8.1.2,<9",
        "PyQRCode>=1.2.1,<2",
        "python-barcode>=0.13.1<1",
    ],
    entry_points={
        "console_scripts": [
            "dymoprint = dymoprint.command_line:main",
        ],
    },
    package_dir={
        "": "src",
        "dymoprint_fonts": "data/fonts",
    },
    packages=["dymoprint", "dymoprint_fonts"],
    package_data={
        "dymoprint_fonts": ["*"],
    },
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Printing",
    ],
)
