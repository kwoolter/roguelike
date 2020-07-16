from setuptools import setup

setup(
    name='roguelike',
    version='1.0.0',
    packages=['roguelike', 'roguelike.view', 'roguelike.model', 'roguelike.controller'],
    url='https://github.com/kwoolter/roguelike.git',
    license='',
    author='kwoolter',
    author_email='',
    description='',
    install_requires = ['pygame', 'numpy', 'tcod']
)
