import os
import json
import glob

from flask import Blueprint, render_template, jsonify, request


challenge_paths: list[str] = glob.glob(os.path.join(os.path.dirname(__file__), "*.json"))
challenge_dicts: list[dict] = [json.load(open(path)) for path in challenge_paths]
challenge_variants: list[str] = [path.split("/")[-1].replace(".json", "") for path in challenge_paths]
challenges: dict = {variant: challenges.get("challenges", []) for variant, challenges in zip(challenge_variants, challenge_dicts)}
paged = Blueprint('paged', __name__, template_folder="templates", static_folder="static")


@paged.route('/<variant>/<id>', methods=["GET"])
def init(variant: str, id: str):
    return render_template('arkose_paged/index.html', variant=variant, id=id)


@paged.route('/challenge.html', methods=["GET"])
def challenge():
    return render_template('arkose_paged/challenge.html')


@paged.route('/<variant>/<id>/challenge', methods=["GET"])
def request_challenge(variant: str, id: str):
    print(request.path, request.url)
    if variant not in challenges:
        return jsonify(message=f"Challenge variant not found"), 404
    
    id = int(id)
    variant_challenges = challenges.get(variant, [])
    if not (0 < id <= len(variant_challenges)):
        return jsonify(message=f"Challenge ID must be in range [1, {len(variant_challenges)}]"), 400

    challenge = variant_challenges[id - 1]
    return jsonify(challenge)


@paged.route("/<variant>/<id>/submit", methods=["POST"])
def submit_challenge(variant: str, id: str):
    content: dict = request.json
    state = content.get("state", None)
    variant_challenges = challenges.get(variant, [])
    challenge: dict = variant_challenges[int(id) - 1]
    labels = challenge.get("labels", [])

    print(state, labels)

    solved = True if int(state) == labels[0] else False

    return jsonify(solved=solved, id=id)