"""Setup for encarne."""
from setuptools import setup, find_packages

setup(
    name='encarne',
    author='Arne Beer',
    author_email='arne@twobeer.de',
    version='1.5.2',
    description='Automatically convert all movies in your library to h.265',
    keywords='bash command service',
    url='http://github.com/nukesor/encarne',
    license='MIT',
    install_requires=[
        'pueue',
        'lxml',
        'humanfriendly',
        'SQLAlchemy~=1.2.0',
        'sqlalchemy-utils~=0.33.0',
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Environment :: Console',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'encarne=encarne:main',
        ],
    })
