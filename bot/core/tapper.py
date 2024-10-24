import asyncio
from urllib.parse import unquote

from aiohttp import ClientSession
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

    async def login(self, http_client: ClientSession, tg_web_data: str) -> dict:
        """
        Сделать проверку что time() < token_expires_at, тогда рефрешить
        Потом в https://api-game.whitechain.io/api/refresh-token передавать refresh_token
        """
        try:
            response = await http_client.post(url='https://api-game.whitechain.io/api/login',
                                              json={"init_data": tg_web_data})
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Access Token: {error}")
            await asyncio.sleep(delay=3)

    async def get_profile_data(self, http_client: ClientSession):
        try:
            response = await http_client.get(url='https://api-game.whitechain.io/api/user')
            response.raise_for_status()

            response_json = await response.json()
            profile_data = response_json['user']

            return profile_data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Profile Data: {error}")
            await asyncio.sleep(delay=3)

    async def get_boosts_info(self, http_client: ClientSession) -> dict:
        """Количество доступных turbo/recharge бустов"""
        try:
            response = await http_client.get(url='https://api-game.whitechain.io/api/user-boosts-status')
            response.raise_for_status()

            response_json = await response.json()
            boosts_info = response_json['data']

            return boosts_info
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Boosts Info: {error}")
            await asyncio.sleep(delay=3)

    async def send_taps(self, http_client: ClientSession, taps: int) -> dict:
        try:
            response = await http_client.post(url='https://api-game.whitechain.io/api/claim-points',
                                              json={'points': taps})
            response.raise_for_status()

            response_json = await response.json()

            return response_json['user']
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Tapping: {error}")
            await asyncio.sleep(delay=3)

    async def apply_boost(self, http_client: ClientSession, boost_id: str) -> list[dict]:
        try:
            response = await http_client.post(url=f'https://api-game.whitechain.io/api/apply-boost/{boost_id}')
            response.raise_for_status()

            response_json = await response.json()

            return response_json['data']
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply Boost: {error}")
            await asyncio.sleep(delay=3)

            return False

    async def claim(self, http_client: ClientSession) -> list[dict]:
        """Просто раз в 24 * 3600 буду клеймить и +вайб"""
        try:
            response = await http_client.post(url='https://api-game.whitechain.io/api/user/daily-rewards/claim')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when claim: {error}")
            await asyncio.sleep(delay=3)
