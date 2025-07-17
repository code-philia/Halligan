import json


rockstack = json.load(open("./rotated.json")) 
challenges = rockstack["challenges"]

prev_label = 0
for challenge in challenges:
    labels = challenge.get("labels", [])
    challenge["labels"][0] = challenge["labels"][0] + 1

with open("./rotatedv2.json", "w") as f:
    json.dump({"challenges": challenges}, f)