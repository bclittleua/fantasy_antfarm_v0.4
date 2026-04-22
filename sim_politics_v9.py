from __future__ import annotations

from typing import Dict, List, Optional, Tuple

class PoliticsMixin:
    def _change_actor_rep(self, actor: Actor, delta: int) -> None:
        actor.reputation = max(0, actor.reputation + delta)


    def _change_polity_favor(self, actor: Actor, delta: int, polity_id: Optional[int] = None) -> None:
        target_polity = polity_id if polity_id is not None else getattr(actor, "polity_id", None)
        if target_polity is None:
            return
        if getattr(actor, "polity_id", None) == target_polity:
            actor.polity_favor = max(-100, min(100, getattr(actor, "polity_favor", 50) + delta))
            if actor.polity_favor < 0 and actor.loyalty is not None and actor.loyalty != actor.id:
                actor.loyalty = None


    def _apply_selective_polity_penalty(
        self,
        members: List[Actor],
        full_loss: int,
        follower_loss: int,
        instigator_ids: Optional[set[int]] = None,
    ) -> None:
        instigator_ids = instigator_ids or set()
        for member in members:
            if not member.alive or member.polity_id is None:
                continue
            loss = full_loss if member.id in instigator_ids else follower_loss
            if loss:
                self._change_polity_favor(member, -loss)


    def _polity_side_penalty(self, members: List[Actor]) -> None:
        polities = {m.polity_id for m in members if m.alive and m.polity_id is not None}
        if len(polities) <= 1:
            return
        instigators = set()
        for member in members:
            if not member.alive:
                continue
            party = self.world.get_party(member)
            if party is not None and party.leader_id is not None:
                instigators.add(party.leader_id)
            else:
                instigators.add(member.id)
        self._apply_selective_polity_penalty(
            members,
            CROSS_POLITY_PARTY_FAVOR_LOSS,
            CROSS_POLITY_PARTY_FAVOR_LOSS_FOLLOWER,
            instigators,
        )


    def _actor_can_join_polity(self, actor: Actor, ruler: Actor) -> bool:
        if not actor.alive:
            return False
        if ruler.is_good() and actor.is_evil():
            return False
        if ruler.is_evil() and actor.is_good():
            return False
        return True


    def _strongest_party_ally(self, party: Party, exclude_id: Optional[int] = None) -> Optional[Actor]:
        world = self.world
        members = []
        for mid in party.member_ids:
            if mid == exclude_id:
                continue
            actor = world.actors.get(mid)
            if actor and actor.alive:
                members.append(actor)
        if not members:
            return None
        return max(
            members,
            key=lambda a: (
                getattr(a, "polity_favor", 50),
                a.reputation,
                a.power_rating(),
                a.charisma,
                a.luck,
            ),
        )


    def _handle_party_succession(self) -> None:
        world = self.world
        for party in list(world.parties.values()):
            if len(party.member_ids) <= 1:
                world.archive_party(party, "Collapsed after attrition")
                continue
            leader = world.actors.get(party.leader_id) if party.leader_id is not None else None
            if leader is not None and leader.alive and leader.id in party.member_ids:
                continue

            successor = None
            if leader is not None:
                if leader.spouse_id is not None:
                    spouse = world.actors.get(leader.spouse_id)
                    if spouse and spouse.alive and spouse.id in party.member_ids:
                        successor = spouse
                if successor is None:
                    children = []
                    for mid in party.member_ids:
                        actor = world.actors.get(mid)
                        if actor is None or not actor.alive:
                            continue
                        if actor.mother_id == leader.id or actor.father_id == leader.id:
                            children.append(actor)
                    if children:
                        successor = max(children, key=lambda a: (a.reputation, a.power_rating(), a.charisma, a.luck))
            if successor is None:
                successor = self._strongest_party_ally(party, exclude_id=leader.id if leader else None)

            if successor is None:
                world.archive_party(party, "Collapsed after leader death")
                continue

            old_name = leader.short_name() if leader is not None else "its fallen leader"
            world._transfer_party_leadership(party, successor, fate_note=f"Succeeded by {successor.short_name()} after the fall of {old_name}")
            world.log(
                f"{successor.short_name()} takes command of {party.name or f'Party {party.id}'} after the fall of {old_name}.",
                importance=2,
                category="succession",
            )


    def _eligible_polity_child_successors(self, polity: Polity, ruler: Actor) -> List[Actor]:
        world = self.world
        children = []
        for actor in world.actors.values():
            if not actor.alive:
                continue
            if actor.mother_id == ruler.id or actor.father_id == ruler.id:
                children.append(actor)
        return children


    def _strongest_polity_ally(self, polity: Polity, exclude_id: Optional[int] = None) -> Optional[Actor]:
        world = self.world
        members = []
        for aid in polity.member_actor_ids:
            if aid == exclude_id:
                continue
            actor = world.actors.get(aid)
            if actor and actor.alive and self._actor_can_join_polity(actor, world.actors.get(polity.ruler_id, actor)):
                members.append(actor)
        if not members:
            return None
        return max(
            members,
            key=lambda a: (
                getattr(a, "polity_favor", 50),
                a.reputation,
                a.power_rating(),
                a.charisma,
                a.luck,
            ),
        )


    def _eligible_successor(self, polity: Polity) -> Optional[Actor]:
        world = self.world
        ruler = world.actors.get(polity.ruler_id)
        if ruler and ruler.spouse_id is not None:
            spouse = world.actors.get(ruler.spouse_id)
            if spouse and spouse.alive and spouse.polity_id == polity.id:
                return spouse
        children = []
        if ruler:
            for actor in world.actors.values():
                if not actor.alive or actor.polity_id != polity.id:
                    continue
                if actor.mother_id == ruler.id or actor.father_id == ruler.id:
                    children.append(actor)
        if children:
            return max(children, key=lambda a: (a.reputation, a.power_rating(), a.charisma))
        members = [world.actors[aid] for aid in polity.member_actor_ids if aid in world.actors and world.actors[aid].alive]
        if not members:
            return None
        return max(members, key=lambda a: (a.reputation, a.power_rating(), a.charisma))


    def _handle_polity_succession(self) -> None:
        world = self.world
        for polity in list(world.polities.values()):
            ruler = world.actors.get(polity.ruler_id)
            if ruler and ruler.alive:
                continue
            successor = self._eligible_successor(polity)
            if successor is None:
                for region_id in polity.region_ids:
                    if region_id in world.regions and world.regions[region_id].polity_id == polity.id:
                        world.regions[region_id].polity_id = None
                        world.regions[region_id].contested_by = None
                world.log(f"{polity.name} collapses after the death of its ruler.", importance=3, category="polity")
                world.archive_polity(polity, 'Collapsed after ruler death')
                continue
            hist = getattr(world, 'polity_history', {}).get(polity.id)
            old_ruler_name = ruler.short_name() if ruler is not None else "its fallen ruler"
            polity.ruler_id = successor.id
            successor.loyalty = successor.id
            successor.polity_id = polity.id
            successor.polity_favor = max(getattr(successor, "polity_favor", 50), 90)
            if hist is not None:
                if hist.leaders:
                    if hist.leaders[-1].name == old_ruler_name and hist.leaders[-1].fate in ("Founder", "Current ruler"):
                        hist.leaders[-1].fate = f"Succeeded by {successor.short_name()}"
                    elif hist.leaders[-1].name == successor.short_name():
                        hist.leaders[-1].fate = "Current ruler"
                if not hist.leaders or hist.leaders[-1].name != successor.short_name():
                    hist.leaders.append(PolityLeaderRecord(name=successor.short_name(), fate="Current ruler"))
                hist.current_ruler_id = successor.id
                hist.current_ruler_name = successor.short_name()
            world.log(f"{successor.short_name()} succeeds to the rule of {polity.name}.", importance=3, category="succession")


    def _claim_region_for_polity(self, polity: Polity, region_id: int) -> None:
        world = self.world
        region = world.regions[region_id]
        old_polity = region.polity_id
        if old_polity == polity.id and region_id in polity.region_ids:
            region.contested_by = None
            region.under_siege_by = None
            region.siege_progress = 0
            return
        region.polity_id = polity.id
        region.contested_by = None
        region.under_siege_by = None
        region.siege_progress = 0
        region.siege_started_tick = -999999
        if region_id not in polity.region_ids:
            polity.region_ids.append(region_id)
        if old_polity is not None and old_polity in world.polities and old_polity != polity.id:
            old = world.polities[old_polity]
            old.region_ids = [rid for rid in old.region_ids if rid != region_id]
        world.log(f"{polity.name} claims {world.region_name(region_id)}.", importance=2, category="polity")

    def _capture_threshold_for_region(self, region: Region) -> int:
        base = 100
        base += max(0, region.order // 2)
        base += region.danger * 4
        if region.polity_id is not None:
            base += 25
        return min(180, base)

    def _capture_progress_gain(self, polity: Polity, region: Region, ruler: Actor, friendly: List[Actor], rivals: List[Actor]) -> int:
        gain = 8
        gain += min(16, len(friendly) * 2)
        gain += min(12, polity.strength // 700)
        gain += min(8, max(0, ruler.reputation - POLITY_REGION_CLAIM_MIN_REPUTATION) // 10)
        gain -= min(18, len(rivals) * 3)
        gain -= min(14, region.order // 8)
        if region.polity_id is not None and region.polity_id != polity.id:
            gain -= 8
        return max(4, gain)

    def _begin_or_progress_region_capture(self, polity: Polity, region_id: int, ruler: Actor, friendly: List[Actor], rivals: List[Actor]) -> None:
        world = self.world
        region = world.regions[region_id]
        if region.polity_id == polity.id:
            region.under_siege_by = None
            region.siege_progress = 0
            region.siege_started_tick = -999999
            return

        if region.under_siege_by not in (None, polity.id):
            current_besieger = world.polities.get(region.under_siege_by)
            current_strength = current_besieger.strength if current_besieger is not None else 0
            challenger_strength = polity.strength + len(friendly) * 20
            if challenger_strength <= current_strength + 150:
                return
            region.siege_progress = max(0, region.siege_progress // 2)

        if region.under_siege_by != polity.id:
            region.under_siege_by = polity.id
            region.siege_progress = 0
            region.siege_started_tick = world.tick
            region.contested_by = polity.id
            world.log(f"{polity.name} begins subjugating {world.region_name(region_id)}.", importance=2, category="polity")
            return

        gain = self._capture_progress_gain(polity, region, ruler, friendly, rivals)
        region.siege_progress = min(self._capture_threshold_for_region(region), region.siege_progress + gain)
        region.contested_by = polity.id

        threshold = self._capture_threshold_for_region(region)
        if region.siege_progress >= threshold:
            self._claim_region_for_polity(polity, region_id)
            region.ruler_id = ruler.id
            if ruler.is_good():
                world.adjust_region_state(region_id, control_delta=3, order_delta=2)
            elif ruler.is_evil():
                world.adjust_region_state(region_id, control_delta=-3, order_delta=-1)
            else:
                world.adjust_region_state(region_id, control_delta=1, order_delta=1)
        elif region.siege_progress >= int(threshold * 0.66) and world.tick % 90 == 0:
            world.log(f"{polity.name} tightens its grip on {world.region_name(region_id)}.", importance=1, category="polity")

    def _decay_region_capture(self, polity: Polity, region_id: int) -> None:
        world = self.world
        region = world.regions[region_id]
        if region.under_siege_by != polity.id:
            return
        decay = 8 + max(0, region.order // 15)
        region.siege_progress = max(0, region.siege_progress - decay)
        if region.siege_progress <= 0:
            region.under_siege_by = None
            region.contested_by = None
            region.siege_started_tick = -999999
            world.log(f"{polity.name} loses its hold on {world.region_name(region_id)}.", importance=1, category="polity")


    def _polity_commoner_total(self, polity: Polity) -> int:
        world = self.world
        if not hasattr(world, 'commoners_by_region'):
            return 0
        return sum(world.commoners_by_region.get(rid, 0) for rid in polity.region_ids)


    def _dominant_polity(self) -> Optional[Polity]:
        world = self.world
        if not world.polities:
            return None
        return max(world.polities.values(), key=lambda p: (len(p.region_ids), p.strength, p.legitimacy))


    def _living_polity_members(self, polity: Polity) -> List[Actor]:
        world = self.world
        members = []
        for aid in polity.member_actor_ids:
            actor = world.actors.get(aid)
            if actor and actor.alive:
                members.append(actor)
        return members


    def _find_internal_claimant(self, polity: Polity) -> Optional[Actor]:
        world = self.world
        ruler = world.actors.get(polity.ruler_id)
        if ruler is None:
            return None
        members = []
        for actor in self._living_polity_members(polity):
            if actor.id == ruler.id:
                continue
            if actor.reputation < max(60, ruler.reputation // 3):
                continue
            if actor.loyalty == ruler.id and actor.reputation < ruler.reputation * 0.75:
                continue
            members.append(actor)
        if not members:
            return None
        return max(members, key=lambda a: (a.reputation, a.power_rating(), a.charisma, a.luck))


    def _polity_assassination_defense(self, polity: Polity, ruler: Actor) -> int:
        world = self.world
        party = world.get_party(ruler)
        party_guard = len(party.member_ids) * ASSASSINATION_GUARD_PER_PARTY_MEMBER if party is not None else 0
        local_loyalists = 0
        for actor in world.actors_in_region(ruler.region_id):
            if not actor.alive or actor.id == ruler.id:
                continue
            if actor.loyalty == ruler.id or actor.polity_id == polity.id:
                local_loyalists += 1
        local_guard = local_loyalists * ASSASSINATION_GUARD_PER_LOCAL_LOYALIST
        legitimacy_guard = int(polity.legitimacy * ASSASSINATION_LEGITIMACY_WEIGHT)
        return party_guard + local_guard + legitimacy_guard


    def _resolve_polity_assassination(self, polity: Polity, ruler: Actor, claimant: Optional[Actor]) -> None:
        world = self.world
        polity.last_challenge_tick = world.tick
        polity.challenge_count += 1
        assassin_power = (claimant.reputation if claimant else 40) + (claimant.luck if claimant else 10) + self.rng.randint(1, 30)
        defense = ruler.reputation + ruler.luck + max(0, polity.stability) + self.rng.randint(1, 30)
        if assassin_power > defense and self.rng.random() < 0.35:
            source = claimant.short_name() if claimant else 'unknown hands'
            world.log(f"An assassination plot from {source} brings down {ruler.full_name()} of {polity.name}.", importance=3, category='polity_challenge')
            if claimant is not None and claimant.alive:
                self._change_actor_rep(claimant, 6)
                self._change_polity_favor(claimant, -10, polity.id)
            self._mark_actor_dead(ruler, 'assassination', importance=3)
            polity.stability = max(0, polity.stability - 20)
            self._destabilize_polity_regions(polity, 8, 10, max_regions=3)
            self._maybe_fragment_polity(polity)
            self._handle_polity_succession()
            return
        ruler.recovering = max(ruler.recovering, 3)
        polity.stability = max(0, polity.stability - 8)
        if claimant is not None and claimant.alive:
            self._change_actor_rep(claimant, -FAILED_ASSASSINATION_REP_LOSS)
            self._change_polity_favor(claimant, -FAILED_ASSASSINATION_FAVOR_LOSS, polity.id)
        self._destabilize_polity_regions(polity, 3, 4, max_regions=2)
        world.log(f"An assassination plot against {ruler.full_name()} of {polity.name} fails, but the court is shaken.", importance=2, category='polity_challenge')


    def _resolve_polity_claimant_war(self, polity: Polity, ruler: Actor, claimant: Actor) -> None:
        world = self.world
        polity.last_challenge_tick = world.tick
        polity.challenge_count += 1
        ruler_score = ruler.reputation + ruler.power_rating() + polity.legitimacy + polity.stability + self.rng.randint(1, 40)
        claimant_support = len([a for a in self._living_polity_members(polity) if a.loyalty in (None, claimant.id)])
        claimant_score = claimant.reputation + claimant.power_rating() + claimant.charisma + claimant_support + self.rng.randint(1, 40)
        if claimant_score > ruler_score:
            world.log(f"{claimant.short_name()} rises as a claimant against {ruler.full_name()} in {polity.name} and wins the struggle for the throne.", importance=3, category='polity_challenge')
            self._mark_actor_dead(ruler, 'civil war', importance=3)
            polity.ruler_id = claimant.id
            claimant.loyalty = claimant.id
            claimant.polity_id = polity.id
            claimant.polity_favor = 100
            polity.stability = max(20, polity.stability - 10)
            self._destabilize_polity_regions(polity, 6, 8, max_regions=4)
            for actor in self._living_polity_members(polity):
                if actor.id != claimant.id and self._actor_can_join_polity(actor, claimant):
                    actor.loyalty = claimant.id
            return
        claimant.recovering = max(claimant.recovering, 4)
        self._change_actor_rep(claimant, -FAILED_COUP_REP_LOSS)
        self._change_polity_favor(claimant, -FAILED_COUP_FAVOR_LOSS, polity.id)
        coup_followers = [a for a in self._living_polity_members(polity) if a.id != claimant.id and a.loyalty == claimant.id]
        self._apply_selective_polity_penalty(coup_followers, FAILED_COUP_FAVOR_LOSS // 2, max(1, FAILED_COUP_FAVOR_LOSS // 4), {a.id for a in coup_followers})
        polity.stability = max(0, polity.stability - 5)
        self._destabilize_polity_regions(polity, 2, 3, max_regions=2)
        world.log(f"{ruler.full_name()} defeats the claimant {claimant.short_name()} and holds {polity.name} together.", importance=2, category='polity_challenge')
        if self.rng.random() < 0.20:
            self._mark_actor_dead(claimant, 'failed coup', importance=2)


    def _resolve_polity_regional_revolt(self, polity: Polity, ruler: Actor, claimant: Optional[Actor]) -> None:
        world = self.world
        if len(polity.region_ids) <= 1:
            return
        polity.last_challenge_tick = world.tick
        polity.challenge_count += 1
        revolt_candidates = [rid for rid in polity.region_ids if rid != polity.capital_region_id]
        if not revolt_candidates:
            return
        region_id = self.rng.choice(revolt_candidates)
        region = world.regions[region_id]
        region.contested_by = polity.id
        defense = ruler.reputation + polity.strength // 20 + polity.legitimacy + self.rng.randint(1, 25)
        challenge = (claimant.reputation if claimant else 60) + len([a for a in world.actors_in_region(region_id) if a.alive]) + self.rng.randint(1, 25)
        if challenge > defense:
            polity.region_ids = [rid for rid in polity.region_ids if rid != region_id]
            region.polity_id = None
            region.contested_by = None
            polity.stability = max(0, polity.stability - 12)
            self._destabilize_polity_regions(polity, 5, 6, max_regions=3)
            self._maybe_fragment_polity(polity)
            world.log(f"Revolt tears {world.region_name(region_id)} away from {polity.name}.", importance=3, category='polity_challenge')
            if claimant and claimant.alive and claimant.polity_id == polity.id:
                self._change_actor_rep(claimant, 8)
                self._change_polity_favor(claimant, -20, polity.id)
                claimant.polity_id = None
                claimant.loyalty = None
                local_members = [a.id for a in world.actors_in_region(region_id) if a.alive and a.is_adventurer() and a.id != claimant.id and claimant.can_join_party_with(a)]
                member_ids = [claimant.id] + local_members[:10]
                if claimant.reputation >= POLITY_REGION_CLAIM_MIN_REPUTATION:
                    new_polity = world.create_polity(claimant, region_id, member_ids)
                    if new_polity:
                        world.log(f"{claimant.short_name()} establishes {new_polity.name} after a successful revolt in {world.region_name(region_id)}.", importance=3, category='polity_challenge')
            return
        if claimant is not None and claimant.alive:
            self._change_actor_rep(claimant, -FAILED_REVOLT_REP_LOSS)
            self._change_polity_favor(claimant, -FAILED_REVOLT_FAVOR_LOSS, polity.id)
            revolt_followers = [a for a in world.actors_in_region(region_id) if a.alive and a.id != claimant.id and a.loyalty == claimant.id]
            self._apply_selective_polity_penalty(revolt_followers, FAILED_REVOLT_FAVOR_LOSS // 2, max(1, FAILED_REVOLT_FAVOR_LOSS // 4), {a.id for a in revolt_followers})
        polity.stability = max(0, polity.stability - 6)
        self._destabilize_polity_regions(polity, 2, 3, max_regions=2)
        self._maybe_fragment_polity(polity)
        world.log(f"{ruler.full_name()} crushes a revolt in {world.region_name(region_id)} and preserves {polity.name}.", importance=2, category='polity_challenge')


    def _maybe_challenge_polities(self) -> None:
        world = self.world
        if world.tick % POLITY_CHALLENGE_CHECK_TICKS != 0:
            return
        for polity in list(world.polities.values()):
            ruler = world.actors.get(polity.ruler_id)
            if ruler is None or not ruler.alive:
                continue
            if world.tick - polity.last_challenge_tick < POLITY_CHALLENGE_COOLDOWN_TICKS:
                continue
            if world.tick < getattr(polity, "succession_grace_until", -999999):
                continue
            region_count = len(polity.region_ids)
            if region_count < 1:
                continue
            claimant = self._find_internal_claimant(polity)
            age = self._calculate_age(ruler)
            pressure = 0.01 + region_count * 0.01
            pressure += min(0.10, max(0, ruler.reputation - 120) * 0.0002)
            pressure += max(0.0, age - 50) * 0.002
            pressure += max(0.0, 60 - polity.stability) * 0.003
            if ruler.is_evil():
                pressure += EVIL_POLITY_EXTRA_CHALLENGE_PRESSURE
            if claimant is not None:
                pressure += 0.08
            pressure = min(0.35, pressure)
            if polity.stability <= 0:
                self._destabilize_polity_regions(polity, 4, 5, max_regions=max(1, len(polity.region_ids) // 2))
                self._maybe_fragment_polity(polity)
            if self.rng.random() >= pressure:
                continue
            challenge_type = self.rng.choices(
                ['claimant', 'assassination', 'revolt'],
                weights=[5 if claimant else 1, 3, 4 if region_count >= 3 else 1],
                k=1,
            )[0]
            if challenge_type == 'claimant' and claimant is not None:
                self._resolve_polity_claimant_war(polity, ruler, claimant)
            elif challenge_type == 'revolt':
                self._resolve_polity_regional_revolt(polity, ruler, claimant)
            else:
                self._resolve_polity_assassination(polity, ruler, claimant)



    def _monster_deity_contributions(self) -> Dict[Deity, int]:
        world = self.world
        contributions = {deity: 0 for deity in Deity}
        for monster in world.living_monsters():
            if monster.kind == MonsterKind.GOBLIN:
                contributions[Deity.LORD_OF_DARKNESS] += max(1, getattr(monster, 'horde_size', 1) * MONSTER_INFLUENCE_GOBLIN_PER_HEAD)
            elif monster.kind == MonsterKind.DRAGON:
                temperament = getattr(monster, 'dragon_temperament', 'malevolent')
                if temperament == 'benevolent':
                    contributions[Deity.LORD_OF_LIGHT] += MONSTER_INFLUENCE_DRAGON
                else:
                    contributions[Deity.GOD_OF_CHANCE] += MONSTER_INFLUENCE_DRAGON
        return contributions

    def _deity_influence_totals(self):
        world = self.world
        soul_weight = 2
        totals = {}
        total_influence = 0
        faith_map = getattr(world, 'commoner_faith_by_region', {})
        monster_support = self._monster_deity_contributions()
        for deity in Deity:
            living = len([actor for actor in world.living_actors() if actor.deity == deity])
            commoners = sum(region_faith.get(deity, 0) for region_faith in faith_map.values())
            souls = world.souls_by_deity.get(deity, 0)
            monster_influence = monster_support.get(deity, 0)
            influence = living + commoners + (souls * soul_weight) + monster_influence
            totals[deity] = influence
            total_influence += influence
        shares = {deity: ((totals[deity] / total_influence) * 100.0 if total_influence > 0 else 0.0) for deity in Deity}
        return totals, shares

    def _dominant_deity_regions(self, deity: Deity) -> List[Region]:
        world = self.world
        faith_map = getattr(world, 'commoner_faith_by_region', {})
        ranked = []
        for region in world.regions.values():
            region_faith = faith_map.get(region.id, {})
            total = sum(region_faith.values())
            deity_count = region_faith.get(deity, 0)
            favored = 1 if self._v10_region_favored_deity(region.id) == deity else 0
            ranked.append((deity_count, favored, region.order, world.commoners_by_region.get(region.id, 0), region))
        ranked.sort(key=lambda item: (item[0], item[1], item[2], item[3]), reverse=True)
        return [item[-1] for item in ranked]

    def _region_faith_share(self, region_id: int, deity: Deity) -> float:
        faith_map = getattr(self.world, 'commoner_faith_by_region', {}).get(region_id, {})
        total = sum(faith_map.values())
        if total <= 0:
            return 0.0
        return faith_map.get(deity, 0) / total

    def _shift_faith_between_deities(self, region_id: int, from_deity: Deity, to_deity: Deity, amount: int) -> int:
        if amount <= 0 or from_deity == to_deity:
            return 0
        faith_map = self.world.commoner_faith_by_region.setdefault(region_id, {deity: 0 for deity in Deity})
        moved = min(amount, faith_map.get(from_deity, 0))
        if moved <= 0:
            return 0
        faith_map[from_deity] = max(0, faith_map.get(from_deity, 0) - moved)
        faith_map[to_deity] = faith_map.get(to_deity, 0) + moved
        return moved

    def _bleed_dominant_influence(self) -> bool:
        world = self.world
        totals, shares = self._deity_influence_totals()
        leader, leader_share = max(shares.items(), key=lambda item: item[1])
        if leader_share <= IMMORTAL_DOMINANCE_BLEED_THRESHOLD:
            return False
        excess = leader_share - IMMORTAL_DOMINANCE_BLEED_THRESHOLD
        if excess <= 0:
            return False
        regions = self._dominant_deity_regions(leader)[:max(2, IMMORTAL_PRESSURE_MAX_REGIONS)]
        if not regions:
            return False
        shifted_total = 0
        recipients = [d for d in Deity if d != leader]
        recipient_weights = {d: max(1, totals.get(d, 0)) for d in recipients}
        weight_total = sum(recipient_weights.values()) or 1
        for region in regions:
            faith_map = world.commoner_faith_by_region.get(region.id, {})
            deity_count = faith_map.get(leader, 0)
            if deity_count <= 0:
                continue
            region_share = self._region_faith_share(region.id, leader)
            bleed_rate = IMMORTAL_DOMINANCE_BLEED_RATE + (excess / 100.0) * IMMORTAL_DOMINANCE_EXCESS_MULTIPLIER
            bleed_rate *= max(0.35, region_share)
            bleed = min(deity_count, max(1, int(deity_count * bleed_rate)))
            if bleed <= 0:
                continue
            faith_map[leader] = max(0, deity_count - bleed)
            assigned = 0
            for i, deity in enumerate(recipients):
                if i == len(recipients) - 1:
                    add = bleed - assigned
                else:
                    add = int(bleed * (recipient_weights[deity] / weight_total))
                    assigned += add
                faith_map[deity] = faith_map.get(deity, 0) + add
            shifted_total += bleed
        if shifted_total > 0:
            world.log(
                f"The worship of {leader.value} grows complacent and begins to fracture under its own weight.",
                importance=2,
                category='divine_pressure',
            )
            return True
        return False

    def _apply_divine_disaster(self) -> bool:
        world = self.world
        if not hasattr(world, 'last_divine_disaster_tick'):
            world.last_divine_disaster_tick = -999999
        if world.tick - world.last_divine_disaster_tick < IMMORTAL_DISASTER_COOLDOWN_TICKS:
            return False

        totals, shares = self._deity_influence_totals()
        desperate, desperate_share = min(shares.items(), key=lambda item: item[1])
        dominant, dominant_share = max(shares.items(), key=lambda item: item[1])

        if desperate == dominant or desperate_share > IMMORTAL_DESPERATION_THRESHOLD:
            return False

        targets = self._dominant_deity_regions(dominant)[:IMMORTAL_DISASTER_MAX_REGIONS]
        if not targets:
            return False

        world.last_divine_disaster_tick = world.tick
        total_disrupted = 0
        names = []
        for region in targets:
            region_id = region.id
            names.append(world.region_name(region_id))
            region_faith = world.commoner_faith_by_region.setdefault(region_id, {deity: 0 for deity in Deity})
            local_share = self._region_faith_share(region_id, dominant)
            global_shield = min(IMMORTAL_DISASTER_SHIELD_CAP, (dominant_share / 100.0) * 0.20 + local_share * 0.55)
            base_damage = IMMORTAL_DISASTER_BASE_SHAKE + ((dominant_share - IMMORTAL_DESPERATION_THRESHOLD) / 100.0) * IMMORTAL_DISASTER_EXCESS_MULTIPLIER
            effective_damage = max(0.01, min(IMMORTAL_DISASTER_MAX_SHAKE, base_damage * (1.0 - global_shield)))
            dominant_count = region_faith.get(dominant, 0)
            faith_loss = min(dominant_count, max(1, int(dominant_count * effective_damage))) if dominant_count > 0 else 0
            if faith_loss > 0:
                region_faith[dominant] = max(0, dominant_count - faith_loss)
                redirected = max(1, int(faith_loss * 0.60))
                region_faith[desperate] = region_faith.get(desperate, 0) + redirected
                remainder = faith_loss - redirected
                other_targets = [d for d in Deity if d not in (dominant, desperate)]
                for _ in range(remainder):
                    region_faith[self.rng.choice(other_targets or [desperate])] += 1
                total_disrupted += faith_loss
            commoners = getattr(world, 'commoners_by_region', {}).get(region_id, 0)
            if commoners > 0:
                harm = min(commoners, max(0, int(commoners * (effective_damage * 0.20))))
                if harm > 0:
                    world.commoners_by_region[region_id] = max(0, commoners - harm)
                    if hasattr(self, '_remove_commoner_deaths'):
                        self._remove_commoner_deaths(region_id, harm)
            world.adjust_region_state(region_id, control_delta=-max(1, int(6 * effective_damage)), order_delta=-max(2, int(12 * effective_damage)))

        if total_disrupted > 0:
            target_text = ", ".join(names[:-1]) + (f", and {names[-1]}" if len(names) > 1 else names[0])
            world.log(
                f"With {desperate.value} nearly cast down, the immortal lashes out at the realms of {dominant.value}. Storm, famine, and omen strike {target_text}, shaking the faith of the flock.",
                importance=3,
                category='divine_disaster',
            )
            return True
        return False

    def _apply_immortal_influence_pressure(self) -> None:
        self._bleed_dominant_influence()
        self._apply_divine_disaster()

    def _region_alignment_lean(self, region: Region) -> str:
        if region.control <= -30:
            return 'evil'
        if region.control >= 30:
            return 'good'
        return 'contested'

    def _champion_spawn_regions(self, deity: Deity) -> List[int]:
        world = self.world
        regions = list(world.regions.values())
        contested = [r for r in regions if self._region_alignment_lean(r) == 'contested']
        weakest = sorted(regions, key=lambda r: (r.order, abs(r.control), r.danger))[:max(3, len(regions)//3)]
        if deity == Deity.LORD_OF_DARKNESS:
            aligned = [r for r in regions if self._region_alignment_lean(r) == 'evil']
            fallback = [r for r in weakest if self._region_alignment_lean(r) != 'good'] or contested or weakest
            return [r.id for r in (aligned or fallback)]
        if deity == Deity.LORD_OF_LIGHT:
            aligned = [r for r in regions if self._region_alignment_lean(r) == 'good' or r.order >= 50]
            fallback = contested or weakest
            return [r.id for r in (aligned or fallback)]
        chance_pool = contested or weakest or regions
        return [r.id for r in chance_pool]

    def _spawn_divine_champion(self, deity: Deity) -> Optional[Actor]:
        world = self.world
        candidate_region_ids = self._champion_spawn_regions(deity)
        if not candidate_region_ids:
            return None
        region_id = self.rng.choice(candidate_region_ids)
        role_weights = [(Role.FIGHTER, 5), (Role.WARDEN, 3), (Role.WIZARD, 2)]
        roles, weights = zip(*role_weights)
        role = self.rng.choices(roles, weights=weights, k=1)[0]
        if deity == Deity.LORD_OF_LIGHT:
            alignment = self.rng.choice([Alignment.LAWFUL_GOOD, Alignment.NEUTRAL_GOOD, Alignment.CHAOTIC_GOOD])
        elif deity == Deity.LORD_OF_DARKNESS:
            alignment = self.rng.choice([Alignment.LAWFUL_EVIL, Alignment.NEUTRAL_EVIL, Alignment.CHAOTIC_EVIL])
        else:
            alignment = self.rng.choice([Alignment.LAWFUL_GOOD, Alignment.NEUTRAL_GOOD, Alignment.CHAOTIC_GOOD, Alignment.LAWFUL_EVIL, Alignment.NEUTRAL_EVIL, Alignment.CHAOTIC_EVIL])
        stats = list(self._roll_stats(role))
        banned = {2}
        if role == Role.FIGHTER:
            banned.add(0)
        elif role == Role.WARDEN:
            banned.add(1)
        elif role == Role.WIZARD:
            banned.add(3)
        weakness_choices = [i for i in range(7) if i not in banned]
        weakness = self.rng.choice(weakness_choices)
        for i in range(7):
            stats[i] += 5
        stats[weakness] -= 5
        stats = [max(3, s) for s in stats]
        hp = self._base_hp(role, stats[2])
        first, surname, sex = self._random_person_identity()
        traits = self.rng.sample(TRAITS, k=2)
        year, _, _, _, _ = world.current_calendar()
        actor = Actor(
            id=world.next_actor_id,
            name=first,
            surname=surname,
            role=role,
            alignment=alignment,
            deity=deity,
            strength=stats[0], dexterity=stats[1], constitution=stats[2], intelligence=stats[3], wisdom=stats[4], charisma=stats[5], luck=stats[6],
            hp=hp, max_hp=hp,
            region_id=region_id,
            traits=traits,
            birth_year=year - self.rng.randint(18, 35),
            birth_month=self.rng.randint(1, 12),
            birth_day=self.rng.randint(1, 30),
            spouse_id=None,
            sex=sex,
            reputation=12,
            deity_conviction=100,
            champion_of=deity,
        )
        world.actors[world.next_actor_id] = actor
        world.next_actor_id += 1
        world.generated_by_role[role] += 1
        if hasattr(actor, 'sync_progression'):
            actor.sync_progression(initial=True)
        if actor.title is None:
            actor.title = f"Champion of {deity.value}"
        return actor

    def _maybe_spawn_divine_champions(self) -> bool:
        world = self.world
        if world.tick % 90 != 0:
            return False
        if not hasattr(world, 'last_champion_tick_by_deity'):
            world.last_champion_tick_by_deity = {deity: -999999 for deity in Deity}
        _, shares = self._deity_influence_totals()
        spawned = False
        for deity in Deity:
            if shares.get(deity, 0.0) >= 10.0:
                continue
            if any(actor.alive and getattr(actor, 'champion_of', None) == deity for actor in world.living_actors()):
                continue
            if world.tick - world.last_champion_tick_by_deity.get(deity, -999999) < DIVINE_CHAMPION_COOLDOWN_TICKS:
                continue
            champion = self._spawn_divine_champion(deity)
            if champion is None:
                continue
            world.last_champion_tick_by_deity[deity] = world.tick
            world.log(f"With {deity.value} diminished and desperate, {champion.full_name()} rises in {world.region_name(champion.region_id)} as a divine champion.", importance=3, category='champion')
            spawned = True
        return spawned

    def _maybe_spawn_dragon_for_polities(self) -> bool:
        world = self.world
        dragons = [m for m in world.living_monsters() if m.kind == MonsterKind.DRAGON]
        if len(dragons) >= MAX_WILD_DRAGONS:
            return False
        candidates = []
        for polity in world.polities.values():
            if len(polity.region_ids) < DRAGON_ATTRACTION_MIN_REGIONS:
                continue
            if world.tick - polity.last_dragon_tick < DRAGON_ATTRACTION_COOLDOWN_TICKS:
                continue
            commoners = self._polity_commoner_total(polity)
            if commoners < DRAGON_ATTRACTION_MIN_COMMONERS:
                continue
            candidates.append((commoners + polity.strength + len(polity.region_ids) * 50, polity))
        if not candidates:
            return False
        _, polity = max(candidates, key=lambda item: item[0])
        if self.rng.random() >= 0.35:
            return False
        target_region_id = max(polity.region_ids, key=lambda rid: world.commoners_by_region.get(rid, 0) if hasattr(world, 'commoners_by_region') else 0)
        dragon = self._make_dragon(target_region_id)
        world.monsters[dragon.id] = dragon
        world.generated_monsters_by_kind[dragon.kind] += 1
        polity.last_dragon_tick = world.tick
        world.log(f"Drawn by the swelling wealth and population of {polity.name}, a {dragon.name} descends upon {world.region_name(target_region_id)}.", importance=3, category='monster_spawn')
        return True


    def _maybe_spawn_horror_for_dominance(self) -> bool:
        world = self.world
        horrors = [m for m in world.living_monsters() if m.kind == MonsterKind.ANCIENT_HORROR]
        if horrors:
            return False
        dominant = self._dominant_polity()
        if dominant is None:
            return False
        if len(dominant.region_ids) / max(1, len(world.regions)) <= ANCIENT_HORROR_DOMINANCE_RATIO:
            return False
        if world.tick - dominant.last_horror_tick < ANCIENT_HORROR_COOLDOWN_TICKS:
            return False
        target_region_id = dominant.capital_region_id if dominant.capital_region_id in world.regions else dominant.region_ids[0]
        horror = self._make_horror(target_region_id)
        if horror is None:
            return False
        world.monsters[horror.id] = horror
        world.generated_monsters_by_kind[horror.kind] += 1
        dominant.last_horror_tick = world.tick
        world.log(f"As {dominant.name} comes to dominate the continent, the ancient horror {horror.name} awakens beneath {world.region_name(target_region_id)}.", importance=3, category='monster_spawn')
        return True


    def _update_polities(self) -> None:
        world = self.world
        self._handle_polity_succession()
        # Formation
        min_rep, min_party_size = self._dynamic_polity_thresholds()
        for party in list(world.parties.values()):
            if party.leader_id is None or len(party.member_ids) < min_party_size:
                continue
            leader = world.actors.get(party.leader_id)
            if leader is None or not leader.alive or leader.polity_id is not None:
                continue
            if leader.reputation < min_rep:
                continue
            region = world.regions[leader.region_id]
            if abs(region.control) < 30:
                continue
            polity = world.create_polity(leader, leader.region_id, party.member_ids)
            if polity is None:
                continue
            if leader.title is None:
                if leader.is_good():
                    leader.title = f"King of {region.name}"
                elif leader.is_evil():
                    leader.title = f"Tyrant of {region.name}"
                else:
                    leader.title = f"Master of {region.name}"
        # Loyalty drift and region claims
        for polity in list(world.polities.values()):
            ruler = world.actors.get(polity.ruler_id)
            if ruler is None or not ruler.alive:
                continue
            members = [a for a in world.living_actors() if a.region_id in polity.region_ids or a.loyalty == ruler.id]
            polity.member_actor_ids = []
            for actor in members:
                if self._actor_can_join_polity(actor, ruler):
                    actor.polity_id = polity.id
                    actor.loyalty = ruler.id
                    actor.polity_favor = max(getattr(actor, "polity_favor", 50), 55)
                    polity.member_actor_ids.append(actor.id)
            polity.strength = sum(world.actors[aid].power_rating() for aid in polity.member_actor_ids if aid in world.actors)
            world._update_polity_history(polity)
            # claim adjacent regions with sufficient friendly presence
            candidate_regions = set()
            for region_id in list(polity.region_ids):
                candidate_regions.update(world.regions[region_id].neighbors)
            for region_id in candidate_regions:
                region = world.regions[region_id]
                local = [a for a in world.actors_in_region(region_id) if a.alive]
                friendly = [a for a in local if a.polity_id == polity.id]
                rivals = [a for a in local if a.polity_id not in (None, polity.id)]
                can_press_claim = len(friendly) >= max(3, len(rivals) + 2) and (ruler.reputation >= POLITY_REGION_CLAIM_MIN_REPUTATION)
                if can_press_claim:
                    self._begin_or_progress_region_capture(polity, region_id, ruler, friendly, rivals)
                else:
                    self._decay_region_capture(polity, region_id)
        self._maybe_challenge_polities()
        self._apply_immortal_influence_pressure()
        self._maybe_spawn_divine_champions()


