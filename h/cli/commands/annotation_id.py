# -*- coding: utf-8 -*-

import click

from uuid import UUID

from h.db.types import _get_hex_from_urlsafe, _get_urlsafe_from_hex


@click.group("annotation-id")
def annotation_id():
    """Utility commands to convert annotation IDS."""


@annotation_id.command("from-urlsafe")
@click.argument("urlsafe_id")
def from_urlsafe(urlsafe_id):
    """Convert an annotation ID from its URL-safe representation."""
    click.echo(str(UUID(_get_hex_from_urlsafe(urlsafe_id))))


@annotation_id.command("to-urlsafe")
@click.argument("annotation_id")
def to_urlsafe(annotation_id):
    """Convert an annotation ID into its URL-safe representation."""
    click.echo(_get_urlsafe_from_hex(UUID(annotation_id).hex))
