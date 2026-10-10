"""The map's HTTP API on the local server (`bdo_server.py`): pins so far.

Other programs find the server through `local_server.json` (`app_dirs.py`,
`server_info_file`) and send its token as `Authorization: Bearer <token>`.
docs/map-api.md describes the endpoints. No CORS headers: a web page in a
browser cannot send the token header, so only local programs reach the API.
"""

from __future__ import annotations

import json
from collections.abc import Callable

from aiohttp import web

from map_pins import PIN_TYPES, PinError, PinStore, parse_pin_request

API_PREFIX = "/api/map"


def add_map_api(app: web.Application, token: str, store: Callable[[], PinStore | None]) -> None:
    """Register the map API routes on `app`; `store` returns the pin store, None before the app set it."""
    api = _MapApi(token, store)
    app.router.add_get(f"{API_PREFIX}/pins", api.list_pins)
    app.router.add_post(f"{API_PREFIX}/pins", api.place_pin)
    app.router.add_delete(f"{API_PREFIX}/pins", api.clear_pins)
    app.router.add_delete(f"{API_PREFIX}/pins/{{pin_id}}", api.remove_pin)


def _error(status: int, message: str) -> web.Response:
    return web.json_response({"error": message}, status=status)


class _MapApi:
    def __init__(self, token: str, store: Callable[[], PinStore | None]) -> None:
        self._authorization = f"Bearer {token}"
        self._store = store

    async def list_pins(self, request: web.Request) -> web.Response:
        store = self._checked_store(request)
        return web.json_response({"pins": [pin.to_dict() for pin in store.pins()]})

    async def place_pin(self, request: web.Request) -> web.Response:
        store = self._checked_store(request)
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return _error(400, "the body is not JSON")
        try:
            pin = store.place(parse_pin_request(data))
        except PinError as ex:
            return _error(400, str(ex))
        return web.json_response({"pin": pin.to_dict()}, status=201)

    async def remove_pin(self, request: web.Request) -> web.Response:
        store = self._checked_store(request)
        if not store.remove(request.match_info["pin_id"]):
            return _error(404, "no pin with that id")
        return web.Response(status=204)

    async def clear_pins(self, request: web.Request) -> web.Response:
        """DELETE /pins removes every pin; ?type=player only the pins of that type."""
        store = self._checked_store(request)
        pin_type = request.query.get("type")
        if pin_type is not None and pin_type not in PIN_TYPES:
            return _error(400, f"type must be one of {', '.join(PIN_TYPES)}, got {pin_type!r}")
        return web.json_response({"removed": store.clear(pin_type)})

    def _checked_store(self, request: web.Request) -> PinStore:
        if request.headers.get("Authorization") != self._authorization:
            raise web.HTTPUnauthorized(
                text=json.dumps({"error": "missing or wrong token"}), content_type="application/json"
            )
        store = self._store()
        if store is None:
            raise web.HTTPServiceUnavailable(
                text=json.dumps({"error": "the app has no pin store yet"}), content_type="application/json"
            )
        return store
