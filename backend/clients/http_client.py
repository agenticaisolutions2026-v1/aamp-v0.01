import httpx

http_client = httpx.AsyncClient(
    timeout=30.0
)