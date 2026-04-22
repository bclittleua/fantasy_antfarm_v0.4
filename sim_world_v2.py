from __future__ import annotations

from typing import Dict, List, Optional, Tuple

class WorldBuildMixin:
    def _build_world(self, seed: str) -> World:
        regions = self._generate_regions(REGION_COUNT)
        scaled_initial_population = max(1, int(round(INITIAL_POPULATION * self.population_scale)))
        actors = self._generate_population(scaled_initial_population, regions)
        for actor in actors.values():
            if actor.is_adventurer():
                actor.duty_shift = self.rng.randrange(ADVENTURER_SHIFT_COUNT)
        monsters = self._generate_initial_monsters(regions)
        world = World(rng=self.rng, regions=regions, actors=actors, monsters=monsters, parties={}, seed_used=seed)
        world.next_actor_id = max(actors.keys(), default=0) + 1
        world.spawned_horror_titles = set(self._spawned_horror_titles)
        world.generated_by_role = self._count_generated_roles(actors)
        world.generated_monsters_by_kind = self._count_generated_monsters(monsters)
        world.region_activity = {rid: 0 for rid in regions}
        world.refugee_arrivals = 0
        world.refugee_commoners = 0
        world.population_scale = self.population_scale
        world.source_files = {
            "simulator": Path(__file__).name,
            "class": "class_v14.py",
            "population": "population_v8.py",
            "legacy": "legacy_v4.py",
            "relics": "relics_v2.py",
            "summary": "summary_v19.py",
        }
        self._seed_relics(world)
        world.initial_population = scaled_initial_population
        world.log(
            "A small continent of forest, plains, and highlands fills with common folk, wandering adventurers, lurking monsters, and distant divine attention.",
            importance=3,
            category="world",
        )
        return world


    def _count_generated_roles(self, actors: Dict[int, Actor]) -> Dict[Role, int]:
        counts = {role: 0 for role in Role}
        for actor in actors.values():
            counts[actor.role] += 1
        return counts


    def _count_generated_monsters(self, monsters: Dict[int, Monster]) -> Dict[MonsterKind, int]:
        counts = {kind: 0 for kind in MonsterKind}
        for monster in monsters.values():
            counts[monster.kind] += 1
        return counts


    def _generate_regions(self, count: int) -> Dict[int, Region]:
        regions: Dict[int, Region] = {}
        used_names = set()

        for region_id in range(count):
            biome = BIOMES[region_id % len(BIOMES)]
            size_factor = self.rng.uniform(REGION_SIZE_MIN, REGION_SIZE_MAX)
            if biome == "Plains":
                cap_min, cap_max = PLAINS_CAP_MIN, PLAINS_CAP_MAX
            elif biome == "Forest":
                cap_min, cap_max = FOREST_CAP_MIN, FOREST_CAP_MAX
            else:
                cap_min, cap_max = HIGHLANDS_CAP_MIN, HIGHLANDS_CAP_MAX
            base_capacity = int(self.rng.randint(cap_min, cap_max) * size_factor * self.population_scale)
            regions[region_id] = Region(
                id=region_id,
                name=self._unique_region_name(used_names),
                biome=biome,
                danger=self.rng.randint(1, 5),
                base_capacity=base_capacity,
                size_factor=size_factor,
            )
        for region_id in range(count):
            neighbors = set()
            if region_id > 0:
                neighbors.add(region_id - 1)
            if region_id < count - 1:
                neighbors.add(region_id + 1)
            while len(neighbors) < min(3, count - 1) and self.rng.random() < 0.55:
                pick = self.rng.randrange(count)
                if pick != region_id:
                    neighbors.add(pick)
            regions[region_id].neighbors = sorted(neighbors)
        for region_id, region in regions.items():
            for neighbor_id in list(region.neighbors):
                if region_id not in regions[neighbor_id].neighbors:
                    regions[neighbor_id].neighbors.append(region_id)
                    regions[neighbor_id].neighbors.sort()
        return regions


    def _unique_region_name(self, used_names: set[str]) -> str:
        while True:
            name = f"{self.rng.choice(REGION_PREFIXES)}{self.rng.choice(REGION_SUFFIXES)}"
            if name not in used_names:
                used_names.add(name)
                return name


    def _region_base_capacity(self, biome: str) -> int:
        if biome == "Plains":
            low, high = PLAINS_CAP_MIN, PLAINS_CAP_MAX
        elif biome == "Forest":
            low, high = FOREST_CAP_MIN, FOREST_CAP_MAX
        else:
            low, high = HIGHLANDS_CAP_MIN, HIGHLANDS_CAP_MAX
        size_factor = self.rng.uniform(REGION_SIZE_MIN, REGION_SIZE_MAX)
        return int(self.rng.randint(low, high) * size_factor)


    def _effective_region_capacity(self, region) -> int:
        capacity = max(1, getattr(region, "base_capacity", 1_000_000))
        modifier = 1.0
        modifier *= 0.75 + (region.order / 200.0)          # 0.75 .. 1.25
        modifier *= 0.85 + (max(-50, region.control) / 400.0)  # ~0.725 .. 1.10
        modifier *= max(0.70, 1.05 - (region.danger * 0.05))   # danger pressure
        return max(1000, int(capacity * modifier))


    def _generate_initial_monsters(self, regions: Dict[int, Region]) -> Dict[int, Monster]:
        monsters: Dict[int, Monster] = {}
        seeded_horror = False
        for region_id in regions:
            goblins = self.rng.randint(2, 5)
            for _ in range(goblins):
                monster = self._make_goblin(region_id)
                monsters[monster.id] = monster
            if self.rng.random() < 0.15:
                monster = self._make_giant(region_id)
                monsters[monster.id] = monster
            if self.rng.random() < 0.01:
                monster = self._make_dragon(region_id)
                monsters[monster.id] = monster
            if (not seeded_horror) and self.rng.random() < 0.03:
                monster = self._make_horror(region_id)
                if monster is not None:
                    monsters[monster.id] = monster
                    seeded_horror = True
        return monsters


    def _make_goblin(self, region_id: int) -> Monster:
        monster_id = self._consume_monster_id()
        return Monster(
            id=monster_id,
            name=f"Goblin rabble {monster_id}",
            kind=MonsterKind.GOBLIN,
            region_id=region_id,
            power=self.rng.randint(2, 4),
            hostility=6,
            charisma=self.rng.randint(2, 6),
            intelligence=self.rng.randint(4, 8),
            horde_size=self.rng.randint(4, 12),
            reputation=1,
        )


    def _make_giant(self, region_id: int) -> Monster:
        monster_id = self._consume_monster_id()
        return Monster(
            id=monster_id,
            name=self.rng.choice(GIANT_TYPES),
            kind=MonsterKind.GIANT,
            region_id=region_id,
            power=self.rng.randint(12, 18),
            hostility=7,
            charisma=4,
            intelligence=6,
            horde_size=1,
            reputation=5,
        )


    def _make_dragon(self, region_id: int) -> Monster:
        monster_id = self._consume_monster_id()
        color = self.rng.choice(CHROMATIC_DRAGONS)
        temperament = self._dragon_temperament(color)
        hostility = 4 if temperament == "benevolent" else 6 if temperament == "ambivalent" else 9
        return Monster(
            id=monster_id,
            name=f"{color} Dragon",
            kind=MonsterKind.DRAGON,
            region_id=region_id,
            power=self.rng.randint(28, 40),
            hostility=hostility,
            charisma=8,
            intelligence=12,
            horde_size=1,
            reputation=12,
            dragon_color=color,
            dragon_temperament=temperament,
        )


    def _make_horror(self, region_id: int) -> Optional[Monster]:
        available = [h for h in HORROR_TITLES if h not in self._spawned_horror_titles]
        if not available:
            return None

        name = self.rng.choice(available)
        self._spawned_horror_titles.add(name)

        monster_id = self._consume_monster_id()
        return Monster(
            id=monster_id,
            name=name,
            kind=MonsterKind.ANCIENT_HORROR,
            region_id=region_id,
            power=self.rng.randint(35, 50),
            hostility=9,
            charisma=12,
            intelligence=16,
            horde_size=1,
            reputation=20,
        )


    def _consume_monster_id(self) -> int:
        monster_id = self._monster_id_counter
        self._monster_id_counter += 1
        return monster_id


    def _random_seed_string(self) -> str:
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        return "".join(random.SystemRandom().choice(alphabet) for _ in range(12))


