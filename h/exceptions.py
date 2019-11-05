class InvalidUserId(Exception):
    def __init__(self, user_id):
        super().__init__(f"User id '{user_id}' is not valid")
