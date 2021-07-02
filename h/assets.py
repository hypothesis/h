"""View for serving static assets under `/assets`"""

import os.path

from h_assets import Environment, assets_view


def includeme(config):
    h_root = os.path.dirname(__file__)

    assets_env = Environment(
        assets_base_url="/assets",
        bundle_config_path=f"{h_root}/assets.ini",
        manifest_path=f"{h_root}/../build/manifest.json",
    )

    # Store asset environment in registry for use in registering `asset_urls`
    # Jinja2 helper in `app.py`.
    config.registry["assets_env"] = assets_env

    config.add_view(route_name="assets", view=assets_view(assets_env))
