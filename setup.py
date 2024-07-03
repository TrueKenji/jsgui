from setuptools import setup, find_packages

setup(
    name='jsgui',
    version='0.9.1',
    packages=find_packages(),
    description='jsgui provides gui to edit json files based on a schema file',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',  # for Markdown
    author='TrueKenji',
    url='https://github.com/truekenji/jsgui',
    install_requires=[
        'numpy',
        'jsonschema',
        'decomply',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    keywords=['GUI', 'JSON Schema', 'JSON', 'tkinter', 'decomply', 'Visualisation']
)
