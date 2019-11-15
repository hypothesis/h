class InvalidUserId(Exception):
    """The userid does not meet the expected pattern."""

    def __init__(self, user_id):
        super().__init__(f"User id '{user_id}' is not valid")
