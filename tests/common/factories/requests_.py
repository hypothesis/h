import json
from io import BytesIO

import requests
from factory import Factory, Faker, post_generation
from requests.structures import CaseInsensitiveDict


class Response(Factory):
    class Meta:
        model = requests.Response

    encoding = "utf-8"
    status_code = Faker(
        "random_element", elements=[200, 201, 301, 304, 401, 404, 500, 501]
    )

    @post_generation
    def headers(response, _create, headers, **_kwargs):
        """Lower-case all header names. Requests requires this."""
        if headers:
            response.headers = CaseInsensitiveDict(
                {key.lower(): value for key, value in headers.items()}
            )

    @post_generation
    def json_data(response, _create, json_data, **_kwargs):
        """Set raw and content-type if json_data is given."""
        if json_data is not None:
            response.headers.setdefault(
                "content-type", f"application/json; charset={response.encoding}"
            )

            response.raw = json.dumps(json_data)

    @post_generation
    def raw(response, _create, raw, **_kwargs):
        """Encode raw body strings to bytes."""
        raw = response.raw or raw

        if isinstance(raw, str):
            response.raw = BytesIO(raw.encode(response.encoding))

    @classmethod
    def _create(cls, model_class, *_args, **kwargs):
        response = model_class()

        for field, value in kwargs.items():
            setattr(response, field, value)

        return response
