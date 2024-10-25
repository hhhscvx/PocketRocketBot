from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoostsInfo:
    turbo_id: str
    turbo_count: int
    energy_id: str
    energy_count: int
