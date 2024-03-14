import logging

from flask import Flask

app = Flask(__name__)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(name)s - %(levelname)s - \n%(message)s"
)
