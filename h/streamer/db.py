import logging
from contextlib import contextmanager

from sqlalchemy import text

from h import db

LOG = logging.getLogger(__name__)


def get_session(settings):
    """Get a DB session from the provided settings."""
    return db.Session(bind=db.create_engine(settings["sqlalchemy.url"]))


@contextmanager
def read_only_transaction(session):
    """Wrap a call in a read only transaction context manager."""
    try:
        session.execute(
            text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE READ ONLY DEFERRABLE")
        )

        yield

    except (KeyboardInterrupt, SystemExit):
        session.rollback()
        raise
    except Exception as exc:  # pylint:disable=broad-except
        LOG.warning("Caught exception during streamer transaction:", exc_info=exc)
        session.rollback()
    else:
        session.commit()
    finally:
        session.close()
