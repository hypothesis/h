# -*- coding: utf-8 -*-

import json

import click

from h.schemas.annotation_import import AnnotationImportSchema


@click.command('import')
@click.argument('annotation_file', type=click.File('rb'))
def import_annotations(annotation_file):

    with annotation_file:
        raw_annotations = json.load(annotation_file)

    click.echo('{} annotations to import'.format(len(raw_annotations)))

    schema = AnnotationImportSchema()
    validated_annotations = [schema.validate(ann) for ann in raw_annotations]

    top_level = [a for a in validated_annotations if a['motivation'] == 'commenting']
    replies = [a for a in validated_annotations if a['motivation'] == 'replying']
    click.echo('{} top-level annotations'.format(len(top_level)))
    click.echo('{} replies'.format(len(replies)))

    group_id = 'foobangwibble'

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
        click.echo(json.dumps(top_level_payload(annotation), indent=2))
