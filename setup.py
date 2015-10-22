# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys

import versioneer


class PyTest(TestCommand):
    user_options = [
        ('cov', None, 'measure coverage')
    ]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.cov = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['h']
        self.test_suite = True
        if self.cov:
            self.test_args += ['--cov', 'h',
                               '--cov-config', '.coveragerc']

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

cmdclass = versioneer.get_cmdclass()
cmdclass['test'] = PyTest

INSTALL_REQUIRES = [
    'PyJWT>=1.0.0,<2.0.0',
    'SQLAlchemy>=0.8.0',
    'alembic>=0.7.0',
    'annotator>=0.14.2,<0.15',
    'blinker>=1.3,<1.4',
    'cryptacular>=1.4,<1.5',
    'cryptography>=0.7',
    'deform>=0.9,<1.0',
    'deform-jinja2>=0.5,<0.6',
    'elasticsearch>=1.1.0,<2.0.0',
    'gevent>=1.0.2,<1.1.0',
    'gnsq>=0.3.0,<0.4.0',
    'gunicorn>=19.2,<20',
    'jsonpointer==1.0',
    'jsonschema==1.3.0',
    'oauthlib==0.6.3',
    'pyramid>=1.5,<1.6',
    'psycogreen>=1.0',
    'psycopg2>=2.6.1',
    'pyramid_mailer>=0.13',
    'pyramid-oauthlib>=0.2.0,<0.3.0',
    'pyramid_tm>=0.7',
    'python-dateutil>=2.1',
    'python-slugify>=1.1.3,<1.2.0',
    'python-statsd>=1.7.0,<1.8.0',
    'webassets>=0.10,<0.11',
    'pyramid_webassets>=0.9,<1.0',
    'pyramid-jinja2>=2.3.3',
    'raven>=5.3.0,<5.4.0',
    'requests>=2.7.0',
    'ws4py>=0.3,<0.4',
    'zope.sqlalchemy>=0.7.6,<0.8.0',

    # Version pin for known bug
    # https://github.com/repoze/repoze.sendmail/issues/31
    'repoze.sendmail<4.2',
]

DEV_EXTRAS = ['pyramid_debugtoolbar>=2.1', 'prospector[with_pyroma]', 'pep257',
              'pyramid_multiauth', 'sphinxcontrib-httpdomain']
TESTING_EXTRAS = ['mock>=1.3.0', 'pytest>=2.5', 'pytest-cov', 'factory-boy']
CLAIM_EXTRAS = ['mandrill']
YAML_EXTRAS = ['PyYAML']

setup(
    name='h',
    version=versioneer.get_version(),
    description='The Internet. Peer-reviewed.',
    long_description='\n\n'.join([
        open('README.rst', 'rt').read(),
        open('CHANGES.txt', 'rt').read(),
    ]),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
    ],
    keywords='annotation web javascript',
    author='Hypothes.is Project & contributors',
    author_email='contact@hypothes.is',
    url='https://docs.hypothes.is',
    license='Simplified (2-Clause) BSD License',
    packages=find_packages(exclude=['*.test']),
    include_package_data=True,
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
    extras_require={
        'dev': DEV_EXTRAS + YAML_EXTRAS,
        'testing': TESTING_EXTRAS,
        'claim': CLAIM_EXTRAS,
        'YAML': YAML_EXTRAS,
    },
    tests_require=DEV_EXTRAS + TESTING_EXTRAS,
    setup_requires=['setuptools_git'],
    cmdclass=cmdclass,
    package_data={
        'h': [
            'browser/**/*',
            'static/**/*',
            'templates/**/*',
        ]
    },
    entry_points={
        'paste.app_factory': [
            'main=h.app:create_app',
            'api=h.app:create_api',
        ],
        'console_scripts': [
            'hypothesis=h.script:main',
            'hypothesis-buildext=h.buildext:main',
            'hypothesis-invite=h.claim.invite:main',
            'hypothesis-worker=h.worker:main',
        ],
        'h.worker': [
            'notification=h.notification.worker:run',
            'nipsa=h.api.nipsa.worker:worker',
        ],
        'h.annotool': [
            'prepare=h.api.search:prepare',
        ]
    },
)
