import json

from jsonschema import Draft7Validator


with open('bulk_api/instruction.json') as fh:
    schema = json.load(fh)


print(Draft7Validator.check_schema(schema))