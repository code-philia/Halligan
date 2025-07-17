import os
import json

from flask import Blueprint, render_template, jsonify, request


challenges_path = os.path.join(os.path.dirname(__file__), "challenges.json")
challenges_file = open(challenges_path)
challenges_dict: dict = json.load(challenges_file)
challenges: list = challenges_dict.get("challenges", [])
recaptchav2 = Blueprint('recaptchav2', __name__, template_folder="templates", static_folder="static")


@recaptchav2.route('/<id>', methods=["GET"])
def init(id: str):
    return render_template('recaptchav2/index.html', id=id)


@recaptchav2.route('/checkbox.html', methods=["GET"])
def checkbox():
    return render_template('recaptchav2/checkbox.html')


@recaptchav2.route('/challenge_binary.html', methods=["GET"])
def binary():
    return render_template('recaptchav2/challenge_binary.html')


@recaptchav2.route('/challenge_tile.html', methods=["GET"])
def tile():
    return render_template('recaptchav2/challenge_tile.html')


@recaptchav2.route('/challenge/<id>', methods=["GET"])
def request_challenge(id: str):
    id = int(id)
    if id <= 0 or id > len(challenges):
        return jsonify(message=f"Challenge ID must be in range [1, {len(challenges)}]"), 400

    challenge = challenges[id - 1]
    return jsonify(challenge)


@recaptchav2.route("/submit", methods=["POST"])
def submit_challenge():
    content: dict = request.json
    id = content.get("id", None)
    id = int(id)
    state = content.get("state", None)
    challenge: dict = challenges[id - 1]
    labels = challenge.get("labels", [])

    # Compute sets from the state and labels
    set_state = set([i for i, x in enumerate(state) if x])
    set_labels = set(labels)

    # Compute Jaccard index
    intersection = len(set_state & set_labels)  # |A ∩ B|
    union = len(set_state | set_labels)         # |A ∪ B|

    solved = False
    if union > 0:
        jaccard_index = intersection / union
        solved = True if jaccard_index >= 0.75 else False
    
    return jsonify(solved=solved, id=id)