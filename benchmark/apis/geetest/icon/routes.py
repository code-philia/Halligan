import os
import json
from flask import Blueprint, render_template, jsonify, request


challenges_path = os.path.join(os.path.dirname( __file__ ), "challenges.json")
challenges_file = open(challenges_path)
challenges_dict: dict = json.load(challenges_file)
challenges: list = challenges_dict.get("challenges", [])
icon = Blueprint('icon', __name__, template_folder="templates", static_folder="static")


@icon.route('/<id>', methods=["GET"])
def test(id: str):
    return render_template('geetest_icon/index.html', id=id)

@icon.route('/challenge.html', methods=["GET"])
def challenge():
    return render_template('geetest_icon/challenge.html')

@icon.route('/challenge/<id>', methods=["GET"])
def request_challenge(id: str):
    id = int(id)
    if id <= 0 or id > len(challenges):
        return jsonify(message=f"Challenge ID must be in range [1, {len(challenges)}]"), 400

    challenge = challenges[id - 1]
    return jsonify(challenge)

@icon.route("/submit", methods=["POST"])
def submit_challenge():
    content: dict = request.json
    id = content.get("id", None)
    id = int(id)
    state = content.get("state", None)
    challenge: dict = challenges[id - 1]
    labels = challenge.get("labels", [])

    print(state)
    print(labels)

    solved = False
    if len(state) == len(labels): 
        solved = all([label[0] <= mark[0] <= label[2] and label[1] <= mark[1] <= label[3] for mark, label in zip(state, labels)])

    return jsonify(solved=solved, id=id)