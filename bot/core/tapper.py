import asyncio

from pyrogram import Client

from ..utils import logger
from ..config import InvalidSession, settings
from .headers import headers


class Tapper:
    def __init__(self, tg_client: Client) -> None:
        self.session_name = tg_client.name
        self.tg_client = tg_client
