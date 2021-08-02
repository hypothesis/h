"""View for serving static assets under `/assets`"""

import os.path

import importlib_resources
from h_assets import Environment, assets_view


def includeme(config):
    h_files = importlib_resources.files("h")

    assets_env = Environment(
        assets_base_url="/assets",
        bundle_config_path=h_files / "assets.ini",
        manifest_path=h_files / "../build/manifest.json",
    )

    # Store asset environment in registry for use in registering `asset_urls`
    # Jinja2 helper in `app.py`.
    config.registry["assets_env"] = assets_env

    config.add_view(route_name="assets", view=assets_view(assets_env))
