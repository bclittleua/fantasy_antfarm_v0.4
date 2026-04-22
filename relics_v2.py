from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

RELIC_SPECS = [
    ("Excalibur", 6, 10, "A blade that makes rulers and rebels alike larger than life."),
    ("The Holy Grail", 4, 12, "A vessel of renewal that steadies the hand that bears it."),
    ("The One Ring", 7, 14, "Power condensed into a whispering circle of gold."),
    ("The Spear of Destiny", 5, 10, "A weapon said to bend the course of wars."),
    ("The Black Blade", 6, 8, "A cursed edge that exalts any killer who holds it."),
    ("The Phoenix Crown", 5, 9, "An ancient diadem that draws followers and ambition."),
]

@dataclass
class Relic:
    id: int
    name: str
    region_id: int
    holder_id: Optional[int] = None
    power_bonus: int = 4
    reputation_bonus: int = 8
    description: str = ""


class RelicMixin:
    def _seed_relics(self, world) -> None:
        chosen = self.rng.sample(list(world.regions.keys()), k=min(4, len(world.regions)))
        for region_id, spec in zip(chosen, RELIC_SPECS[:len(chosen)]):
            name, power_bonus, reputation_bonus, description = spec
            relic = Relic(
                id=world.next_relic_id,
                name=name,
                region_id=region_id,
                holder_id=None,
                power_bonus=power_bonus,
                reputation_bonus=reputation_bonus,
                description=description,
            )
            world.relics[relic.id] = relic
            world.next_relic_id += 1

    def _local_unclaimed_relics(self, region_id: int):
        return [
            relic for relic in self.world.relics.values()
            if relic.holder_id is None and relic.region_id == region_id
        ]

    def _claim_relic(self, actor, relic) -> None:
        if actor.relic_id is not None:
            return
        actor.relic_id = relic.id
        relic.holder_id = actor.id
        actor.reputation += relic.reputation_bonus
        self.world.log(
            f"{actor.short_name()} claims {relic.name} in {self.world.region_name(actor.region_id)}.",
            importance=3,
            category="relic",
        )

    def _drop_relic(self, actor) -> None:
        if actor.relic_id is None:
            return
        relic = self.world.relics.get(actor.relic_id)
        if relic is not None:
            relic.holder_id = None
            relic.region_id = actor.region_id
            self.world.log(
                f"{relic.name} is lost in {self.world.region_name(actor.region_id)} after the fall of {actor.short_name()}.",
                importance=2,
                category="relic",
            )
        actor.relic_id = None

    def _seek_relic(self, actor) -> bool:
        if actor.relic_id is not None:
            return False
        relics = self._local_unclaimed_relics(actor.region_id)
        if not relics:
            return False
        chance = 0.20 + min(0.25, actor.reputation / 400.0)
        if actor.party_id is not None:
            chance += 0.10
        if self.rng.random() < min(0.75, chance):
            relic = max(relics, key=lambda r: (r.power_bonus, r.reputation_bonus))
            self._claim_relic(actor, relic)
            self._spend_action(actor)
            return True
        return False
