from pathlib import Path
from setuptools import setup, find_packages

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="streamlit-folder-upload",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Streamlit component for folder uploads with drag and drop support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/streamlit-folder-upload",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Streamlit",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    install_requires=[
        "streamlit>=1.2.0",
    ],
)
