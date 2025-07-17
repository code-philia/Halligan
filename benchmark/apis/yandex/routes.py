from flask import Blueprint

from .text.routes import text
from .kaleidoscope.routes import kaleidoscope

yandex = Blueprint('yandex', __name__)
yandex.register_blueprint(text, url_prefix="/text")
yandex.register_blueprint(kaleidoscope, url_prefix="/kaleidoscope")