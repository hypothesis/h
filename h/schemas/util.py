from __future__ import unicode_literals

import colander
from webob.multidict import MultiDict

from h.schemas.base import ValidationError


def _colander_exception_msg(exc):
    """
    Combine error messages from a :class:`colander.Invalid` exception.

    :type exc: colander.Invalid
    :rtype: str
    """
    msg_dict = exc.asdict()
    for child in exc.children:
        msg_dict.update(child.asdict())
    msg_list = ["{}: {}".format(field, err) for field, err in msg_dict.items()]
    return "\n".join(msg_list)


def _multidict_to_dict(schema, multidict):
    """
    Combine or drop repeated fields in a ``MultiDict`` according to a schema.

    Prepare a query param ``MultiDict`` for validation against a schema by
    converting repeated fields to lists or keeping only the last value.
    """
    dict_ = multidict.dict_of_lists()
    for key, values in dict_.items():
        node = schema.get(key)

        if not node or not isinstance(node.typ, colander.Sequence):
            dict_[key] = values[-1]
    return dict_


def _dict_to_multidict(dict_):
    """Convert a validated query param dict back to a ``MultiDict``."""
    result = MultiDict()
    for key, value in dict_.items():
        if isinstance(value, list):
            for item in value:
                result.add(key, item)
        else:
            result.add(key, value)
    return result


def validate_query_params(schema, params):
    """
    Validate query parameters using a Colander schema.

    Repeated fields in the input are either preserved or discarded except for
    the last value depending on whether the corresponding schema node is
    a sequence.

    :param schema: Colander schema to validate data with.
    :type schema: colander.Schema
    :param params: Query parameter dict, usually `request.params`.
    :type params: webob.multidict.MultiDict
    :rtype: webob.multidict.MultiDict
    :raises ValidationError:
    """
    param_dict = _multidict_to_dict(schema, params)

    try:
        parsed = schema.deserialize(param_dict)
    except colander.Invalid as exc:
        raise ValidationError(_colander_exception_msg(exc))

    return _dict_to_multidict(parsed)
