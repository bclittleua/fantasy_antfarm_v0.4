from __future__ import annotations

from typing import Dict, List, Optional, Tuple

class MonsterMixin:
    def _monster_spawn_scale(self) -> float:
        state = self._recovery_state()
        if state == 'crisis':
            return RECOVERY_MONSTER_SPAWN_SCALE_CRISIS
        if state == 'low':
            return RECOVERY_MONSTER_SPAWN_SCALE_LOW
        return 1.0


    def _build_region_threat_snapshot(self) -> Dict[int, Dict[str, bool]]:
        world = self.world
        snapshot: Dict[int, Dict[str, bool]] = {}
        for region_id in world.regions:
            local_actors = world.actors_in_region(region_id)
            local_monsters = world.monsters_in_region(region_id)
            snapshot[region_id] = {
                "evil_adventurers": any(actor.is_adventurer() and actor.is_evil() for actor in local_actors),
                "major_monsters": any(
                    monster.alive and monster.kind in (MonsterKind.GOBLIN, MonsterKind.GIANT, MonsterKind.DRAGON, MonsterKind.ANCIENT_HORROR)
                    for monster in local_monsters
                ),
            }
        return snapshot


    def _dragon_temperament(self, color: str) -> str:
        if color in BENEVOLENT_DRAGONS:
            return "benevolent"
        if color in AMBIVALENT_DRAGONS:
            return "ambivalent"
        return "malevolent"


    def _monster_hostile_to_actor(self, monster: Monster, actor: Actor) -> bool:
        if monster.kind != MonsterKind.DRAGON:
            return True
        temperament = getattr(monster, "dragon_temperament", "malevolent")
        if temperament == "benevolent":
            return actor.is_evil()
        if temperament == "ambivalent":
            return actor.is_evil() or actor.reputation >= 90
        return True


    def _monster_strength_bonus(self, monster: Monster) -> int:
        age_bonus = min(MONSTER_MAX_AGE_BONUS, getattr(monster, 'age_ticks', 0) // MONSTER_AGE_POWER_STEP_TICKS)
        xp_bonus = min(MONSTER_MAX_XP_BONUS, getattr(monster, 'monster_xp', 0) // MONSTER_XP_POWER_STEP)
        return age_bonus + xp_bonus


    def _monster_survival_ratio(self, monster: Monster) -> float:
        base = max(1, monster.power)
        effective = max(1, monster.effective_power())
        return min(2.0, effective / base)


    def _monster_should_retreat_from_actor(self, monster: Monster, actor: Actor) -> bool:
        world = self.world
        if getattr(monster, 'retreat_until_tick', -1) > world.tick:
            return True
        side = world.side_members(actor)
        side_power = sum(member.power_rating() for member in side if member.alive)
        monster_power = monster.effective_power()
        party = world.get_party(actor)
        party_size = len(party.member_ids) if party is not None else 1
        if party_size >= 3 and monster.kind == MonsterKind.GIANT and self.rng.random() < 0.75:
            return True
        if party_size >= 4 and monster.kind == MonsterKind.DRAGON and self.rng.random() < 0.85:
            return True
        if side_power >= monster_power * MONSTER_RETREAT_AVOID_RATIO and self.rng.random() < 0.90:
            return True
        if side_power >= monster_power * 0.75 and monster.kind in (MonsterKind.DRAGON, MonsterKind.GIANT) and self.rng.random() < 0.70:
            return True
        return False


    def _monster_retreat(self, monster: Monster) -> bool:
        world = self.world
        region = world.regions[monster.region_id]
        if not region.neighbors:
            monster.retreat_until_tick = world.tick + self.rng.randint(MONSTER_RETREAT_COOLDOWN_MIN, MONSTER_RETREAT_COOLDOWN_MAX)
            return False
        destination = min(
            region.neighbors,
            key=lambda rid: (
                len([a for a in world.actors_in_region(rid) if a.alive and a.is_adventurer()]),
                -world.regions[rid].danger,
                self.rng.random(),
            ),
        )
        old_region = monster.region_id
        monster.region_id = destination
        monster.retreat_until_tick = world.tick + self.rng.randint(MONSTER_RETREAT_COOLDOWN_MIN, MONSTER_RETREAT_COOLDOWN_MAX)
        if monster.kind != MonsterKind.GOBLIN:
            world.log(f"{monster.name} slips away from {world.region_name(old_region)} to {world.region_name(destination)}.", importance=1, category="monster_retreat")
        return True


    def _tick_monster_age_and_terror(self) -> None:
        world = self.world
        for monster in world.living_monsters():
            monster.age_ticks = getattr(monster, 'age_ticks', 0) + 1
            if getattr(monster, 'retreat_until_tick', -1) < world.tick and monster.kind != MonsterKind.ANCIENT_HORROR and self.rng.random() < 0.02:
                monster.monster_xp = getattr(monster, 'monster_xp', 0) + 1
        if world.tick % MONSTER_TERROR_ORDER_DECAY_INTERVAL != 0:
            return
        for monster in world.living_monsters():
            terror = 0
            if monster.kind == MonsterKind.GOBLIN:
                terror = 1 + self._monster_strength_bonus(monster) // 12 if monster.horde_size >= 8 else 0
            elif monster.kind == MonsterKind.GIANT:
                terror = 4 + self._monster_strength_bonus(monster) // 6
            elif monster.kind == MonsterKind.DRAGON:
                terror = 2 + self._monster_strength_bonus(monster) // 8
            elif monster.kind == MonsterKind.ANCIENT_HORROR:
                terror = 6 + self._monster_strength_bonus(monster) // 4
            if terror:
                world.adjust_region_state(monster.region_id, control_delta=0, order_delta=-terror)


    def _monster_spawn_check(self) -> None:
        world = self.world
        if world.tick % 30 != 0:
            return
        spawn_scale = self._monster_spawn_scale()
        if spawn_scale <= 0:
            return
        if self._recovery_state() != 'crisis' and self._maybe_spawn_horror_for_dominance():
            return
        if self._recovery_state() != 'crisis' and self._maybe_spawn_dragon_for_polities():
            return
        region_id = self.rng.choice(list(world.regions.keys()))
        roll = self.rng.random() / max(0.01, spawn_scale)
        new_monster: Optional[Monster] = None
        if roll < 0.20:
            new_monster = self._make_goblin(region_id)
        elif roll < 0.225:
            giants = [m for m in world.living_monsters() if m.kind == MonsterKind.GIANT]
            if len(giants) < MAX_WILD_GIANTS:
                new_monster = self._make_giant(region_id)
        elif roll < 0.228:
            dragons = [m for m in world.living_monsters() if m.kind == MonsterKind.DRAGON]
            if len(dragons) < MAX_WILD_DRAGONS:
                new_monster = self._make_dragon(region_id)
        if new_monster is not None:
            world.monsters[new_monster.id] = new_monster
            world.generated_monsters_by_kind[new_monster.kind] += 1
            if new_monster.kind != MonsterKind.GOBLIN:
                world.log(f"Rumors spread of a {new_monster.name} appearing near {world.region_name(region_id)}.", importance=2, category="monster_spawn")


    def _monster_turn(self, monster: Monster) -> None:
        world = self.world
        if getattr(monster, "retreat_until_tick", -1) > world.tick:
            return
        if monster.kind == MonsterKind.GOBLIN:
            self._goblin_turn(monster)
            return
        if monster.kind == MonsterKind.DRAGON:
            dragons = [m for m in world.living_monsters() if m.kind == MonsterKind.DRAGON]
            if len(dragons) < MAX_WILD_DRAGONS and self.rng.random() < DRAGON_REPRO_CHANCE:
                baby = self._make_dragon(monster.region_id)
                world.monsters[baby.id] = baby
                world.generated_monsters_by_kind[baby.kind] += 1
        if monster.kind != MonsterKind.ANCIENT_HORROR and self.rng.random() < 0.18:
            region = world.regions[monster.region_id]
            if region.neighbors:
                monster.region_id = self.rng.choice(region.neighbors)
        locals_ = world.actors_in_region(monster.region_id)
        aggression = 0.10 * self._monster_spawn_scale()
        aggression += min(0.08, self._monster_strength_bonus(monster) * 0.004)
        commoners = world.commoners_by_region.get(monster.region_id, 0) if hasattr(world, 'commoners_by_region') else 0
        if commoners > 0 and monster.kind in (MonsterKind.GOBLIN, MonsterKind.GIANT, MonsterKind.DRAGON, MonsterKind.ANCIENT_HORROR):
            raid_rate = MONSTER_COMMONER_RAID_BASE + self._monster_strength_bonus(monster) * MONSTER_COMMONER_RAID_SCALE
            if monster.kind == MonsterKind.DRAGON:
                raid_rate += 0.01
            elif monster.kind == MonsterKind.ANCIENT_HORROR:
                raid_rate += 0.02
            if self.rng.random() < min(0.35, raid_rate):
                loss = 0
                if monster.kind == MonsterKind.GOBLIN:
                    loss = self.rng.randint(1, max(2, monster.horde_size))
                elif monster.kind == MonsterKind.GIANT:
                    loss = self.rng.randint(4, 14 + self._monster_strength_bonus(monster))
                elif monster.kind == MonsterKind.DRAGON:
                    loss = self.rng.randint(12, 40 + self._monster_strength_bonus(monster) * 2)
                else:
                    loss = self.rng.randint(20, 60 + self._monster_strength_bonus(monster) * 3)
                loss = min(commoners, loss)
                if loss > 0:
                    world.commoners_by_region[monster.region_id] = max(0, commoners - loss)
                    self._remove_commoner_deaths(monster.region_id, loss)
                    monster.monster_xp = getattr(monster, 'monster_xp', 0) + max(1, loss // 5)
                    world.adjust_region_state(monster.region_id, control_delta=-2, order_delta=-(2 + min(8, loss // 8)))
                    world.log(f"{monster.name} terrorizes {world.region_name(monster.region_id)}, leaving {loss} commoners dead or scattered.", importance=2, category="monster_attack")
                    if monster.kind != MonsterKind.ANCIENT_HORROR and self.rng.random() < 0.65:
                        self._monster_retreat(monster)
                    return
        if monster.kind == MonsterKind.DRAGON:
            temperament = getattr(monster, "dragon_temperament", "malevolent")
            if temperament == "benevolent":
                targets = [a for a in locals_ if a.alive and a.is_evil()]
                if targets and self.rng.random() < 0.20:
                    target = self.rng.choice(targets)
                    if self.rng.random() < 0.35:
                        self._mark_actor_dead(target, f"judgment of {monster.name}", importance=2)
                        target.death_killer_id = None
                        monster.monster_xp = getattr(monster, "monster_xp", 0) + 2
                        world.log(f"{monster.name} descends on {target.short_name()} in {world.region_name(monster.region_id)}.", importance=2, category="dragon_judgment")
                    else:
                        target.recovering = max(target.recovering, 3)
                        monster.monster_xp = getattr(monster, "monster_xp", 0) + 1
                    world.adjust_region_state(monster.region_id, control_delta=1, order_delta=1)
                return
            if temperament == "ambivalent":
                rich_region = getattr(world, "commoners_by_region", {}).get(monster.region_id, 0) >= 700
                targets = [a for a in locals_ if a.alive and a.is_evil()]
                if targets and self.rng.random() < 0.15:
                    target = self.rng.choice(targets)
                    if self.rng.random() < 0.28:
                        self._mark_actor_dead(target, f"wrath of {monster.name}", importance=2)
                        monster.monster_xp = getattr(monster, "monster_xp", 0) + 2
                    else:
                        target.recovering = max(target.recovering, 2)
                        monster.monster_xp = getattr(monster, "monster_xp", 0) + 1
                    world.adjust_region_state(monster.region_id, control_delta=1, order_delta=0)
                    return
                if not rich_region:
                    return

        if monster.kind in (MonsterKind.DRAGON, MonsterKind.GIANT, MonsterKind.ANCIENT_HORROR) and locals_ and self.rng.random() < aggression:
            hostile_targets = [a for a in locals_ if a.alive]
            if not hostile_targets:
                return
            strongest_group = max((world.side_power(a) for a in hostile_targets), default=0)
            if strongest_group >= monster.effective_power() * MONSTER_RETREAT_AVOID_RATIO and monster.kind != MonsterKind.ANCIENT_HORROR:
                self._monster_retreat(monster)
                return
            victims = self.rng.sample(hostile_targets, k=min(len(hostile_targets), self.rng.randint(1, 3)))
            deaths = 0
            for victim in victims:
                if self.rng.random() < 0.30:
                    self._mark_actor_dead(victim, f"monster attack by {monster.name}")
                    deaths += 1
                else:
                    victim.recovering = max(victim.recovering, 2)
            monster.monster_xp = getattr(monster, "monster_xp", 0) + max(1, deaths + len(victims))
            world.adjust_region_state(monster.region_id, control_delta=-2, order_delta=-3)
            world.log(f"{monster.name} brings ruin to {world.region_name(monster.region_id)}, leaving {deaths} dead.", importance=2, category="monster_attack")
            if monster.kind != MonsterKind.ANCIENT_HORROR and self.rng.random() < 0.35:
                self._monster_retreat(monster)


    def _goblin_turn(self, monster: Monster) -> None:
        world = self.world
        if monster.patron_actor_id is not None:
            patron = world.actors.get(monster.patron_actor_id)
            if patron and patron.alive:
                monster.region_id = patron.region_id
                if self.rng.random() < 0.30:
                    monster.horde_size += 1
                return
            monster.patron_actor_id = None
        evil_leaders = [actor for actor in world.actors_in_region(monster.region_id) if actor.is_adventurer() and actor.is_evil() and actor.reputation >= 8 and actor.charisma >= 12]
        if evil_leaders and self.rng.random() < 0.30:
            leader = max(evil_leaders, key=lambda a: (a.reputation, a.charisma))
            monster.patron_actor_id = leader.id
            world.log(f"{leader.short_name()} brings {monster.name} to heel in {world.region_name(monster.region_id)}.", importance=2, category="goblin_loyalty")
            return
        if self.rng.random() < 0.25:
            region = world.regions[monster.region_id]
            if region.neighbors:
                monster.region_id = self.rng.choice(region.neighbors)
        locals_ = world.actors_in_region(monster.region_id)
        raid_chance = 0.30 * self._monster_spawn_scale()
        if locals_ and self.rng.random() < raid_chance:
            commoners = [actor for actor in locals_ if actor.role == Role.COMMONER]
            if commoners:
                losses = min(len(commoners), self.rng.randint(0, 2))
                if losses > 0:
                    victims = self.rng.sample(commoners, k=losses)
                    for victim in victims:
                        self._mark_actor_dead(victim, f"goblin raid by {monster.name}")
                if self.rng.random() < 0.35:
                    monster.horde_size += 1
                world.adjust_region_state(monster.region_id, control_delta=-2, order_delta=-2)
                world.log(f"{monster.name} raids {world.region_name(monster.region_id)} with {monster.horde_size} goblins at its back.", importance=2, category="goblin_raid")


    def _hunt_monsters(self, actor: Actor) -> bool:
        world = self.world
        monsters = [monster for monster in world.monsters_in_region(actor.region_id) if monster.alive]
        if not monsters:
            return False
        if actor.is_good() or actor.reputation >= 8:
            hostile_monsters = [m for m in monsters if self._monster_hostile_to_actor(m, actor)]
            if not hostile_monsters:
                return False
            target = max(hostile_monsters, key=lambda m: m.effective_power())
            if target.kind == MonsterKind.DRAGON:
                party = world.get_party(actor)
                party_size = len(party.member_ids) if party else 1
                if actor.reputation < 12 and party_size < 3 and actor.mind_score() >= 10:
                    return False
            return self._resolve_monster_battle(actor, target)
        return False


    def _monster_slayer_member_ids(self, slayer: Actor) -> list[int]:
        world = self.world
        party = world.get_party(slayer)
        member_ids = [slayer.id]
        if party is not None:
            for mid in party.member_ids:
                member = world.actors.get(mid)
                if member is not None and member.alive and member.is_adventurer() and mid not in member_ids:
                    member_ids.append(mid)
        if len(member_ids) < PARTY_FOUNDING_MIN_MEMBERS:
            locals_ = [a for a in world.actors_in_region(slayer.region_id) if a.alive and a.is_adventurer() and a.id not in member_ids]
            locals_.sort(key=lambda a: (a.reputation, a.power_rating(), a.charisma, a.luck), reverse=True)
            for other in locals_:
                if len(member_ids) >= max(PARTY_FOUNDING_MIN_MEMBERS, 6):
                    break
                member_ids.append(other.id)
        return member_ids

    def _elevate_monster_slayer(self, slayer: Actor, monster: Monster) -> None:
        world = self.world
        region = world.regions[slayer.region_id]
        commoners = getattr(world, 'commoners_by_region', {}).get(region.id, 0)
        gratitude = 1 + min(18, commoners // 40)
        if monster.kind == MonsterKind.DRAGON:
            gratitude += 6
        elif monster.kind == MonsterKind.GIANT:
            gratitude += 3
        elif monster.kind == MonsterKind.ANCIENT_HORROR:
            gratitude += 12
        slayer.reputation += gratitude
        region_control_boost = 3 if monster.kind == MonsterKind.GIANT else 5 if monster.kind == MonsterKind.DRAGON else 8 if monster.kind == MonsterKind.ANCIENT_HORROR else 1
        world.adjust_region_state(region.id, control_delta=region_control_boost if not slayer.is_evil() else -region_control_boost, order_delta=2 + region_control_boost)

        if monster.kind not in (MonsterKind.GIANT, MonsterKind.DRAGON, MonsterKind.ANCIENT_HORROR):
            return

        if getattr(region, 'polity_id', None) is None:
            chance = 0.20
            if monster.kind == MonsterKind.GIANT:
                chance = 0.35
            elif monster.kind == MonsterKind.DRAGON:
                chance = 0.60
            elif monster.kind == MonsterKind.ANCIENT_HORROR:
                chance = 1.00
            if commoners >= 100:
                chance += 0.15
            if region.order < 50:
                chance += 0.10
            if self.rng.random() < min(1.0, chance):
                member_ids = self._monster_slayer_member_ids(slayer)
                polity = world.create_polity(slayer, region.id, member_ids)
                if polity is not None:
                    polity.stability = 15 if monster.kind == MonsterKind.GIANT else 22 if monster.kind == MonsterKind.DRAGON else 28
                    polity.legitimacy = max(polity.legitimacy, 35 + min(45, gratitude))
                    world.log(f"The people of {world.region_name(region.id)} raise {slayer.full_name()} to the throne after the fall of {monster.name}.", importance=3, category='polity')
            return

        polity = world.polities.get(region.polity_id) if hasattr(world, 'polities') else None
        if polity is None:
            return
        ruler = world.actors.get(polity.ruler_id) if polity.ruler_id is not None else None
        slayer.polity_id = polity.id
        slayer.loyalty = None
        slayer.polity_favor = min(getattr(slayer, 'polity_favor', 50), -40)
        polity.stability = max(0, polity.stability - (6 if monster.kind == MonsterKind.GIANT else 10 if monster.kind == MonsterKind.DRAGON else 16))
        world.adjust_region_state(region.id, control_delta=-3 if slayer.is_evil() else 0, order_delta=-2)
        if ruler is not None and ruler.id != slayer.id:
            if hasattr(self, '_register_nemesis'):
                self._register_nemesis(slayer, ruler)
                self._register_nemesis(ruler, slayer)
            world.log(f"The fall of {monster.name} makes {slayer.full_name()} a threat to the rule of {polity.name} in {world.region_name(region.id)}.", importance=3, category='polity')


    def _resolve_monster_battle(self, actor: Actor, monster: Monster) -> bool:
        world = self.world
        party = world.get_party(actor)
        party_size = len(party.member_ids) if party else 1

        if monster.kind == MonsterKind.DRAGON and party_size < 5:
            return False

        if monster.kind == MonsterKind.ANCIENT_HORROR and party_size < 9:
            return False
        if self._monster_should_retreat_from_actor(monster, actor):
            self._monster_retreat(monster)
            world.log(f"{monster.name} avoids a stand-up fight against {actor.short_name()}.", importance=1, category="monster_retreat")
            return True
        world = self.world
        side_power = world.side_power(actor)
        side_power += world.side_charisma(actor) // 4
        side_power += max(0, actor.luck - 10) // 2
        if actor.role == Role.WIZARD:
            side_power += 3
        monster_power = monster.effective_power()
        own_mind = world.side_mind(actor)
        battle_roll = side_power + self.rng.randint(1, 10) + max(0, actor.luck - 10) // 2
        monster_roll = monster_power + self.rng.randint(1, 10)

        if monster.kind == MonsterKind.DRAGON:
            monster_roll += 8
        if monster.kind == MonsterKind.ANCIENT_HORROR:
            monster_roll += 15
        if monster.kind == MonsterKind.DRAGON and side_power < monster_power and own_mind >= 9 and self.rng.random() < 0.85:
            self._retreat(actor, reason=f"{monster.name} is too dangerous")
            return True
        if monster_power > side_power and own_mind >= 10 and self.rng.random() < 0.65:
            self._retreat(actor, reason=f"{monster.name} is too dangerous")
            return True

        battle_roll = side_power + self.rng.randint(1, 10) + max(0, actor.luck - 10) // 2
        monster_roll = monster_power + self.rng.randint(1, 10)
        if monster.kind == MonsterKind.DRAGON:
            monster_roll += 8
        if battle_roll >= monster_roll:
            monster.alive = False
            credited_members = self._distribute_monster_rewards(actor, monster, party)
            slayer = credited_members[0] if credited_members else actor
            if monster.kind == MonsterKind.DRAGON:
                self._grant_title(slayer, "Dragonslayer")
                world.log(f"{slayer.short_name()} slays {monster.name} in {world.region_name(actor.region_id)}.", importance=3, category="legendary_monster_kill")
            elif monster.kind == MonsterKind.GIANT:
                self._grant_title(slayer, "Giantbreaker")
                world.log(f"{slayer.short_name()} fells {monster.name} in {world.region_name(actor.region_id)}.", importance=2, category="monster_kill")
            elif monster.kind == MonsterKind.ANCIENT_HORROR:
                self._grant_title(slayer, "Bane of the Deep")
                world.log(f"{slayer.short_name()} destroys the {monster.name} in {world.region_name(actor.region_id)}.", importance=3, category="legendary_monster_kill")
            else:
                world.log(f"{slayer.short_name()} defeats {monster.name} in {world.region_name(actor.region_id)}.", importance=2, category="monster_kill")
            self._elevate_monster_slayer(slayer, monster)
            world.adjust_region_state(actor.region_id, control_delta=3, order_delta=3)
            self._apply_combat_cooldown(world.side_members(actor))
            for member in world.side_members(actor):
                self._apply_fatigue(member, 4 if monster.kind in (MonsterKind.DRAGON, MonsterKind.ANCIENT_HORROR) else 3)
            self._post_battle_rest(world.side_members(actor), legendary=monster.kind in (MonsterKind.DRAGON, MonsterKind.ANCIENT_HORROR))
            return True

        monster.monster_xp = getattr(monster, 'monster_xp', 0) + max(1, len(world.side_members(actor)))
        casualties = self._apply_losses(world.side_members(actor), severity=0.12 + monster_power / 100, cause=f"monster attack by {monster.name}")
        routed_members = world.side_members(actor)
        self._apply_rout(routed_members)
        world.adjust_region_state(actor.region_id, control_delta=-1, order_delta=-2)
        self._apply_combat_cooldown(routed_members)
        if monster.kind != MonsterKind.ANCIENT_HORROR and self.rng.random() < 0.75:
            self._monster_retreat(monster)
        for member in routed_members:
            self._apply_fatigue(member, 5 if monster.kind in (MonsterKind.DRAGON, MonsterKind.ANCIENT_HORROR) else 3)
        self._post_battle_rest(routed_members, routed=True, legendary=monster.kind in (MonsterKind.DRAGON, MonsterKind.ANCIENT_HORROR))
        world.log(f"{monster.name} repels {actor.short_name()} in {world.region_name(actor.region_id)}, leaving {casualties} dead.", importance=2, category="monster_attack")
        return True


    def _distribute_monster_rewards(self, actor: Actor, monster: Monster, party: Optional[Party]) -> List[Actor]:
        world = self.world
        participants = world.side_members(actor)
        if not participants:
            return []

        xp_values = {
            MonsterKind.GOBLIN: MONSTER_XP_GOBLIN,
            MonsterKind.GIANT: MONSTER_XP_GIANT,
            MonsterKind.DRAGON: MONSTER_XP_DRAGON,
            MonsterKind.ANCIENT_HORROR: MONSTER_XP_HORROR,
        }
        total_xp = xp_values.get(monster.kind, 50)
        if not hasattr(world, "region_activity"):
            world.region_activity = {rid: 0 for rid in world.regions}
        activity = world.region_activity.get(actor.region_id, 0)
        reduction_steps = activity // REGION_ACTIVITY_XP_STEP
        reduction = min(REGION_ACTIVITY_XP_REDUCTION_CAP, reduction_steps * REGION_ACTIVITY_XP_REDUCTION)
        total_xp = max(1, int(round(total_xp * (1.0 - reduction))))

        scored: List[Tuple[int, Actor]] = []
        for member in participants:
            score = member.power_rating() + self.rng.randint(1, 6)
            if member.role == Role.WIZARD:
                score += 2
            elif member.role == Role.WARDEN:
                score += 1
            if member.hp < max(2, member.max_hp // 2):
                score -= 2
            if party is not None and party.leader_id == member.id:
                score = int(score * LEADER_XP_WEIGHT_MULTIPLIER)
            score = max(1, score)
            scored.append((score, member))

        total_weight = sum(score for score, _ in scored) or len(scored)
        scored.sort(key=lambda item: item[0], reverse=True)

        credit_count = max(1, (len(scored) + 3) // 4)
        credited_ids = {member.id for _, member in scored[:credit_count]}
        if party is not None and party.leader_id is not None:
            credited_ids.add(party.leader_id)

        xp_remaining = total_xp
        for i, (weight, member) in enumerate(scored):
            if i == len(scored) - 1:
                xp_gain = xp_remaining
            else:
                xp_gain = int(total_xp * weight / total_weight)
                xp_remaining -= xp_gain
            if hasattr(member, 'gain_experience'):
                member.gain_experience(xp_gain)
            else:
                member.experience += xp_gain
            self._change_actor_rep(member, xp_gain // XP_TO_REP_DIVISOR)

        credited_members: List[Actor] = []
        for member in participants:
            if member.id not in credited_ids:
                continue
            credited_members.append(member)
            member.monster_kills += 1
            if monster.kind == MonsterKind.DRAGON:
                member.dragon_kills += 1
                member.kills += 1
            elif monster.kind == MonsterKind.ANCIENT_HORROR:
                member.horror_kills += 1
                member.kills += 1
            elif monster.kind == MonsterKind.GIANT:
                member.giant_kills += 1
                member.kills += 1
            elif monster.kind != MonsterKind.GOBLIN:
                member.kills += 1

        world.region_activity[actor.region_id] = world.region_activity.get(actor.region_id, 0) + 1
        return credited_members


