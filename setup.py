from setuptools import setup, find_packages
setup(
    name="pwnshell",
    version="0.1",
    packages=find_packages(),
    entry_points={
    	'console_scripts': ['pwnshell=pwnshell.main:main']
    },
    install_requires=['art', 'termcolor'],
)
