import asyncio
from pprint import pprint
from random import randint
from time import time
from urllib.parse import unquote

from aiohttp import ClientSession, ClientTimeout
from better_proxy import Proxy
from aiohttp_proxy import ProxyConnector
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView

from bot.utils import logger, BoostsInfo, UpgradesInfo
from bot.config import InvalidSession, settings
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
        try:
            response = await http_client.post(url='https://api-game.whitechain.io/api/login',
                                              json={"init_data": tg_web_data})
            response.raise_for_status()

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while getting Access Token: {error}")
            await asyncio.sleep(delay=3)

    async def equip_ship(self, http_client: ClientSession):
        """
        Надевает корабль, если еще не экипирован
        """
        try:
            response = await http_client.post(
                url=f'https://api-game.whitechain.io/api/select-ship/{settings.SHIP_TO_EQUIP}'
            )

            return await response.json()
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when select ship: {error}")
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

    async def get_upgrades_info(self, http_client: ClientSession) -> UpgradesInfo:
        try:
            response = await http_client.get(url=f'https://api-game.whitechain.io/api/user-current-improvements')
            response.raise_for_status()

            resp_json = await response.json()

            upgrades = resp_json['data']
            taps_info = {}
            energy_info = {}
            recharge_info = {}
            autopilot_info = {}
            for upgrade in upgrades:
                match upgrade['improvement']['name']:
                    case 'Wings':
                        taps_info = upgrade
                    case 'Fuselage':
                        energy_info = upgrade
                    case 'Reactor':
                        recharge_info = upgrade
                    case 'Autopilot':
                        autopilot_info = upgrade

            upgrades_info = UpgradesInfo(
                tap_id=taps_info['improvement']['id'],
                energy_id=energy_info['improvement']['id'],
                recharge_id=recharge_info['improvement']['id'],
                autopilot_id=autopilot_info['improvement']['id'],
                tap_upgrade_price=taps_info['next_level']['points'],
                energy_upgrade_price=energy_info['next_level']['points'],
                recharge_upgrade_price=recharge_info['next_level']['points'],
                autopilot_upgrade_price=autopilot_info['next_level']['points'],
                tap_next_level=taps_info['current_level']['level'] + 1,
                energy_next_level=energy_info['current_level']['level'] + 1,
                recharge_next_level=recharge_info['current_level']['level'] + 1,
                autopilot_next_level=autopilot_info['current_level']['level'] + 1,
            )

            return upgrades_info

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Get Upgrades: {error}")
            await asyncio.sleep(delay=3)

    async def get_multitap_upgrade(self, http_client: ClientSession) -> int:
        try:
            response = await http_client.get(url=f'https://api-game.whitechain.io/api/user-current-improvements')
            response.raise_for_status()

            resp_json = await response.json()

            return resp_json['data'][3]['current_level']['level'] + 1

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
            raise error

    async def check_proxy(self, http_client: ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def run(self, proxy: str | None) -> None:
        access_token_expires_at = 0
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
                        if login['user']['ship'] is None:
                            logger.info(f"Ship is not equipped, try to equip..")
                            await asyncio.sleep(1)
                            await self.equip_ship(http_client)
                            logger.success(f"Ship Equiped!")

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

                    tap_multiply = await self.get_multitap_upgrade(http_client)
                    taps = randint(*settings.RANDOM_TAPS_COUNT) * tap_multiply
                    tapped = await self.send_taps(http_client, taps=taps)

                    if not tapped:
                        continue

                    available_energy = int(tapped.get('current_energy'))
                    balance = int(tapped['current_points'])
                    logger.success(f"{self.session_name} | Successful tapped! | "
                                   f"Balance: <c>{balance}</c> (<g>+{taps}</g>)")

                    boosts_info = await self.get_boosts_info(http_client)
                    upgrades_info = await self.get_upgrades_info(http_client)

                    if (boosts_info.energy_count > 0
                            and available_energy < settings.MIN_AVAILABLE_ENERGY
                            and settings.APPLY_DAILY_ENERGY is True):
                        logger.info(f"{self.session_name} | Sleep 5s before activating the daily energy boost")
                        await asyncio.sleep(delay=5)

                        status = await self.apply_boost(http_client=http_client, boost_id=boosts_info.energy_id)
                        if status:
                            logger.success(f"{self.session_name} | Energy boost applied")

                            await asyncio.sleep(delay=1)
                            continue

                    if boosts_info.turbo_count > 0 and settings.APPLY_DAILY_TURBO is True:
                        logger.info(f"{self.session_name} | Sleep 5s before activating the daily turbo boost")
                        await asyncio.sleep(delay=5)

                        status = await self.apply_boost(http_client=http_client, boost_id=boosts_info.turbo_id)
                        if status:
                            logger.success(f"{self.session_name} | Turbo boost applied")

                            await asyncio.sleep(delay=1)

                    if (settings.AUTO_UPGRADE_TAP is True
                            and balance > upgrades_info.tap_upgrade_price
                            and upgrades_info.tap_next_level <= settings.MAX_TAP_LEVEL):
                        logger.info(
                            f"{self.session_name} | Sleep 5s before upgrade tap to {upgrades_info.tap_next_level} lvl")
                        await asyncio.sleep(delay=5)

                        status = await self.upgrade(http_client=http_client, upgrade_id=upgrades_info.tap_id)
                        if status is True:
                            logger.success(
                                f"{self.session_name} | Tap upgraded to {upgrades_info.tap_next_level} lvl")

                            await asyncio.sleep(delay=1)

                        continue

                    if (settings.AUTO_UPGRADE_ENERGY is True
                            and balance > upgrades_info.energy_upgrade_price
                            and upgrades_info.energy_next_level <= settings.MAX_ENERGY_LEVEL):
                        logger.info(
                            f"{self.session_name} | Sleep 5s before upgrade energy to {upgrades_info.energy_next_level} lvl")
                        await asyncio.sleep(delay=5)

                        status = await self.upgrade(http_client=http_client, upgrade_id=upgrades_info.energy_id)
                        if status is True:
                            logger.success(
                                f"{self.session_name} | Energy upgraded to {upgrades_info.energy_next_level} lvl")

                            await asyncio.sleep(delay=1)

                        continue

                    if (settings.AUTO_UPGRADE_CHARGE is True
                            and balance > upgrades_info.recharge_upgrade_price
                            and (next_autopilot_level := upgrades_info.recharge_next_level) <= settings.MAX_CHARGE_LEVEL):
                        logger.info(
                            f"{self.session_name} | Sleep 5s before upgrade charge to {next_autopilot_level} lvl")
                        await asyncio.sleep(delay=5)

                        status = await self.upgrade(http_client=http_client, upgrade_id=upgrades_info.recharge_id)
                        if status is True:
                            logger.success(f"{self.session_name} | Charge upgraded to {next_autopilot_level} lvl")

                            await asyncio.sleep(delay=1)

                        continue

                    if (settings.AUTO_UPGRADE_AUTOBOT is True
                            and balance > upgrades_info.autopilot_upgrade_price
                            and (next_autopilot_level := upgrades_info.autopilot_next_level) <= settings.MAX_AUTOBOT_LEVEL):
                        logger.info(
                            f"{self.session_name} | Sleep 5s before upgrade autopilot to {next_autopilot_level} lvl")
                        await asyncio.sleep(delay=5)

                        status = await self.upgrade(http_client=http_client, upgrade_id=upgrades_info.autopilot_id)
                        if status is True:
                            logger.success(f"{self.session_name} | Autopilot upgraded to {next_autopilot_level} lvl")

                            await asyncio.sleep(delay=1)

                        continue

                    if available_energy < (settings.MIN_AVAILABLE_ENERGY * tap_multiply):
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
