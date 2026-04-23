# Fantasy Antfarm v0.4

An autonomous simulation of a fantasy world where individuals—commoners, adventurers, monsters, and gods—interact over decades or centuries without player intervention. Adventurers emerge in several classes—such as fighters, wizards, wanderers, and bards—each contributing differently to combat, leadership, and social cohesion.

This is not a game in the traditional sense. It is a system that *runs itself*, producing emergent history: heroes rise and fall, regions collapse into tyranny or flourish under order, monsters carve out domains, and divine forces subtly shift the balance.

You can observe the world, but you cannot control it.

---

## Overview

Fantasy Antfarm simulates:

- **Population dynamics** (birth, aging, death)
- **Adventurer behavior** (questing, combat, alliances)
- **Faction emergence** (parties → polities)
- **Regional alignment shifts** (good, evil, contested)
- **Monster ecosystems**
- **Divine influence through worship and death**
- **Historical record generation**

The simulation advances in discrete **ticks**, each representing a unit of time within a structured calendar system.

---

## Running the Simulation

### Basic Usage

```bash
python fantfarm_v0.4.py
```

### Optional Flags

```bash
python fantfarm_v0.4.py --year 50 --pop-scale 0.5 -v
```

- `--year N` → Run simulation for `N` years
- `--pop-scale X` → Scale starting population
- `-v` / `--verbose` → Print live event log
- `--psum N` → Print a summary at N interval, years

### Output

- Console log (if verbose)
- End-of-run summary / chronicle
- Optional saved logs depending on configuration

---

## Simulation Structure

### Tick Loop

Each tick executes:

1. **Time advancement**
2. **Population updates**
   - Aging
   - Births
   - Natural deaths
3. **Actor turns**
   - Commoners (aggregate)
   - Adventurers (individual)
   - Monsters (individual)
4. **Region updates**
   - Alignment shifts
   - Order calculation
5. **Social structures**
   - Party formation
   - Party growth
   - Polity formation
6. **Divine accounting**
   - Worship tracking
   - Soul weighting
7. **Event logging**

---

## Actors

### Commoners (Aggregate)

- Represent roughly 80% of the population
- Do not act individually
- Provide:
  - Population growth
  - Recruitment pool for adventurers
  - Victims of monsters and villains
- Influence:
  - Regional stability
  - Alignment drift

### Adventurers

Adventurers are autonomous agents with:

- Alignment (good / evil / neutral emergent behavior)
- Reputation
- Strength / capability scaling
- Social behavior (alliances, parties)

#### Per-Tick Behavior

Each adventurer evaluates:

1. **Environment**
   - Nearby threats
   - Region condition
2. **Intent**
   - Quest
   - Fight
   - Recruit
   - Rest
3. **Action**
   - Engage monster or rival
   - Join or form party
   - Move regions
   - Influence alignment

---

## Adventurer Classes

Adventurers are drawn from several classes, each with a different role in the simulation.

### Fighter
- High survivability
- Strong in direct combat
- Often serves as the backbone of a party
- Best suited for frontline encounters and sustained fighting

### Wizard
- Rare
- High-impact abilities
- Lower survivability, but strong influence on difficult encounters
- More likely to swing major conflicts than endure long attritional ones

### Wanderer
- A ranger/rogue hybrid
- Mobile and opportunistic
- Flexible combat and exploration role
- Often acts independently before joining larger groups

### Bard
- Social support and influence specialist
- Contributes less through raw force and more through coordination, morale, and reputation effects
- More likely to strengthen parties, improve cohesion, and amplify the success of stronger companions
- Functions as a force multiplier rather than a primary combatant

---

## Reputation System

Reputation is **earned, not assigned**.

### Sources

- Slaying monsters
- Defeating villains
- Protecting populations
- Leading successful parties

### Effects

- High reputation:
  - Attracts allies
  - Increases chance of party leadership
  - Leads to commemoration events
- Infamy (evil reputation):
  - Attracts hostile or dark-aligned actors
  - Enables oppressive control of regions

---

## Parties

### Formation

Adventurers form parties when:

- Alignment is compatible (not strict, but influential)
- Proximity allows interaction
- A leader emerges, often the highest-reputation member

### Behavior

- Move as a unit
- Engage stronger threats
- Grow via recruitment
- Stabilize or destabilize regions

### Size Tiers (Emergent)

- Small (2–4)
- Medium (5–8)
- Large (9–14)
- Company (15+)

---

## Polities (Nations / Governments)

Polities form when:

- A party reaches sufficient size and influence
- A region becomes dominated by that group

### Effects

- Establish regional control
- Enforce alignment (good or evil)
- Affect order:
  - Good → stability
  - Evil → oppression (order without justice)

Polities persist until:

- Leadership collapses
- Overthrown by rival forces
- Population collapse

---

## Regions

Each region tracks:

- Alignment:
  - Good
  - Evil
  - Contested
- Order (0–100)
- Population health

### Dynamics

- Good actors increase order and stability
- Evil actors increase control but may suppress population
- Monsters reduce stability and population

---

## Monsters

Monsters are not mindless enemies—they are actors with behavior patterns.

### Types

#### Goblins

- Weak individually
- Can form hordes
- May align with evil leaders

#### Giants

- Strong threats to populations
- Less social

#### Dragons

- Rare and powerful
- Prefer territory and hoarding behavior
- Low activity, high impact

#### Ancient Horrors

- Unique entities
- Region-bound
- Exist as long-term destabilizers

### Monster Behavior Per Tick

Monsters decide whether to:

- Hunt
- Roam
- Rest

They may attack:

- Commoners
- Adventurers
- Rival monsters (rare)

Monsters can:

- Establish dominance in regions
- Become long-term environmental threats

---

## Immortals (Gods)

Three primary divine forces:

- **Lord of Light**
- **Lord of Darkness**
- **God of Chance**

### Influence Model

Gods do not act directly.

They accumulate influence through:

- Worshippers (living)
- Souls (dead followers), weighted more heavily

### Effects

- Subtle bias on outcomes
- Long-term tilt in alignment trends
- Narrative framing in summaries

The **God of Chance** acts as a stabilizer and disruptor, introducing unpredictability.

---

## Event System

The simulation records notable events such as:

- Births of major figures
- Deaths, especially notable actors
- Monster slayings
- Region changes
- Commemorations

### Example

```text
Goldfire 25: Ysra's Day in Ironmere — Observed in honor of Ysra Merrin.
    For slaying the white dragon at Frostmoor.
```

---

## End States

The simulation may naturally reach:

- Total collapse (population death)
- Total domination (all regions aligned)
- Long-term equilibrium

Or it may simply terminate at the specified year.

---

## Philosophy

Fantasy Antfarm is designed to:

- Avoid forced balance
- Allow collapse as a valid outcome
- Generate **stories**, not victories

If the world falls into darkness, that is not failure—it is history.

---

## Future Directions

- Expanded lineage / dynasty tracking
- More complex monster ecology
- Deeper political systems
- Improved performance for long runs












# fantasy_antfarm_v0.4
```
1) be sure all files (11) are in same folder
2) requires python 3.5+
3) for options, run: python fantfarm_v71.py --help
4) recommended settings:
    python fantfarm_v71.py -v --year 100 --pop-scale .2 --psum 1
    this will run sim for 100 years at 20% of the population_by_region cap (will speed up runtime),
    show all events, and print a summary report every 1 year
```


