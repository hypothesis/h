from setuptools import setup, find_packages

setup(
    name = 'hypothesis',
    version = '0.0.1',
    packages = find_packages(),

    install_requires = [
        'annotator>=0.7.6',
        'apex>=0.9.5dev',
        'pyramid>=1.3',
        'pyramid_jinja2>=1.2',
        'pyramid_fanstatic>=0.3',
        'pyramid_tm>=0.3',
        'setuptools>=0.6c11'
    ],

    author = 'Hypothes.is Project & contributors',
    maintainer = 'Randall Leeds',
    maintainer_email = 'tilgovi@hypothes.is',
    description = 'The Internet. Peer-reviewed.',
    long_description = """A platform for collaborative evaluation of information.""",
    license = 'Simplified (2-Clause) BSD License',
    keywords = 'annotation web javascript',

    url = 'http://hypothes.is/',
    download_url = 'https://github.com/hypothesis/hypothes.is',

    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
    ],

    include_package_data = True,
    zip_safe = False,

    entry_points = {
        'fanstatic.libraries': [
            'hypothesis=hypothesis.resources:library'
        ],
        'paste.app_factory': [
            'main=hypothesis:main'
        ],
        'zest.releaser.prereleaser.middle': [
            'prepare=hypothesis.scripts:prepare'
        ]
    }
)
