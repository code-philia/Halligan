import os
import json
from flask import Blueprint, render_template, jsonify, request


challenges_path = os.path.join(os.path.dirname( __file__ ), "challenges.json")
challenges_file = open(challenges_path)
challenges_dict: dict = json.load(challenges_file)
challenges: list = challenges_dict.get("challenges", [])
images: list = challenges_dict.get("images", [])
gobang = Blueprint('gobang', __name__, template_folder="templates", static_folder="static")


@gobang.route('/<id>', methods=["GET"])
def test(id: str):
    return render_template('geetest_gobang/index.html', id=id)

@gobang.route('/challenge.html', methods=["GET"])
def challenge():
    return render_template('geetest_gobang/challenge.html')

@gobang.route('/challenge/<id>', methods=["GET"])
def request_challenge(id: str):
    id = int(id)
    if id <= 0 or id > len(challenges):
        return jsonify(message=f"Challenge ID must be in range [1, {len(challenges)}]"), 400

    challenge = challenges[id - 1]
    grid = challenge["grid"]
    challenge["images"] = {item: images[item] for row in grid for item in row}
    
    return jsonify(challenge)

@gobang.route("/submit", methods=["POST"])
def submit_challenge():
    content: dict = request.json
    id = content.get("id", None)
    id = int(id)
    state = content.get("state", None)
    solved = (
        # Rows
        any(len(set(row)) == 1 and row[-1] != 0 for row in state) or 
        # Columns
        any(len(set(col)) == 1 and col[-1] != 0 for col in zip(*state)) or
        # Diagonals
        len(set(state[i][i] for i in range(len(state)))) == 1 and state[0][0] != 0 or
        len(set(state[i][len(state) - i - 1] for i in range(len(state)))) == 1 and state[0][len(state) - 1] != 0
    )
    return jsonify(solved=solved, id=id)