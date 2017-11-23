# -*- coding: utf-8 -*-

import json

import click

from h.schemas.annotation_import import AnnotationImportSchema


def err_echo(message):
    click.echo(message, err=True)


@click.command('import')
@click.argument('annotation_file', type=click.File('rb'))
def import_annotations(annotation_file):

    with annotation_file:
        raw_annotations = json.load(annotation_file)

    err_echo('{} annotations to import'.format(len(raw_annotations)))

    schema = AnnotationImportSchema()
    validated_annotations = [schema.validate(ann) for ann in raw_annotations]

    top_level = [a for a in validated_annotations if a['motivation'] == 'commenting']
    replies = [a for a in validated_annotations if a['motivation'] == 'replying']
    group_id = 'foobangwibble'
    err_echo('{} top-level annotations'.format(len(top_level)))
    err_echo('{} replies'.format(len(replies)))

    shared_permissions = {
            'read': ['group:{}'.format(group_id)],
    }

    def top_level_payload(annotation):
        return {
                'group': group_id,
                'permissions': shared_permissions,
                'references': [],
                'tags': [],
                'target': [],
                'text': annotation['body'][0]['value'],
                'uri': annotation['target'],
        }

    for annotation in top_level:
        err_echo(json.dumps(top_level_payload(annotation), indent=2))
