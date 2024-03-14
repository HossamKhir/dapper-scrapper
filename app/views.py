import json
import threading

from flask import jsonify, request

from config import app

from .utils import count_patterns_in_urls, log_pattern_mentions


@app.route("/count-patterns", methods=["POST"])
def count_patterns():
    data = request.get_json()

    # Validate input JSON
    if not data or "accounts" not in data or "patterns" not in data:
        return (
            jsonify({"error": "Invalid input format, requires accounts and patterns."}),
            400,
        )

    urls = data["accounts"]
    patterns = data["patterns"]

    counter, errors = count_patterns_in_urls(urls, patterns)

    response = {
        "counter": counter,  # A dictionary of patterns and their counts
        "errors": errors,  # A list of errors, if any occurred
    }

    return jsonify(response), 200


@app.route("/count-patterns-interval", methods=["POST"])
def count_patterns_interval():
    data = request.get_json()

    # Validation of JSON data
    try:
        urls = data["accounts"]
        patterns = data["patterns"]
        interval = int(data["interval"])
    except (KeyError, TypeError, ValueError):
        return json.dumps({"error": "Invalid JSON format"}), 400

    # Starting a new background thread with timed interval
    stop_event = threading.Event()
    background_thread = threading.Thread(
        target=log_pattern_mentions,
        args=(urls, patterns, interval, stop_event),
    )
    background_thread.start()

    return json.dumps({"message": "Pattern counting started."}), 200
