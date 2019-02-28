#!/usr/bin/env python3
"""
Ratchet mechanism Prospector wrapper script.

A Prospector wrapper script that implements a "ratchet mechanism" based on a
record of preexisting Prospector warnings in a lint.json file.

When you run this script it runs Prospector and fails (exits with non-zero) if
any file has a different number of Prospector messages (either more or fewer)
than is recorded for that file in lint.json.

Files with Prospector messages don't cause this script to fail if the file has
the same number of messages as in lint.json.

The idea is that preexisting messages won't fail this linter, but adding any
new linter messages will cause this linter to fail.
"""
from __future__ import unicode_literals

import argparse
import json
import logging
import multiprocessing
import os
import subprocess
import sys


#: The path to this script file.
SCRIPT_PATH = os.path.realpath(__file__)

#: The path to the data file.
DATA_PATH = os.path.splitext(SCRIPT_PATH)[0] + ".json"


class Message:
    """
    A wrapper class for a Prospector message.

    Handles parsing a message from Prospector's JSON output and providing easy
    access to the contents of that message.
    """

    def __init__(self, message_dict):
        self.dict = message_dict

        #: The actual human-readable linter message, e.g. "Unused argument 'request'".
        self.message = self.dict["message"]

        #: The relative path to the file that this message comes from, e.g. "h/views/organizations.py".
        self.path = self.dict["location"]["path"]

        #: The line number that this message comes from as an int, e.g. 27.
        self.line_number = self.dict["location"]["line"]

        #: The linter that this message came from, e.g. "pylint" or "pep257".
        self.linter = self.dict["source"]

        #: The linter's code name for this message, e.g. "import-error" or "D202".
        self.code = self.dict["code"]

    def __str__(self):
        return (
            f"{self.path}:{self.line_number} {self.linter} {self.code} {self.message}"
        )

    def __repr__(self):
        return str(self)


class LintedFile:
    """A file path and its associated messages from a run of Prospector."""

    def __init__(self, path, messages=None):
        self.path = path

        if messages is None:
            messages = []

        self.messages = messages

    def __str__(self):
        return f"{self.path} with {len(self.messages)} messages"

    def __repr__(self):
        return str(self)


class ProspectorOutput:
    """The output from a run of Prospector."""

    def __init__(self, output):
        # Prospector's JSON output as a dict.
        self._output = json.loads(output)

        # Prospector's messages grouped by file.
        # A dict mapping file path strings to LintedFile objects/
        self._files_by_path = self._group_messages_by_file()

    def save(self):
        open(DATA_PATH, "w").write(json.dumps(self._output, indent=4))

    def __getitem__(self, path):
        try:
            linted_file = self._files_by_path[path]
        except KeyError:
            linted_file = self._files_by_path[path] = LintedFile(path)
        return linted_file

    def _group_messages_by_file(self):
        """Return Prospector's messages grouped by file."""

        messages = [Message(message) for message in self._output["messages"]]

        # A dict mapping path strings to LintedFile objects containing all the
        # messages for those paths as Message objects.
        files_by_path = {}

        for message in messages:
            if message.path not in files_by_path:
                files_by_path[message.path] = LintedFile(message.path)

            files_by_path[message.path].messages.append(message)

        return files_by_path

    @classmethod
    def from_prospector(cls, paths):
        try:
            output = subprocess.check_output(["tox", "-qqe", "py36-prospector", "--", "--output-format", "json"] + paths)
        except subprocess.CalledProcessError as err:
            output = err.output

        return cls(output)

    @classmethod
    def from_file(cls):
        return cls(open(DATA_PATH).read())


class Ratchet:
    def __init__(self):
        self._messages_from_file = None
        self._messages_from_prospector = None

    def check(self, paths):
        self._messages_from_file = ProspectorOutput.from_file()
        self._messages_from_prospector = ProspectorOutput.from_prospector(paths)

        errors = []
        for path in self._messages_from_prospector._files_by_path:
            try:
                self.check_path(path)
            except Exception as err:
                errors.append(err)

        return errors

    def check_path(self, path):
        current_file = self._messages_from_prospector[path]
        current_num_messages = len(current_file.messages)

        saved_file = self._messages_from_file[path]
        saved_num_messages = len(saved_file.messages)

        if current_num_messages == saved_num_messages:
            return

        difference = abs(current_num_messages - saved_num_messages)

        if current_num_messages > saved_num_messages:
            raise RuntimeError(
                f"{difference} new linter messages found in {path}.\n\n"
                f"You need to remove {difference} linter messages from {path}.\n"
                f"You've added {difference} new linter messages to {path}.\n"
                f"{path} has {saved_num_messages} messages in {DATA_PATH} but "
                f"{current_num_messages} currently."
            )

        raise RuntimeError(
            f"{difference} fewer linter messages found in {path}.\n\n"
            f"You need to run `./scripts/lint.py --save` to update lint.json "
            f"because you've removed {difference} linter messages from {path}."
        )

    def save(self):
        self._messages_from_prospector.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="*")
    parser.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Create or update lint.json with the current linter messages",
    )

    args = parser.parse_args()

    ratchet = Ratchet()

    errors = ratchet.check(args.path)


    if args.save:
        ratchet.save()
    else:
        for error in errors:
            print(error)

        if errors:
            sys.exit(1)


if __name__ == "__main__":
    main()
