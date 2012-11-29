#!/usr/bin/env python
from os import environ
from os.path import join


def main():
    """Runs the hypothes.is server."""
    from pyramid.scripts.pserve import main

    main()


if __name__ == '__main__':
    # If  a virtual environment is present make sure it's being used.
    virtual_env = environ.get('VIRTUAL_ENV', '.')
    activate = join(virtual_env, 'bin', 'activate_this.py')
    execfile(activate, dict(__file__=activate))

    main()
