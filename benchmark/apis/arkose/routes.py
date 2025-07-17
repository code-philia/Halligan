from flask import Blueprint

from .multichoice.routes import multichoice
from .paged.routes import paged

arkose = Blueprint('arkose', __name__)
arkose.register_blueprint(multichoice, url_prefix="/multichoice")
arkose.register_blueprint(paged, url_prefix="/paged")