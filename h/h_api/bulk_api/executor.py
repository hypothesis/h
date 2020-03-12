"""Implementations of an 'Executor' responsible for running bulk commands."""
from h.h_api.bulk_api.model.report import Report
from h.h_api.enums import CommandResult, CommandType


class Executor:
    """A callback to provide concrete functionality for actions in BulkJob."""

    def configure(self, config):
        """
        Configure the job from the provided config object.

        This is an opportunity for the executor to setup any global options
        required to process subsequent actions correctly. Typically this is
        the first command and only happens once.

        :param config: A `Configuration` object
        """
        pass

    def execute_batch(self, command_type, data_type, default_config, batch):
        """
        Execute the actions specified, returning any referenced ids.

        The implementer is expected to:

         * Execute the actions
         * Respect the configuration passed
         * Return a list of `Report` objects in the same order as the items
           in the batch

        :param command_type: The CommandType being executed (e.g. CommandType.UPSERT)
        :param data_type: The DataType being modified, e.g. DataType.USER
        :param default_config: Configuration which applies to all actions
        :param batch: A list of Command models
        :return: A list of `Report` objects
        """
        raise NotImplementedError()

    def get_items(self, data_type, ids, config):
        """
        Return the items identified by `ids`.

        The items returned should be in the same order as requested in `ids`.

        The config here is a dict of options which modify the behavior of the
        whole batch. For example `{"on_duplicate": "continue"}` for a create
        command.

        :param data_type: The data type to retrieve
        :param ids: The ids of the objects to retrieve
        :param config: A dict of configuration options to modify processing
        :return: An iterable of data objects
        """

        pass


class AutomaticReportExecutor(Executor):
    """An Executor which automatically creates reports.

    To enable items which later on rely on id references, executors are
    expected to return the concrete id when an object is created or found.

    This object fakes this process so you can test to see if the references
    are all valid in your object without actually inserting them into the DB.
    """

    def execute_batch(self, command_type, data_type, default_config, batch):
        """Return fake ids for all items in the batch with id references."""

        fake_status = (
            CommandResult.CREATED
            if command_type is CommandType.CREATE
            else CommandResult.UPDATED
        )

        return [Report(fake_status, id_=index) for index in range(len(batch))]
