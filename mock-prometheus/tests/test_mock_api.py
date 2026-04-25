from app import app
from mock_data import CPU_OVERVIEW_QUERY, GPU_QUERY


def test_query_returns_demo_vector():
    client = app.test_client()

    response = client.get("/api/v1/query", query_string={"query": CPU_OVERVIEW_QUERY})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["data"]["resultType"] == "vector"
    assert payload["data"]["result"][0]["value"][1] == "42.5"


def test_query_range_returns_demo_matrix():
    client = app.test_client()

    response = client.get(
        "/api/v1/query_range",
        query_string={
            "query": GPU_QUERY,
            "start": "2026-04-22T00:00:00+00:00",
            "end": "2026-04-22T01:00:00+00:00",
            "step": "1m",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["data"]["resultType"] == "matrix"
    assert len(payload["data"]["result"][0]["values"]) >= 2


def test_query_returns_error_for_unsupported_promql():
    client = app.test_client()

    response = client.get("/api/v1/query", query_string={"query": "up"})

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["status"] == "error"
    assert payload["error"] == "Unsupported query"
