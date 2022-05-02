from uuid import UUID

import click

from h.db.types import URLSafeUUID


@click.group("annotation-id")
def annotation_id():
    """Add utility commands to convert annotation IDS."""


@annotation_id.command("from-urlsafe")
@click.argument("urlsafe_id")
def from_urlsafe(urlsafe_id):
    """Convert an annotation ID from its URL-safe representation."""
    click.echo(str(UUID(URLSafeUUID.url_safe_to_hex(urlsafe_id))))


@annotation_id.command("to-urlsafe")
@click.argument("annotation_id")
def to_urlsafe(annotation_id):  # pylint: disable=redefined-outer-name
    """Convert an annotation ID into its URL-safe representation."""
    click.echo(URLSafeUUID.hex_to_url_safe(UUID(annotation_id).hex))
