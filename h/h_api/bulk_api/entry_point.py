"""Wrappers for common ways to use the bulk API."""

import json
from io import StringIO
from json import JSONDecodeError

from h.h_api.bulk_api.command_builder import CommandBuilder
from h.h_api.bulk_api.command_processor import CommandProcessor
from h.h_api.bulk_api.executor import AutomaticReportExecutor, Executor
from h.h_api.bulk_api.observer import Observer, SerialisingObserver
from h.h_api.exceptions import InvalidJSONError


class BulkAPI:
    """Convenience methods for streaming to and from the BulkAPI."""

    @classmethod
    def from_lines(cls, lines, executor, observer=None):
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

        CommandProcessor(executor=executor, observer=observer).process(
            cls._commands_from_ndjson(lines)
        )

    @classmethod
    def from_string(cls, string, executor, observer=None):
        """
        Read from a string of NDJSON.

        Convenience wrapper for `from_lines`.
        """

        cls.from_lines(cls._string_to_lines(string), executor, observer)

    @classmethod
    def from_byte_stream(cls, byte_stream, executor, observer=None):
        """
        Read from a stream of NDJSON bytes.

        Convenience wrapper for `from_lines`.
        """

        cls.from_lines(cls._bytes_to_lines(byte_stream), executor, observer)

    @classmethod
    def to_stream(cls, handle, commands):
        """
        Check a series of commands for correctness and stream to NDJSON.

        :param handle: File-like object to write NDJSON to
        :param commands: Iterator of commands to process
        """
        CommandProcessor(
            executor=AutomaticReportExecutor(),
            observer=SerialisingObserver(handle),
            # We want to know as soon as we can if we've passed in rubbish
            batch_size=1,
        ).process(commands)

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
        """Turn multiple lines of JSON into Command objects.

        :param lines: An iterable of JSON strings
        :return: A generator of `Command` objects
        """
        for line_number, line in enumerate(lines):
            try:
                data = json.loads(line)
            except JSONDecodeError as e:
                raise InvalidJSONError(
                    f"Invalid JSON on line {line_number}: {e.args[0]}"
                )

            # Try catch JSON errors here
            yield CommandBuilder.from_data(data)

    @staticmethod
    def _string_to_lines(string):
        """Split a string on new-lines.

        :param string: A string to split
        :return: A generator of strings containing single lines
        """

        lines = (line.strip() for line in string.strip().split("\n"))
        return (line for line in lines if line)

    @staticmethod
    def _bytes_to_lines(stream, chunk_size=16384):
        """Split a stream of bytes on new-lines.

        :param stream: A file-like object
        :return: A generator of strings containing single lines
        """
        line = b""

        while True:
            block = stream.read(chunk_size)
            if not len(block):
                break

            # As long as our block contains new lines, split strings out of it
            while b"\n" in block:
                head, block = block.split(b"\n", 1)

                line += head
                if line:
                    yield line

                line = b""

            line += block

        if line:
            yield line
