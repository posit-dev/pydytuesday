from setuptools import setup, find_packages

VERSION = '0.0.1' 
DESCRIPTION = 'A Python port of the TidyTuesday Downloader'
LONG_DESCRIPTION = 'A port of the tidytuesdayR package to download TidyTuesday datasets'

# Setting up
setup(
       # the name must match the folder name 'verysimplemodule'
        name="PyDyTuesday", 
        version=VERSION,
        author="Andreas Varotsis",
        author_email="andreas.varotsis@gmail.com>",
        description=DESCRIPTION,
        long_description= open('README.rst').read(),
        packages=find_packages(),
        license='MIT',
        install_requires=[], # add any additional packages that 
        # needs to be installed along with your package. Eg: 'caer'
        keywords=['python', 'Tidy Tuesday', 'learning'],
        classifiers= [
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
        ]
)