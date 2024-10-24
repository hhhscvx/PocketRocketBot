import asyncio
from urllib.parse import unquote

import aiohttp
from better_proxy import Proxy
from aiohttp_proxy import ProxyConnector
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView

from ..utils import logger
from ..config import InvalidSession, settings
from .headers import headers


class Tapper:
    def __init__(self, tg_client: Client) -> None:
        self.session_name = tg_client.name
        self.tg_client = tg_client

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy: Proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            with_tg = True

            if not self.tg_client.is_connected:
                with_tg = False
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer('pocket_rocket_game_bot')
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"{self.session_name} | FloodWait {fl}")
                    logger.info(f"{self.session_name} | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestWebView(
                peer=peer,
                bot=peer,
                platform='android',
                from_bot_menu=False,
                url='https://rocketf.whitechain.io/'
            ))

            auth_url = web_view.url
            query = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            self.user_id = (await self.tg_client.get_me()).id

            if with_tg is False:
                await self.tg_client.disconnect()

            return query

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def login(self, http_client: aiohttp.ClientSession, tg_web_data: str) -> dict:
        try:
            response = await http_client.post(url='https://api-game.whitechain.io/api/login',
                                              json={"init_data": tg_web_data})
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Access Token: {error}")
            await asyncio.sleep(delay=3)