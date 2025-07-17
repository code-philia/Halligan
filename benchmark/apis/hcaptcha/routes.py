import os
import json

from flask import Blueprint, render_template, jsonify, request


challenges_path = os.path.join(os.path.dirname(__file__), "challenges.json")
challenges_file = open(challenges_path)
challenges_dict: dict = json.load(challenges_file)
challenges: list = challenges_dict.get("challenges", [])
hcaptcha = Blueprint('hcaptcha', __name__, template_folder="templates", static_folder="static")


@hcaptcha.route('/<id>', methods=["GET"])
def init(id: str):
    return render_template('hcaptcha/index.html', id=id)


@hcaptcha.route('/checkbox.html', methods=["GET"])
def checkbox():
    return render_template('hcaptcha/checkbox.html')


@hcaptcha.route('/challenge_binary.html', methods=["GET"])
def binary():
    return render_template('hcaptcha/challenge_binary.html')


@hcaptcha.route('/challenge_area.html', methods=["GET"])
def area():
    return render_template('hcaptcha/challenge_area.html')


@hcaptcha.route('/challenge/<id>', methods=["GET"])
def request_challenge(id: str):
    id = int(id)
    if id <= 0 or id > len(challenges):
        return jsonify(message=f"Challenge ID must be in range [1, {len(challenges)}]"), 400

    challenge = challenges[id - 1]
    return jsonify(challenge)


@hcaptcha.route("/submit", methods=["POST"])
def submit_challenge():
    content: dict = request.json
    id = content.get("id", None)
    id = int(id)
    state = content.get("state", None)
    challenge_type = content.get("challenge_type", None)

    challenge: dict = challenges[id - 1]
    labels = challenge.get("labels", [])

    solved = False
    match challenge_type:
        case "binary": solved = True if set([i for i, x in enumerate(state) if x]) == set(labels) else False
        case "area": solved = True if labels[0] <= state[0] <= labels[2] and labels[1] <= state[1] <= labels[3] else False
    
    return jsonify(solved=solved, id=id)