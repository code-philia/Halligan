import os
import json
from flask import Blueprint, render_template, jsonify, request


challenges_path = os.path.join(os.path.dirname( __file__ ), "challenges.json")
challenges_file = open(challenges_path)
challenges_dict: dict = json.load(challenges_file)
challenges: list = challenges_dict.get("challenges", [])
baidu = Blueprint('baidu', __name__, template_folder="templates", static_folder="static")


@baidu.route('/<id>', methods=["GET"])
def test(id: str):
    return render_template('baidu/index.html', id=id)

@baidu.route('/challenge.html', methods=["GET"])
def challenge():
    return render_template('baidu/challenge.html')

@baidu.route('/challenge/<id>', methods=["GET"])
def request_challenge(id: str):
    id = int(id)
    if id <= 0 or id > len(challenges):
        return jsonify(message=f"Challenge ID must be in range [1, {len(challenges)}]"), 400

    challenge = challenges[id - 1]
    return jsonify(challenge)

@baidu.route("/submit", methods=["POST"])
def submit_challenge():
    content: dict = request.json
    id = content.get("id", None)
    id = int(id)
    state = content.get("state", None)
    challenge: dict = challenges[id - 1]
    labels = challenge.get("labels", [])

    tolerance = 15
    difference = abs(float(state) - labels[0])
    solved = True if difference <= tolerance else False
    
    return jsonify(solved=solved, id=id)