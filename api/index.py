"""Vercel entry point. Every request is rewritten here (see vercel.json) and handled by the studio's own request handler."""
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server  # noqa: E402


class handler(BaseHTTPRequestHandler):
    """Vercel looks for a class named handler. It takes every method from the studio's handler (server.H), so there is one implementation."""


for _name, _value in vars(server.H).items():
    if not _name.startswith("__"):
        setattr(handler, _name, _value)
