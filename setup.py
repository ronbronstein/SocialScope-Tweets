from setuptools import setup, find_packages
import os

# Create required directories if they don't exist
for directory in ['logs', 'output']:
    os.makedirs(directory, exist_ok=True)

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="socialscope-tweets",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Matrix-themed Twitter scraper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/SocialScope-Tweets",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "socialscope=main:main",
        ],
    },
)