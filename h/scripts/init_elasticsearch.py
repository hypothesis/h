#!/usr/bin/env python3
"""
Initialize the search index.

Usage:

    python3 -m h.scripts.init_elasticsearch conf/development.ini

"""
import argparse
import os

from pyramid.paster import bootstrap

from h import search


def main():
    parser = argparse.ArgumentParser(description="Initialize the search index.")

    parser.add_argument(
        "config_uri",
        help="the URI to the config file, e.g. 'conf/production.ini'",
    )

    args = parser.parse_args()

    # In production environments a short Elasticsearch request timeout is
    # typically set and initializing a new search index can take longer than
    # the timeout, so override any custom timeout with a high value.
    os.environ["ELASTICSEARCH_CLIENT_TIMEOUT"] = "30"

    with bootstrap(args.config_uri) as env:
        settings = env["registry"].settings
        client = search.get_client(settings)

        print("Initializing Elasticsearch index")
        search.init(client, check_icu_plugin=settings.get("es.check_icu_plugin", True))


if __name__ == "__main__":
    main()
