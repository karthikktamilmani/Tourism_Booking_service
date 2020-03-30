from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config.update(
    SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/'
)

from app import Bookticket
