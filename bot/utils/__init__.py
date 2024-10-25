from .logger import logger
from .schemas import BoostsInfo


import os

if not os.path.exists(path="sessions"):
    os.mkdir(path="sessions")
