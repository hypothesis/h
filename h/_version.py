# -*- coding: utf-8 -*-

import datetime
import subprocess

try:
    from subprocess import DEVNULL  # Python 3
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

__all__ = ('get_version',)

# git-archive substitution markers. When this file is written out by a `git
# archive` command, these will be replaced by the short commit hash and the
# commit date, respectively.
VERSION_GIT_REF = '$Format:%h$'
VERSION_GIT_DATE = '$Format:%ct$'

# Fallback version in case we cannot derive the version.
VERSION_UNKNOWN = '0+unknown'


def fetch_git_ref():
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],
                                   stderr=DEVNULL).strip()


def fetch_git_date(ref):
    ts = subprocess.check_output(['git', 'show', '-s', '--format=%ct', ref])
    return datetime.datetime.fromtimestamp(int(ts))


def fetch_git_dirty():
    # Ensure git index is up-to-date first. This usually isn't necessary, but
    # can be needed inside a docker container where the index is out of date.
    subprocess.call(['git', 'update-index', '-q', '--refresh'])
    dirty_tree = subprocess.call(['git', 'diff-files', '--quiet']) != 0
    dirty_index = subprocess.call(['git', 'diff-index', '--quiet',
                                   '--cached', 'HEAD']) != 0
    return dirty_tree or dirty_index


def git_version():
    ref = fetch_git_ref()
    date = fetch_git_date(ref)
    dirty = fetch_git_dirty()
    return pep440_version(date, ref, dirty)


def git_archive_version():
    ref = VERSION_GIT_REF
    date = datetime.datetime.fromtimestamp(int(VERSION_GIT_DATE))
    return pep440_version(date, ref)


def pep440_version(date, ref, dirty=False):
    """Build a PEP440-compliant version number from the passed information."""
    return '{date}+g{ref}{dirty}'.format(date=date.strftime('%Y%m%d'),
                                         ref=ref,
                                         dirty='.dirty' if dirty else '')


def get_version():
    """Fetch the current application version."""
    # First we try to retrieve the current application version from git.
    try:
        return git_version()
    except subprocess.CalledProcessError:
        pass

    # We are not in a git checkout or extracting the version from git failed,
    # so we attempt to read a version written into the header of this file by
    # `git archive`.
    if not VERSION_GIT_REF.startswith('$'):
        return git_archive_version()

    # If neither of these strategies work, we fall back to VERSION_UNKNOWN.
    return VERSION_UNKNOWN
