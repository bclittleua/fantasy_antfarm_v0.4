
from __future__ import annotations
from typing import Optional, Tuple, List, Dict
import io
import re
from pathlib import Path
from contextlib import redirect_stdout


def _aggregate_commoners(world) -> int:
    return sum(getattr(world, 'commoners_by_region', {}).values()) if hasattr(world, 'commoners_by_region') else 0


def _living_population(world) -> int:
    return len(world.living_actors()) + _aggregate_commoners(world)


def _living_by_role(world, sim):
    living_by_role = {role: 0 for role in sim.Role}
    for actor in world.living_actors():
        living_by_role[actor.role] += 1
    if hasattr(world, 'commoners_by_region'):
        living_by_role[sim.Role.COMMONER] = _aggregate_commoners(world)
    return living_by_role


def _commoner_deity_counts(world, sim) -> Dict[object, int]:
    counts = {deity: 0 for deity in sim.Deity}
    faith = getattr(world, "commoner_faith_by_region", {})
    for region_map in faith.values():
        for deity in sim.Deity:
            counts[deity] += region_map.get(deity, 0)
    return counts


def _deity_influence_summary(sim) -> List[Tuple[object, int, int, int, int, float]]:
    surviving = sim.world.living_actors()
    soul_weight = 2
    commoner_counts = _commoner_deity_counts(sim.world, sim)
    results = []
    total_influence = 0
    for deity in sim.Deity:
        living = len([actor for actor in surviving if actor.deity == deity])
        commoners = commoner_counts.get(deity, 0)
        souls = sim.world.souls_by_deity.get(deity, 0)
        influence = living + commoners + (souls * soul_weight)
        results.append((deity, living, commoners, souls, influence, 0.0))
        total_influence += influence
    if total_influence <= 0:
        return [(deity, living, commoners, souls, influence, 0.0) for deity, living, commoners, souls, influence, _ in results]
    final = []
    for deity, living, commoners, souls, influence, _ in results:
        final.append((deity, living, commoners, souls, influence, influence / total_influence * 100.0))
    return final


def _pick_top_hero_and_villain(sim) -> Tuple[Optional[object], Optional[object]]:
    everyone = [a for a in sim.world.actors.values() if a.is_adventurer()]
    heroes = [a for a in everyone if not a.is_evil()]
    villains = [a for a in everyone if a.is_evil()]
    hero = max(heroes, key=_adventurer_score, default=None)
    villain = max(villains, key=_villain_score, default=None)
    return hero, villain


def _adventurer_score(actor):
    return (
        actor.reputation,
        actor.dragon_kills,
        actor.horror_kills,
        actor.monster_kills,
        actor.kills,
        actor.power_rating(),
    )


def _villain_score(actor):
    return (
        actor.reputation,
        actor.regions_oppressed,
        actor.kills,
        actor.monster_kills,
        actor.power_rating(),
    )


def _historical_population_estimate(world):
    living_adventurers = len(world.living_actors())
    total_adventurers = len(world.actors)
    dead_adventurers = total_adventurers - living_adventurers
    living_commoners = sum(world.commoners_by_region.values()) if hasattr(world, "commoners_by_region") else 0
    return living_adventurers + dead_adventurers + living_commoners


def _source_files(world):
    if hasattr(world, "source_files"):
        return world.source_files
    return {}


def _month_names(sim, world):
    return getattr(sim, "MONTH_NAMES", None) or getattr(world, "MONTH_NAMES", None) or [
        "Dawnsreach", "Rainmoot", "Bloomtide", "Suncrest", "Goldfire", "Highsun",
        "Harvestwane", "Emberfall", "Duskmarch", "Frostturn", "Deepcold", "Yearsend",
    ]


def _short_date_from_parts(day, month, year, month_names):
    if day is None or month is None or year is None:
        return "Unknown"
    if not isinstance(month, int) or month < 1 or month > len(month_names):
        return f"{int(day):02d} ? {int(year)}"
    return f"{int(day):02d} {month_names[month - 1]} {int(year)}"


def _short_date_from_timestamp(timestamp: Optional[str]) -> str:
    if not timestamp:
        return "Unknown"
    m = re.match(r"Year\s+(-?\d+),\s+\w+,\s+([A-Za-z]+)\s+(\d+),", str(timestamp))
    if not m:
        return "Unknown"
    year = int(m.group(1))
    month_name = m.group(2)
    day = int(m.group(3))
    return f"{day:02d} {month_name} {year}"


def _short_birth_date(sim, world, actor) -> str:
    return _short_date_from_parts(
        getattr(actor, "birth_day", None),
        getattr(actor, "birth_month", None),
        getattr(actor, "birth_year", None),
        _month_names(sim, world),
    )


def _death_line(actor) -> str:
    if not getattr(actor, "death_timestamp", None):
        return "—"
    cause = getattr(actor, "death_cause", None) or "Unknown"
    return f"{_short_date_from_timestamp(actor.death_timestamp)} — {cause}"


def _print_section(title: str) -> None:
    print(title)
    print("-" * 72)


def _event_bucket(events):
    births, deaths, feats, monsters, parties, politics, immortals = [], [], [], [], [], [], []
    for event in events:
        cat = getattr(event, "category", "") or ""
        text = getattr(event, "text", "")
        low = text.lower()

        if cat in {"birth", "legacy_birth", "coming_of_age"}:
            births.append(event)
            continue
        if cat in {"notable_death", "champion_death"} or " dies " in low or low.startswith("an assassination plot"):
            deaths.append(event)
            continue
        if cat in {"monster_attack", "monster_spawn", "monster_retreat", "goblin_raid", "goblin_loyalty", "dragon_judgment", "legendary_monster_kill"} or any(
            term in low for term in ["dragon", "giant", "goblin", "ancient horror", "horror", "terrorizes", "brings ruin", "rumors spread of a"]
        ):
            monsters.append(event)
            continue
        if cat in {"party_coup", "party_split"} or "party forms" in low or "seizes control of" in low or "fractures" in low:
            parties.append(event)
            continue
        if cat in {"polity", "polity_challenge", "succession"} or any(
            term in low for term in ["kingdom of", "succeeds to the rule", "collapses after the death of its ruler", "subjugating", "claims ", "revolt tears", "preserves "]
        ):
            politics.append(event)
            continue
        if cat in {"champion", "champion_death", "recovery"} or any(
            term in low for term in ["champion of", "worship of", "fracture under its own weight", "shield", "curse", "god of chance", "lord of light", "lord of darkness"]
        ):
            immortals.append(event)
            continue
        feats.append(event)
    return births, deaths, feats, monsters, parties, politics, immortals


def _top_adventurers(world):
    return sorted(
        [actor for actor in world.actors.values() if actor.is_adventurer()],
        key=_adventurer_score,
        reverse=True,
    )


def _print_adventurer_block(world, sim, title, adventurers, limit):
    print(f"\n{title}")
    print("  |------------------------------------------------------------------")
    for actor in adventurers[:limit]:
        spouse = world.actors.get(actor.spouse_id)
        bff = world.actors.get(actor.best_friend_id)
        nemesis = world.actors.get(actor.nemesis_id)
        retired = getattr(actor, "retired", False)
        print(f"  | {actor.full_name()}")
        print(f"  |   role={actor.role.value}  alignment={actor.alignment.name}  deity={actor.deity.value}")
        print(f"  |   lvl={getattr(actor, 'level', 1)}  rep={actor.reputation}  xp={getattr(actor, 'experience', 0)}")
        print(f"  |   kills={actor.kills}  mkills={actor.monster_kills}  dragons={actor.dragon_kills}  horrors={actor.horror_kills}")
        print(f"  |   Born: {_short_birth_date(sim, world, actor)}")
        print(f"  |   Died: {_death_line(actor)}")
        print(f"  |   spouse={spouse.short_name() if spouse else None}  bfForever={bff.short_name() if bff else None}  nemesis={nemesis.short_name() if nemesis else None}")
        status = "living" if actor.alive else "dead"
        if retired and actor.alive:
            status += " retired"
        print(f"  |   status={status}  region={world.region_name(actor.region_id)}")
        print("  |------------------------------------------------------------------")


def _tick_to_short_date(sim, tick: Optional[int]) -> str:
    if tick is None:
        return "Unknown"
    tick = int(tick)
    day_index = tick // 3
    year = day_index // 360 + 1
    day_of_year = day_index % 360
    month = day_of_year // 30 + 1
    day = day_of_year % 30 + 1
    return _short_date_from_parts(day, month, year, _month_names(sim, sim.world))


def _print_event_list(title, events, limit):
    print(title)
    if not events:
        print("  None.")
        print()
        return
    for event in events[-limit:]:
        print(f"  [{event.timestamp}] {event.text}")
    print()


def print_summary(sim, years=None) -> None:
    world = sim.world
    for region_id in world.regions:
        world.evaluate_region_rule(region_id)

    hero, villain = _pick_top_hero_and_villain(sim)
    living_population = _living_population(world)
    historical_population_estimate = _historical_population_estimate(world)
    living_by_role = _living_by_role(world, sim)
    aggregate_commoners = _aggregate_commoners(world)
    source_files = _source_files(world)

    good_regions = len([r for r in world.regions.values() if r.control >= 20])
    evil_regions = len([r for r in world.regions.values() if r.control <= -20])
    contested = len(world.regions) - good_regions - evil_regions
    avg_order = sum(region.order for region in world.regions.values()) / len(world.regions)

    all_adv = _top_adventurers(world)
    births, deaths, feats, monsters, parties, politics, immortals = _event_bucket(world.events)

    _print_section("RUN METRICS")
    print(f"Seed: {world.seed_used}")
    print(f"Ticks simulated: {world.tick}")
    if years is not None:
        print(f"Summary label: {years}")
    if hasattr(world, "initial_population"):
        print(f"Initial population target: {getattr(world, 'initial_population', 'unknown')}")
    if hasattr(world, "population_scale"):
        print(f"Population scale: {getattr(world, 'population_scale', 1.0):g}")
    runtime_seconds = getattr(world, "runtime_seconds", None)
    if runtime_seconds is not None:
        print(f"Realtime duration: {runtime_seconds:.2f} seconds ({runtime_seconds / 60.0:.2f} minutes)")
    year, month, day, tod, season = world.current_calendar()
    print(f"Current date: Year {year}, {season}, {_month_names(sim, world)[month - 1]} {day}, {tod}")
    print(f"Living population: {living_population}")
    print(f"Historical population estimate: {historical_population_estimate}")
    print(f"Living adventurers: {len(world.living_actors())}")
    print(f"Dead adventurers recorded: {len(world.actors) - len(world.living_actors())}")
    print(f"Living monsters: {len(world.living_monsters())} / {sum(world.generated_monsters_by_kind.values())}")
    print(f"Active parties: {len(world.parties)}")
    if source_files:
        print("Source files:")
        for key in ("simulator", "class", "population", "legacy", "relics", "summary"):
            if key in source_files:
                print(f"  {key:10} {source_files[key]}")
    print()

    _print_section("DEMOGRAPHICS")
    print("Population by role:")
    for role in sim.Role:
        print(f"  {role.value:10} {living_by_role[role]:8} / {world.generated_by_role.get(role, 0):8}")
    print("Birth metrics:")
    print(f"  Commoner births: {getattr(world, 'commoner_births', 0)}")
    print(f"  Adventurer-lineage births: {getattr(world, 'adventurer_lineage_births', 0)}")
    print(f"  Living commoners (aggregate): {aggregate_commoners}")
    refugee_arrivals = getattr(world, 'refugee_arrivals', 0)
    refugee_commoners = getattr(world, 'refugee_commoners', 0)
    if refugee_arrivals or refugee_commoners:
        print(f"  Refugee waves: {refugee_arrivals}")
        print(f"  Refugees settled: {refugee_commoners}")
    print("Immortal influence:")
    for deity, living, commoners, souls, influence, pct in _deity_influence_summary(sim):
        print(f"  {deity.value:16} living={living:4} commoners={commoners:8} souls={souls:5} influence={influence:9} share={pct:5.1f}%")
    print()

    _print_section("WORLD CONDITION")
    if evil_regions == len(world.regions) or (avg_order < 15 and evil_regions >= len(world.regions) - 1):
        assessment = "The continent is fully lost to darkness. Little hope remains."
    elif avg_order >= 60 and good_regions >= evil_regions:
        assessment = "The continent is broadly stable and still capable of thriving."
    elif avg_order < 35 or evil_regions > good_regions + 2:
        assessment = "The continent is slipping into chaos and oppression."
    else:
        assessment = "The continent remains divided, with pockets of order resisting wider instability."
    print(f"Good-leaning regions: {good_regions}")
    print(f"Evil-leaning regions: {evil_regions}")
    print(f"Contested regions: {contested}")
    print(f"Average order: {avg_order:.1f}")
    print(f"Assessment: {assessment}")
    print()

    _print_section("TOP ADVENTURER LISTS")
    if hero is not None:
        print("Most celebrated hero:")
        print(f"  {hero.full_name()} — {hero.alignment.value}, {hero.role.value}, rep={hero.reputation}, region={world.region_name(hero.region_id)}")
        print(f"  Born: {_short_birth_date(sim, world, hero)}")
        print(f"  Died: {_death_line(hero)}")
        print(f"  Deeds: {hero.notable_deeds_summary()}")
        print()
    if villain is not None:
        print("Most feared villain:")
        print(f"  {villain.full_name()} — {villain.alignment.value}, {villain.role.value}, rep={villain.reputation}, region={world.region_name(villain.region_id)}")
        print(f"  Born: {_short_birth_date(sim, world, villain)}")
        print(f"  Died: {_death_line(villain)}")
        print(f"  Deeds: {villain.notable_deeds_summary()}")
        print()

    _print_adventurer_block(world, sim, "Top 25 adventurers, living and dead:", all_adv, 25)
    for role_name in ("FIGHTER", "WARDEN", "WIZARD", "BARD"):
        role = getattr(sim.Role, role_name, None)
        if role is None:
            continue
        role_adv = [a for a in all_adv if a.role == role]
        _print_adventurer_block(world, sim, f"Top 10 {role.value}s:", role_adv, 10)
    print()

    _print_section("NOTABLE BIRTHS")
    _print_event_list("", births, 20)

    _print_section("NOTABLE DEATHS")
    _print_event_list("", deaths, 30)

    _print_section("NOTABLE FEATS")
    _print_event_list("", feats, 30)

    _print_section("MONSTER ACTIVITY")
    print("Monsters still abroad:")
    living_monsters_by_kind = {kind: 0 for kind in sim.MonsterKind}
    for monster in world.living_monsters():
        living_monsters_by_kind[monster.kind] += 1
    for kind in sim.MonsterKind:
        print(f"  {kind.value:14} {living_monsters_by_kind[kind]:3} / {world.generated_monsters_by_kind[kind]:3}")
    print()
    _print_event_list("", monsters, 25)

    _print_section("PARTY ACTIVITY")
    party_history = list(getattr(world, 'party_history', {}).values())
    if party_history:
        print("Top parties in history:")
        ranked_parties = sorted(party_history, key=lambda p: (p.peak_size, p.peak_reputation, p.founded_tick), reverse=True)[:10]
        for party in ranked_parties:
            region_name = world.region_name(party.last_region_id) if party.last_region_id is not None and party.last_region_id in world.regions else "Unknown"
            print(f"  {party.name} — founder={party.founder_name}, peak_size={party.peak_size}, peak_rep={party.peak_reputation}, last_region={region_name}, fate={party.fate}")
        print()
    influential_party = max(
        world.parties.values(),
        key=lambda p: (len(p.member_ids), sum(world.actors[mid].reputation for mid in p.member_ids if mid in world.actors)),
        default=None,
    )
    if influential_party is not None:
        leader_name = world.actors[influential_party.leader_id].short_name() if influential_party.leader_id in world.actors else "Unknown"
        print(f"Most influential active party: {influential_party.name or f'Party {influential_party.id}'} — leader={leader_name}, size={len(influential_party.member_ids)}, large_group={influential_party.is_large_group}")
        print()
    _print_event_list("", parties, 25)

    _print_section("POLITICAL ACTIVITY")
    polity_history = list(getattr(world, 'polity_history', {}).values())
    if polity_history:
        print("Top polities in history:")
        ranked_polities = sorted(polity_history, key=lambda p: (p.peak_regions, p.peak_strength, p.founded_tick), reverse=True)[:10]
        for polity in ranked_polities:
            capital_name = world.region_name(polity.capital_region_id) if polity.capital_region_id is not None and polity.capital_region_id in world.regions else "Unknown"
            print("  /" + "=" * 66 + "\\")
            print(f"  | {polity.name}")
            print(f"  |   founded={_tick_to_short_date(sim, getattr(polity, 'founded_tick', None))}")
            print(f"  |   founder={polity.founder_name}")
            print(f"  |   current_ruler={getattr(polity, 'current_ruler_name', 'Unknown')}")
            print(f"  |   alignment={polity.alignment}")
            print(f"  |   peak_regions={polity.peak_regions}  peak_strength={polity.peak_strength}")
            print(f"  |   capital={capital_name}")
            print(f"  |   fate={polity.fate}")
            if getattr(polity, 'leaders', None):
                print("  |   ruler history:")
                for leader in polity.leaders:
                    print(f"  |     - {leader.name}: {leader.fate}")
            print("  \\" + "=" * 66 + "/")
        print()
    if hasattr(world, 'polities') and world.polities:
        print("Active polities:")
        for polity in sorted(world.polities.values(), key=lambda p: (len(getattr(p, 'region_ids', [])), getattr(p, 'strength', 0), p.name), reverse=True)[:12]:
            ruler_name = world.actors[polity.ruler_id].short_name() if polity.ruler_id in world.actors and world.actors[polity.ruler_id].alive else 'None'
            print(f"  {polity.name} — ruler={ruler_name}, alignment={polity.alignment.value}, regions={len(polity.region_ids)}, stability={getattr(polity, 'stability', 0)}, legitimacy={getattr(polity, 'legitimacy', 0)}, challenges={getattr(polity, 'challenge_count', 0)}")
        print()
    _print_event_list("", politics, 25)

    _print_section("IMMORTAL ACTIONS")
    _print_event_list("", immortals, 20)


def write_summary(sim, years) -> Path:
    seed = sim.world.seed_used
    label = str(years)
    if label.isdigit():
        filename = f"fantfarm_{seed}_{label}year_summary.txt"
    else:
        filename = f"fantfarm_{seed}_{label}_summary.txt"

    output_dir = Path(getattr(sim.world, "output_dir", "."))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print_summary(sim, years)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(buffer.getvalue())

    return output_path
