"""Batching and dispatching jobs to work on."""

from contextlib import contextmanager

from h.h_api.exceptions import CommandSequenceException


class CommandBatch:
    """A batch of commands.

    This object will group similar commands together and decide when they
    should be executed. The number of commands should always be a number we
    are comfortable dealing with in memory at once.
    """

    def __init__(self, on_flush, batch_size=100):
        """
        :param on_flush: Callback to call when it's time to execute
        :param batch_size: The max size of a batch
        """

        self.on_flush = on_flush

        self.batch = None
        self.batch_size = batch_size
        self.finished_tasks = set()
        self.current_task = None

    def flush(self):
        """Flush the current batch of commands to the callback."""

        if not self.batch:
            self.batch = None
            return

        command_type, data_type = self.current_task
        self.on_flush(command_type, data_type, self.batch)

        self.batch = None

    @contextmanager
    def add(self, command):
        """
        A context manager for adding a command to the batch.

        Making this a context manager allows us to do the prep-work we need
        to before and after a command is added.

        In order to ensure that the final batch of commands is correctly
        processed the caller must call `flush()` after all `add()` calls are
        complete.
        """

        self._check_sequence(command)

        # The above command might result in flushing previous commands. This
        # may be necessary to process this command as the previous batch could
        # return a concrete id for a reference we rely on now.
        yield

        if self.batch is None:
            self.batch = []

        self.batch.append(command)

        if self.batch and len(self.batch) >= self.batch_size:
            self.flush()

    def _check_sequence(self, command):
        """Check to see if the command sequence is wrong / requires a flush."""

        command_key = (command.type, command.body.type)

        if self.current_task is None:
            self.current_task = command_key
            return

        if command_key == self.current_task:
            return

        if command_key in self.finished_tasks:
            raise CommandSequenceException("Cannot return to old task")

        # Looks like we are switching to a new task
        self.flush()

        self.finished_tasks.add(self.current_task)
        self.current_task = command_key
