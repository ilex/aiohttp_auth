"""Setup script."""
import os.path
import re
from setuptools import setup, find_packages


install_requires = ['aiohttp', 'ticket_auth==0.1.4']


tests_require = ['pytest', 'pytest-aiohttp', 'pytest-cov', 'aiohttp_session']


def version():
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(cur_dir, 'aiohttp_auth', '__init__.py'), 'r') as f:
        try:
            version = re.findall(
                r"^__version__ = '([^']+)'\r?$",
                f.read(), re.M)[0]
        except IndexError:
            raise RuntimeError('Could not determine version.')

        return version


long_description = '\n'.join((open('README.rst').read(),
                              open('CHANGELOG.rst').read()))


setup(
    name="aiohttp_auth_autz",
    version=version(),
    description=('Authorization and authentication '
                 'middleware plugin for aiohttp.'),
    long_description=long_description,
    setup_requires=['pytest-runner'],
    install_requires=install_requires,
    tests_require=tests_require,
    packages=find_packages(exclude=['tests*']),
    author='Gnarly Chicken',
    author_email='gnarlychicken@gmx.com',
    maintainer='ilex (fork author)',
    url='https://github.com/ilex/aiohttp_auth_autz',
    license='MIT',
    classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'Topic :: Internet :: WWW/HTTP :: Session',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
        ]
)
