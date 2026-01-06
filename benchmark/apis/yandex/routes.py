from flask import Blueprint

from .kaleidoscope.routes import kaleidoscope
from .text.routes import text

yandex = Blueprint("yandex", __name__)
yandex.register_blueprint(text, url_prefix="/text")
yandex.register_blueprint(kaleidoscope, url_prefix="/kaleidoscope")
