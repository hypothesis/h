"""View for serving static assets under `/assets`."""

import importlib_resources
from h_assets import Environment, assets_view
from pyramid.settings import asbool


def includeme(config):  # pragma: no cover
    auto_reload = asbool(config.registry.settings.get("h.reload_assets", False))
    h_files = importlib_resources.files("h")

    assets_env = Environment(
        assets_base_url="/assets",
        bundle_config_path=h_files / "assets.ini",
        manifest_path=h_files / "../build/manifest.json",
        auto_reload=auto_reload,
    )

    # Store asset environment in registry for use in registering `asset_urls`
    # Jinja2 helper in `app.py`.
    config.registry["assets_env"] = assets_env

    config.add_view(route_name="assets", view=assets_view(assets_env))
