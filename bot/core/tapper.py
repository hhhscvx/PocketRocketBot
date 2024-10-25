import asyncio
from random import randint
from time import time
from urllib.parse import unquote

from aiohttp import ClientSession, ClientTimeout
from better_proxy import Proxy
from aiohttp_proxy import ProxyConnector
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView

from ..utils import logger, BoostsInfo
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

    async def refresh_token(self, http_client: ClientSession, refresh_token: str) -> dict:
        try:
            response = await http_client.post(url='https://api-game.whitechain.io/api/refresh-token',
                                              json={"refresh_token": refresh_token})
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

    async def get_boosts_info(self, http_client: ClientSession) -> BoostsInfo:
        try:
            response = await http_client.get(url='https://api-game.whitechain.io/api/user-boosts-status')
            response.raise_for_status()

            response_json = await response.json()
            boosts_info = response_json['data']
            boosts = BoostsInfo(
                turbo_id=boosts_info[0]['id'],
                turbo_count=boosts_info[0]['charges_left'],
                energy_id=boosts_info[1]['id'],
                energy_count=boosts_info[1]['charges_left'],
            )

            return boosts
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

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply Boost: {error}")
            await asyncio.sleep(delay=3)

    async def get_upgrade_price(self, http_client: ClientSession, upgrade_id: str) -> int | None:
        try:
            response = await http_client.get(url=f'https://api-game.whitechain.io/api/user-current-improvements')
            response.raise_for_status()

            resp_json = await response.json()

            for upgrade in resp_json['data']:
                if upgrade['next_level']['id'] == upgrade_id:
                    return upgrade['next_level']['points']

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Get Upgrades: {error}")
            await asyncio.sleep(delay=3)

    async def upgrade(self, http_client: ClientSession, upgrade_id: str) -> dict:
        try:
            response = await http_client.post(url=f'https://api-game.whitechain.io/api/upgrade-ship/{upgrade_id}')
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Upgrade: {error}")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, http_client: ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def run(self, proxy: str | None) -> None:
        access_token_expires_at = 0
        last_claimed_time = 0  # TODO клейм вернуть
        refresh_token = ''

        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        async with ClientSession(headers=headers, connector=proxy_conn) as http_client:
            if proxy:
                await self.check_proxy(http_client=http_client, proxy=proxy)

            while True:
                try:
                    if access_token_expires_at == 0:
                        tg_web_data = await self.get_tg_web_data(proxy=proxy)
                        login = await self.login(http_client=http_client, tg_web_data=tg_web_data)

                        http_client.headers["Authorization"] = f'Bearer {login["token"]}'
                        headers["Authorization"] = f'Bearer {login["token"]}'
                        refresh_token = login['refresh_token']
                        access_token_expires_at = login['refresh_token_expires_at']

                        balance = login['user']['current_points']

                        logger.info(f"{self.session_name} | Login! | Balance: {balance}")
                    elif time() > access_token_expires_at:
                        refresh = await self.refresh_token(http_client, refresh_token=refresh_token)

                        http_client.headers["Authorization"] = f'Bearer {refresh["token"]}'
                        headers["Authorization"] = f'Bearer {refresh["token"]}'
                        refresh_token = refresh['refresh_token']
                        access_token_expires_at = refresh['refresh_token_expires_at']

                        balance = refresh['user']['current_points']

                        logger.info(f"{self.session_name} | Refresh Token | Balance: {balance}")

                    taps = randint(*settings.RANDOM_TAPS_COUNT)
                    tapped = await self.send_taps(http_client, taps=taps)

                    if not tapped:
                        continue

                    available_energy = int(tapped.get('current_energy'))
                    balance = int(tapped['current_points'])
                    logger.success(f"{self.session_name} | Successful tapped! | "
                                   f"Balance: <c>{balance}</c> (<g>+{taps}</g>)")

                    boosts_info = await self.get_boosts_info(http_client)

                    if (boosts_info.energy_count > 0
                            and available_energy < settings.MIN_AVAILABLE_ENERGY
                            and settings.APPLY_DAILY_ENERGY is True):
                        logger.info(f"{self.session_name} | Sleep 5s before activating the daily energy boost")
                        await asyncio.sleep(delay=5)

                        status = await self.apply_boost(http_client=http_client, boost_id=boosts_info.energy_id)
                        if status:
                            logger.success(f"{self.session_name} | Energy boost applied")

                            await asyncio.sleep(delay=1)

                    if boosts_info.turbo_count > 0 and settings.APPLY_DAILY_TURBO is True:
                        logger.info(f"{self.session_name} | Sleep 5s before activating the daily turbo boost")
                        await asyncio.sleep(delay=5)

                        status = await self.apply_boost(http_client=http_client, boost_id=boosts_info.turbo_id)
                        if status:
                            logger.success(f"{self.session_name} | Turbo boost applied")

                            await asyncio.sleep(delay=1)
                            

                    if available_energy < settings.MIN_AVAILABLE_ENERGY:
                        sleep_time = randint(*settings.SLEEP_BY_MIN_ENERGY)
                        logger.info(f"{self.session_name} | Minimum energy reached: {available_energy}")
                        logger.info(f"{self.session_name} | Sleep {sleep_time}s")

                        await asyncio.sleep(delay=sleep_time)

                        continue

                except InvalidSession as error:
                    raise error

                except Exception as error:
                    logger.error(f"{self.session_name} | Unknown error: {error}")
                    await asyncio.sleep(delay=3)

                else:
                    sleep_between_clicks = randint(*settings.SLEEP_BETWEEN_TAP)

                    logger.info(f"Sleep {sleep_between_clicks}s")
                    await asyncio.sleep(delay=sleep_between_clicks)


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
