# -*- coding: utf-8 -*-
# Taken from:
# https://pyramid-cookbook.readthedocs.org/en/latest/templates/customrenderers.html
# with minor modifications
import unicodecsv as csv
from h._compat import StringIO


class CSV(object):
    def __init__(self, info):
        pass

    def __call__(self, value, system):
        """ Returns a plain CSV-encoded string with content-type
        ``text/csv``. The content-type may be overridden by
        setting ``request.response.content_type``."""

        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = 'text/csv'

        fout = StringIO()
        writer = csv.writer(fout,
                            delimiter=',',
                            quotechar=',',
                            quoting=csv.QUOTE_MINIMAL)

        writer.writerow(value.get('header', []))
        writer.writerows(value.get('rows', []))

        return fout.getvalue()
