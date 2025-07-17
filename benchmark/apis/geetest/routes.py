from flask import Blueprint

from .slide.routes import slide
from .icon.routes import icon
from .iconcrush.routes import iconcrush
from .gobang.routes import gobang


geetest = Blueprint('geetest', __name__)
geetest.register_blueprint(slide, url_prefix="/slide")
geetest.register_blueprint(icon, url_prefix="/icon")
geetest.register_blueprint(iconcrush, url_prefix="/iconcrush")
geetest.register_blueprint(gobang, url_prefix="/gobang")