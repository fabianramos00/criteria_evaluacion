import httpx


_async_clients: dict[bool, httpx.AsyncClient] = {}
_sync_clients: dict[bool, httpx.Client] = {}


def get_async_client(verify: bool = True) -> httpx.AsyncClient:
    client = _async_clients.get(verify)
    if client is None or client.is_closed:
        client = httpx.AsyncClient(
            verify=verify,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        _async_clients[verify] = client
    return client


def get_sync_client(verify: bool = False) -> httpx.Client:
    client = _sync_clients.get(verify)
    if client is None or client.is_closed:
        client = httpx.Client(
            verify=verify,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        _sync_clients[verify] = client
    return client


async def close_clients() -> None:
    for client in _async_clients.values():
        await client.aclose()
    for client in _sync_clients.values():
        client.close()
    _async_clients.clear()
    _sync_clients.clear()
