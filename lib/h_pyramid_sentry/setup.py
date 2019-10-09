from setuptools import setup, find_packages

VERSION = "1.0.dev0"

INSTALL_REQUIRES = [
    'sentry-sdk',
    'pyramid',
    'celery',
]
TESTS_REQUIRE = INSTALL_REQUIRES + [
    'pytest',
    'coverage',
]

setup(
    name="h_pyramid_sentry",
    description="A Pyramid plugin for Sentry to suppress errors",
    version=VERSION,

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
