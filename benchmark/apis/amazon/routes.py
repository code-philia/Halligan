import os
import json
import math
from flask import Blueprint, render_template, jsonify, request


challenges_path = os.path.join(os.path.dirname( __file__ ), "challenges.json")
challenges_file = open(challenges_path)
challenges_dict: dict = json.load(challenges_file)
challenges: list = challenges_dict.get("challenges", [])
amazon = Blueprint('amazon', __name__, template_folder="templates", static_folder="static")


@amazon.route('/<id>', methods=["GET"])
def test(id: str):
    return render_template('amazon/index.html', id=id)

@amazon.route('/challenge.html', methods=["GET"])
def challenge():
    return render_template('amazon/challenge.html')

@amazon.route('/challenge/<id>', methods=["GET"])
def request_challenge(id: str):
    id = int(id)
    if id <= 0 or id > len(challenges):
        return jsonify(message=f"Challenge ID must be in range [1, {len(challenges)}]"), 400

    challenge = challenges[id - 1]
    return jsonify(challenge)

@amazon.route("/submit", methods=["POST"])
def submit_challenge():
    content: dict = request.json
    id = content.get("id", None)
    id = int(id)
    state = content.get("state", None)
    challenge: dict = challenges[id - 1]
    labels = challenge.get("labels", [])

    distance = math.sqrt((state[0] - labels[0])**2 + (state[1] - labels[1])**2)
    solved = distance < 0.1
    
    return jsonify(solved=solved, id=id)