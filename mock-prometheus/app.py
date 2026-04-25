from __future__ import annotations

from flask import Flask, jsonify, request

from mock_data import build_instant_result, build_range_result

app = Flask(__name__)


def error_response(message: str, status_code: int = 400):
    return (
        jsonify(
            {
                "status": "error",
                "errorType": "bad_data",
                "error": message,
            }
        ),
        status_code,
    )


@app.get("/api/v1/query")
def query():
    promql = request.args.get("query", "")
    result = build_instant_result(promql)
    if result is None:
        return error_response("Unsupported query")

    return jsonify({"status": "success", "data": result})


@app.get("/api/v1/query_range")
def query_range():
    promql = request.args.get("query", "")
    start = request.args.get("start")
    end = request.args.get("end")
    step = request.args.get("step")

    if not start or not end or not step:
        return error_response("start, end and step are required")

    try:
        result = build_range_result(promql, start, end, step)
    except ValueError as exc:
        return error_response(str(exc))

    if result is None:
        return error_response("Unsupported query")

    return jsonify({"status": "success", "data": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)
