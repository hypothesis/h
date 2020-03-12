"""A value object for returning database modification results."""

from h.h_api.enums import CommandResult


class Report:
    """A model for reporting the result of database modification."""

    # Attach this here for the convenience of the consuming library
    CommandResult = CommandResult

    def __init__(self, outcome, id_):
        """
        :param outcome: An instance of CommandResult
        :param id_: The id of the resource update
        """
        if id_ is None:
            raise ValueError("Id is required for successful outcomes")

        self.outcome = self.CommandResult(outcome)
        self.id = id_
