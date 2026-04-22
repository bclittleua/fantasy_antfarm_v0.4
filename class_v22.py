import random
from dataclasses import dataclass, field
from typing import Any
from enum import Enum
from typing import Dict, List, Optional, Tuple

TIME_OF_DAY = ["Morning", "Midday", "Night"]
MONTH_NAMES = [
    "Dawnsreach", "Rainmoot", "Bloomtide", "Suncrest", "Goldfire", "Highsun",
    "Harvestwane", "Emberfall", "Duskmarch", "Frostturn", "Deepcold", "Yearsend",
]

ALIGNMENT_AXES = {
    "Lawful Good": (1, 1),
    "Neutral Good": (0, 1),
    "Chaotic Good": (-1, 1),
    "Lawful Neutral": (1, 0),
    "True Neutral": (0, 0),
    "Chaotic Neutral": (-1, 0),
    "Lawful Evil": (1, -1),
    "Neutral Evil": (0, -1),
    "Chaotic Evil": (-1, -1),
}
GOOD_ALIGNMENTS = {"Lawful Good", "Neutral Good", "Chaotic Good"}
EVIL_ALIGNMENTS = {"Lawful Evil", "Neutral Evil", "Chaotic Evil"}


class Alignment(Enum):
    LAWFUL_GOOD = "Lawful Good"
    NEUTRAL_GOOD = "Neutral Good"
    CHAOTIC_GOOD = "Chaotic Good"
    LAWFUL_NEUTRAL = "Lawful Neutral"
    TRUE_NEUTRAL = "True Neutral"
    CHAOTIC_NEUTRAL = "Chaotic Neutral"
    LAWFUL_EVIL = "Lawful Evil"
    NEUTRAL_EVIL = "Neutral Evil"
    CHAOTIC_EVIL = "Chaotic Evil"

    @property
    def law_axis(self) -> int:
        if "Lawful" in self.value:
            return 1
        if "Chaotic" in self.value:
            return -1
        return 0

    @property
    def moral_axis(self) -> int:
        if "Good" in self.value:
            return 1
        if "Evil" in self.value:
            return -1
        return 0


class Role(Enum):
    COMMONER = "Commoner"
    FIGHTER = "Fighter"
    WIZARD = "Wizard"
    WARDEN = "Warden"
    BARD = "Bard"


class MonsterKind(Enum):
    GOBLIN = "Goblin"
    GIANT = "Giant"
    DRAGON = "Dragon"
    ANCIENT_HORROR = "Ancient Horror"


class Deity(Enum):
    LORD_OF_DARKNESS = "Lord of Darkness"
    LORD_OF_LIGHT = "Lord of Light"
    GOD_OF_CHANCE = "God of Chance"


@dataclass
class Region:
    id: int
    name: str
    biome: str
    danger: int
    neighbors: List[int] = field(default_factory=list)
    control: int = 0
    order: int = 60
    ruler_id: Optional[int] = None
    polity_id: Optional[int] = None
    contested_by: Optional[int] = None
    under_siege_by: Optional[int] = None
    siege_progress: int = 0
    siege_started_tick: int = -999999
    base_capacity: int = 0
    size_factor: float = 1.0


@dataclass
class Party:
    id: int
    member_ids: List[int] = field(default_factory=list)
    goal: str = "quest"
    name: Optional[str] = None
    leader_id: Optional[int] = None
    is_large_group: bool = False

    def size_tier(self) -> str:
        n = len(self.member_ids)
        if n >= 20:
            return "company"
        if n >= 15:
            return "very_large"
        if n >= 9:
            return "large"
        if n >= 5:
            return "medium"
        return "small"


@dataclass
class PartyHistory:
    id: int
    name: str
    founder_id: Optional[int]
    founded_tick: int
    founder_name: str = "Unknown"
    peak_size: int = 0
    peak_reputation: int = 0
    last_region_id: Optional[int] = None
    active: bool = True
    fate: str = "Active"
    disbanded_tick: Optional[int] = None


@dataclass
class PolityLeaderRecord:
    name: str
    fate: str = "Founder"


@dataclass
class PolityHistory:
    id: int
    name: str
    founded_tick: int
    founder_id: Optional[int]
    founder_name: str = "Unknown"
    current_ruler_id: Optional[int] = None
    current_ruler_name: str = "Unknown"
    alignment: str = "Unknown"
    capital_region_id: Optional[int] = None
    peak_regions: int = 0
    peak_strength: int = 0
    active: bool = True
    fate: str = "Active"
    ended_tick: Optional[int] = None
    leaders: List[PolityLeaderRecord] = field(default_factory=list)


@dataclass
class Actor:
    id: int
    name: str
    role: Role
    alignment: Alignment
    deity: Deity
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    luck: int
    hp: int
    max_hp: int
    region_id: int
    traits: List[str]
    birth_year: int
    birth_month: int
    birth_day: int
    surname: str
    sex: str
    spouse_id: Optional[int] = None
    mother_id: Optional[int] = None
    father_id: Optional[int] = None
    last_birth_tick: int = -999999
    title: Optional[str] = None
    alive: bool = True
    party_id: Optional[int] = None
    kills: int = 0
    recovering: int = 0
    reputation: int = 0
    monster_kills: int = 0
    dragon_kills: int = 0
    horror_kills: int = 0
    giant_kills: int = 0
    regions_defended: int = 0
    regions_oppressed: int = 0
    protects_region: Optional[int] = None
    loyalty: Optional[int] = None
    polity_id: Optional[int] = None
    polity_favor: int = 50
    experience: int = 0
    level: int = 1
    level_bonus_hp: int = 0
    champion_of: Optional[Deity] = None
    converted_followers: int = 0
    champion_rep_steps: int = 0
    death_timestamp: Optional[str] = None
    death_cause: Optional[str] = None
    death_killer_id: Optional[int] = None
    resting_until_tick: int = -1
    duty_shift: int = 0
    relic_id: Optional[int] = None
    fatigue_actions: int = 0
    short_rests_since_long: int = 0
    deity_conviction: int = 50
    governance_ideology: Optional[float] = None
    economic_ideology: Optional[float] = None
    best_friend_id: Optional[int] = None
    nemesis_id: Optional[int] = None
    nemesis_power: int = 0
    revenge_target_id: Optional[int] = None
    revenge_for_actor_id: Optional[int] = None
    retired: bool = False
    retirement_year: Optional[int] = None
    bard_last_song_tick: int = -999999

    def __post_init__(self) -> None:
        if self.governance_ideology is None:
            base = self.alignment.law_axis * 0.45
            stat_pull = ((self.wisdom - 10) * 0.03) + ((self.charisma - 10) * 0.02)
            self.governance_ideology = max(-1.0, min(1.0, base + stat_pull))
        if self.economic_ideology is None:
            base = self.alignment.moral_axis * -0.20
            stat_pull = ((self.intelligence - 10) * 0.03) - ((self.strength - 10) * 0.02) + ((self.wisdom - 10) * 0.01)
            self.economic_ideology = max(-1.0, min(1.0, base + stat_pull))
        self.sync_progression(initial=True)

    @staticmethod
    def level_thresholds() -> List[int]:
        return [0, 100, 250, 500, 900, 1500, 2400]

    def compute_level(self) -> int:
        xp = max(0, int(getattr(self, 'experience', 0)))
        thresholds = self.level_thresholds()
        level = 1
        for i in range(1, len(thresholds)):
            if xp >= thresholds[i]:
                level = i + 1
            else:
                break
        while xp >= thresholds[-1]:
            next_threshold = int(round(thresholds[-1] * 1.6))
            thresholds.append(next_threshold)
            if xp >= next_threshold:
                level += 1
            else:
                break
        return level

    def hp_gain_per_level(self) -> int:
        return max(1, round(self.constitution * 0.25))

    def sync_progression(self, initial: bool = False, reset_base: bool = False) -> None:
        old_bonus = 0 if initial else max(0, getattr(self, 'level_bonus_hp', 0))
        base_max_hp = max(1, getattr(self, 'max_hp', 1) - old_bonus)
        if reset_base:
            base_max_hp = max(1, getattr(self, 'max_hp', base_max_hp))
            old_bonus = 0
        new_level = self.compute_level()
        new_bonus = self.hp_gain_per_level() * max(0, new_level - 1)
        old_hp = getattr(self, 'hp', base_max_hp)
        hp_delta = new_bonus - (0 if initial else getattr(self, 'level_bonus_hp', 0))
        self.level = new_level
        self.level_bonus_hp = new_bonus
        self.max_hp = base_max_hp + new_bonus
        if getattr(self, 'alive', True):
            self.hp = max(1, min(self.max_hp, old_hp + hp_delta))
        else:
            self.hp = 0

    def gain_experience(self, amount: int) -> int:
        amount = max(0, int(amount))
        if amount <= 0:
            return 0
        previous_level = getattr(self, 'level', 1)
        self.experience = max(0, int(getattr(self, 'experience', 0)) + amount)
        self.sync_progression()
        return max(0, self.level - previous_level)

    def ideology_vector(self) -> Tuple[float, float]:
        return (float(self.governance_ideology or 0.0), float(self.economic_ideology or 0.0))

    def ideology_similarity(self, other: "Actor") -> float:
        g1, e1 = self.ideology_vector()
        g2, e2 = other.ideology_vector()
        governance_similarity = 1.0 - min(2.0, abs(g1 - g2)) / 2.0
        economic_similarity = 1.0 - min(2.0, abs(e1 - e2)) / 2.0
        return max(0.0, min(1.0, (governance_similarity + economic_similarity) / 2.0))

    def can_form_bff_with(self, other: "Actor") -> bool:
        if not self.alive or not other.alive:
            return False
        if not self.is_adventurer() or not other.is_adventurer():
            return False
        if self.id == other.id:
            return False
        if self.spouse_id == other.id or other.spouse_id == self.id:
            return True
        if self.is_evil() != other.is_evil():
            if self.is_good() or other.is_good():
                return False
        return self.ideology_similarity(other) >= 0.60 and not self.is_ideological_enemy(other)

    def is_male(self) -> bool:
        return str(self.sex).upper().startswith("M")

    def is_female(self) -> bool:
        return str(self.sex).upper().startswith("F")

    def full_name(self) -> str:
        if self.title:
            return f"{self.name} {self.surname}, {self.title}"
        return f"{self.name} {self.surname}"

    def short_name(self) -> str:
        return f"{self.name} {self.surname}"

    def birth_text(self) -> str:
        return f"{MONTH_NAMES[self.birth_month - 1]} {self.birth_day}"

    def notable_deeds_summary(self) -> str:
        deeds = []
        if self.dragon_kills:
            deeds.append(f"slaying {self.dragon_kills} dragon{'s' if self.dragon_kills != 1 else ''}")
        if self.horror_kills:
            deeds.append(f"destroying {self.horror_kills} ancient horror{'s' if self.horror_kills != 1 else ''}")
        if self.giant_kills:
            deeds.append(f"felling {self.giant_kills} giant{'s' if self.giant_kills != 1 else ''}")
        if self.regions_defended:
            deeds.append(f"defending {self.regions_defended} region{'s' if self.regions_defended != 1 else ''}")
        if self.regions_oppressed:
            deeds.append(f"oppressing {self.regions_oppressed} region{'s' if self.regions_oppressed != 1 else ''}")
        if self.kills and not deeds:
            deeds.append(f"claiming {self.kills} kills")
        return '; '.join(deeds) if deeds else 'living long enough to be remembered'

    def ideology(self) -> Tuple[int, int]:
        return ALIGNMENT_AXES[self.alignment.value]

    def is_adventurer(self) -> bool:
        return self.role is not Role.COMMONER

    def is_good(self) -> bool:
        return self.alignment.value in GOOD_ALIGNMENTS

    def is_evil(self) -> bool:
        return self.alignment.value in EVIL_ALIGNMENTS

    def is_neutral_morality(self) -> bool:
        return self.alignment.value not in GOOD_ALIGNMENTS and self.alignment.value not in EVIL_ALIGNMENTS

    def needs_rest(self) -> bool:
        return self.hp <= max(2, self.max_hp // 2) or self.recovering > 0

    def decline_age(self) -> int:
        if self.role == Role.WIZARD:
            return 80
        if self.role in (Role.FIGHTER, Role.WARDEN, Role.BARD):
            return 55
        return 999

    def retirement_age(self) -> int:
        if self.role == Role.WIZARD:
            return 100
        if self.role in (Role.FIGHTER, Role.WARDEN, Role.BARD):
            return 65
        return 999

    def is_declining_with_age(self, age: int) -> bool:
        return age >= self.decline_age()

    def can_retire(self) -> bool:
        return self.role in (Role.FIGHTER, Role.WARDEN, Role.WIZARD, Role.BARD)

    def mind_score(self) -> int:
        return self.intelligence + self.wisdom

    def level_estimate(self) -> int:
        if self.role == Role.COMMONER:
            return 1
        return max(1, getattr(self, 'level', 1))

    def power_rating(self) -> int:
        base = self.level_estimate() * 3
        base += (self.strength + self.dexterity + self.constitution) // 4
        base += self.reputation // 3
        base += (self.luck - 10) // 3
        base += 4 if self.relic_id is not None else 0
        if self.role == Role.FIGHTER:
            base += (self.strength + self.constitution) // 4
        elif self.role == Role.WIZARD:
            base += (self.intelligence + self.wisdom) // 3
            base += 2
        elif self.role == Role.WARDEN:
            base += (self.dexterity + self.wisdom) // 4
        elif self.role == Role.BARD:
            base += (self.charisma + self.wisdom) // 5
        return max(1, base)

    def can_join_party_with(self, other: "Actor") -> bool:
        if not self.alive or not other.alive:
            return False
        if not self.is_adventurer() or not other.is_adventurer():
            return False
        if self.id == other.id:
            return False

        self_law, self_moral = ALIGNMENT_AXES[self.alignment.value]
        other_law, other_moral = ALIGNMENT_AXES[other.alignment.value]
        law_gap = abs(self_law - other_law)
        moral_gap = abs(self_moral - other_moral)
        return law_gap <= 1 and moral_gap <= 1

    def is_ideological_enemy(self, other: "Actor") -> bool:
        self_law, self_moral = ALIGNMENT_AXES[self.alignment.value]
        other_law, other_moral = ALIGNMENT_AXES[other.alignment.value]
        law_gap = abs(self_law - other_law)
        moral_gap = abs(self_moral - other_moral)
        return law_gap + moral_gap >= 3

    def attitude_toward(self, other: "Actor") -> str:
        if self.id == other.id or not self.alive or not other.alive:
            return "ignore"

        if getattr(self, "champion_of", None) is not None and getattr(other, "champion_of", None) is not None and getattr(self, "champion_of", None) != getattr(other, "champion_of", None):
            return "oppose"

        if self.is_adventurer() and other.role == Role.COMMONER:
            if self.is_good():
                return "protect"
            if self.is_evil():
                return "prey"
            return "ignore"

        if self.role == Role.COMMONER and other.is_adventurer():
            if other.is_evil():
                return "fear"
            if other.is_good():
                return "trust"
            return "ignore"

        if self.is_adventurer() and other.is_adventurer() and self.is_ideological_enemy(other):
            return "oppose"

        return "ignore"


@dataclass
class Polity:
    id: int
    name: str
    alignment: Alignment
    ruler_id: int
    capital_region_id: int
    region_ids: List[int] = field(default_factory=list)
    member_actor_ids: List[int] = field(default_factory=list)
    founded_tick: int = 0
    legitimacy: int = 60
    stability: int = 60
    strength: int = 0
    last_challenge_tick: int = -999999
    last_dragon_tick: int = -999999
    last_horror_tick: int = -999999
    challenge_count: int = 0
    succession_grace_until: int = -999999


@dataclass
class Monster:
    id: int
    name: str
    kind: MonsterKind
    region_id: int
    power: int
    hostility: int
    charisma: int
    intelligence: int
    alive: bool = True
    horde_size: int = 1
    reputation: int = 0
    patron_actor_id: Optional[int] = None
    dragon_color: Optional[str] = None
    dragon_temperament: str = "malevolent"
    age_ticks: int = 0
    monster_xp: int = 0
    retreat_until_tick: int = -1

    def effective_power(self) -> int:
        age_bonus = min(20, self.age_ticks // 180)
        xp_bonus = min(15, self.monster_xp // 3)
        return self.power + max(0, self.horde_size - 1) + age_bonus + xp_bonus


@dataclass
class Event:
    tick: int
    timestamp: str
    text: str
    importance: int = 1
    category: str = "general"


@dataclass
class Commemoration:
    name: str
    month: int
    day: int
    reason: str
    region_id: Optional[int] = None
    actor_id: Optional[int] = None


@dataclass
class World:
    rng: random.Random
    regions: Dict[int, Region]
    actors: Dict[int, Actor]
    monsters: Dict[int, Monster]
    parties: Dict[int, Party]
    polities: Dict[int, Polity] = field(default_factory=dict)
    events: List[Event] = field(default_factory=list)
    commemorations: List[Commemoration] = field(default_factory=list)
    tick: int = 0
    next_party_id: int = 1
    next_polity_id: int = 1
    next_monster_id: int = 1
    seed_used: Optional[str] = None
    generated_by_role: Dict[Role, int] = field(default_factory=lambda: {role: 0 for role in Role})
    generated_monsters_by_kind: Dict[MonsterKind, int] = field(default_factory=lambda: {kind: 0 for kind in MonsterKind})
    souls_by_deity: Dict[Deity, int] = field(default_factory=lambda: {deity: 0 for deity in Deity})
    spawned_horror_titles: set = field(default_factory=set)
    last_horror_spawn_tick: int = -999999
    commoner_births: int = 0
    adventurer_lineage_births: int = 0
    next_actor_id: int = 1
    pair_children_count: Dict[Tuple[int, int], int] = field(default_factory=dict)
    party_history: Dict[int, PartyHistory] = field(default_factory=dict)
    polity_history: Dict[int, PolityHistory] = field(default_factory=dict)
    relics: Dict[int, Any] = field(default_factory=dict)
    next_relic_id: int = 1
    commoner_faith_by_region: Dict[int, Dict[Deity, int]] = field(default_factory=dict)

    def season_name(self, month: int) -> str:
        if month <= 3:
            return "Spring"
        if month <= 6:
            return "Summer"
        if month <= 9:
            return "Autumn"
        return "Winter"

    def current_calendar(self) -> Tuple[int, int, int, str, str]:
        day_index = self.tick // 3
        year = day_index // 360 + 1
        day_of_year = day_index % 360
        month = day_of_year // 30 + 1
        day = day_of_year % 30 + 1
        tod = TIME_OF_DAY[self.tick % 3]
        season = self.season_name(month)
        return year, month, day, tod, season

    def current_timestamp(self) -> str:
        year, month, day, tod, season = self.current_calendar()
        return f"Year {year}, {season}, {MONTH_NAMES[month - 1]} {day}, {tod}"

    def log(self, text: str, importance: int = 1, category: str = "general") -> None:
        self.events.append(Event(tick=self.tick, timestamp=self.current_timestamp(), text=text, importance=importance, category=category))

    def living_actors(self):
        if hasattr(self, "_living_actor_cache"):
            return self._living_actor_cache
        return [a for a in self.actors.values() if a.alive]

    def living_monsters(self):
        if hasattr(self, "_living_monster_cache"):
            return self._living_monster_cache
        return [m for m in self.monsters.values() if m.alive]

    def region_name(self, region_id: int) -> str:
        return self.regions[region_id].name

    def actors_in_region(self, region_id):
        if hasattr(self, "_actors_by_region_cache"):
            return self._actors_by_region_cache.get(region_id, [])
        return [a for a in self.living_actors() if a.region_id == region_id]

    def monsters_in_region(self, region_id):
        if hasattr(self, "_monsters_by_region_cache"):
            return self._monsters_by_region_cache.get(region_id, [])
        return [m for m in self.living_monsters() if m.region_id == region_id]

    def adjust_region_state(self, region_id: int, control_delta: int = 0, order_delta: int = 0) -> None:
        region = self.regions[region_id]
        region.control = max(-100, min(100, region.control + control_delta))
        region.order = max(0, min(100, region.order + order_delta))

    def evaluate_region_rule(self, region_id: int) -> None:
        region = self.regions[region_id]
        local = [actor for actor in self.actors_in_region(region_id) if actor.is_adventurer()]
        if not local:
            region.ruler_id = None
            return

        ranked = sorted(local, key=lambda actor: (actor.reputation, actor.kills, actor.power_rating(), actor.charisma), reverse=True)
        candidate = ranked[0]
        if abs(region.control) >= 30 and region.order >= 25 and candidate.reputation >= 10:
            region.ruler_id = candidate.id
        else:
            region.ruler_id = None

    def add_commemoration(self, name: str, month: int, day: int, reason: str, region_id: Optional[int] = None, actor_id: Optional[int] = None) -> None:
        for item in self.commemorations:
            if item.name == name and item.month == month and item.day == day and item.region_id == region_id:
                return
        self.commemorations.append(
            Commemoration(name=name, month=month, day=day, reason=reason, region_id=region_id, actor_id=actor_id)
        )

    def commemorations_today(self) -> List[Commemoration]:
        _, month, day, _, _ = self.current_calendar()
        return [item for item in self.commemorations if item.month == month and item.day == day]


    def _ensure_party_history(self, party: Party) -> None:
        if party.id in self.party_history:
            return
        leader = self.actors.get(party.leader_id) if party.leader_id is not None else None
        self.party_history[party.id] = PartyHistory(
            id=party.id,
            name=party.name or f"Party {party.id}",
            founder_id=party.leader_id,
            founder_name=leader.short_name() if leader is not None else "Unknown",
            founded_tick=self.tick,
            peak_size=len(party.member_ids),
            peak_reputation=sum(self.actors[mid].reputation for mid in party.member_ids if mid in self.actors),
            last_region_id=leader.region_id if leader is not None else None,
        )

    def _update_party_history(self, party: Party) -> None:
        self._ensure_party_history(party)
        hist = self.party_history[party.id]
        hist.name = party.name or hist.name
        hist.peak_size = max(hist.peak_size, len(party.member_ids))
        hist.peak_reputation = max(hist.peak_reputation, sum(self.actors[mid].reputation for mid in party.member_ids if mid in self.actors))
        leader = self.actors.get(party.leader_id) if party.leader_id is not None else None
        if leader is not None:
            hist.last_region_id = leader.region_id

    def archive_party(self, party: Party, fate: str) -> None:
        self._ensure_party_history(party)
        hist = self.party_history[party.id]
        if hist.active:
            hist.active = False
            hist.fate = fate
            hist.disbanded_tick = self.tick
        for mid in list(party.member_ids):
            actor = self.actors.get(mid)
            if actor is not None:
                actor.party_id = None
                actor.loyalty = None
        self.parties.pop(party.id, None)

    def _ensure_polity_history(self, polity: Polity) -> None:
        if polity.id in self.polity_history:
            return
        founder = self.actors.get(polity.ruler_id)
        founder_name = founder.short_name() if founder is not None else "Unknown"
        self.polity_history[polity.id] = PolityHistory(
            id=polity.id,
            name=polity.name,
            founded_tick=polity.founded_tick,
            founder_id=polity.ruler_id,
            founder_name=founder_name,
            current_ruler_id=polity.ruler_id,
            current_ruler_name=founder_name,
            alignment=polity.alignment.value,
            capital_region_id=polity.capital_region_id,
            peak_regions=len(polity.region_ids),
            peak_strength=polity.strength,
            leaders=[PolityLeaderRecord(name=founder_name, fate="Founder")],
        )

    def _update_polity_history(self, polity: Polity) -> None:
        self._ensure_polity_history(polity)
        hist = self.polity_history[polity.id]
        hist.name = polity.name
        hist.peak_regions = max(hist.peak_regions, len(polity.region_ids))
        hist.peak_strength = max(hist.peak_strength, polity.strength)
        ruler = self.actors.get(polity.ruler_id)
        if ruler is not None:
            hist.current_ruler_id = ruler.id
            hist.current_ruler_name = ruler.short_name()
            if not hist.leaders:
                hist.leaders.append(PolityLeaderRecord(name=ruler.short_name(), fate="Founder"))
            elif hist.leaders[-1].name != ruler.short_name():
                hist.leaders.append(PolityLeaderRecord(name=ruler.short_name(), fate="Current ruler"))
            else:
                hist.leaders[-1].fate = "Current ruler" if hist.active else hist.leaders[-1].fate

    def archive_polity(self, polity: Polity, fate: str) -> None:
        self._ensure_polity_history(polity)
        hist = self.polity_history[polity.id]
        if hist.active:
            hist.active = False
            hist.fate = fate
            hist.ended_tick = self.tick
        self.polities.pop(polity.id, None)

    def generate_party_name(self, leader: Actor, region_id: int) -> str:
        good_words = ["Wardens", "Shield", "Dawn", "Watch", "Lantern"]
        evil_words = ["Black", "Dominion", "Pact", "Fang", "Hand"]
        neutral_words = ["Company", "Band", "Order", "Road", "Circle"]
        suffixes = ["Company", "Pact", "Watch", "Band", "Circle", "Host"]
        place = self.region_name(region_id)
        if leader.is_good():
            if self.rng.random() < 0.5:
                return f"{self.rng.choice(good_words)} of {place}"
            return f"{place} {self.rng.choice(suffixes)}"
        if leader.is_evil():
            if self.rng.random() < 0.5:
                return f"{self.rng.choice(evil_words)} {self.rng.choice(suffixes)}"
            return f"{leader.surname}'s {self.rng.choice(suffixes)}"
        if self.rng.random() < 0.5:
            return f"{self.rng.choice(neutral_words)} of {place}"
        return f"{place} {self.rng.choice(suffixes)}"

    def remove_from_party(self, actor: Actor) -> None:
        if actor.party_id is None:
            return
        party = self.parties.get(actor.party_id)
        if party and actor.id in party.member_ids:
            party.member_ids.remove(actor.id)
        actor.party_id = None
        actor.loyalty = None
        if party and len(party.member_ids) <= 1:
            self.archive_party(party, "Collapsed after attrition")

    def cleanup_parties(self) -> None:
        for party_id in list(self.parties.keys()):
            party = self.parties[party_id]
            party.member_ids = [mid for mid in party.member_ids if self.actors[mid].alive]
            for mid in party.member_ids:
                self.actors[mid].party_id = party_id
            if len(party.member_ids) >= 6:
                party.is_large_group = True
            self._update_party_history(party)
            if len(party.member_ids) <= 1:
                self.archive_party(party, "Collapsed after attrition")
    
    def _transfer_party_leadership(self, party: Party, successor: Actor, fate_note: Optional[str] = None) -> None:
        party.leader_id = successor.id
        successor.loyalty = successor.id
        for mid in party.member_ids:
            actor = self.actors.get(mid)
            if actor is None or not actor.alive:
                continue
            actor.party_id = party.id
            if actor.id != successor.id:
                actor.loyalty = successor.id
        self._update_party_history(party)
        if fate_note:
            hist = self.party_history.get(party.id)
            if hist is not None and hist.fate == "Active":
                hist.fate = fate_note

    def create_party(self, members: List[Actor], goal: str = "quest") -> Optional[Party]:
        unique_members = []
        seen = set()
        for member in members:
            if member.alive and member.id not in seen:
                unique_members.append(member)
                seen.add(member.id)
        if len(unique_members) < 2:
            return None

        party = Party(id=self.next_party_id, goal=goal)
        self.next_party_id += 1
        self.parties[party.id] = party
        party.leader_id = unique_members[0].id

        for member in unique_members:
            self.remove_from_party(member)
            member.party_id = party.id
            member.loyalty = party.leader_id
            party.member_ids.append(member.id)

        if len(party.member_ids) >= 3:
            party.name = self.generate_party_name(unique_members[0], unique_members[0].region_id)
        if len(party.member_ids) >= 6:
            party.is_large_group = True
        self._ensure_party_history(party)
        self._update_party_history(party)

        names = ", ".join(self.actors[mid].short_name() for mid in party.member_ids)
        if party.name:
            self.log(f"A party forms in {self.region_name(unique_members[0].region_id)}: {party.name} ({names}).", importance=2, category="party")
        else:
            self.log(f"A party forms in {self.region_name(unique_members[0].region_id)}: {names}.", importance=2, category="party")
        return party

    def get_party(self, actor: Actor) -> Optional[Party]:
        if actor.party_id is None:
            return None
        return self.parties.get(actor.party_id)

    def create_polity(self, ruler: Actor, capital_region_id: int, member_ids: List[int]) -> Optional[Polity]:
        polity = Polity(
            id=self.next_polity_id,
            name=self.generate_polity_name(ruler, capital_region_id),
            alignment=ruler.alignment,
            ruler_id=ruler.id,
            capital_region_id=capital_region_id,
            region_ids=[capital_region_id],
            member_actor_ids=list(dict.fromkeys(member_ids)),
            founded_tick=self.tick,
            legitimacy=min(100, 50 + ruler.reputation // 2),
            stability=60,
        )
        self.next_polity_id += 1
        self.polities[polity.id] = polity
        self.regions[capital_region_id].polity_id = polity.id
        self.regions[capital_region_id].contested_by = None
        self.regions[capital_region_id].ruler_id = ruler.id
        ruler.polity_id = polity.id
        ruler.loyalty = ruler.id
        for actor_id in polity.member_actor_ids:
            actor = self.actors.get(actor_id)
            if actor and actor.alive and not (ruler.is_good() and actor.is_evil()) and not (ruler.is_evil() and actor.is_good()):
                actor.polity_id = polity.id
                actor.loyalty = ruler.id
        self._ensure_polity_history(polity)
        self._update_polity_history(polity)
        party = self.get_party(ruler)
        if party is not None:
            self.archive_party(party, f"Founded {polity.name}")
        self.log(f"{ruler.short_name()} founds {polity.name} in {self.region_name(capital_region_id)}.", importance=3, category="polity")
        return polity

    def generate_polity_name(self, ruler: Actor, region_id: int) -> str:
        place = self.region_name(region_id)
        if ruler.is_good():
            return f"Kingdom of {place}"
        if ruler.is_evil():
            return f"{ruler.surname}'s Dominion"
        return f"Freehold of {place}"


    def side_members(self, actor: Actor) -> List[Actor]:
        party = self.get_party(actor)
        if party is None:
            return [actor] if actor.alive else []
        return [self.actors[mid] for mid in party.member_ids if self.actors[mid].alive]

    def side_power(self, actor: Actor) -> int:
        return sum(member.power_rating() for member in self.side_members(actor))

    def side_charisma(self, actor: Actor) -> float:
        members = self.side_members(actor)
        if not members:
            return 0.0
        return sum(member.charisma for member in members) / len(members)

    def side_mind(self, actor: Actor) -> float:
        members = self.side_members(actor)
        if not members:
            return 0.0
        return sum(member.mind_score() for member in members) / len(members)





def normalized_pair_key(a_id: int, b_id: int) -> Tuple[int, int]:
    if a_id <= b_id:
        return (a_id, b_id)
    return (b_id, a_id)
