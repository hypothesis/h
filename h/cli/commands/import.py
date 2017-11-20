# -*- coding: utf-8 -*-

import click
import json
from datetime import datetime
import strict_rfc3339

from h.schemas.annotation_import import AnnotationImportSchema
from h.models import Annotation


@click.command('import')
@click.pass_context
@click.argument('annotation_file', type=click.File('rb'))
def import_annotations(ctx, annotation_file):
    """Import annotations manually from a file."""
    schema = AnnotationImportSchema()

    with annotation_file:
        raw_annotations = json.load(annotation_file)

    click.echo('{} annotations to import'.format(len(raw_annotations)))

    validated_annotations = [schema.validate(ann) for ann in raw_annotations]

    top_level = [a for a in validated_annotations if a['motivation'] == 'commenting']
    replies = [a for a in validated_annotations if a['motivation'] == 'replying']
    click.echo('{} top-level annotations'.format(len(top_level)))
    click.echo('{} replies'.format(len(replies)))

    def annotation_model(annotation_dict):
        annotation = Annotation()
        annotation.created = datetime.utcfromtimestamp(
                strict_rfc3339.rfc3339_to_timestamp(
                    annotation_dict['created']
                )
            )
        annotation.updated = datetime.utcfromtimestamp(
                strict_rfc3339.rfc3339_to_timestamp(
                    annotation_dict['modified']
                )
            )

        # TODO: validate that this account exists
        annotation.userid = annotation_dict['creator']

        # We've already validated that there's only a single body
        annotation.text = annotation_dict['body'][0]['value']

        annotation.target

        return annotation

    click.echo(annotation_model(top_level[0]))

    # [annotation_model(d) for d in validated_annotations]
