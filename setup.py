import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="comandante",
    version="0.0.3",
    author="Stepan Anokhin",
    author_email="stepan.anokhin@gmail.com",
    description="A toolkit for building command-line interfaces",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stepan-anokhin/comandante",
    packages=setuptools.find_packages(".", exclude=['tests']),
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7',
    test_suite="tests",
)
