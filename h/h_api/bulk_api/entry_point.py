"""Wrappers for common ways to use the bulk API."""

import json
from io import StringIO

from h.h_api.bulk_api.bulk_job import BulkJob
from h.h_api.bulk_api.command_builder import CommandBuilder
from h.h_api.bulk_api.executor import Executor, FakeReportExecutor
from h.h_api.bulk_api.observer import Observer, SerialisingObserver


class BulkAPI:
    """Convenience methods for streaming to and from the BulkAPI."""

    @classmethod
    def from_stream(cls, lines, executor, observer=None):
        """
        Read from a stream of lines where each line is one command.

        :param lines: An iterator of strings
        :param executor: `Executor` to process batches of commands
        :param observer: `Observer` to view individual commands
        """
        if observer is None:
            observer = Observer()

        if not isinstance(observer, Observer):
            raise TypeError(f"Expected 'Observer' instance not '{type(observer)}'")

        if not isinstance(executor, Executor):
            raise TypeError(f"Expected 'Executor' instance not '{type(executor)}'")

        BulkJob(executor=executor, observer=observer).process_commands(
            cls._commands_from_ndjson(lines)
        )

    @classmethod
    def from_string(cls, string, executor, observer=None):
        """
        Read from a string of NDJSON.

        Convenience wrapper for `from_stream`.
        """

        lines = (line for line in string.strip().split("\n"))

        cls.from_stream(lines, executor, observer)

    @classmethod
    def to_stream(cls, handle, commands):
        """
        Check a series of commands for correctness and stream to NDJSON.

        :param handle: File-like object to write NDJSON to
        :param commands: Iterator of commands to process
        """
        BulkJob(
            executor=FakeReportExecutor(),
            observer=SerialisingObserver(handle),
            # We want to know as soon as we can if we've passed in rubbish
            batch_size=1,
        ).process_commands(commands)

    @classmethod
    def to_string(cls, commands):
        """
        Check a series of commands for correctness and create an NDJSON string.

        Convenience wrapper for `to_stream`.
        """

        handle = StringIO()

        BulkAPI.to_stream(handle, commands)

        return handle.getvalue()

    @staticmethod
    def _commands_from_ndjson(lines):
        for line_number, line in enumerate(lines):
            # Try catch JSON errors here
            yield CommandBuilder.from_data(json.loads(line))
