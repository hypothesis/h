"""Interface for processing batches of commands."""
from collections import defaultdict

from h.h_api.bulk_api.command_batcher import CommandBatcher
from h.h_api.bulk_api.id_references import IdReferences
from h.h_api.bulk_api.model.command import ConfigCommand
from h.h_api.bulk_api.model.report import Report
from h.h_api.bulk_api.observer import Observer
from h.h_api.enums import CommandStatus
from h.h_api.exceptions import CommandSequenceError, InvalidDeclarationError


class CommandProcessor:
    """
    Manager which will check and run a number of bulk API commands.

    The manager is responsible for:

     * Checking the correctness of commands and their order
     * Batching similar commands together for batch processing
     * Dispatching batches of commands to an `Executor` to execute them
     * Reporting each command to an `Observer` to look at
    """

    def __init__(self, executor, observer=None, batch_size=100):
        """
        :param executor: An executor to carry out commands
        :param observer: An observer to view commands
        :param batch_size: Commands to wait for before executing
        """

        self.executor = executor
        self.observer = observer or Observer()

        # Pass _execute_batch() to the CommandBatcher so it can call us back
        # when the batch is ready.
        self.batcher = CommandBatcher(
            on_flush=self._execute_batch, batch_size=batch_size
        )

        # A container for any custom references to objects
        self.id_refs = IdReferences()
        self.reports = defaultdict(list)
        self.config = None
        self.command_count = 0

    def process(self, commands):
        """Process an iterable of Command objects."""

        for command in commands:
            self._process_single_command(command)

        # Flush out the last batch of commands (if any)
        self.batcher.flush()

        self._check_command_count(final=True)

        self._report_back()

    def _process_single_command(self, command):
        """Process a single command."""

        self.observer.observe_command(command, status=CommandStatus.AS_RECEIVED)

        self.command_count += 1
        self._check_command_count()

        if isinstance(command, ConfigCommand):
            self._configure(command.body)
        else:
            self._add_to_batch(command)

        self.observer.observe_command(command, status=CommandStatus.POST_EXECUTE)

    def _configure(self, config):
        """Configure this object and the executor."""

        if self.config is not None:
            raise CommandSequenceError("Cannot currently re-configure jobs")

        self.executor.configure(config)
        self.config = config

    def _add_to_batch(self, command):
        """Add a single command to the batch.

This may cause the CommandBatcher to call the on_flush() callback that we passed to it
(self._execute_batch()) if it decides that it's time to execute the next batch.
        """

        if self.config is None:
            raise CommandSequenceError("Not configured yet")

        with self.batcher.add(command):
            # If we have any id references like `"id": {"$ref": ...}` we need
            # to fill these out before we pass them to the executor. We do this
            # now to get the earliest warning if we have any id references
            # which don't match up
            self.id_refs.fill_out(command.body.raw)

    def _check_command_count(self, final=False):
        """Check the command count matches expectations.

        :param final: This is the final count check, not incremental
        """

        if not self.config:
            return

        total = self.config.total_instructions

        if not final:
            if self.command_count > total:
                raise InvalidDeclarationError(
                    f"More instructions ({self.command_count}) received than declared ({total})"
                )

        elif self.command_count != total:
            raise InvalidDeclarationError(
                f"Expected more instructions. Found {self.command_count} expected {total}"
            )

    def _execute_batch(self, command_type, data_type, batch):
        """Prepare and execute a batch of commands.

        This is passed to the `CommandBatcher` object which will call us back
        here when a batch is ready.
        """

        # Get configuration for this combo of command and data type
        default_config = self.config.defaults_for(command_type, data_type)

        # Prep commands to be sent to the executor
        #
        # All items in batch are the same type. We can use the first one
        # to process the items in place. This will effect any command type
        # specific commands which can be done for the executor
        batch[0].prepare_for_execute(batch, default_config)

        # We expect the executor to return a mapping from custom id references
        # to concrete ids for any items with `$anchor`
        reports = self.executor.execute_batch(
            command_type=command_type,
            data_type=data_type,
            default_config=default_config,
            batch=batch,
        )

        self._process_reports(data_type, batch, reports)

    def _process_reports(self, data_type, batch, reports):
        """
        Store reports and update id references returned by the executor.

        :param data_type: The data type these references are for
        :param batch: The batch of commands containing id references
        :param reports: A list of Report objects
        """
        if not isinstance(reports, list) or any(
            not isinstance(item, Report) for item in reports
        ):
            raise TypeError(f"Expected a list of Report objects not: {reports}")

        if len(reports) != len(batch):
            raise IndexError(
                "The number of reports does not match the number of objects"
            )

        for command, report in zip(batch, reports):
            reference = command.body.id_reference
            if reference is not None:
                self.id_refs.add_concrete_id(data_type, reference, report.id)

        if self.config.view is not None:
            # Store reports for each item, so we ask for the objects to produce
            # our final response
            self.reports[data_type].append(reports)

    def _report_back(self):
        if not self.reports:
            # Nothing to report!
            return

        # TODO! Implement reporting back
        raise NotImplementedError()
