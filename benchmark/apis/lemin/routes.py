import os
import json
from flask import Blueprint, render_template, jsonify, request


challenges_path = os.path.join(os.path.dirname( __file__ ), "challenges.json")
challenges_file = open(challenges_path)
challenges_dict: dict = json.load(challenges_file)
challenges: list = challenges_dict.get("challenges", [])
lemin = Blueprint('lemin', __name__, template_folder="templates", static_folder="static")


@lemin.route('/<id>', methods=["GET"])
def init(id: str):
    return render_template('lemin/index.html', id=id)

@lemin.route('/test', methods=["GET"])
def test():
    return render_template('lemin/lemin.html')

@lemin.route('/challenge.html', methods=["GET"])
def challenge():
    return render_template('lemin/challenge.html')

@lemin.route('/challenge/<id>', methods=["GET"])
def request_challenge(id: str):
    id = int(id)
    if id <= 0 or id > len(challenges):
        return jsonify(message=f"Challenge ID must be in range [1, {len(challenges)}]"), 400

    challenge = challenges[id - 1]
    return jsonify(challenge)

@lemin.route("/submit", methods=["POST"])
def submit_challenge():
    content: dict = request.json
    id = content.get("id", None)
    id = int(id)
    state = content.get("state", None)
    challenge: dict = challenges[id - 1]

    with open("./temp.txt", "a") as f:
        f.write(f"{state}\n")

    labels = challenge.get("labels", [])

    solved = False
    if len(state) == len(labels): 
        solved = all([mark == label for mark, label in zip(state, labels)])

    return jsonify(solved=solved, id=id)