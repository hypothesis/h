from setuptools import setup, find_packages

setup(
    name = 'hypothes.is',
    version = '0.0.1',
    packages = find_packages(),

    install_requires = [
        'pyramid==1.3',
        'pyramid_jinja2==1.3',
        'pyramid_fanstatic==0.3',
        'which==1.0'
    ],

    author = 'Randall Leeds (Hypothes.is Project)',
    author_email = 'tilgovi@hypothes.is',
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
)
