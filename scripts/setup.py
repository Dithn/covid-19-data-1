"""setup script."""


import os

from setuptools import find_packages, setup

this_directory = os.path.abspath(os.path.dirname(__file__))
# with open(os.path.join(this_directory, "README.md")) as f:
#    long_description = f.read()

with open(os.path.join(this_directory, "requirements.txt")) as f:
    requirements = f.readlines()
with open(os.path.join(this_directory, "requirements-docs.txt")) as f:
    requirements_docs = f.readlines()

setup(
    name="cowidev",
    version="0.0.1.dev0",
    description="Update tools for OWID COVID dataset.",
    # long_description=long_description,
    long_description_content_type="text/markdown",
    author="Our World in Data",
    author_email="info@ourworldindata.org",
    license="MIT",
    install_requires=requirements,
    packages=find_packages("src"),
    package_dir={"": "src"},
    # py_modules=[
    #     os.path.splitext(os.path.basename(path))[0] for path in glob.glob("scripts/cowidev/*.py")
    # ],
    # py_modules=[
    #     os.path.splitext(os.path.basename(path))[0] for path in glob.glob("scripts/*.py")
    # ],
    url="http://github.com/owid/covid-19-data",
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    keywords="Automation, Covid, Covid-19, Vaccination",
    project_urls={
        "Github": "http://github.com/owid/covid-19-data/scripts/",
        "Bug Tracker": "http://github.com/owid/covid-19-data/issues",
    },
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "cowid=cowidev.cmd.__main__:cli",
        ]
    },
    extras_require={"docs": requirements_docs},
)
