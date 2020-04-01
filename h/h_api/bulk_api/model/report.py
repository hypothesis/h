"""A value object for returning database modification results."""


class Report:
    """A model for reporting the result of database modification."""

    def __init__(self, id_, public_id=None):
        """
        :param id_: The id of the updated resource
        :param public_id: The user friendly id of the resource
        """
        if id_ is None:
            raise ValueError("id_ is required for successful outcomes")

        self.id = id_
        self.public_id = id_ if public_id is None else public_id

    def __repr__(self):
        return f"<{self.__class__.__name__}: '{self.id}' ({self.public_id})>"
