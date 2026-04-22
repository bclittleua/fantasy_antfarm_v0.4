from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import argparse
from fractions import Fraction
import random
import time
from typing import Dict, List, Optional, Tuple
import importlib.util
import sys
from pathlib import Path
from class_v22 import (
    Alignment, Role, MonsterKind, Deity,
    Region, Party, Actor, Monster, Event,
    Commemoration, World, Polity, PolityLeaderRecord,
)

BASE_DIR = Path(__file__).resolve().parent
SUMMARY_MODULE_PATH = BASE_DIR / "summary_v30.py"
POPULATION_MODULE_PATH = BASE_DIR / "population_v11.py"
LEGACY_MODULE_PATH = BASE_DIR / "legacy_v6.py"
RELICS_MODULE_PATH = BASE_DIR / "relics_v2.py"
#Do not forget class_v22.py (imported above)

def _import_module_from_path(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name!r} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _parse_population_scale(raw: str) -> float:
    text = str(raw).strip()
    if not text:
        raise argparse.ArgumentTypeError("Population scale cannot be empty.")
    try:
        scale = float(Fraction(text))
    except Exception as exc:
        raise argparse.ArgumentTypeError(
            "Population scale must be a positive number or fraction like 2, 0.25, or 1/4."
        ) from exc
    if scale <= 0:
        raise argparse.ArgumentTypeError("Population scale must be greater than 0.")
    return scale




def _make_run_output_dir(seed: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in str(seed))
    safe = safe.strip("._") or "seed"
    return BASE_DIR / "seedRuns_v71" / safe

summary = _import_module_from_path("fantfarm_summary", SUMMARY_MODULE_PATH)
population_module = _import_module_from_path("fantfarm_population", POPULATION_MODULE_PATH)
PopulationMixin = population_module.PopulationMixin
legacy_module = _import_module_from_path("fantfarm_legacy", LEGACY_MODULE_PATH)
LegacyMixin = legacy_module.LegacyMixin
relic_module = _import_module_from_path("fantfarm_relics", RELICS_MODULE_PATH)
RelicMixin = relic_module.RelicMixin
Relic = relic_module.Relic
RELIC_SPECS = relic_module.RELIC_SPECS

party_runtime_module = _import_module_from_path("fantfarm_party_runtime", BASE_DIR / "sim_party_v2.py")
PartyMixin = party_runtime_module.PartyMixin
politics_runtime_module = _import_module_from_path("fantfarm_politics_runtime", BASE_DIR / "sim_politics_v9.py")
PoliticsMixin = politics_runtime_module.PoliticsMixin
monster_runtime_module = _import_module_from_path("fantfarm_monster_runtime", BASE_DIR / "sim_monsters_v3.py")
MonsterMixin = monster_runtime_module.MonsterMixin
combat_runtime_module = _import_module_from_path("fantfarm_combat_runtime", BASE_DIR / "sim_combat_v5.py")
CombatMixin = combat_runtime_module.CombatMixin
world_runtime_module = _import_module_from_path("fantfarm_world_runtime", BASE_DIR / "sim_world_v2.py")
WorldBuildMixin = world_runtime_module.WorldBuildMixin

DEFAULT_SEED = None
REGION_COUNT = 13 #default 12
INITIAL_POPULATION = 10000 #default 500
TICKS_PER_YEAR = 1080 #default 1080
DEFAULT_YEARS = 1 #default 1
VERBOSE_EVENT_IMPORTANCE = 1 #default 1
WIZARD_PROMOTION_CHANCE = 0.01 #default 0.02
MAX_WILD_GIANTS = 13
MAX_WILD_DRAGONS = 3
DRAGON_REPRO_CHANCE = 0.005
HORROR_UNIQUE = True
BENEVOLENT_DRAGONS = {"White", "Blue"}
AMBIVALENT_DRAGONS = {"Green", "Red"}
ACTIONS_PER_TICK = 1
COMBAT_COOLDOWN_TICKS = 4
ADVENTURER_SHIFT_COUNT = 3
POST_BATTLE_REST_MIN = 12
POST_BATTLE_REST_MAX = 36
POST_ROUT_REST_MIN = 24
POST_ROUT_REST_MAX = 72
POST_MONSTER_REST_MIN = 18
POST_MONSTER_REST_MAX = 48
POST_LEGENDARY_REST_MIN = 60
POST_LEGENDARY_REST_MAX = 180
MONSTER_AGE_POWER_STEP_TICKS = 180
MONSTER_MAX_AGE_BONUS = 20
MONSTER_XP_POWER_STEP = 3
MONSTER_MAX_XP_BONUS = 15
MONSTER_LOW_HP_RETREAT_RATIO = 0.50
MONSTER_CRITICAL_HP_RETREAT_RATIO = 0.30
MONSTER_RETREAT_AVOID_RATIO = 1.25
MONSTER_RETREAT_COOLDOWN_MIN = 12
MONSTER_RETREAT_COOLDOWN_MAX = 36
MONSTER_SHORT_REST_MIN = 12
MONSTER_SHORT_REST_MAX = 36
MONSTER_LONG_REST_MIN = 48
MONSTER_LONG_REST_MAX = 144
MONSTER_POST_RAID_REST_MIN = 18
MONSTER_POST_RAID_REST_MAX = 54
MONSTER_TERROR_ORDER_DECAY_INTERVAL = 30
MONSTER_COMMONER_RAID_BASE = 0.04
MONSTER_COMMONER_RAID_SCALE = 0.003
SHORT_REST_FATIGUE_THRESHOLD = 3
LONG_REST_FATIGUE_THRESHOLD = 6
SHORT_RESTS_BEFORE_LONG = 2
SHORT_REST_MIN = 6
SHORT_REST_MAX = 18
LONG_REST_MIN = 30
LONG_REST_MAX = 90
LEADER_LONG_REST_MIN = 18
LEADER_LONG_REST_MAX = 54
POLITY_MIN_REPUTATION = 120
POLITY_MIN_PARTY_SIZE = 30
PARTY_FOUNDING_PERCENTILE = 0.80
PARTY_FOUNDING_MIN_MEMBERS = 3
EVIL_PARTY_COUP_CHECK_TICKS = 30
EVIL_PARTY_COUP_BASE_CHANCE = 0.05
EVIL_PARTY_COUP_REP_MARGIN = 12
EVIL_POLITY_EXTRA_CHALLENGE_PRESSURE = 0.05
POLITY_REGION_CLAIM_MIN_REPUTATION = 80
FAILED_COUP_REP_LOSS = 18
FAILED_COUP_FAVOR_LOSS = 35
FAILED_ASSASSINATION_REP_LOSS = 12
FAILED_ASSASSINATION_FAVOR_LOSS = 30
FAILED_REVOLT_REP_LOSS = 10
FAILED_REVOLT_FAVOR_LOSS = 20
CROSS_POLITY_PARTY_FAVOR_LOSS = 6
CROSS_POLITY_PARTY_FAVOR_LOSS_FOLLOWER = 2
MIXED_POLITY_PARTY_LEADER_FAVOR_LOSS = 8
MIXED_POLITY_PARTY_FOLLOWER_FAVOR_LOSS = 3
POLITY_CHALLENGE_CHECK_TICKS = 30
POLITY_CHALLENGE_COOLDOWN_TICKS = 120
SUCCESSION_GRACE_TICKS = 180
ASSASSINATION_GUARD_PER_PARTY_MEMBER = 2
ASSASSINATION_GUARD_PER_LOCAL_LOYALIST = 3
ASSASSINATION_LEGITIMACY_WEIGHT = 0.25
DRAGON_ATTRACTION_MIN_REGIONS = 3
DRAGON_ATTRACTION_MIN_COMMONERS = 400
DRAGON_ATTRACTION_COOLDOWN_TICKS = 180
ANCIENT_HORROR_DOMINANCE_RATIO = 0.5
ANCIENT_HORROR_COOLDOWN_TICKS = 540
ANCIENT_HORROR_WORLD_COOLDOWN_TICKS = TICKS_PER_YEAR * 25
DIVINE_CHAMPION_COOLDOWN_TICKS = TICKS_PER_YEAR * 3
RELIGIOUS_CONVERSION_REGION_COOLDOWN_TICKS = 90
RELIGIOUS_FAVORED_CONVERSION_RATE = 0.003
RELIGIOUS_HERO_CONVERSION_RATE = 0.0015
ADVENTURER_DEITY_CONVERSION_COOLDOWN_TICKS = 180
CHAMPION_ACTIVE_CONVERSION_RATE = 0.0001
CHAMPION_ACTIVE_CONVERSION_MIN = 5
CHAMPION_ACTIVE_CONVERSION_MAX = 250
IMMORTAL_DOMINANCE_BLEED_THRESHOLD = 65.0
IMMORTAL_DOMINANCE_BLEED_RATE = 0.010
IMMORTAL_DOMINANCE_EXCESS_MULTIPLIER = 0.060
IMMORTAL_PRESSURE_MAX_REGIONS = 5
IMMORTAL_DESPERATION_THRESHOLD = 5.0
IMMORTAL_DISASTER_COOLDOWN_TICKS = TICKS_PER_YEAR * 2
IMMORTAL_DISASTER_MAX_REGIONS = 3
IMMORTAL_DISASTER_BASE_SHAKE = 0.08
IMMORTAL_DISASTER_EXCESS_MULTIPLIER = 0.18
IMMORTAL_DISASTER_MAX_SHAKE = 0.28
IMMORTAL_DISASTER_SHIELD_CAP = 0.70
MONSTER_INFLUENCE_GOBLIN_PER_HEAD = 1
MONSTER_INFLUENCE_DRAGON = 12

RECOVERY_ADVENTURER_CRISIS_THRESHOLD = 50
RECOVERY_ADVENTURER_LOW_THRESHOLD = 120
RECOVERY_PARTYLESS_BONUS = 0.25
RECOVERY_POLITYLESS_REPUTATION = 80
RECOVERY_POLITYLESS_PARTY_SIZE = 12
RECOVERY_CRISIS_REPUTATION = 60
MONSTER_XP_GOBLIN = 20
MONSTER_XP_GIANT = 150
MONSTER_XP_DRAGON = 500
MONSTER_XP_HORROR = 1000
LEADER_XP_WEIGHT_MULTIPLIER = 1.75
XP_TO_REP_DIVISOR = 100
PARTY_SPLIT_SIZE_THRESHOLD = 40
PARTY_SPLIT_BASE_CHANCE = 0.03
PARTY_SPLIT_PER_MEMBER = 0.002
REGION_ACTIVITY_XP_STEP = 3
REGION_ACTIVITY_XP_REDUCTION = 0.05
REGION_ACTIVITY_XP_REDUCTION_CAP = 0.50
RECOVERY_CRISIS_PARTY_SIZE = 8
RECOVERY_MONSTER_SPAWN_SCALE_LOW = 0.45
RECOVERY_MONSTER_SPAWN_SCALE_CRISIS = 0.20
RECOVERY_REGION_ORDER_STEP = 2
RECOVERY_REGION_CONTROL_STEP = 2
REFUGEE_COMMONER_THRESHOLD = 250
REFUGEE_ORDER_THRESHOLD = 60.0
REFUGEE_BASE_CHANCE = 0.12
REFUGEE_CRISIS_BONUS = 0.12
REFUGEE_LOW_BONUS = 0.06
REFUGEE_BATCH_MIN = 60
REFUGEE_BATCH_MAX = 180
REFUGEE_REGION_MIN = 1
REFUGEE_REGION_MAX = 3
REGION_SIZE_MIN = 0.75
REGION_SIZE_MAX = 1.25
PLAINS_CAP_MIN = 1_500_000
PLAINS_CAP_MAX = 2_500_000
FOREST_CAP_MIN = 1_000_000
FOREST_CAP_MAX = 2_000_000
HIGHLANDS_CAP_MIN = 500_000
HIGHLANDS_CAP_MAX = 1_500_000

BIOMES = ["Forest", "Plains", "Highlands"]
TIME_OF_DAY = ["Morning", "Midday", "Evening"]
MONTH_NAMES = [
    "Dawnsreach", "Rainmoot", "Bloomtide", "Suncrest", "Goldfire", "Highsun",
    "Harvestwane", "Emberfall", "Duskmarch", "Frostburn", "Deepcold", "Yearsend",
]
MALE_FIRST_NAMES = [
    "Alden", "Bram", "Cade", "Dain", "Eamon", "Fenn", "Galen", "Hale", "Ivor", "Joran",
    "Kellan", "Loric", "Marek", "Niall", "Orin", "Perrin", "Quill", "Rook", "Soren", "Torin",
    "Ulric", "Vale", "Wren", "Yorick", "Zane", "Aster", "Beck", "Corin", "Darian", "Eldric",
    "Fenric", "Garrik", "Hadrian", "Ilan", "Jarek", "Kael", "Leif", "Merrik", "Nash", "Orrin",
    "Pike", "Ronan", "Silas", "Thane", "Varric", "Wyatt", "Ash", "Rowan", "Tobin", "Dorian",
    "Brian", "Zachary", "Eric", "Pix", "Wolfhud", "Arnold",
]

FEMALE_FIRST_NAMES = [
    "Brina", "Cora", "Edda", "Iris", "Kara", "Lysa", "Nora", "Pella", "Rhea", "Talia",
    "Vera", "Ysra", "Mira", "Thora", "Ember", "Sera", "Ayla", "Brenna", "Celeste", "Delia",
    "Elara", "Fiona", "Gwen", "Halea", "Isolde", "Jessa", "Keira", "Lyra", "Maren", "Nessa",
    "Orla", "Petra", "Quinna", "Rosal", "Selene", "Tarin", "Una", "Valea", "Willa", "Yara",
    "Zora", "Aster", "Brynn", "Cora", "Daphne", "Eris", "Freya", "Greta", "Helena", "Junia",
    "Serafina", "Amanda", "Hazaela",
]

SURNAMES = [
    "Dunn", "Morrow", "Vale", "Briar", "Hart", "Stone", "Ash", "Tanner", "Mills", "Rook",
    "Thorne", "Crowe", "Marsh", "Voss", "Hale", "Wythe", "Fen", "Merrin", "Grove", "Ward",
    "Black", "Hollow", "Reed", "Mercer", "Cross", "Flint", "Dale", "Kestrel", "Rowan", "Pike",
    "Torr", "Wren", "Gage", "Farrow", "Dusk", "Harrow", "Bramble", "Colt", "Drake", "Ember",
    "Fox", "Graves", "Hawke", "Ivory", "Knoll", "Locke", "Mire", "North", "Oaken", "Pryce",
    "Quarry", "Raven", "Slate", "Thatch", "Umber", "Valewood", "Westfall", "Yew", "Zephyr", "Storm",
    "Winter", "Summer", "Redfern", "Wolf", "Iron", "Green", "Gold", "Frost", "Oak", "River", "Little",
    "Brist", "Gregersen", "Schwarzenegger",
]

REGION_PREFIXES = [
    "Green", "Stone", "Ash", "Wolf", "Oak", "Frost", "Gold", "Mist", "Black",
    "River", "Iron", "High", "Deep", "Red",
]

REGION_SUFFIXES = [
    "vale", "run", "mere", "watch", "field", "wood", "reach", "moor", "ford",
    "crest", "pass", "hollow", "heath", "fall",
]

TRAITS = [
    "brave", "cruel", "greedy", "patient", "zealous", "proud", "loyal", "cunning",
    "rash", "suspicious", "merciful", "vengeful", "stern", "curious", "brooding",
]

ROLE_WEIGHTS: List[Tuple[Role, int]] = [
    (Role.COMMONER, 80),
    (Role.FIGHTER, 8),
    (Role.WARDEN, 7),
    (Role.WIZARD, 2),
    (Role.BARD, 3),
]

CHROMATIC_DRAGONS = ["Red", "Blue", "Green", "Black", "White"]
GIANT_TYPES = ["Hill Giant", "Stone Giant", "Frost Giant"]
HORROR_TITLES = ["Whispering Maw", "Sleeper Below", "Many-Eyed Tide", "Void Saint"]
population_module.MALE_FIRST_NAMES = MALE_FIRST_NAMES
population_module.FEMALE_FIRST_NAMES = FEMALE_FIRST_NAMES
population_module.SURNAMES = SURNAMES
population_module.TRAITS = TRAITS
population_module.ROLE_WEIGHTS = ROLE_WEIGHTS
population_module.WIZARD_PROMOTION_CHANCE = WIZARD_PROMOTION_CHANCE
population_module.MONTH_NAMES = MONTH_NAMES
population_module.Alignment = Alignment
population_module.Role = Role
population_module.Deity = Deity
population_module.MonsterKind = MonsterKind
population_module.Actor = Actor
legacy_module.MALE_FIRST_NAMES = MALE_FIRST_NAMES
legacy_module.FEMALE_FIRST_NAMES = FEMALE_FIRST_NAMES
legacy_module.TRAITS = TRAITS
legacy_module.Alignment = Alignment
legacy_module.Role = Role
legacy_module.Deity = Deity
legacy_module.Actor = Actor

_RUNTIME_MODULES = [
    party_runtime_module,
    politics_runtime_module,
    monster_runtime_module,
    combat_runtime_module,
    world_runtime_module,
]

def _inject_runtime_globals() -> None:
    shared = {
        "Alignment": Alignment,
        "Role": Role,
        "MonsterKind": MonsterKind,
        "Deity": Deity,
        "Region": Region,
        "Party": Party,
        "Actor": Actor,
        "Monster": Monster,
        "Event": Event,
        "Commemoration": Commemoration,
        "World": World,
        "Polity": Polity,
        "PolityLeaderRecord": PolityLeaderRecord,
        "Path": Path,
        "random": random,
        "time": time,
    }
    for name, value in list(globals().items()):
        if name.isupper():
            shared[name] = value
    for module in _RUNTIME_MODULES:
        module.__dict__.update(shared)

_inject_runtime_globals()


class Simulator(CombatMixin, MonsterMixin, PoliticsMixin, PartyMixin, WorldBuildMixin, RelicMixin, LegacyMixin, PopulationMixin):
    Role = Role
    MonsterKind = MonsterKind
    Deity = Deity
    MONTH_NAMES = MONTH_NAMES

    def __init__(
        self,
        seed: Optional[str] = DEFAULT_SEED,
        verbose: bool = False,
        verbose_delay: float = 0.0,
        verbose_min_importance: int = VERBOSE_EVENT_IMPORTANCE,
        population_scale: float = 1.0,
    ) -> None:
        if seed is None:
            seed = self._random_seed_string()
        self.rng = random.Random(seed)
        self.verbose = verbose
        self.verbose_delay = max(0.0, verbose_delay)
        self.verbose_min_importance = max(1, verbose_min_importance)
        self._last_printed_event_index = 0
        self._monster_id_counter = 1
        self._spawned_horror_titles = set()
        self.population_scale = max(0.0001, float(population_scale))
        self.world = self._build_world(seed)
        self.world.output_dir = _make_run_output_dir(seed)
        self.world.output_dir.mkdir(parents=True, exist_ok=True)

    def _mark_actor_dead(self, actor: Actor, cause: str, importance: int = 1) -> None:
        if not actor.alive:
            return
        actor.alive = False
        actor.hp = 0
        actor.recovering = 0
        actor.death_timestamp = self.world.current_timestamp()
        actor.death_cause = cause
        self.world.souls_by_deity[actor.deity] += 1
        commemorated = any(item.actor_id == actor.id for item in self.world.commemorations)
        notable = bool(actor.title or actor.monster_kills or actor.kills or actor.reputation >= 10 or commemorated)
        self._drop_relic(actor)
        actor.loyalty = None
        killer = self.world.actors.get(actor.death_killer_id) if actor.death_killer_id is not None else None
        self._propagate_revenge_from_death(actor, killer)
        self._resolve_revenge_if_needed(actor)
        if notable:
            self.world.log(
                f"{actor.full_name()} dies in {self.world.region_name(actor.region_id)}. Cause: {cause}.",
                importance=max(2, importance),
                category="notable_death",
            )
        if getattr(actor, "champion_of", None) is not None:
            self.world.log(
                f"{actor.full_name()}, champion of {actor.champion_of.value}, falls in {self.world.region_name(actor.region_id)}. Cause: {cause}.",
                importance=3,
                category="champion_death",
            )

    def _living_adventurer_count(self) -> int:
        return len(self.world.living_actors())

    def _recovery_state(self) -> str:
        living = self._living_adventurer_count()
        if living < RECOVERY_ADVENTURER_CRISIS_THRESHOLD:
            return 'crisis'
        if living < RECOVERY_ADVENTURER_LOW_THRESHOLD:
            return 'low'
        return 'normal'


    def _dynamic_polity_thresholds(self) -> Tuple[int, int]:
        world = self.world
        state = self._recovery_state()
        if not world.polities:
            return (RECOVERY_POLITYLESS_REPUTATION, RECOVERY_POLITYLESS_PARTY_SIZE)
        if state == 'crisis':
            return (RECOVERY_CRISIS_REPUTATION, RECOVERY_CRISIS_PARTY_SIZE)
        return (POLITY_MIN_REPUTATION, POLITY_MIN_PARTY_SIZE)

    def _apply_recovery_pressure(self) -> None:
        world = self.world
        if world.tick % 30 != 0:
            return
        state = self._recovery_state()
        if state == 'normal':
            return
        for region in world.regions.values():
            local_monsters = world.monsters_in_region(region.id)
            dangerous = any(m.alive and m.kind in (MonsterKind.DRAGON, MonsterKind.ANCIENT_HORROR, MonsterKind.GIANT, MonsterKind.GOBLIN) for m in local_monsters)
            commoners = world.commoners_by_region.get(region.id, 0) if hasattr(world, 'commoners_by_region') else 0
            if dangerous:
                continue
            if commoners >= 100:
                world.adjust_region_state(region.id, control_delta=RECOVERY_REGION_CONTROL_STEP, order_delta=RECOVERY_REGION_ORDER_STEP)
            elif commoners >= 50:
                world.adjust_region_state(region.id, control_delta=1, order_delta=1)
        if not world.polities:
            world.log("With the great powers broken, surviving communities slowly begin to restore order.", importance=2, category="recovery")
        else:
            world.log("Exhausted realms pull back from the brink and begin to gather strength again.", importance=2, category="recovery")


    def _aggregate_commoner_total(self) -> int:
        world = self.world
        return sum(world.commoners_by_region.values()) if hasattr(world, 'commoners_by_region') else 0

    def _safe_refugee_regions(self) -> List[Region]:
        world = self.world
        candidates: List[Region] = []
        for region in world.regions.values():
            local_monsters = world.monsters_in_region(region.id)
            dangerous = any(
                m.alive and m.kind in (MonsterKind.DRAGON, MonsterKind.ANCIENT_HORROR, MonsterKind.GIANT)
                for m in local_monsters
            )
            if dangerous:
                continue
            if region.order < 45:
                continue
            candidates.append(region)
        candidates.sort(key=lambda r: (r.order, r.control, -r.danger, self.rng.random()), reverse=True)
        return candidates

    def _maybe_arrive_refugees(self) -> None:
        world = self.world
        if world.tick % 30 != 0 or not hasattr(world, 'commoners_by_region'):
            return
        total_commoners = self._aggregate_commoner_total()
        avg_order = sum(region.order for region in world.regions.values()) / max(1, len(world.regions))
        if total_commoners >= REFUGEE_COMMONER_THRESHOLD:
            return
        if avg_order >= REFUGEE_ORDER_THRESHOLD:
            return

        chance = REFUGEE_BASE_CHANCE
        state = self._recovery_state()
        if state == 'crisis':
            chance += REFUGEE_CRISIS_BONUS
        elif state == 'low':
            chance += REFUGEE_LOW_BONUS

        chance += min(0.18, max(0, REFUGEE_COMMONER_THRESHOLD - total_commoners) / max(1, REFUGEE_COMMONER_THRESHOLD) * 0.18)
        chance += min(0.12, max(0.0, REFUGEE_ORDER_THRESHOLD - avg_order) / max(1.0, REFUGEE_ORDER_THRESHOLD) * 0.12)

        safe_regions = self._safe_refugee_regions()
        if not safe_regions:
            return
        if self.rng.random() >= min(0.75, chance):
            return

        num_regions = min(len(safe_regions), self.rng.randint(REFUGEE_REGION_MIN, REFUGEE_REGION_MAX))
        arrivals = self.rng.sample(safe_regions, k=num_regions)
        total_arrivals = 0
        for region in arrivals:
            batch = self.rng.randint(REFUGEE_BATCH_MIN, REFUGEE_BATCH_MAX)
            if region.order >= 70:
                batch += self.rng.randint(10, 40)
            world.commoners_by_region[region.id] += batch
            faith_map = world.commoner_faith_by_region.setdefault(region.id, {deity: 0 for deity in Deity})
            favored = self._v10_region_favored_deity(region.id)
            self._v10_bulk_apply_faith_addition(faith_map, batch, favored=favored)
            total_arrivals += batch
            world.adjust_region_state(region.id, control_delta=1, order_delta=-1)

        world.refugee_arrivals = getattr(world, 'refugee_arrivals', 0) + 1
        world.refugee_commoners = getattr(world, 'refugee_commoners', 0) + total_arrivals

        if len(arrivals) == 1:
            world.log(
                f"Refugees from beyond the continent reach {arrivals[0].name}, bringing {total_arrivals} desperate souls to its gates.",
                importance=3,
                category="refugees",
            )
        else:
            names = ", ".join(region.name for region in arrivals[:-1]) + f", and {arrivals[-1].name}" if len(arrivals) > 1 else arrivals[0].name
            world.log(
                f"Refugee caravans from beyond the continent reach {names}, bringing {total_arrivals} desperate souls in search of shelter.",
                importance=3,
                category="refugees",
            )

    def _destabilize_polity_regions(self, polity: Polity, control_loss: int, order_loss: int, max_regions: Optional[int] = None) -> None:
        world = self.world
        region_ids = list(polity.region_ids)
        if max_regions is not None and len(region_ids) > max_regions:
            self.rng.shuffle(region_ids)
            region_ids = region_ids[:max_regions]
        for region_id in region_ids:
            world.adjust_region_state(region_id, control_delta=-abs(control_loss), order_delta=-abs(order_loss))

    def _maybe_fragment_polity(self, polity: Polity) -> bool:
        world = self.world
        if polity.stability > 0 or len(polity.region_ids) < 2:
            return False
        fringe = [rid for rid in polity.region_ids if rid != polity.capital_region_id]
        if not fringe:
            return False
        split_count = max(1, len(fringe) // 3)
        self.rng.shuffle(fringe)
        breakaway = fringe[:split_count]
        for region_id in breakaway:
            polity.region_ids = [rid for rid in polity.region_ids if rid != region_id]
            world.regions[region_id].polity_id = None
            world.regions[region_id].contested_by = None
            world.adjust_region_state(region_id, control_delta=-10, order_delta=-10)
        world.log(f"{polity.name} splinters under the strain, losing hold of {len(breakaway)} region{'s' if len(breakaway) != 1 else ''}.", importance=3, category='polity_challenge')
        return True

    def run(self, ticks: int, periodic_summary_years: int = 0) -> None:
        periodic_summary_years = max(0, int(periodic_summary_years))
        summary_every_ticks = periodic_summary_years * TICKS_PER_YEAR if periodic_summary_years > 0 else 0
        run_start = time.perf_counter()

        for _ in range(ticks):
            self.step()

            if summary_every_ticks > 0 and self.world.tick % summary_every_ticks == 0:
                elapsed_years = self.world.tick // TICKS_PER_YEAR
                self.world.runtime_seconds = time.perf_counter() - run_start
                summary.write_summary(self, elapsed_years)

            if self.verbose:
                self._print_new_events()
                if self.verbose_delay > 0:
                    time.sleep(self.verbose_delay)

    def _prepare_turn_caches(self) -> None:
        world = self.world

        # Cache the relative reputation threshold once per tick instead of
        # re-sorting living adventurers for every founder check.
        living_reps = [a.reputation for a in world._living_actor_cache if a.is_adventurer()]
        if living_reps:
            living_reps.sort()
            index = min(len(living_reps) - 1, max(0, int((len(living_reps) - 1) * PARTY_FOUNDING_PERCENTILE)))
            world._party_founder_rep_threshold_cache = living_reps[index]
        else:
            world._party_founder_rep_threshold_cache = 0

        # Cache parties by leader region for local join checks.
        parties_by_region = {rid: [] for rid in world.regions}
        for party in world.parties.values():
            if not party.member_ids or party.leader_id is None:
                continue
            leader = world.actors.get(party.leader_id)
            if leader is None or not leader.alive:
                continue
            parties_by_region.setdefault(leader.region_id, []).append(party)
        world._parties_by_region_cache = parties_by_region

    def step(self) -> None:
        world = self.world
        world.tick += 1
        self._current_year, self._current_month, self._current_day, self._current_tod, self._current_season = world.current_calendar()

        monthly_phase = (world.tick % 30 == 0)
        seasonal_phase = (world.tick % 90 == 0)
        governance_phase = monthly_phase
        maintenance_phase = (world.tick % 10 == 0)

        if maintenance_phase:
            world.cleanup_parties()
            self._handle_party_succession()

        self._population_tick()

        if governance_phase:
            self._legacy_tick()
            self._update_polities()
            self._apply_recovery_pressure()
            self._maybe_arrive_refugees()

        self._rebuild_world_caches()
        self._prepare_turn_caches()

        for actor in world._living_actor_cache:
            actor.actions_remaining = ACTIONS_PER_TICK
            if not hasattr(actor, "combat_cooldown"):
                actor.combat_cooldown = 0
            if actor.combat_cooldown > 0:
                actor.combat_cooldown -= 1
            if actor.recovering > 0:
                actor.recovering -= 1
            heal_chance = 0.20 + max(0, actor.luck - 10) * 0.01
            if actor.hp < actor.max_hp and (actor.recovering > 0 or actor.combat_cooldown > 0 or self.rng.random() < heal_chance):
                actor.hp = min(actor.max_hp, actor.hp + 1)

        if world.tick % 3 == 1:
            self._observe_birthdays_and_commemorations()

        self._apply_seasonal_drift()
        self._tick_monster_age_and_terror()
        self._monster_spawn_check()

        active_actor_ids = []
        for actor in world._living_actor_cache:
            if not actor.is_adventurer():
                continue
            if getattr(actor, 'resting_until_tick', -1) > world.tick:
                continue
            if self._is_actor_hot(actor):
                active_actor_ids.append(actor.id)
                continue
            if not self._is_shift_active(actor):
                continue
            if actor.party_id is None:
                active_actor_ids.append(actor.id)
                continue
            party = world.parties.get(actor.party_id)
            if party is None or party.leader_id == actor.id:
                active_actor_ids.append(actor.id)

        self.rng.shuffle(active_actor_ids)
        for actor_id in active_actor_ids:
            actor = world.actors.get(actor_id)
            if actor is None or not actor.alive:
                continue
            self._adventurer_turn(actor)

        self._rebuild_world_caches()

        monster_ids = [monster.id for monster in world._living_monster_cache]
        self.rng.shuffle(monster_ids)
        for monster_id in monster_ids:
            monster = world.monsters.get(monster_id)
            if monster is not None and monster.alive:
                self._monster_turn(monster)

        if governance_phase or seasonal_phase:
            self._rebuild_world_caches()

        if monthly_phase:
            for region_id in world.regions:
                world.evaluate_region_rule(region_id)
            self._apply_religious_conversion()
            self._apply_reputation_decay()
            self._decay_region_activity()
            self._apply_party_fragmentation()
            self._apply_evil_party_instability()
            self._emit_monthly_summary()
        if seasonal_phase:
            self._emit_season_summary()
    def _observe_birthdays_and_commemorations(self) -> None:
        PopulationMixin._observe_birthdays_and_commemorations(self)
        world = self.world
        for item in world.commemorations_today():
            if self.rng.random() < 0.35:
                if item.region_id is None:
                    world.log(f"The continent observes {item.name}. {item.reason}", importance=2, category="commemoration")
                else:
                    world.log(f"{world.region_name(item.region_id)} observes {item.name}. {item.reason}", importance=2, category="commemoration")

    def _apply_seasonal_drift(self) -> None:
        world = self.world
        _, month, _, tod, season = world.current_calendar()
        if tod != "Night":
            return
        for region in world.regions.values():
            local = [actor for actor in world.actors_in_region(region.id) if actor.is_adventurer()]
            good = len([actor for actor in local if actor.is_good()])
            evil = len([actor for actor in local if actor.is_evil()])
            if good > evil:
                world.adjust_region_state(region.id, control_delta=1, order_delta=1)
            elif evil > good:
                world.adjust_region_state(region.id, control_delta=-1, order_delta=-1)
            else:
                if region.order < 55:
                    world.adjust_region_state(region.id, order_delta=1)
            if season == "Winter" and region.biome in ("Forest", "Highlands"):
                world.adjust_region_state(region.id, order_delta=-1)
            elif season == "Summer" and region.biome == "Plains":
                world.adjust_region_state(region.id, order_delta=1)

    def _emit_monthly_summary(self) -> None:
        world = self.world
        _, month, _, _, season = world.current_calendar()
        good_regions = len([r for r in world.regions.values() if r.control >= 20])
        evil_regions = len([r for r in world.regions.values() if r.control <= -20])
        contested = len(world.regions) - good_regions - evil_regions
        world.log(
            f"{MONTH_NAMES[month - 1]} closes in {season}: {good_regions} regions lean toward order, {evil_regions} toward oppression, {contested} remain contested.",
            importance=2,
            category="monthly",
        )

    def _emit_season_summary(self) -> None:
        world = self.world
        _, _, _, _, season = world.current_calendar()
        avg_order = sum(region.order for region in world.regions.values()) / len(world.regions)
        world.log(
            f"{season} ends with the continent's average order at {avg_order:.1f}.",
            importance=2,
            category="seasonal",
        )

    def _print_new_events(self) -> None:
        world = self.world
        new_events = world.events[self._last_printed_event_index:]
        for event in new_events:
            if event.importance >= self.verbose_min_importance:
                print(f"[{event.timestamp}] {event.text}")
        self._last_printed_event_index = len(world.events)

    def _pick_top_hero_and_villain(self) -> Tuple[Optional[Actor], Optional[Actor]]:
        living = self.world.living_actors()
        heroes = [a for a in living if a.is_adventurer() and not a.is_evil()]
        villains = [a for a in living if a.is_adventurer() and a.is_evil()]
        hero = max(heroes, key=lambda a: (a.reputation, a.dragon_kills, a.horror_kills, a.monster_kills, a.kills, a.power_rating()), default=None)
        villain = max(villains, key=lambda a: (a.reputation, a.regions_oppressed, a.kills, a.monster_kills, a.power_rating()), default=None)
        return hero, villain

    def _deity_influence_summary(self) -> List[Tuple[Deity, int, float]]:
        surviving = self.world.living_actors()
        total = len(surviving)
        results: List[Tuple[Deity, int, float]] = []
        for deity in Deity:
            count = len([actor for actor in surviving if actor.deity == deity])
            pct = (count / total * 100.0) if total else 0.0
            results.append((deity, count, pct))
        return results

    def _top_region(self) -> Region:
        return max(self.world.regions.values(), key=lambda r: (r.order, r.control, -r.danger))

    def _top_deity(self) -> Tuple[Deity, int, float]:
        return max(self._deity_influence_summary(), key=lambda item: item[2])

    def _hero_tale(self, hero: Actor) -> str:
        pieces = []
        if hero.title:
            pieces.append(f"Known as {hero.title}")
        if hero.dragon_kills:
            pieces.append(f"slew {hero.dragon_kills} dragon{'s' if hero.dragon_kills != 1 else ''}")
        if hero.horror_kills:
            pieces.append(f"broke {hero.horror_kills} ancient horror{'s' if hero.horror_kills != 1 else ''}")
        if hero.regions_defended:
            pieces.append(f"defended {hero.regions_defended} threatened frontier{'s' if hero.regions_defended != 1 else ''}")
        if not pieces:
            pieces.append(f"earned renown through {hero.kills} victories")
        return f"{hero.full_name()} {'; '.join(pieces)} from {self.world.region_name(hero.region_id)}."

    def _villain_tale(self, villain: Actor) -> str:
        pieces = []
        if villain.title:
            pieces.append(f"Bearing the name {villain.title}")
        if villain.regions_oppressed:
            pieces.append(f"oppressed {villain.regions_oppressed} region{'s' if villain.regions_oppressed != 1 else ''}")
        if villain.kills:
            pieces.append(f"left {villain.kills} bodies in their wake")
        if not pieces:
            pieces.append(f"spread fear from {self.world.region_name(villain.region_id)}")
        return f"{villain.full_name()} {'; '.join(pieces)}."

    def _chronicle_title(self, hero: Optional[Actor], top_region: Region, top_deity: Deity) -> str:
        if hero is not None:
            return f"The Chronicle of {hero.short_name()}, {top_region.name}, and {top_deity.value}"
        return f"The Chronicle of {top_region.name} under {top_deity.value}"

    def _ideology_similarity(self, actor: Actor, other: Actor) -> float:
        return actor.ideology_similarity(other)

    def _assign_best_friend(self, actor: Actor, other: Actor) -> bool:
        if actor.id == other.id or not actor.alive or not other.alive:
            return False
        spouse = self.world.actors.get(actor.spouse_id) if actor.spouse_id is not None else None
        if spouse is not None and spouse.alive and spouse.id != other.id:
            return False
        if actor.best_friend_id is not None:
            current = self.world.actors.get(actor.best_friend_id)
            if current is not None and current.alive:
                return current.id == other.id
        actor.best_friend_id = other.id
        return True

    def _forge_bff_pair(self, actor: Actor, other: Actor) -> bool:
        if not actor.can_form_bff_with(other):
            return False
        changed = self._assign_best_friend(actor, other)
        changed = self._assign_best_friend(other, actor) or changed
        return changed

    def _register_nemesis(self, actor: Actor, enemy: Actor, revenge: bool = False, revenge_for: Optional[Actor] = None) -> bool:
        if actor.id == enemy.id or not actor.alive or not enemy.alive:
            return False
        if getattr(actor, 'revenge_target_id', None) is not None and actor.revenge_target_id != enemy.id:
            target = self.world.actors.get(actor.revenge_target_id)
            if target is not None and target.alive:
                return False
            actor.revenge_target_id = None
            actor.revenge_for_actor_id = None
        enemy_power = enemy.power_rating()
        if revenge:
            actor.nemesis_id = enemy.id
            actor.nemesis_power = enemy_power
            actor.revenge_target_id = enemy.id
            actor.revenge_for_actor_id = revenge_for.id if revenge_for is not None else None
            return True
        current = self.world.actors.get(actor.nemesis_id) if actor.nemesis_id is not None else None
        if current is not None and current.alive and enemy_power <= getattr(actor, 'nemesis_power', 0):
            return current.id == enemy.id
        actor.nemesis_id = enemy.id
        actor.nemesis_power = enemy_power
        return True

    def _best_nemesis_candidate(self, actor: Actor, enemies: List[Actor]) -> Optional[Actor]:
        candidates = [e for e in enemies if e.alive and e.is_adventurer() and actor.is_ideological_enemy(e)]
        if not candidates:
            return None
        candidates.sort(key=lambda e: (abs(actor.power_rating() - e.power_rating()), -e.power_rating(), self.rng.random()))
        return candidates[0]

    def _update_post_battle_relationships(self, attackers: List[Actor], defenders: List[Actor]) -> None:
        atk_survivors = [a for a in attackers if a.alive and a.is_adventurer()]
        def_survivors = [a for a in defenders if a.alive and a.is_adventurer()]

        for side in (atk_survivors, def_survivors):
            for i, actor in enumerate(side):
                if actor.spouse_id is not None:
                    spouse = self.world.actors.get(actor.spouse_id)
                    if spouse is not None and spouse.alive and spouse.id in [m.id for m in side]:
                        self._forge_bff_pair(actor, spouse)
                        continue
                if actor.best_friend_id is not None:
                    current = self.world.actors.get(actor.best_friend_id)
                    if current is not None and current.alive:
                        continue
                partners = [other for other in side[i+1:] if actor.can_form_bff_with(other)]
                if partners:
                    partner = max(partners, key=lambda other: (actor.ideology_similarity(other), -abs(actor.power_rating() - other.power_rating()), self.rng.random()))
                    self._forge_bff_pair(actor, partner)

        for actor in atk_survivors:
            target = self._best_nemesis_candidate(actor, def_survivors)
            if target is not None:
                self._register_nemesis(actor, target)
        for actor in def_survivors:
            target = self._best_nemesis_candidate(actor, atk_survivors)
            if target is not None:
                self._register_nemesis(actor, target)

    def _propagate_revenge_from_death(self, victim: Actor, killer: Optional[Actor]) -> None:
        if killer is None or not killer.alive or killer.id == victim.id:
            return
        avengers: Dict[int, Actor] = {}
        spouse = self.world.actors.get(victim.spouse_id) if victim.spouse_id is not None else None
        if spouse is not None and spouse.alive and spouse.is_adventurer():
            avengers[spouse.id] = spouse
        best_friend = self.world.actors.get(victim.best_friend_id) if victim.best_friend_id is not None else None
        if best_friend is not None and best_friend.alive and best_friend.is_adventurer():
            avengers[best_friend.id] = best_friend
        party = self.world.get_party(victim)
        if party is not None:
            for mid in party.member_ids:
                if mid == victim.id:
                    continue
                member = self.world.actors.get(mid)
                if member is not None and member.alive and member.is_adventurer():
                    avengers[mid] = member
        for avenger in avengers.values():
            self._register_nemesis(avenger, killer, revenge=True, revenge_for=victim)

    def _resolve_revenge_if_needed(self, fallen: Actor) -> None:
        for actor in self.world.living_actors():
            if getattr(actor, 'revenge_target_id', None) != fallen.id:
                continue
            actor.revenge_target_id = None
            actor.revenge_for_actor_id = None
            if getattr(actor, 'nemesis_id', None) == fallen.id:
                actor.nemesis_id = None
                actor.nemesis_power = 0

    def _rebuild_world_caches(self) -> None:
        world = self.world
        world._living_actor_cache = [a for a in world.actors.values() if a.alive]
        world._living_monster_cache = [m for m in world.monsters.values() if m.alive]
        world._actors_by_region_cache = {rid: [] for rid in world.regions}
        for actor in world._living_actor_cache:
            world._actors_by_region_cache[actor.region_id].append(actor)
        world._monsters_by_region_cache = {rid: [] for rid in world.regions}
        for monster in world._living_monster_cache:
            world._monsters_by_region_cache[monster.region_id].append(monster)

    def _apply_reputation_decay(self):
        for actor in self.world.actors.values():
            if not actor.alive:
                continue
            rep = actor.reputation
            if rep <= 0:
                continue
            if rep > 300:
                rate = 0.03
            elif rep > 100:
                rate = 0.02
            else:
                rate = 0.01
            decay = max(1, int(rep * rate))
            actor.reputation -= decay


def _v10_generate_population(self, count: int, regions: Dict[int, "Region"]) -> Dict[int, Actor]:
    actors: Dict[int, Actor] = {}
    ratio = self.rng.uniform(0.02, 0.04)
    adventurer_count = max(1, int(round(count * ratio)))
    role_choices = [Role.FIGHTER, Role.WARDEN, Role.WIZARD, Role.BARD]
    role_weights = [12, 6, 2, 2]
    current_year = 1
    actor_id = 1
    for _ in range(adventurer_count):
        role = self.rng.choices(role_choices, weights=role_weights, k=1)[0]
        alignment = self.rng.choice(list(Alignment))
        deity = self._weighted_random_deity(alignment)
        stats = self._roll_stats(role)
        hp = self._base_hp(role, stats[2])
        region_id = self.rng.choice(list(regions.keys()))
        first, surname, sex = self._random_person_identity()
        traits = self.rng.sample(TRAITS, k=2)
        age = self._initial_age_for_role(role)
        birth_year = current_year - age
        actors[actor_id] = Actor(
            id=actor_id,
            name=first,
            surname=surname,
            role=role,
            alignment=alignment,
            deity=deity,
            strength=stats[0],
            dexterity=stats[1],
            constitution=stats[2],
            intelligence=stats[3],
            wisdom=stats[4],
            charisma=stats[5],
            luck=stats[6],
            hp=hp,
            max_hp=hp,
            region_id=region_id,
            traits=traits,
            birth_year=birth_year,
            birth_month=self.rng.randint(1, 12),
            birth_day=self.rng.randint(1, 30),
            spouse_id=None,
            sex=sex,
        )
        actor_id += 1
    return actors

def _v10_build_world(self, seed: str) -> World:
    regions = self._generate_regions(REGION_COUNT)
    scaled_initial_population = max(1, int(round(INITIAL_POPULATION * self.population_scale)))
    actors = self._generate_population(scaled_initial_population, regions)
    monsters = self._generate_initial_monsters(regions)
    world = World(rng=self.rng, regions=regions, actors=actors, monsters=monsters, parties={}, seed_used=seed)
    world.next_actor_id = max(actors.keys(), default=0) + 1
    world.spawned_horror_titles = set(self._spawned_horror_titles)
    world.generated_by_role = self._count_generated_roles(actors)
    world.generated_monsters_by_kind = self._count_generated_monsters(monsters)
    commoner_total = max(0, scaled_initial_population - len(actors))
    world.commoners_by_region = {rid: 0 for rid in regions}
    world.commoner_faith_by_region = {rid: {deity: 0 for deity in Deity} for rid in regions}
    for _ in range(commoner_total):
        rid = self.rng.choice(list(regions.keys()))
        world.commoners_by_region[rid] += 1
        deity = self._v10_commoner_birth_deity(rid, world=world)
        world.commoner_faith_by_region[rid][deity] += 1
    world.generated_by_role[Role.COMMONER] = commoner_total
    world.aggregate_commoner_mode = True
    world.population_scale = self.population_scale
    world.initial_population = scaled_initial_population
    world.source_files = {
        "simulator": Path(__file__).name,
        "class": "class_v22.py",
        "population": "population_v11.py",
        "legacy": "legacy_v6.py",
        "relics": "relics_v2.py",
        "summary": "summary_v30.py",
    }
    world.log(
        "A small continent of forest, plains, and highlands fills with aggregated common folk, wandering adventurers, lurking monsters, and distant divine attention.",
        importance=3,
        category="world",
    )
    return world



def _v10_region_favored_deity(self, region_id: int, world=None):
    world = world if world is not None else getattr(self, "world", None)
    if world is None:
        return None
    region = world.regions.get(region_id)
    if region is None:
        return None
    polity_id = getattr(region, "polity_id", None)
    if polity_id is not None and hasattr(world, "polities") and polity_id in world.polities:
        ruler = world.actors.get(world.polities[polity_id].ruler_id)
        if ruler is not None and ruler.alive:
            return ruler.deity
    ruler_id = getattr(region, "ruler_id", None)
    if ruler_id is not None and ruler_id in world.actors:
        ruler = world.actors.get(ruler_id)
        if ruler is not None and ruler.alive:
            return ruler.deity
    return None

def _v10_bulk_apply_faith_addition(self, faith_map, total, favored=None):
    if total <= 0:
        return 0
    current_total = sum(faith_map.get(d, 0) for d in Deity)
    if current_total <= 0:
        weights = {d: 1 for d in Deity}
        if favored is not None:
            weights[favored] += 2
    else:
        weights = {d: max(1, faith_map.get(d, 0)) for d in Deity}
        if favored is not None:
            weights[favored] += max(1, current_total // 10)

    weight_total = sum(weights.values()) or 1
    assigned = 0
    for i, deity in enumerate(Deity):
        if i == len(Deity) - 1:
            add = total - assigned
        else:
            add = int(total * (weights[deity] / weight_total))
            assigned += add
        faith_map[deity] = faith_map.get(deity, 0) + add
    return total

def _v10_bulk_apply_faith_loss(self, faith_map, total):
    if total <= 0:
        return 0
    current_total = sum(faith_map.get(d, 0) for d in Deity)
    if current_total <= 0:
        return 0
    actual = min(total, current_total)
    assigned = 0
    for i, deity in enumerate(Deity):
        available = faith_map.get(deity, 0)
        if i == len(Deity) - 1:
            loss = min(available, actual - assigned)
        else:
            loss = min(available, int(actual * (available / current_total)))
            assigned += loss
        faith_map[deity] = max(0, available - loss)

    removed = current_total - sum(faith_map.get(d, 0) for d in Deity)
    leftover = actual - removed
    if leftover > 0:
        ranked = sorted(Deity, key=lambda d: faith_map.get(d, 0), reverse=True)
        for deity in ranked:
            if leftover <= 0:
                break
            take = min(leftover, faith_map.get(deity, 0))
            faith_map[deity] -= take
            leftover -= take
    return actual


def _v10_shift_commoner_faith(self, src_region_id: int, dst_region_id: int, amount: int) -> int:
    world = self.world
    if amount <= 0 or not hasattr(world, "commoner_faith_by_region"):
        return 0
    src = world.commoner_faith_by_region.setdefault(src_region_id, {deity: 0 for deity in Deity})
    dst = world.commoner_faith_by_region.setdefault(dst_region_id, {deity: 0 for deity in Deity})
    available = sum(src.get(d, 0) for d in Deity)
    moved = min(amount, available)
    if moved <= 0:
        return 0

    src_total = sum(src.get(d, 0) for d in Deity) or 1
    transferred = {d: 0 for d in Deity}
    assigned = 0
    for i, deity in enumerate(Deity):
        if i == len(Deity) - 1:
            take = moved - assigned
        else:
            take = min(src.get(deity, 0), int(moved * (src.get(deity, 0) / src_total)))
            assigned += take
        transferred[deity] = take
        src[deity] = max(0, src.get(deity, 0) - take)
        dst[deity] = dst.get(deity, 0) + take

    leftover = moved - sum(transferred.values())
    if leftover > 0:
        ranked = sorted(Deity, key=lambda d: src.get(d, 0), reverse=True)
        for deity in ranked:
            if leftover <= 0:
                break
            take = min(leftover, src.get(deity, 0))
            src[deity] -= take
            dst[deity] += take
            leftover -= take
    return moved

def _v10_add_commoner_births(self, region_id: int, births: int) -> None:
    world = self.world
    if births <= 0:
        return
    faith_map = world.commoner_faith_by_region.setdefault(region_id, {deity: 0 for deity in Deity})
    favored = self._v10_region_favored_deity(region_id)
    self._v10_bulk_apply_faith_addition(faith_map, births, favored=favored)

def _v10_remove_commoner_deaths(self, region_id: int, deaths: int) -> int:
    world = self.world
    faith_map = world.commoner_faith_by_region.setdefault(region_id, {deity: 0 for deity in Deity})
    if deaths <= 0:
        return 0
    return self._v10_bulk_apply_faith_loss(faith_map, deaths)

def _v10_allocate_actor_id(self) -> int:
    new_id = self.world.next_actor_id
    self.world.next_actor_id += 1
    return new_id

def _v10_spawn_adventurer_from_commoners(self, region_id: int) -> Optional[Actor]:
    world = self.world
    if world.commoners_by_region.get(region_id, 0) <= 0:
        return None
    world.commoners_by_region[region_id] -= 1
    role = self.rng.choices([Role.FIGHTER, Role.WARDEN, Role.WIZARD], weights=[60, 38, 2], k=1)[0]
    alignment = self.rng.choice(list(Alignment))
    faith_map = world.commoner_faith_by_region.setdefault(region_id, {deity: 0 for deity in Deity})
    available = [deity for deity in Deity if faith_map.get(deity, 0) > 0]
    if available:
        deity = max(available, key=lambda d: faith_map.get(d, 0) + self.rng.random())
        faith_map[deity] -= 1
    else:
        deity = self._weighted_random_deity(alignment, region_id=region_id)
    stats = self._roll_stats(role)
    hp = self._base_hp(role, stats[2])
    first, surname, sex = self._random_person_identity()
    age = 16
    current_year = self._current_year if hasattr(self, '_current_year') else 1
    actor = Actor(
        id=self._allocate_actor_id(),
        name=first,
        surname=surname,
        role=role,
        alignment=alignment,
        deity=deity,
        strength=stats[0],
        dexterity=stats[1],
        constitution=stats[2],
        intelligence=stats[3],
        wisdom=stats[4],
        charisma=stats[5],
        luck=stats[6],
        hp=hp,
        max_hp=hp,
        region_id=region_id,
        traits=self.rng.sample(TRAITS, k=2),
        birth_year=current_year - age,
        birth_month=self.rng.randint(1, 12),
        birth_day=self.rng.randint(1, 30),
        spouse_id=None,
        sex=sex,
    )
    local_polities = [p for p in world.polities.values() if region_id in p.region_ids]
    if local_polities:
        strongest = max(local_polities, key=lambda p: (len(p.region_ids), len(p.member_actor_ids), p.legitimacy))
        ruler = world.actors.get(strongest.ruler_id)
        if ruler and ((actor.is_good() and not ruler.is_evil()) or (actor.is_evil() and ruler.is_evil()) or (actor.is_neutral_morality() and not (actor.is_evil() and ruler.is_good()))):
            actor.polity_id = strongest.id
            actor.loyalty = strongest.ruler_id
            strongest.member_actor_ids.append(actor.id)
    actor.duty_shift = self.rng.randrange(ADVENTURER_SHIFT_COUNT)
    world.actors[actor.id] = actor
    world.generated_by_role[role] += 1
    world.log(
        f"{actor.short_name()} rises from the common folk of {world.region_name(region_id)} and takes up the life of a {role.value.lower()}.",
        importance=2,
        category="coming_of_age",
    )
    return actor

def _v10_population_tick(self) -> None:
    world = self.world
    if not hasattr(world, 'commoners_by_region'):
        return
    for region_id, region in world.regions.items():
        count = world.commoners_by_region.get(region_id, 0)
        if count <= 0:
            continue

        local_actors = world.actors_in_region(region_id)
        local_monsters = world.monsters_in_region(region_id)
        evil_adventurers = sum(1 for a in local_actors if a.alive and a.is_adventurer() and a.is_evil())
        good_adventurers = sum(1 for a in local_actors if a.alive and a.is_adventurer() and a.is_good())
        monster_threat = sum(
            1 + (self._monster_strength_bonus(m) // 6)
            for m in local_monsters
            if m.alive and m.kind in (MonsterKind.GOBLIN, MonsterKind.GIANT, MonsterKind.DRAGON, MonsterKind.ANCIENT_HORROR)
        )

        effective_capacity = self._effective_region_capacity(region)
        pressure = count / max(1, effective_capacity)

        growth_rate = 0.0006
        if region.order >= 60:
            growth_rate += 0.0003
        if region.control >= 20:
            growth_rate += 0.0002
        if region.control <= -20:
            growth_rate -= 0.0003
        if monster_threat > 0:
            growth_rate -= min(0.0005, monster_threat * 0.00005)

        logistic_factor = max(-0.50, 1.0 - pressure)
        base_births = count * growth_rate * logistic_factor
        births = 0
        if base_births > 0:
            births = int(base_births)
            if self.rng.random() < (base_births - births):
                births += 1

        death_rate = 0.00003 + region.danger * 0.00001
        if region.order <= 35:
            death_rate += 0.00004
        if region.control <= -20:
            death_rate += 0.00002
        death_rate += evil_adventurers * 0.000005
        death_rate += monster_threat * 0.00006
        death_rate -= good_adventurers * 0.00001

        if count > 300:
            death_rate *= 0.7
        if count > 800:
            death_rate *= 0.5

        if pressure > 1.0:
            over = pressure - 1.0
            death_rate += min(0.01, over * 0.0025)

        death_rate = max(0.0, death_rate)
        deaths_float = count * death_rate
        deaths = int(deaths_float)
        if self.rng.random() < (deaths_float - deaths):
            deaths += 1
        deaths = min(count, deaths)

        migrants = 0
        overcrowded = pressure > 1.0
        threatened = evil_adventurers > good_adventurers or monster_threat > 0 or region.control <= -20
        if region.neighbors and (threatened or overcrowded):
            migrate_rate = 0.0002 + evil_adventurers * 0.00005 + monster_threat * 0.00008
            if region.control <= -20:
                migrate_rate += 0.00010
            if overcrowded:
                migrate_rate += min(0.03, (pressure - 1.0) * 0.01)

            migrants_float = count * migrate_rate
            migrants = int(migrants_float)
            if self.rng.random() < (migrants_float - migrants):
                migrants += 1
            migrants = min(count - deaths, migrants)
            migrants = min(migrants, int(count * 0.03))

            if migrants > 0:
                current_score = self._region_safety_score(region_id)
                better_neighbors = []
                for nid in region.neighbors:
                    neighbor = world.regions[nid]
                    neighbor_count = world.commoners_by_region.get(nid, 0)
                    neighbor_capacity = self._effective_region_capacity(neighbor)
                    neighbor_pressure = neighbor_count / max(1, neighbor_capacity)
                    if self._region_safety_score(nid) <= current_score:
                        continue
                    if neighbor_pressure >= pressure:
                        continue
                    better_neighbors.append(nid)

                if better_neighbors:
                    better_neighbors.sort(
                        key=lambda nid: (
                            self._region_safety_score(nid),
                            -(world.commoners_by_region.get(nid, 0) / max(1, self._effective_region_capacity(world.regions[nid]))),
                            -world.regions[nid].danger,
                        ),
                        reverse=True,
                    )
                    top_score = self._region_safety_score(better_neighbors[0])
                    destinations = [nid for nid in better_neighbors if self._region_safety_score(nid) == top_score]
                    for _ in range(migrants):
                        dest = self.rng.choice(destinations)
                        world.commoners_by_region[dest] += 1
                        self._shift_commoner_faith(region_id, dest, 1)
                else:
                    migrants = 0

        world.commoners_by_region[region_id] = max(0, count + births - deaths - migrants)
        self._add_commoner_births(region_id, births)
        self._remove_commoner_deaths(region_id, deaths)
        world.generated_by_role[Role.COMMONER] += births
        world.commoner_births += births

        if births >= 3 and self.rng.random() < 0.10:
            world.log(
                f"{births} children are born among the common folk of {world.region_name(region_id)}.",
                importance=1,
                category="birth",
            )
        if deaths >= 3 and self.rng.random() < 0.12:
            world.log(
                f"{deaths} commoners perish in {world.region_name(region_id)} from hunger, fear, and hard living.",
                importance=1,
                category="hardship",
            )
        if migrants >= 5 and self.rng.random() < 0.18:
            world.log(
                f"{migrants} commoners flee {world.region_name(region_id)} in search of safer roads.",
                importance=1,
                category="flight",
            )

    if world.tick % 30 == 0:
        state = self._recovery_state() if hasattr(self, '_recovery_state') else 'normal'
        for region_id in world.regions:
            count = world.commoners_by_region.get(region_id, 0)
            if count <= 0:
                continue
            promotions = 0
            pressure = max(0.0, 0.0004 * count)
            region = world.regions[region_id]
            if region.order >= 60:
                pressure += 0.10
            if region.control <= -20:
                pressure += 0.12
            if state == 'low':
                pressure += 0.18
            elif state == 'crisis':
                pressure += 0.35
            if self.rng.random() < min(0.95, pressure):
                promotions = 1
                if count >= 800 and self.rng.random() < (0.20 if state == 'normal' else 0.45):
                    promotions += 1
                if state == 'crisis' and count >= 300 and self.rng.random() < 0.35:
                    promotions += 1
            for _ in range(promotions):
                if world.commoners_by_region.get(region_id, 0) <= 0:
                    break
                self._spawn_adventurer_from_commoners(region_id)

def _v10_commoner_turn(self, actor: Actor) -> None:
    return

def _v10_handle_adventurer_births_aggregate(self) -> None:
    world = self.world
    for actor in list(world.living_actors()):
        if not actor.is_adventurer() or actor.spouse_id is None:
            continue
        spouse = world.actors.get(actor.spouse_id)
        if spouse is None or not spouse.alive or not spouse.is_adventurer():
            continue
        age_a = self._calculate_age(actor)
        age_b = self._calculate_age(spouse)
        if age_a < 18 or age_b < 18:
            continue
        if actor.sex == spouse.sex:
            continue
        female = actor if getattr(actor, "sex", "F") == "F" else spouse
        male = spouse if female is actor else actor
        female_age = self._calculate_age(female)
        male_age = self._calculate_age(male)
        if female_age > 45 or male_age > 60:
            continue
        if actor.id > spouse.id:
            continue
        last_birth_tick = max(getattr(actor, 'last_birth_tick', -999999), getattr(spouse, 'last_birth_tick', -999999))
        if world.tick - last_birth_tick < legacy_module.LegacyMixin.ADVENTURER_BIRTH_COOLDOWN_TICKS:
            continue
        chance = 0.0015
        region = world.regions[actor.region_id]
        if region.order >= 60:
            chance += 0.001
        if region.control >= 20:
            chance += 0.0005
        if region.control <= -20:
            chance -= 0.0005
        if self.rng.random() < max(0.0002, min(0.006, chance)):
            world.commoners_by_region[actor.region_id] = world.commoners_by_region.get(actor.region_id, 0) + 1
            if hasattr(world, 'commoner_faith_by_region'):
                deity = self._weighted_random_deity(actor.alignment, region_id=actor.region_id, parent_deities=[actor.deity, spouse.deity])
                world.commoner_faith_by_region[actor.region_id][deity] += 1
            world.generated_by_role[Role.COMMONER] += 1
            world.adventurer_lineage_births += 1
            actor.last_birth_tick = world.tick
            spouse.last_birth_tick = world.tick
            world.log(
                f"A child is born to {actor.short_name()} and {spouse.short_name()} in {world.region_name(actor.region_id)}.",
                importance=2,
                category="legacy_birth",
            )

def _v10_legacy_tick(self) -> None:
    self._cleanup_adventurer_spouses()
    self._handle_adventurer_pairing()
    self._v10_handle_adventurer_births_aggregate()
    self._update_ruling_houses()

def _v10_print_summary_extra(sim, years=None) -> None:
    world = sim.world
    total_commoners = sum(getattr(world, 'commoners_by_region', {}).values())
    true_living_population = len(world.living_actors()) + total_commoners
    print()
    print("AGGREGATE CIVILIAN MODEL")
    print("-" * 72)
    print("Commoners are modeled as regional counts, not individual actors.")
    print(f"Living aggregated commoners: {total_commoners}")
    print(f"True living population estimate: {true_living_population}")
    print("Commoners by region:")
    for region_id, count in world.commoners_by_region.items():
        print(f"  {world.region_name(region_id):14} {count}")

Simulator._generate_population = _v10_generate_population

def _v10_commoner_birth_deity(self, region_id: int, world=None) -> Deity:
    world = world if world is not None else getattr(self, "world", None)
    if world is not None:
        faith = getattr(world, "commoner_faith_by_region", {}).get(region_id, {})
        region = world.regions.get(region_id)
        favored = None
        if region is not None:
            polity_id = getattr(region, "polity_id", None)
            if polity_id is not None and polity_id in world.polities:
                ruler = world.actors.get(world.polities[polity_id].ruler_id)
                if ruler is not None and ruler.alive:
                    favored = ruler.deity
            if favored is None and getattr(region, "ruler_id", None) is not None:
                ruler = world.actors.get(region.ruler_id)
                if ruler is not None and ruler.alive:
                    favored = ruler.deity
        if faith and sum(faith.values()) > 0 and self.rng.random() < 0.75:
            if favored is not None and favored in faith and self.rng.random() < 0.65:
                return favored
            return max(Deity, key=lambda d: faith.get(d, 0) + self.rng.random() * 0.25)

    alignment = self.rng.choice(list(Alignment))
    return self._weighted_random_deity(alignment, region_id=region_id)

def _v10_apply_religious_conversion(self) -> None:
    world = self.world
    if not hasattr(world, "commoner_faith_by_region"):
        world.commoner_faith_by_region = {rid: {deity: 0 for deity in Deity} for rid in world.regions}
    if not hasattr(world, "last_religious_conversion_tick_by_region"):
        world.last_religious_conversion_tick_by_region = {rid: -999999 for rid in world.regions}

    for region_id, region in world.regions.items():
        faith = world.commoner_faith_by_region.setdefault(region_id, {deity: 0 for deity in Deity})
        total_commoners = world.commoners_by_region.get(region_id, 0)
        favored = self._v10_region_favored_deity(region_id)
        last_tick = world.last_religious_conversion_tick_by_region.get(region_id, -999999)
        conversion_ready = (world.tick - last_tick) >= RELIGIOUS_CONVERSION_REGION_COOLDOWN_TICKS

        hero_bias = {}
        for actor in world.actors_in_region(region_id):
            if not actor.alive or not actor.is_adventurer():
                continue
            hero_bias[actor.deity] = hero_bias.get(actor.deity, 0) + max(0, actor.reputation)

        moved_any = False
        if conversion_ready and favored is not None and total_commoners > 0:
            converts = max(0, int(total_commoners * RELIGIOUS_FAVORED_CONVERSION_RATE))
            if converts > 0:
                sources = [d for d in Deity if d != favored]
                pool = sum(faith.get(d, 0) for d in sources)
                if pool > 0:
                    moved = min(converts, pool)
                    assigned = 0
                    for i, deity in enumerate(sources):
                        available = faith.get(deity, 0)
                        if i == len(sources) - 1:
                            loss = min(available, moved - assigned)
                        else:
                            loss = min(available, int(moved * (available / pool)))
                            assigned += loss
                        faith[deity] = max(0, available - loss)
                    faith[favored] = faith.get(favored, 0) + moved
                    moved_any = moved_any or moved > 0

        if conversion_ready and hero_bias and total_commoners > 0:
            dominant = max(hero_bias, key=lambda d: hero_bias[d])
            converts = max(0, int(total_commoners * RELIGIOUS_HERO_CONVERSION_RATE))
            if converts > 0:
                sources = [d for d in Deity if d != dominant]
                pool = sum(faith.get(d, 0) for d in sources)
                if pool > 0:
                    moved = min(converts, pool)
                    assigned = 0
                    for i, deity in enumerate(sources):
                        available = faith.get(deity, 0)
                        if i == len(sources) - 1:
                            loss = min(available, moved - assigned)
                        else:
                            loss = min(available, int(moved * (available / pool)))
                            assigned += loss
                        faith[deity] = max(0, available - loss)
                    faith[dominant] = faith.get(dominant, 0) + moved
                    moved_any = moved_any or moved > 0
                    champion_candidates = [a for a in world.actors_in_region(region_id) if a.alive and a.is_adventurer() and getattr(a, 'champion_of', None) == dominant]
                    if champion_candidates:
                        champion = max(champion_candidates, key=lambda a: (a.deity_conviction, a.reputation, a.power_rating()))
                        champion.converted_followers = getattr(champion, 'converted_followers', 0) + moved
                        rep_steps = champion.converted_followers // 100
                        new_steps = rep_steps - getattr(champion, 'champion_rep_steps', 0)
                        if new_steps > 0:
                            champion.reputation += new_steps
                            champion.champion_rep_steps = rep_steps

        if moved_any:
            world.last_religious_conversion_tick_by_region[region_id] = world.tick

        local_adventurers = [a for a in world.actors_in_region(region_id) if a.alive and a.is_adventurer()]
        if local_adventurers:
            dominant_local = max(Deity, key=lambda d: faith.get(d, 0))
            for actor in local_adventurers:
                if actor.deity == dominant_local:
                    actor.deity_conviction = min(100, actor.deity_conviction + 1)
                    continue
                last_personal = getattr(actor, 'last_deity_conversion_tick', -999999)
                if world.tick - last_personal < ADVENTURER_DEITY_CONVERSION_COOLDOWN_TICKS:
                    actor.deity_conviction = min(100, actor.deity_conviction + 1)
                    continue
                chance = 0.0
                if favored is not None and actor.deity != favored:
                    chance += 0.08
                if dominant_local != actor.deity:
                    chance += 0.04
                chance += min(0.12, hero_bias.get(dominant_local, 0) / 1200.0)
                chance -= max(0, actor.deity_conviction - 50) / 250.0
                if self.rng.random() < max(0.0, min(0.25, chance)):
                    actor.deity = dominant_local
                    actor.deity_conviction = max(10, actor.deity_conviction - 5)
                    actor.last_deity_conversion_tick = world.tick
                else:
                    actor.deity_conviction = min(100, actor.deity_conviction + 1)


Simulator._build_world = _v10_build_world
Simulator._population_tick = _v10_population_tick
Simulator._commoner_turn = _v10_commoner_turn
Simulator._legacy_tick = _v10_legacy_tick
Simulator._allocate_actor_id = _v10_allocate_actor_id
Simulator._spawn_adventurer_from_commoners = _v10_spawn_adventurer_from_commoners
Simulator._v10_handle_adventurer_births_aggregate = _v10_handle_adventurer_births_aggregate
Simulator._v10_region_favored_deity = _v10_region_favored_deity
Simulator._v10_commoner_birth_deity = _v10_commoner_birth_deity
Simulator._v10_bulk_apply_faith_addition = _v10_bulk_apply_faith_addition
Simulator._v10_bulk_apply_faith_loss = _v10_bulk_apply_faith_loss
Simulator._apply_religious_conversion = _v10_apply_religious_conversion
Simulator._add_commoner_births = _v10_add_commoner_births
Simulator._remove_commoner_deaths = _v10_remove_commoner_deaths
Simulator._shift_commoner_faith = _v10_shift_commoner_faith

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the fantasy antfarm simulation.",
        epilog=(
            "Operators: --verbose/-v for live events, --delay for pacing live output, "
            "--seed for reproducible alphanumeric worlds, --years for yearly duration override, "
            "--verbose-importance to filter live event noise."
        ),
    )
    parser.add_argument("--seed", type=str, default=DEFAULT_SEED, help="Alphanumeric seed for world generation. Omit for a fresh random world.")
    parser.add_argument("--years", type=int, default=DEFAULT_YEARS, help="How many years to simulate. Whole years only. Default is 1.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print events as the simulation runs instead of waiting for the final summary.")
    parser.add_argument("--delay", type=float, default=0.0, help="Optional delay in seconds between ticks when verbose mode is enabled.")
    parser.add_argument("--verbose-importance", type=int, default=VERBOSE_EVENT_IMPORTANCE, help="1-3, 3 = most. Only print live events at or above this importance level in verbose mode.")
    parser.add_argument("--pop-scale", "--population-scale", dest="pop_scale", type=_parse_population_scale, default=1.0, help="Scale regional population and capacity. Accepts values like 2, 0.25, or 1/4.")
    parser.add_argument("--psum", type=int, default=0, help="Write periodic summary snapshots every N simulated years. Example: --psum 1 or --psum 5. Default is off.")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    years = max(1, args.years)
    ticks = years * TICKS_PER_YEAR
    simulator = Simulator(
        seed=args.seed,
        verbose=args.verbose,
        verbose_delay=args.delay,
        verbose_min_importance=args.verbose_importance,
        population_scale=args.pop_scale,
    )
    simulator.world.source_files = {
        "simulator": Path(__file__).name,
        "class": "class_v22.py",
        "population": "population_v11.py",
        "legacy": "legacy_v6.py",
        "summary": "summary_v30.py",
    }

    simulator.world.output_dir = _make_run_output_dir(simulator.world.seed_used)
    simulator.world.output_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.perf_counter()
    interrupted = False
    try:
        simulator.run(ticks, periodic_summary_years=args.psum)
    except KeyboardInterrupt:
        interrupted = True
        print()
        print("Simulation interrupted. Writing partial summary from the current world state.")
    end_time = time.perf_counter()

    simulator.world.runtime_seconds = end_time - start_time
    summary_label = years if not interrupted else f"partial_{simulator.world.tick}ticks"

    summary.print_summary(simulator, summary_label)
    if simulator.world.polities:
        print()
        print("POLITIES")
        print("-" * 72)
        for polity in simulator.world.polities.values():
            ruler = simulator.world.actors.get(polity.ruler_id)
            ruler_name = ruler.short_name() if ruler and ruler.alive else "None"
            print(f"{polity.name}: ruler={ruler_name}, capital={simulator.world.region_name(polity.capital_region_id)}, regions={len(polity.region_ids)}, members={len(polity.member_actor_ids)}")
    _v10_print_summary_extra(simulator, summary_label)
    summary.write_summary(simulator, summary_label)

if __name__ == "__main__":
    main()
