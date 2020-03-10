"""Objects for referencing and de-referencing ids."""

from collections import defaultdict

from h.h_api.enums import DataType
from h.h_api.exceptions import UnpopulatedReferenceError


class IdReferences:
    """
    A store of id references which can discover and populate them.

    If we create one object which relies on another (group membership on a
    group) we will not know the id of the group until the group has been
    updated.

    To get around this you can add a temporary id reference to the group,
    e.g. "my_ref" which is swapped for a concrete id when the group is
    created. We can reference this in the group membership with
    `{"$ref": "my_id"}`.

    It's this classes' job to store and fill out these references.
    """

    REF_KEY = "$ref"

    def __init__(self):
        self._ref_to_concrete = defaultdict(dict)

    def fill_out(self, body):
        """
        Find any references to ids in the data and fill them out.

        We are looking for items like this:

            {"type": <data_type>, "id": {"$ref": <id_ref>}}

        If this matching data is found the object will have the `id` field
        set to the concrete id.

        :param body: Raw JSON API compatible data to modify
        :raise UnpopulatedReferenceError: When no concrete reference can be found
        """
        for data_type, id_ref, data_key, data in self._find_references(body):
            data[data_key] = self._get_concrete_id(data_type, id_ref)

    def add_concrete_id(self, data_type, id_ref, concrete_id):
        """
        Add a concrete id for a reference.

        :data_type: Data type of the object being referenced
        :id_ref: The reference string
        :concrete_id: The real id
        """
        data_type = DataType(data_type)

        self._ref_to_concrete[data_type][id_ref] = concrete_id

    def _get_concrete_id(self, data_type, id_ref):
        data_type = DataType(data_type)
        try:
            return self._ref_to_concrete[data_type][id_ref]
        except KeyError:
            raise UnpopulatedReferenceError(data_type, id_ref)

    @classmethod
    def _find_references(cls, body):
        """Search for references in the relationships of an object.

        :param body: Raw JSON API compatible data to search
        :return: A list of tuples with data type, reference, key and parent
        """

        for relationship in body["data"].get("relationships", {}).values():
            relationship = relationship["data"]
            if not isinstance(relationship["id"], dict):
                continue

            id_ref = relationship["id"].get(cls.REF_KEY)
            if id_ref is not None:
                yield (DataType(relationship["type"]), id_ref, "id", relationship)
