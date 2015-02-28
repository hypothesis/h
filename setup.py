# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys

import versioneer


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['h']
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

cmdclass = versioneer.get_cmdclass()
cmdclass['test'] = PyTest

versioneer.VCS = 'git'
versioneer.versionfile_source = 'h/_version.py'
versioneer.versionfile_build = 'h/_version.py'
versioneer.tag_prefix = 'v'
versioneer.parentdir_prefix = 'h-'

install_requires = [
    'PyJWT>=0.4.3,<0.5',
    'SQLAlchemy>=0.8.0',
    'alembic>=0.6.3',
    'annotator>=0.14.0,<0.15',
    'blinker>=1.3,<1.4',
    'clik==0.3.1',
    'cryptography>=0.7',
    'deform>=0.9,<1.0',
    'elasticsearch>=1.1.0',
    'gnsq>=0.2.0,<0.3.0',
    'gunicorn>=19.2,<20',
    'horus>=0.9.15',
    'jsonpointer==1.0',
    'jsonschema==1.3.0',
    'oauthlib==0.6.3',
    'pyramid>=1.5',
    'pyramid-basemodel>=0.2',
    'pyramid-layout>=0.9',
    'pyramid_mailer>=0.13',
    'pyramid-oauthlib>=0.2.0,<0.3.0',
    'pyramid_tm>=0.7',
    'python-dateutil>=2.1',
    'python-statsd>=1.7.0,<1.8.0',
    'pyramid_webassets>=0.9,<1.0',
    'pyramid-jinja2>=2.3.3',
    'pyramid_redis_sessions>=1.0a2',
    'raven>=5.1.1,<5.2.0',
    'requests>=2.2.1',
    'ws4py>=0.3,<0.4',

    # Version pin for known bug
    # https://github.com/repoze/repoze.sendmail/issues/31
    'repoze.sendmail<4.2',
]

development_extras = ['pyramid_debugtoolbar>=2.1', 'prospector', 'pep257']
testing_extras = ['mock', 'pytest>=2.5', 'pytest-cov']

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
    install_requires=install_requires,
    extras_require={
        'dev': development_extras,
        'testing': testing_extras,
        'YAML': ['PyYAML']
    },
    tests_require=development_extras + testing_extras + ['PyYAML'],
    cmdclass=cmdclass,
    package_data={
        'h': [
            'css/*.css',
            'js/*.js',
            'js/**/*.js',
            'lib/*.css',
            'lib/*.js',
            'lib/images/*',
            'lib/polyfills/*.js',
            'locale/*',
            'images/*.png',
            'images/icomoon/fonts/*',
            'images/svg/*.svg',
            'templates/*.html',
            'templates/*.pt',
            'templates/*.txt',
            'templates/deform/*.pt',
            'templates/emails/*.txt',
        ]
    },
    entry_points={
        'paste.app_factory': ['main=h:main'],
        'console_scripts': [
            'hypothesis=h.script:main',
            'hypothesis-worker=h.worker:main',
        ],
        'h.worker': [
            'notification=h.notification.worker:run',
        ]
    },
)
