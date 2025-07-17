import os
import json

from flask import Blueprint, render_template, jsonify, request


challenges_path = os.path.join(os.path.dirname(__file__), "challenges.json")
challenges_file = open(challenges_path)
challenges_dict: dict = json.load(challenges_file)
challenges: list = challenges_dict.get("challenges", [])
botdetect = Blueprint('botdetect', __name__, template_folder="templates", static_folder="static")


@botdetect.route('/<id>', methods=["GET"])
def init(id: str):
    return render_template('botdetect/index.html', id=id)


@botdetect.route('/challenge/<id>', methods=["GET"])
def request_challenge(id: str):
    id = int(id)
    if id <= 0 or id > len(challenges):
        return jsonify(message=f"Challenge ID must be in range [1, {len(challenges)}]"), 400

    challenge = challenges[id - 1]
    return jsonify(challenge)


@botdetect.route("/submit", methods=["POST"])
def submit_challenge():
    content: dict = request.json
    id = content.get("id", None)
    id = int(id)
    state: str = content.get("state", "")
    challenge: dict = challenges[id - 1]
    labels: list[str] = challenge.get("labels", [])

    solved = True if labels[0].lower() == state.lower() else False
    return jsonify(solved=solved, id=id)