import requests

MOCK_API_URL = "http://127.0.0.1:5001/api/data"

def call_mock_api():
    """
    Calls the mock API and returns the response.
    """
    try:
        response = requests.get(MOCK_API_URL)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Unexpected status code: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
