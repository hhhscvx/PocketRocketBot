from .logger import logger
from .schemas import BoostsInfo, UpgradesInfo


import os

if not os.path.exists(path="sessions"):
    os.mkdir(path="sessions")
