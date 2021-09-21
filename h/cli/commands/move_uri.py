import click

from h import models
from h.models.document import merge_documents
from h.search.index import BatchIndexer
from h.util import uri


@click.command("move-uri")
@click.option("--old", required=True, help="Old URI with annotations and documents.")
@click.option(
    "--new",
    required=True,
    confirmation_prompt=True,
    help="New URI for matching annotations and documents.",
)
@click.pass_context
def move_uri(ctx, old, new):
    """
    Move annotations and document equivalence data from one URL to another.

    This will **replace** the annotation's ``target_uri`` and all the
    document uri's ``claimant``, plus the matching ``uri`` for self-claim and
    canonical uris.
    """

    request = ctx.obj["bootstrap"]()

    annotations = _fetch_annotations(request.db, old)
    docuris_claimant = _fetch_document_uri_claimants(request.db, old)
    docuris_uri = _fetch_document_uri_canonical_self_claim(request.db, old)

    prompt = (
        "Changing all annotations and document data matching:\n"
        f'"{old}"\nto:\n"{new}"\n'
        f"This will affect {len(annotations)} annotations, {len(docuris_claimant)} "
        f"document uri claimants, and {len(docuris_uri)} document uri self-claims "
        "or canonical uris.\n"
        "Are you sure? [y/N]"
    )
    answer = click.prompt(prompt, default="n", show_default=False)
    if answer != "y":
        print("Aborted")
        return

    for annotation in annotations:
        annotation.target_uri = new

    for docuri in docuris_claimant:
        docuri.claimant = new

    for docuri in docuris_uri:
        docuri.uri = new

    if annotations:
        indexer = BatchIndexer(request.db, request.es, request)
        ids = [a.id for a in annotations]
        indexer.index(ids)

    request.db.flush()

    documents = models.Document.find_by_uris(request.db, [new])
    if documents.count() > 1:
        merge_documents(request.db, documents)

    request.tm.commit()


def _fetch_annotations(session, uri_):
    return (
        session.query(models.Annotation)
        .filter(models.Annotation.target_uri_normalized == uri.normalize(uri_))
        .all()
    )


def _fetch_document_uri_claimants(session, uri_):
    return (
        session.query(models.DocumentURI)
        .filter(models.DocumentURI.claimant_normalized == uri.normalize(uri_))
        .all()
    )


def _fetch_document_uri_canonical_self_claim(session, uri_):
    return (
        session.query(models.DocumentURI)
        .filter(
            models.DocumentURI.uri_normalized == uri.normalize(uri_),
            models.DocumentURI.type.in_(["self-claim", "rel-canonical"]),
        )
        .all()
    )


def _fetch_documents(session, uri_):
    return models.Document.find_by_uris(session, [uri_]).all()
