try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'LinkOverflow for xMatters',
    'author': 'Stephen Herd',
    'url': 'https://github.com/sharkannon/LinkOverflow',
    'author_email': 'sarkannon@gmail.com',
    'version': '0.1',
    'install_requires': ['boto', 'paramiko'],
    'packages': ['LinkOverflow'],
    'scripts': [],
    'name': 'LinkOverflow'
}

setup(**config)