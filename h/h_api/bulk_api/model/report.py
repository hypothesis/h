from h.h_api.enums import CommandResult


class Report:
    # Attach this here for the convenience of the consuming library
    CommandResult = CommandResult

    def __init__(self, outcome, _id):
        if _id is None:
            raise ValueError("Id is required for successful outcomes")

        self.outcome = self.CommandResult(outcome)
        self.id = _id
