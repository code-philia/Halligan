import logging
from logging.handlers import RotatingFileHandler

from apis.amazon import amazon
from apis.baidu import baidu
from apis.botdetect import botdetect
from apis.geetest import geetest
from apis.hcaptcha import hcaptcha
from apis.mtcaptcha import mtcaptcha
from apis.recaptchav2 import recaptchav2
from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import HTTPException

# Optional providers: guard imports so the server can boot without them
arkose = None
lemin = None
tencent = None
yandex = None

try:
    from apis.arkose import arkose as _arkose

    arkose = _arkose
except Exception:
    logging.warning("Optional API 'arkose' not available; skipping registration.")

try:
    from apis.lemin import lemin as _lemin

    lemin = _lemin
except Exception:
    logging.warning("Optional API 'lemin' not available; skipping registration.")

try:
    from apis.tencent import tencent as _tencent

    tencent = _tencent
except Exception:
    logging.warning("Optional API 'tencent' not available; skipping registration.")

try:
    from apis.yandex import yandex as _yandex

    yandex = _yandex
except Exception:
    logging.warning("Optional API 'yandex' not available; skipping registration.")


formatter = logging.Formatter("%(asctime)s - %(message)s")
file_handler = RotatingFileHandler("results.log", maxBytes=5 * 1024 * 1024, backupCount=3)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
results = logging.getLogger("results")
results.setLevel(logging.INFO)
results.addHandler(file_handler)


app: Flask = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok"), 200


@app.after_request
def after_request(response: Response):
    try:
        is_json_response = getattr(response, "is_json", False)
        if not is_json_response and hasattr(response, "content_type"):
            is_json_response = response.content_type and "application/json" in response.content_type
        if is_json_response:
            payload = response.get_json(silent=True) or {}
            if isinstance(payload, dict) and "solved" in payload:
                challenge_id = payload.get("id")
                solved = payload.get("solved")
                results.info(f"Route: {request.base_url}, ID: {challenge_id}, Solved: {solved}")
    except Exception:
        logging.exception("Failed to process after_request logging")
    return response


def handle_exception(e: Exception):
    if isinstance(e, HTTPException):
        return e

    logging.exception("Unhandled exception while processing request")
    return jsonify(message=str(e)), 500


app.register_blueprint(amazon, url_prefix="/amazon")
app.register_blueprint(baidu, url_prefix="/baidu")
app.register_blueprint(botdetect, url_prefix="/botdetect")
app.register_blueprint(geetest, url_prefix="/geetest")
app.register_blueprint(hcaptcha, url_prefix="/hcaptcha")
app.register_blueprint(mtcaptcha, url_prefix="/mtcaptcha")
app.register_blueprint(recaptchav2, url_prefix="/recaptchav2")

if arkose is not None:
    app.register_blueprint(arkose, url_prefix="/arkose")
if lemin is not None:
    app.register_blueprint(lemin, url_prefix="/lemin")
if tencent is not None:
    app.register_blueprint(tencent, url_prefix="/tencent")
if yandex is not None:
    app.register_blueprint(yandex, url_prefix="/yandex")

app.register_error_handler(Exception, handle_exception)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3334, debug=False)
