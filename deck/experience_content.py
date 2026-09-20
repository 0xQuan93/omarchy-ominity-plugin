"""Authored Living Deck selections for the original Ominity cards.

The source rows below are editorial content, keyed by permanent card ID. They
extend, rather than replace, the canonical card prose in ``build_deck.py``.
Selection uses independent SHA-256 lanes so adding or reordering one collection
cannot silently change the other selected objects in a future deck revision.
"""

from __future__ import annotations

import hashlib
import re
from typing import Mapping


DAYPARTS = ("morning", "day", "evening")
VARIANTS = frozenset({"glimmer", "trace", "ripple", "halo", "ember", "grain"})
_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# card ID | two additional reading lenses | evening prompt | three visual
# observations in the order of the canonical symbol list. The first, daytime
# prompt is each card's original reflection question. Keeping this compact
# makes every new sentence and its relationship to the image reviewable.
_ROWS = """
major-00-the-fool|A beginning can be small enough to take with an honest look at the ground.|Trust grows when you notice both the opening and your footing.|What first step did you actually take today?|The cliff marks an edge, not an instruction to jump.|The flower brings a fragile living detail to the threshold.|The open sky gives the traveler room beyond the stone.
major-01-the-magician|Intention becomes visible through the tools already at hand.|Skill asks for a clear purpose before a flourish.|Where did your attention become action today?|The table gathers usable things into one place.|The raised hand draws attention upward while another points to the tools.|The loop suggests a continuous exchange between vision and practice.
major-02-the-high-priestess|Quiet can hold information that a quick answer would miss.|The unseen deserves attention without demanding certainty.|What did you hear after the day's noise settled?|The veil makes the space beyond partly visible.|The moon hangs between the pillars rather than filling the sky.|Still water offers a surface for patient looking.
major-03-the-empress|Care becomes creative when it has rhythm and room.|Growth asks for nourishment, not constant control.|What did you tend that may keep growing?|The garden surrounds the seated figure with living work.|Grain rises where patient tending has taken root.|The river moves through the garden without staying still.
major-04-the-emperor|A boundary can hold a vision without hardening it.|Authority is most useful when its structure can be revised.|Which structure helped you, and which needs adjustment?|The throne gives the seated figure a deliberate frame.|The mountain repeats the seat's hard shape at a larger scale.|The grid makes order visible beside the small free flame.
major-05-the-hierophant|A tradition can become a question you choose to keep asking.|Learning deepens when inherited forms meet lived experience.|Which teaching proved useful in practice today?|The keys sit beneath the teacher and listeners.|The arch creates a shared space for the lesson.|The open book gives the gathered figures something to examine.
major-06-the-lovers|A choice becomes clearer when feeling and action can meet.|Connection asks each person to remain visible and truthful.|Where did your choices align with what you value?|The two figures face each other across a narrow path.|The trees frame the meeting without closing it in.|The sun is shared by both sides of the scene.
major-07-the-chariot|Direction can coexist with feelings that pull in different ways.|Movement becomes purposeful when the reins stay in your hands.|What did you guide with intention today?|The wheels promise movement beneath the still driver.|The two steeds differ, yet share one road.|The star canopy holds a wide sky over a focused journey.
major-08-strength|Gentleness can stay present with a powerful feeling.|Patience gives courage a longer reach than force alone.|Where did a softer grip serve you today?|The lion remains powerful beneath the resting hand.|The open hand meets the mane without a weapon.|The loop floats over the shared calm rather than binding it.
major-09-the-hermit|Solitude can clarify what noise has covered.|A small light is enough for the next bend, even when the route is long.|What became clearer in a quiet moment?|The lantern lights a short stretch instead of the whole mountain.|The path turns beyond the visible pool of light.|The staff gives the traveler something steady to hold.
major-10-wheel-of-fortune|Change has a center even when its edges keep moving.|Timing matters, yet a response remains yours to choose.|What changed today, and how did you respond?|The wheel turns at the center of the scene.|Four corner lights keep their positions around the motion.|The orbit makes repetition and movement visible together.
major-11-justice|Clarity improves when action and effect are weighed together.|A fair repair begins with what can actually be seen.|What evidence changed your judgment today?|The scales hang level before the seated witness.|The sword draws a firm vertical through the space.|The straight line asks the eye to measure both sides.
major-12-the-hanged-man|A pause can loosen a question without solving it at once.|The view changes when you let the scene turn around you.|What looked different after you paused?|The suspended figure rests within a reversed view.|The halo keeps the face bright amid the inversion.|The triangle points toward a changed orientation.
major-13-death|An ending can be honored without being made permanent.|Clearing a threshold is part of making room for life.|What did you release or finish today?|The gate frames passage rather than a sealed wall.|The setting sun marks a cycle that has reached its close.|The shoot crosses the threshold with new growth.
major-14-temperance|A workable rhythm is made through repeated adjustment.|Different needs can meet without losing their shape.|Where did you find a steadier measure today?|The two vessels keep their forms during the exchange.|The stream gives the transfer a visible path.|The horizon stretches beyond this one act of balance.
major-15-the-devil|A pattern is easier to change once its clasp is visible.|Agency begins with naming both the comfort and cost of attachment.|What grip became easier to name today?|The chain looks heavy but has an opening.|The shadow enlarges the scene without hiding the figures.|The flame gives the dark space a point of light.
major-16-the-tower|A hard truth can reveal the ground beneath an old structure.|Tend what is living before deciding how to rebuild.|What remained sound after a disruption?|The lightning reaches the crown of the tower.|The broken tower shows the limits of its old form.|The open ground appears where the stones have fallen.
major-17-the-star|Renewal can arrive in a quiet, repeatable act.|Hope is a resource you may refill slowly.|What small light remained visible today?|The eight stars gather around one larger light.|The jars direct water toward two different places.|The pool receives one stream and holds it.
major-18-the-moon|Uncertainty can be observed without being forced into a verdict.|A winding route may still be worth following carefully.|What remained unclear, and what can wait?|The moon lights a path that is not fully explained.|The towers stand far apart along the wavering route.|The path passes the watchful animals into distance.
major-19-the-sun|Joy becomes more real when you let it be noticed.|Vitality can be shared without demanding a perfect day.|What felt warm or alive today?|The sun takes up nearly the whole sky.|The horse carries the rider through the bright field.|The sunflowers repeat small discs of light below.
major-20-judgement|A review can become a call to act differently.|Awakening asks for an honest response to what you now know.|What did you answer more honestly today?|The trumpet sends one call across the scene.|The open graves hold separate starting points for the figures.|The horizon gives the rising figures a common direction.
major-21-the-world|Completion can be celebrated without closing every opening.|Belonging has room for movement, witness, and change.|What could you mark as complete today?|The wreath is open where a next step may pass.|Four witnesses hold the edges of the scene.|The dancer moves inside the circle rather than standing fixed.
wands-01-ace|An idea becomes a beginning when it finds a hand willing to act.|A spark needs a little room before it needs a plan.|What spark did you give attention to today?|The staff sprouts while being offered outward.|The ember gives the new growth a point of heat.|The open hand releases an invitation into the scene.
wands-02-two|Planning can widen the horizon without postponing the first move.|A vision gains shape through one chosen direction.|What option became clearer today?|The globe suggests a world larger than the parapet.|The parapet gives the traveler a place to survey from.|Two staffs frame an opening rather than a closed gate.
wands-03-three|Work sent outward needs patience for its answer.|Expansion includes listening to what comes back.|What response did you notice from something begun earlier?|The three staffs stand watch after the departure.|The ships have already moved beyond the shore.|The horizon holds what has not returned yet.
wands-04-four|A milestone deserves a place where people can gather.|Welcome is a structure made by many hands.|What could you celebrate with someone else?|Four living posts hold the scene upright.|The garland joins the posts overhead.|The doorway opens toward the little gathering beneath it.
wands-05-five|Friction may reveal different strengths in the same room.|The work is to give shared energy a useful direction.|Which disagreement taught you something today?|The crossed staffs meet at varied angles.|Five sparks show the heat made by contact.|The uneven ground keeps every stance in motion.
wands-06-six|Recognition can be received without pretending the work is finished.|A visible success may invite a wider circle into the effort.|What contribution did you acknowledge today?|The laurel marks a moment of public recognition.|The raised staff stays visible above the street.|The crowd answers with small lights of its own.
wands-07-seven|A boundary can protect a purpose without closing the heart.|Conviction asks for a stance you can explain.|Where did you stand for something today?|The ridge puts one figure in a high, exposed place.|The staffs rise from below toward that position.|The stance is active, with room to adjust.
wands-08-eight|Speed is useful when you can still name the destination.|A message in motion deserves a landing place.|What moved quickly, and where did it land?|The staffs move together through open air.|Diagonal lines make their direction visible.|The distant field leaves the landing unresolved.
wands-09-nine|Experience can guide a boundary without becoming permanent alarm.|Rest and readiness can share the same ground.|What helped you feel steadier after strain?|The bandage records effort already spent.|The fence of staffs forms a visible perimeter.|The watchful eye faces outward from a guarded position.
wands-10-ten|A load can be real without becoming yours alone forever.|Nearness to a goal does not erase the need for limits.|What burden could be shared or set down?|The bundle bends over the traveler.|The road still leads onward beneath the weight.|The town is close enough to be seen.
wands-11-page|Curiosity keeps a new flame alive long enough to learn from it.|The first lesson may matter more than a finished map.|What did you learn by looking closely today?|The young traveler studies rather than charges ahead.|The staff carries a small living flame.|The flame is held near enough to examine.
wands-12-knight|Momentum can carry a bold idea into the world.|Drive works best when it can still hear the terrain.|What did you pursue with energy today?|The rider leans into the journey.|The plume repeats the forward motion above.|The desert wind gives the landscape its own force.
wands-13-queen|Warmth can lead by making others more able to grow.|Confidence need not crowd out watchfulness.|Who felt more able to shine around you today?|The sunflower holds a bright center above the garden.|The cat keeps watch close to the Queen.|The staff turns the light into something held and tended.
wands-14-king|Vision becomes stewardship when it leaves a place to build.|A steady seat can direct fire without putting it out.|What did you help take shape today?|The throne gives the figure a place of responsibility.|The lion recalls courage beside authority.|The flame remains alive at the end of the staff.
cups-01-ace|Openness can make more room than you expected.|A feeling may flow outward without being exhausted.|What feeling found a useful place today?|The cup is full enough to spill over.|The waterfall travels beyond the vessel on both sides.|The dove brings a light presence to the offering.
cups-02-two|Mutuality begins when both sides can bring a full self.|An agreement is stronger when it crosses a real distance.|Where did you meet someone halfway today?|The cups rise into the same shared space.|Joined hands mark the moment of connection.|The bridge lets two figures approach from different sides.
cups-03-three|Celebration can make room for one more person.|Friendship is kept alive by showing up together.|What joy did you share today?|Three cups lift at equal height.|The fruit grounds the gathering in plenty.|The circle stays open at its edge.
cups-04-four|A pause may reveal what an offer really means to you.|Reconsideration is different from refusing everything.|What offer looked different after you rested?|The seated figure looks inward beneath the tree.|The offered cup waits beside rather than in the figure's hand.|The tree offers shade for a longer look.
cups-05-five|Loss deserves space, and remaining support deserves a glance.|Grief and possibility can occupy the same scene.|What support was still present today?|The spilled cups remain visible near the grieving figure.|Two standing cups hold what has not been lost.|The river marks movement beyond this still moment.
cups-06-six|A memory can be a gift when it meets the present gently.|Kindness travels through small, ordinary gestures.|What memory felt kind to revisit today?|The flower cups turn a familiar vessel into an offering.|The courtyard holds the meeting in an older place.|Two children share a small moment beneath the window.
cups-07-seven|Imagination widens choice when you also find the ground.|Many possibilities deserve a patient, practical look.|Which possibility became more real today?|Seven visions offer more than one story.|The cloud holds the vessels above ordinary ground.|The veils keep some forms uncertain.
cups-08-eight|Leaving can be an act of care for what comes next.|A search begins when an old vessel no longer answers.|What did you walk away from or toward today?|The stacked cups stay at the shore.|The night road carries the figure beyond them.|The mountain gives the search a rising shape.
cups-09-nine|Enoughness can be noticed before everything is perfect.|Contentment deserves a moment without apology.|What was enough for you today?|Nine cups line the shelf behind the figure.|The arch makes a shelter of the display.|The smile is quiet, with room for rest.
cups-10-ten|Belonging is made through people who tend a place together.|Harmony can be ordinary work as well as a bright moment.|What made a place feel more like home today?|The cups arc above the scene like a shared shelter.|The home stands below the bright curve.|The family gathers where the arch meets daily life.
cups-11-page|Wonder can arrive inside an ordinary container.|A strange message may deserve curiosity before explanation.|What surprised you in a gentle way today?|The fish surfaces from an unexpected place.|The young dreamer gives the small visitor attention.|The shore keeps another world close by.
cups-12-knight|An offering becomes meaningful when it respects the crossing.|Feeling can move forward at a considerate pace.|What did you offer with care today?|The rider carries a cup rather than a weapon.|The cup stays upright in the offered hand.|The river crossing invites a pause before arrival.
cups-13-queen|Empathy can be deep without losing your own shore.|Care listens closely and keeps its vessel within reach.|Where did you listen with steadiness today?|The ornate cup rewards close attention.|The shore holds the Queen beside moving water.|The throne offers a still seat near the current.
cups-14-king|Composure lets feeling move without denying it.|Care can remain centered in changing conditions.|What helped you stay present today?|The throne stays fixed amid moving water.|The open sea stretches beyond either side.|The cup remains held within the wider scene.
swords-01-ace|A clear thought can open room for an honest next step.|Truth is useful when it can be carried responsibly.|What became clearer today?|The upright blade opens the center of the image.|The crown meets the blade at its highest point.|The clear sky gives the thought breathing room.
swords-02-two|A difficult decision may need more than a guarded position.|Stillness can be a pause for evidence, not a permanent wall.|What information would help you choose?|The crossed blades protect and obstruct at once.|The blindfold limits what the seated figure can see.|The sea remains open beyond the defended posture.
swords-03-three|Pain deserves plain language and a place to be felt.|An honest wound can begin to heal when it is witnessed.|What hurt needed gentleness today?|The heart is the clear center of the image.|Three blades mark the injury without hiding it.|The rain gives the surrounding space a grief of its own.
swords-04-four|Rest can be an intentional part of recovery.|A quieter room may give thought a place to settle.|What rest made space for you today?|The figure has laid the active stance aside.|The window lets light into the still room.|Four blades keep their place while the figure pauses.
swords-05-five|Winning a point may still cost a relationship.|Conflict asks what remains after the sharp words.|What cost did you notice in a disagreement?|Scattered blades show the aftermath rather than the contest.|Departing figures make the distance between people visible.|The wind moves through a field emptied by conflict.
swords-06-six|A passage can carry difficult things without being defined by them.|Movement toward a new bank may be gradual.|What did you carry through a transition today?|The boat holds people and their cargo together.|Six blades travel upright rather than disappearing.|The far bank gives the crossing a direction.
swords-07-seven|Strategy works best when it can face its own motives.|A clever move deserves an honest look at what it leaves behind.|What choice needs a more open explanation?|The stepping figure moves quietly away.|Carried blades make the weight of the choice visible.|The tents remain beside two blades left behind.
swords-08-eight|A visible opening can be hard to trust from inside fear.|Small movements may show where a boundary is looser than it seems.|Where did you find a little room today?|The blindfold has room to loosen.|The blade ring has a gap rather than a sealed edge.|The path continues beyond the enclosing swords.
swords-09-nine|A night thought may feel larger than the day that follows.|Care for the mind can start with naming one real need.|What helped quiet a repeating thought?|The bed locates worry in a sleepless room.|Nine marks hover above the resting place.|The hands bring the figure's feeling into view.
swords-10-ten|An exhausted ending can still contain a dawn.|The next step begins after you acknowledge what has ended.|What is finished enough to let rest?|The fallen figure marks a hard stop.|Ten blades stand against the horizon.|Dawn appears behind the darkest edge.
swords-11-page|Curiosity can keep a sharp mind open.|Vigilance serves best when it listens before striking.|What question sharpened your view today?|The young scout lifts the blade with care.|The sword gives attention a precise line.|The wind makes the scene less settled than the stance.
swords-12-knight|Urgency is useful when it leaves room for a check.|Strong words need a direction as well as force.|Where did you slow a rush just enough?|The rider moves into a demanding sky.|The storm pushes against the forward drive.|The blade points ahead of the horse.
swords-13-queen|Discernment can speak plainly and remain humane.|A firm boundary may leave the air clearer.|What did you say honestly today?|The upright sword keeps a clear line.|The open hand balances firmness with invitation.|The cloud break lets light reach the seat.
swords-14-king|Reason earns trust when it names its evidence and effects.|Authority should make thought accountable to people.|Whose perspective changed your decision today?|The throne gives the figure a position of judgment.|The butterflies offer small signs of change around the seat.|The sword holds a visible standard beside the ruler.
pentacles-01-ace|A practical opening grows through modest, repeated care.|A resource becomes useful when it reaches workable ground.|What small investment did you make today?|The coin is held as something to plant or use.|The garden gate opens onto a prepared place.|The hand brings opportunity into reach.
pentacles-02-two|Balance is a rhythm you revise while life moves.|Priorities become clearer when their currents are visible.|What did you simplify to make room today?|Two coins move in relation rather than standing alone.|The ribbon loops through both demands.|The waves remind the eye that conditions move.
pentacles-03-three|Good work becomes stronger when skills meet.|Making a plan visible invites useful correction.|Whose contribution improved your work today?|The workshop gives different makers a shared place.|Three coins mark the joined craft above them.|The blueprint makes the idea available for discussion.
pentacles-04-four|A reserve can protect freedom when the grip stays flexible.|Security needs a purpose beyond simply holding still.|What resource could circulate more freely?|Four coins occupy different places around the figure.|The gate is closed while the city remains outside.|The city suggests life beyond a guarded position.
pentacles-05-five|A hard season need not be carried unseen.|Practical help can begin with one named need.|What warmth or help did you accept today?|Snow makes the road visibly difficult.|The stained window gives the dark walk a lit point.|The door suggests a place to ask for shelter.
pentacles-06-six|A kind exchange keeps dignity on both sides.|Generosity works best when its terms can be seen.|Where did giving and receiving feel balanced?|The scales hover over the exchange.|Open palms show both need and willingness.|Six coins mark the material stakes of the gesture.
pentacles-07-seven|Growth deserves observation before another change of course.|Patience can include measurement and adjustment.|What evidence of growth did you notice?|The garden holds work already planted.|Seven coins appear among the growing forms.|The leaning staff gives the watcher a place to pause.
pentacles-08-eight|Skill gathers through attentive repetition.|One inspected piece can teach more than a perfect intention.|What did practice teach you today?|The workbench holds the current task close.|The row of coins shows earlier pieces side by side.|The tool stays in reach for another attempt.
pentacles-09-nine|Earned ease can be enjoyed without losing independence.|A tended place can support both solitude and sharing.|What pleasure did you let yourself receive?|The vineyard records long care in ordered rows.|The falcon offers a companion to the solitary figure.|Nine coins make accumulated work visible.
pentacles-10-ten|Legacy is a shelter made useful by the people beneath it.|What lasts should leave room for those who come next.|What might your work make possible for others?|The archway spans more than one person.|Ten coins form a visible pattern overhead.|The family gives the structure its human purpose.
pentacles-11-page|A material possibility becomes a lesson through use.|The learner's first project can reveal the next question.|What did you learn by making today?|The young student studies what is held.|The coin makes the possibility concrete.|The field waits for work beyond the first idea.
pentacles-12-knight|A deliberate pace can make progress dependable.|Reliability includes checking that the destination still matters.|What steady action moved something forward?|The horse carries the figure without a rush.|The plowed field shows work already done.|The coin stays in hand through the journey.
pentacles-13-queen|Care for a place should include the person who tends it.|Comfort is built through practical attention to living needs.|What care did you make room for yourself?|The garden throne is surrounded by living growth.|The rabbit brings a small animal presence near the seat.|The coin rests among the other things being tended.
pentacles-14-king|Prosperity means more when it supports a life beyond possession.|Stewardship asks how resources continue to serve others.|What did you manage with perspective today?|The stone throne gives resources a durable setting.|Vines climb the seat rather than remaining contained by it.|The coin remains close to the figure's hand.
""".strip()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _variant(symbol: str) -> str:
    """Choose a bounded, neutral treatment matching the symbol's material."""
    words = set(_slug(symbol).split("-"))
    if words & {"water", "river", "sea", "pool", "waves", "cup", "cups", "waterfall", "stream", "shore", "rain"}:
        return "ripple"
    if words & {"sun", "moon", "stars", "star", "sky", "light", "flame", "ember", "sparks", "dawn", "lantern"}:
        return "glimmer"
    if words & {"road", "path", "line", "lines", "ribbon", "orbit", "wind", "bridge", "crossing"}:
        return "trace"
    if words & {"flower", "flowers", "garden", "grain", "field", "tree", "vines", "vineyard", "fruit", "shoot", "sunflowers"}:
        return "grain"
    if words & {"wheel", "wheels", "coin", "coins", "crown", "wreath", "arch", "archway", "loop", "halo", "circle"}:
        return "halo"
    return "ember" if words & {"staff", "staffs", "wand", "plume"} else "trace"


def authored_experience(card: Mapping[str, object]) -> dict:
    """Build metadata from this card's hand-written row and canonical symbols."""
    card_id = card["id"]
    try:
        row = next(line.split("|") for line in _ROWS.splitlines() if line.startswith(f"{card_id}|"))
    except StopIteration as exc:
        raise ValueError(f"Missing authored experience for {card_id}") from exc
    if len(row) != 7:
        raise ValueError(f"Expected seven editorial columns for {card_id}")
    _, first, second, evening, *observations = row
    symbols = card["symbols"]
    if len(symbols) != 3:
        raise ValueError(f"Expected three canonical symbols for {card_id}")
    prefix = card_id
    return {
        "facets": [
            {"id": f"{prefix}-lens-{_slug(card['keywords'][0])}", "lens": card["keywords"][0], "text": first},
            {"id": f"{prefix}-lens-{_slug(card['keywords'][1])}", "lens": card["keywords"][1], "text": second},
        ],
        "prompts": [
            {"id": f"{prefix}-prompt-daylight", "text": card["reflection"], "dayparts": ["morning", "day"]},
            {"id": f"{prefix}-prompt-evening", "text": evening, "dayparts": ["evening"]},
        ],
        "art_symbols": [
            {"id": f"{prefix}-symbol-{_slug(label)}", "label": label,
             "variant": _variant(label), "observation": observation}
            for label, observation in zip(symbols, observations)
        ],
    }


def validate_experience(card: Mapping[str, object]) -> None:
    """Reject missing, unstable, ambiguous, or ungrounded authored metadata."""
    metadata = card["experience"]
    if not isinstance(metadata, dict) or set(metadata) != {"facets", "prompts", "art_symbols"}:
        raise ValueError(f"Invalid experience collections for {card['id']}")
    for key, expected in (("facets", 2), ("prompts", 2), ("art_symbols", 3)):
        values = metadata[key]
        if not isinstance(values, list) or len(values) != expected:
            raise ValueError(f"Invalid {key} count for {card['id']}")
        if not all(isinstance(item, dict) for item in values):
            raise ValueError(f"Invalid {key} entries for {card['id']}")
        ids = [item.get("id") for item in values]
        if not all(isinstance(item, str) and _ID.fullmatch(item) for item in ids) or len(set(ids)) != len(ids):
            raise ValueError(f"Invalid {key} IDs for {card['id']}")
        if not all(item.startswith(f"{card['id']}-") for item in ids):
            raise ValueError(f"Unscoped {key} IDs for {card['id']}")
    for item in metadata["facets"]:
        if set(item) != {"id", "lens", "text"} or not all(isinstance(item[k], str) and item[k].strip() for k in ("lens", "text")):
            raise ValueError(f"Invalid facet for {card['id']}")
    covered = set()
    for item in metadata["prompts"]:
        if set(item) != {"id", "text", "dayparts"} or not isinstance(item["text"], str) or not item["text"].strip().endswith("?"):
            raise ValueError(f"Invalid prompt for {card['id']}")
        periods = item["dayparts"]
        if not isinstance(periods, list) or not periods or not all(isinstance(p, str) for p in periods) or not set(periods) <= set(DAYPARTS) or len(periods) != len(set(periods)):
            raise ValueError(f"Invalid prompt dayparts for {card['id']}")
        if covered.intersection(periods):
            raise ValueError(f"Ambiguous prompt dayparts for {card['id']}")
        covered.update(periods)
    if covered != set(DAYPARTS):
        raise ValueError(f"Incomplete prompt dayparts for {card['id']}")
    if set(item["label"] for item in metadata["art_symbols"]) != set(card["symbols"]):
        raise ValueError(f"Art symbols must match canonical symbols for {card['id']}")
    for item in metadata["art_symbols"]:
        if set(item) != {"id", "label", "variant", "observation"} or not isinstance(item["variant"], str) or item["variant"] not in VARIANTS or not isinstance(item["observation"], str) or not item["observation"].strip().endswith("."):
            raise ValueError(f"Invalid art symbol for {card['id']}")


def _choose(seed: bytes, lane: str, choices: list[dict]) -> dict:
    digest = hashlib.sha256(seed + b"\0" + lane.encode("ascii")).digest()
    # Sort by permanent ID so an editorial reorder does not alter selection.
    return min(choices, key=lambda item: hashlib.sha256(digest + item["id"].encode("ascii")).digest()).copy()


def select_experience(card: Mapping[str, object], seed: bytes, daypart: str) -> dict:
    """Select complete authored objects for the immutable Daily Om snapshot."""
    if not isinstance(seed, bytes) or len(seed) != 32:
        raise ValueError("Experience seed must be exactly 32 bytes")
    if daypart not in DAYPARTS:
        raise ValueError(f"Unknown daypart: {daypart!r}")
    validate_experience(card)
    metadata = card["experience"]
    prompts = [item for item in metadata["prompts"] if daypart in item["dayparts"]]
    prompt = _choose(seed, "prompt", prompts)
    prompt["period"] = daypart
    prompt.pop("dayparts")
    return {
        "facet": _choose(seed, "facet", metadata["facets"]),
        "prompt": prompt,
        "symbol": _choose(seed, "symbol", metadata["art_symbols"]),
    }


def validate_deck_content(cards: list[dict]) -> None:
    """Ensure no authored row or card is silently orphaned."""
    if len(cards) != 78 or len({card["id"] for card in cards}) != 78:
        raise ValueError("Living Deck requires 78 unique cards")
    rows = [line.split("|", 1)[0] for line in _ROWS.splitlines()]
    if len(rows) != 78 or len(set(rows)) != 78 or set(rows) != {card["id"] for card in cards}:
        raise ValueError("Authored experience rows do not match the deck")
    for card in cards:
        validate_experience(card)
