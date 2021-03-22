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
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*",
    install_requires=[
        "appdirs",
        "Pillow==6.2.2",
        "PyQRCode==1.2.1",
        "pyBarcode==0.8b1; python_version=='2.7'",
        "python-barcode==0.9.0; python_version > '3.0'",
    ],
    entry_points={
        "console_scripts": [
            "dymoprint = dymoprint.__main__:main_with_debug",
        ],
    },
    package_dir={
        "": "src",
        "dymoprint_fonts": "data/fonts",
    },
    packages = ["dymoprint", "dymoprint_fonts"],
    package_data={
        "dymoprint_fonts": ["*"],
    },
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Printing",
    ]
)
