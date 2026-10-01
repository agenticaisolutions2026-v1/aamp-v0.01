import requests


BASE_URL = "http://127.0.0.1:8000/api/v1"
TIMEOUT = 10

def get(endpoint: str, params: dict | None = None):
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            params=params,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        raise Exception(
            "Unable to connect to the backend. Please ensure the FastAPI server is running."
        )

    except requests.exceptions.Timeout:
        raise Exception(
            "The request timed out. Please try again."
        )

    except requests.exceptions.HTTPError as e:
        raise Exception(
            f"Backend returned an error ({response.status_code}): {response.text}"
        ) from e

    except Exception as e:
        raise Exception(
            f"Unexpected error: {e}"
        ) from e

def post(endpoint: str, payload: dict):
    response = requests.post(
        f"{BASE_URL}{endpoint}",
        json=payload
    )
    response.raise_for_status()
    return response.json()


def put(endpoint: str, payload: dict):
    response = requests.put(
        f"{BASE_URL}{endpoint}",
        json=payload
    )
    response.raise_for_status()
    return response.json()


def delete(endpoint: str):
    response = requests.delete(f"{BASE_URL}{endpoint}")
    response.raise_for_status()
    return response.json()

def patch(endpoint: str, payload: dict):
    response = requests.patch(
        f"{BASE_URL}{endpoint}",
        json=payload,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()