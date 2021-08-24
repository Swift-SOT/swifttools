import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

PKGNAME = "swifttools"

setuptools.setup(
    name=PKGNAME,
    version="2.0",
    author="Phil Evans",
    author_email="pae9@leicester.ac.uk",
    description="Tools for users of the Swift satellite",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/DrPhilEvans/swifttools",
    packages=[PKGNAME] + [f'{PKGNAME}.{p}' for p in setuptools.find_packages(where=PKGNAME)],
    install_requires=['requests', 'python-jose', 'pandas', 'tabulate', 'numpy'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)



