import os

from setuptools import setup, find_packages

PACKAGE = "h_pyramid_sentry"

INSTALL_REQUIRES = [
    'sentry-sdk',
    'pyramid',
    'pyramid_retry',
    'celery',
]

TESTS_REQUIRE = INSTALL_REQUIRES + [
    'pytest',
    'coverage',
]


def from_file(filename):
    with open(filename) as fh:
        return fh.read()


def read_egg_version():
    pkg_info_file = PACKAGE + '.egg-info/PKG-INFO'
    if not os.path.isfile(pkg_info_file):
        return None

    with open(pkg_info_file) as fh:
        for line in fh:
            if line.startswith('Version'):
                return line.strip().split('Version: ')[-1]


def get_version(major_version, build_var='BUILD'):
    # If we have a
    build = os.environ.get(build_var)
    if build:
        return major_version + '.' + build

    # We need to do this for source distributions, as setup.py is re-run when
    # installed this way, and we would always get 'dev0' as the version
    # Wheels and binary installs don't work this way and read from PKG-INFO
    # for them selves
    egg_version = read_egg_version()
    if egg_version:
        return egg_version

    return major_version + '.dev0'


setup(
    # Metadata
    # https://docs.python.org/3/distutils/setupscript.html#additional-meta-data

    name=PACKAGE,
    version=get_version(major_version='1.0'),
    description="A Pyramid plugin for integrating Sentry logging",
    long_description=from_file('README.md'),

    author="Hypothesis Engineering Team",
    author_email="eng@list.hypothes.is",
    maintainer="Hypothesis Engineering Team",
    maintainer_email="eng@list.hypothes.is",
    url="https://web.hypothes.is/",
    project_urls={
        # TODO! - Fix me when moved into a separate repo
        'Source': 'https://github.com/hypothesis/h',
        'Deployment': 'https://jenkins.hypothes.is/job/h/job/master/',
    },

    # From: https://pypi.org/pypi?:action=list_classifiers
    classifiers=[
        # Maybe if we want to put people off less we can change this
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3.6',
        'Framework :: Pyramid',
        'Topic :: System :: Logging',
    ],

    license=from_file('LICENSE'),
    platforms=['Operating System :: OS Independent'],

    # Contents and dependencies

    packages=find_packages(),
    install_requires=INSTALL_REQUIRES,

    # Add support for pip install .[test]
    extras_require={
        'tests': TESTS_REQUIRE
    },

    # Adding pytest support for `python setup.py test` (also see setup.cfg)
    test_suite="tests",
    setup_requires=['pytest-runner'],
    tests_require=TESTS_REQUIRE,
)
