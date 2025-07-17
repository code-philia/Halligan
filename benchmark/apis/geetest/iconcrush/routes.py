import os
import json
from flask import Blueprint, render_template, jsonify, request


challenges_path = os.path.join(os.path.dirname( __file__ ), "challenges.json")
challenges_file = open(challenges_path)
challenges_dict: dict = json.load(challenges_file)
challenges: list = challenges_dict.get("challenges", [])
images: list = challenges_dict.get("images", [])
iconcrush = Blueprint('iconcrush', __name__, template_folder="templates", static_folder="static")


@iconcrush.route('/<id>', methods=["GET"])
def test(id: str):
    return render_template('geetest_iconcrush/index.html', id=id)

@iconcrush.route('/challenge.html', methods=["GET"])
def challenge():
    return render_template('geetest_iconcrush/challenge.html')

@iconcrush.route('/challenge/<id>', methods=["GET"])
def request_challenge(id: str):
    id = int(id)
    if id <= 0 or id > len(challenges):
        return jsonify(message=f"Challenge ID must be in range [1, {len(challenges)}]"), 400

    challenge = challenges[id - 1]
    grid = challenge["grid"]
    challenge["images"] = {item: images[item] for row in grid for item in row}
    
    return jsonify(challenge)

@iconcrush.route("/submit", methods=["POST"])
def submit_challenge():
    content: dict = request.json
    id = content.get("id", None)
    id = int(id)
    state = content.get("state", None)
    solved = any(len(set(row)) == 1 for row in state) or any(len(set(col)) == 1 for col in zip(*state))
    return jsonify(solved=solved, id=id)