from setuptools import setup, find_packages

setup(
    name='encarne',
    author='Arne Beer',
    author_email='arne@twobeer.de',
    version='0.3.0',
    description='A program to automatically convert all movies in your library to h.265',
    keywords='bash command service',
    url='http://github.com/nukesor/encarne',
    license='MIT',
    install_requires=[
        'pueue>=0.6.0',
        'lxml'
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Environment :: Console'
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'encarne=encarne:main'
        ]
    })
