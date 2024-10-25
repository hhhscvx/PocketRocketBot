from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoostsInfo:
    turbo_id: str
    turbo_count: int
    energy_id: str
    energy_count: int


@dataclass(frozen=True, slots=True)
class UpgradesInfo:
    tap_id: str
    energy_id: str
    recharge_id: str
    autopilot_id: str

    tap_upgrade_price: int
    energy_upgrade_price: int
    recharge_upgrade_price: int
    autopilot_upgrade_price: int

    tap_next_level: int
    energy_next_level: int
    recharge_next_level: int
    autopilot_next_level: int
