from setuptools import setup, find_packages

setup(
    name = 'h',
    version = '0.0.1',
    packages = find_packages(),

    install_requires = [
        'annotator>=0.7.6',
        'deform_bootstrap>=0.2.1',
        'horus>=0.9.8',
        'pyramid>=1.3',
        'pyramid_deform>=0.2a4',
        'pyramid_tm>=0.3',
        'pyramid_webassets>=0.7',
        'setuptools>=0.6c11',
        'velruse>=1.0',
    ],

    author = 'Hypothes.is Project & contributors',
    maintainer = 'Randall Leeds',
    maintainer_email = 'tilgovi@hypothes.is',
    description = 'The Internet. Peer-reviewed.',
    long_description = """A platform for collaborative evaluation of information.""",
    license = 'Simplified (2-Clause) BSD License',
    keywords = 'annotation web javascript',

    url = 'http://hypothes.is/',
    download_url = 'https://github.com/hypothesis/h',

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
        'paste.app_factory': [
            'main=h:main'
        ],
        'zest.releaser.prereleaser.middle': [
            'prepare=h.scripts:prepare'
        ]
    }
)
