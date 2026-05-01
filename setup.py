# setup.py (root of aeris-lattice)
from setuptools import setup, find_packages

setup(
    name="aeris-lattice",
    version="3.1.0",
    packages=find_packages(include=["backend*"]),
    include_package_data=True,
    install_requires=open("requirements.txt").read().splitlines(),
)