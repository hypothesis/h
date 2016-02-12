# -*- coding: utf-8 -*-

import os
import re
import subprocess

__all__ = ('get_version',)


VERSION_FMT = (
    # Most recent tag
    re.compile(r'v(?P<tag>\d+\.\d+\.\d+)'),
    # Commits since tag
    re.compile(r'(?P<commits>\d+)'),
    # Git SHA
    re.compile(r'(?P<sha>g[0-9a-f]{7})'),
    # Dirty flag
    re.compile(r'(?P<dirty>dirty)'),
)
VERSION_UNKNOWN = '0+unknown'


def parse_version(ver):
    """Parse a `git describe` version into a dictionary."""
    ver_parts = ver.split('-')
    ver_dict = {}
    for patt, part in zip(VERSION_FMT, ver_parts):
        match = re.match(patt, part)
        if match is not None:
            ver_dict.update(match.groupdict())
    return ver_dict


def pep440_version(ver_dict):
    """Convert a version dictionary into a PEP440 version."""
    if 'tag' not in ver_dict:
        return VERSION_UNKNOWN
    tag = ver_dict['tag']
    local = '.'.join([ver_dict[x]
                      for x in ['commits', 'sha', 'dirty']
                      if x in ver_dict])
    if not local:
        return tag
    return '{}+{}'.format(tag, local)


def get_version():
    """Fetch the current version from git, if possible."""
    git_dir = os.path.join(os.path.dirname(__file__), '../.git')
    if not os.path.isdir(git_dir):
        return VERSION_UNKNOWN

    try:
        cmd = ['git', 'describe', '--tags', '--dirty', '--always']
        ver = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        return VERSION_UNKNOWN

    return pep440_version(parse_version(ver))
