from __future__ import annotations

from asgiref.typing import ASGIApplication
from gunicorn.app.base import BaseApplication
from starlette.types import ASGIApp

from fdk_asgi.app import FnApplication


class FnServer(BaseApplication):
    def __init__(self, app: ASGIApplication | ASGIApp, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return FnApplication(self.application)
