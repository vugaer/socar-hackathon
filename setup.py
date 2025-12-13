from setuptools import setup, find_packages

setup(
    name="caspianpetro",
    version="1.0.0",
    author="SOCAR Hackathon Team",
    description="Legacy seismic data processing for Caspian Petrochemical",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "pandas>=1.3.0",
        "pyarrow>=6.0.0",
        "numpy>=1.20.0",
    ],
    entry_points={
        "console_scripts": [
            "caspianpetro=caspianpetro.cli:main",
        ],
    },
)
