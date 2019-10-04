import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="comandante",
    version="0.0.1",
    author="Stepan Anokhin",
    author_email="stepan.anokhin@gmail.com",
    description="A toolkit for building command-line interfaces",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stepan-anokhin/comandante",
    packages=setuptools.find_packages(".", exclude=['tests']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    test_suite="tests",
)
