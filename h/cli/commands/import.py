# -*- coding: utf-8 -*-

from os import getenv
import json
from collections import namedtuple

import click
import requests

from h.schemas.annotation_import import AnnotationImportSchema


def err_echo(message):
    click.echo(message, err=True)


def required_envvar(envvar):
    result = getenv(envvar)
    if not result:
        raise click.ClickException('The {} environment variable is required'.format(envvar))
    return result


@click.command('import')
@click.argument('annotation_file', type=click.File('rb'))
def import_annotations(annotation_file):

    token = required_envvar('H_API_TOKEN')
    api_root = required_envvar('H_API_ROOT')
    group_id = required_envvar('H_GROUP')

    debug = bool(getenv('H_DEBUG'))

    auth_headers = {'Authorization': 'Bearer {}'.format(token)}

    api_index = requests.get(api_root).json()

    profile_url = api_index['links']['profile']['read']['url']

    profile = requests.get(profile_url, headers=auth_headers).json()

    err_echo('Importing as {}'.format(profile['userid']))

    create_annotation_url = api_index['links']['annotation']['create']['url']

    with annotation_file:
        raw_annotations = json.load(annotation_file)

    err_echo('{} annotations to import'.format(len(raw_annotations)))

    schema = AnnotationImportSchema()
    validated_annotations = [schema.validate(ann) for ann in raw_annotations]

    top_level = [a for a in validated_annotations if a['motivation'] == 'commenting']
    replies = [a for a in validated_annotations if a['motivation'] == 'replying']
    err_echo('{} top-level annotations'.format(len(top_level)))
    err_echo('{} replies'.format(len(replies)))

    child_map = {annotation['id']: [] for annotation in validated_annotations}
    for reply in replies:
        child_map[reply['target']].append(reply)

    def build_tree(root, override_uri=None):
        """Recursively build a tree of Annotation objects.

        Because we need to assign every reply to have the same target URI as its parent, we need to
        pass the `override_uri` parameter down to subsequent invocations of this function.

        This function pulls in two values from its containing scope: `child_map` and `group_id`.

        """
        uri = override_uri or root['target']
        return Annotation(id=root['id'],
                          group_id=group_id,
                          text=root['body'][0]['value'],
                          uri=uri,
                          children=[build_tree(c, uri) for c in child_map[root['id']]])

    annotation_trees = [build_tree(root) for root in top_level]

    for tree_root in annotation_trees:
        process_tree(create_annotation_url, auth_headers, tree_root, references=[], debug=debug)


class Annotation(namedtuple('Annotation', ['id', 'group_id', 'text', 'uri', 'children'])):
    """An individual annotation for import.

    This class has two purposes: to define how the annotation serialises into an API payload, and to
    track any annotations that directly reference this one. This lets us feed the ID of the
    generated annotation into the `references` fields of its children.

    """

    def payload(self, references):
        permissions = {
                'read': ['group:{}'.format(self.group_id)],
        }
        return {
                'imported_id': self.id,
                'group': self.group_id,
                'permissions': permissions,
                'references': references,
                'tags': [],
                'target': [],
                'text': self.text,
                'uri': self.uri,
        }


def process_tree(create_annotation_url, auth_headers, root, references, debug=False):
    """Recursively process a tree of Annotation objects."""
    created_id = created_annotation_id(create_annotation_url, auth_headers, root, references, debug)
    click.echo('{} {}'.format(root.id, created_id))
    for child in root.children:
        process_tree(create_annotation_url, auth_headers, child, references + [created_id], debug)


def created_annotation_id(create_annotation_url, auth_headers, annotation, references, debug=False):
    """Create an annotation through the API and return the ID assigned."""
    payload = annotation.payload(references)

    if debug:
        err_echo(json.dumps(payload, indent=2))

    create_response = requests.post(create_annotation_url, json=payload, headers=auth_headers)

    if not create_response.ok:
        err_reason = create_response.json().get('reason')
        err_echo('Could not create {}. Error: {}'.format(annotation['id'], err_reason))
        raise click.Abort()
    if debug:
        err_echo(json.dumps(create_response.json(), indent=2))

    return create_response.json()['id']
