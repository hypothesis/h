# -*- coding: utf-8 -*-
import re
from raven.handlers.logging import SentryHandler


class FilteredSentryHandler(SentryHandler):
    """Applies an exception filter to the built in raven Sentry Handler."""

    # a tuple of exceptions to not send to Sentry
    IGNORE_EXCEPTIONS = (re.compile('ReadTimeout: HTTPConnectionPool\(.*Read timed out.*'),)

    def can_record(self, record):
        """
        Decides whether to record the record in Sentry.

        Returns True if the record can be recorded by Sentry.
        Returns False if the record is not to be recorded by
        Sentry and instead simply sent to std.out.
        """
        do_record = super(FilteredSentryHandler, self).can_record(record)
        # If pre-existing logic says not to record it avoid wasting time and simply return early.
        if not do_record:
            return do_record
        # if the record is in the ignore exceptions don't record it in Sentry
        exc_message = '{}: {}'.format(type(record.exc_info[1]).__name__, record.exc_info[1])
        for ignore_exc in self.IGNORE_EXCEPTIONS:
            if ignore_exc.match(exc_message):
                return False
        return do_record
