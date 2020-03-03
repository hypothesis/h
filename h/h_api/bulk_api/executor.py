"""Implementations of an 'Executor' responsible for running bulk commands."""
from h.h_api.bulk_api.model.report import Report
from h.h_api.enums import CommandResult, CommandType


class Executor:
    """A callback to provide concrete functionality for actions in BulkJob."""

    def configure(self, config):
        """
        Configure the job from the provided config object.

        :param config: A config object
        :return:
        """
        raise NotImplementedError()

    def execute_batch(self, command_type, data_type, default_config, batch):
        """
        Execute the actions specified, returning any referenced ids.

        The implementer is expected to:

         * Full-fill the action
         * Respect the configuration passed
         * For any objects with an id reference (`$anchor`):
            * Return a dict with the reference to concrete id

        :param command_type: The CommandType being (e.g. UPSERT)
        :param data_type: The DataType being modified
        :param default_config: Configuration which applies to all actions
        :param batch: A list of command objects
        :return: A dict of id de-references
        """
        raise NotImplementedError()

    def get_items(self, data_type, ids, config):
        """
        Retrieve a number of items to report back to the caller.

        The objects returned should be in the same order as sent.

        :param data_type: The data type to retrieve
        :param ids: The ids of the objects to retrieve
        :param config: Any additional config
        :return: An iterable of data objects
        """

        raise NotImplementedError()


class FakeReportExecutor(Executor):
    """An Executor which automatically creates reports.

    To enable items which later on rely on id references, executors are
    expected to return the concrete id when an object is created or found.

    This object fakes this process so you can test to see if the references
    are all valid in your object.
    """

    def configure(self, config):
        pass

    def execute_batch(self, command_type, data_type, default_config, batch):
        """Return fake ids for all items in the batch with id references."""

        fake_status = (
            CommandResult.CREATED
            if command_type is CommandType.CREATE
            else CommandResult.UPDATED
        )

        return [Report(fake_status, _id=index) for index in range(len(batch))]


class DebugExecutor(FakeReportExecutor):
    """An Executor which prints out the objects provided to it."""

    def configure(self, config):
        print(f"Configure {config}")

    def execute_batch(self, command_type, data_type, default_config, batch):
        print(f"Execute {command_type} - {data_type}")
        print("\tConfig", default_config)
        print("\tItems", batch)

        return super().execute_batch(command_type, data_type, default_config, batch)

    def get_items(self, data_type, ids, config):
        print(f"Asked to retrieve {data_type}")
        print("\tIds", ids)
        print("\tConfig", config)

        return super().get_items(data_type, ids, config)
