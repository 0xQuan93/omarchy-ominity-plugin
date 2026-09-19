#!/usr/bin/env python3
"""Build Ominity's original, deterministic 78-card catalog and SVG plates.

All prose and drawings here are original. The traditional card names and suit
structure are shared tarot vocabulary; no published deck artwork is reproduced.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import colorsys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
DECK_DIR = ROOT / "deck"
CARD_DIR = ROOT / "assets" / "cards"

# Columns: title | upright | reversed | interpretation | symbols | reflection |
# keywords | journey station. Symbols and keywords use semicolons within a field.
MAJORS = """
The Fool|Begin with trust; make room for surprise.|A leap made to escape; innocence without attention.|A new path asks for curiosity and a small act of courage. Look down long enough to choose your footing, then move.|cliff;white flower;open sky|What could you begin before you feel entirely ready?|beginnings;trust;possibility|The threshold
The Magician|Gather your tools and act with intention.|Scattered energy; skill used for display.|The resources are already on the table. Name the result you want and bring attention, word, and hand into alignment.|table;raised hand;infinity loop|Which tool in your reach have you overlooked?|agency;craft;focus|The first act
The High Priestess|Listen beneath the obvious; honor what is hidden.|Doubt in your intuition; a secret kept too long.|Pause before forcing an answer. A quiet pattern is becoming visible through dreams, timing, and what remains unsaid.|veil;moon;still water|What do you know when you stop arguing with yourself?|intuition;stillness;inner knowing|The inner door
The Empress|Nourish what wants to grow.|Overgiving; comfort that keeps you still.|Creation needs warmth, rhythm, and room. Tend the body and the place that makes your work possible.|garden;grain;river|What would flourish with steadier care?|abundance;care;creation|The living garden
The Emperor|Give your vision a durable shape.|Rigidity; control mistaken for safety.|A clear boundary can protect what matters. Build a structure that serves people and can be revised when life changes.|stone throne;mountain;grid|What rule supports your freedom, and what rule limits it?|structure;stewardship;boundary|The chosen frame
The Hierophant|Learn from a lineage; test its wisdom in life.|Unexamined convention; rejecting guidance on reflex.|A teacher, ritual, or shared practice can offer a language for your experience. Keep the part that makes you more awake.|keys;arch;open book|Which inherited practice deserves a fresh question?|tradition;learning;ritual|The shared language
The Lovers|Choose in alignment with your values.|A split desire; an agreement made without honesty.|Attraction is only the beginning. Let a meaningful choice reflect who you are becoming and what you can offer in truth.|two figures;tree;sun|What choice lets your heart and actions agree?|choice;union;integrity|The true choice
The Chariot|Direct opposing forces toward one aim.|Momentum without direction; forcing an outcome.|You do not need every feeling to agree before moving. Hold the reins with purpose and adjust as the terrain answers back.|wheels;two steeds;star canopy|What deserves your full direction now?|resolve;movement;self command|The road outward
Strength|Meet intensity with patience and brave tenderness.|Suppressed anger; courage worn as a mask.|Real strength can stay present with a difficult instinct without crushing it. Gentleness gives courage a longer life.|lion;open hand;lemniscate|Where would a softer grip make you stronger?|courage;patience;compassion|The quiet courage
The Hermit|Step back to hear your own signal.|Isolation that closes the door to help.|Solitude can turn experience into wisdom. Carry a small light, and return with what it shows you.|lantern;mountain path;staff|What becomes clear when the noise recedes?|solitude;insight;discernment|The inward climb
Wheel of Fortune|Notice the turning; respond to the moment.|Resistance to change; surrendering your agency to chance.|Conditions shift beyond any single hand. Find the choice available within the turning rather than demanding that the wheel stop.|wheel;four corners;orbit|What can you influence inside a changing season?|cycles;timing;adaptation|The turning point
Justice|Look at the facts and make a fair repair.|Avoiding consequences; a verdict without context.|Clarity asks you to weigh actions and effects together. A just response is accountable, proportionate, and open to evidence.|scales;sword;straight line|What truth would improve this decision?|fairness;accountability;clarity|The honest measure
The Hanged Man|Pause and let a different angle appear.|Stalling disguised as surrender; needless sacrifice.|A pause can loosen an old assumption. Release the urge to solve everything at once and notice what changes when you turn the question around.|suspended figure;halo;inverted triangle|What can you see from the position you resisted?|pause;perspective;release|The turned view
Death|Let an ending make space for life.|Clinging to a finished form; fear of transition.|Something has completed its work. Grieve what deserves grief, then clear a place for the next honest shape.|gate;setting sun;new shoot|What is ready to be honored and released?|ending;renewal;transition|The necessary ending
Temperance|Blend differences at a sustainable pace.|Excess; a forced compromise that serves no one.|Integration is an active craft. Move between two needs carefully until a workable rhythm emerges.|two vessels;stream;horizon|Which extremes could become a useful rhythm?|balance;integration;patience|The living mixture
The Devil|Name the bond that narrows your choices.|Shame after escape; a pattern beginning to loosen.|A habit can feel permanent while still having a clasp. Examine what it offers you, what it costs, and where your hand can open it.|loose chain;shadow;flame|What attachment asks to be seen clearly?|attachment;temptation;agency|The visible chain
The Tower|Let the false structure fall; protect what is alive.|Fear of disruption; rebuilding on the same fracture.|A sudden truth can shake a carefully built story. Tend the immediate needs first, then build with materials that can bear reality.|lightning;broken tower;open ground|What truth is asking for a safer foundation?|rupture;truth;rebuilding|The clearing storm
The Star|Restore hope through small, steady acts.|Exhaustion; losing sight of available support.|After upheaval, the future may arrive as a trickle rather than a trumpet. Refill what is depleted and let simplicity count.|eight stars;water jars;pool|What small source of renewal is already near?|hope;renewal;trust|The open night
The Moon|Travel gently through uncertainty.|Confusion hardened into fear; a story mistaken for fact.|The path is real even when its edges blur. Check your senses, allow dreams to speak, and wait for daylight before making a final claim.|moon;two towers;winding path|What uncertainty can you hold without inventing certainty?|mystery;dream;uncertainty|The night crossing
The Sun|Share the joy of what is plainly alive.|Overexposure; pressure to feel cheerful.|A bright moment deserves to be received without apology. Let warmth make you generous, and give your success room to breathe.|sun;horse;sunflowers|What can you celebrate without explaining it away?|joy;vitality;openness|The clear day
Judgement|Answer a call to change with honesty.|Self-condemnation; ignoring a needed reckoning.|Review the past without living there. Take responsibility, claim what you learned, and step into the next version of your life.|trumpet;open graves;horizon|What part of your life is asking for a clear answer?|awakening;review;renewal|The answering call
The World|Complete the circle and inhabit the wider view.|A threshold delayed; closing before the lesson lands.|A cycle has become whole enough to release. Name what you made, thank what carried you, and notice the new horizon inside the ending.|wreath;four corners;dancing figure|What completion are you ready to acknowledge?|completion;belonging;integration|The open circle
""".strip()

# Minor records: rank | upright | reversed | interpretation | symbols | reflection | keywords.
# These readings are written for daily reflection, never as deterministic claims.
MINORS = {
    "Wands": """
Ace|A spark invites committed action.|Enthusiasm without a place to land.|The first flame is enough to begin a modest experiment. Give the idea a task before it fades into possibility.|sprouting staff;ember;open hand|What could you try today at a small scale?|inspiration;initiative;energy
Two|Survey the horizon and choose a direction.|Planning that never crosses the doorway.|You can see beyond your present walls. Compare the paths, then make one concrete commitment to the wider world.|globe;parapet;two staffs|Which option grows when you actually test it?|planning;vision;choice
Three|Watch for the return of an effort sent outward.|Impatience; expectations that ignore distance.|The work has left your hands and begun a journey of its own. Stay ready to receive feedback and adjust the next shipment.|three staffs;ships;horizon|What response are you waiting for, and how can you prepare?|expansion;feedback;patience
Four|Make a place for shared celebration.|A milestone missed; belonging that feels conditional.|A threshold deserves a pause. Welcome the people who helped and let the structure of home hold the joy.|four posts;garland;doorway|Who belongs at the table for this moment?|welcome;milestone;community
Five|Meet friction without making an enemy of it.|Conflict avoided until it hardens.|Many energies are crossing at once. Set a fair rule for the exchange and look for the useful difference beneath the noise.|crossed staffs;five sparks;uneven ground|What would make this disagreement constructive?|friction;practice;negotiation
Six|Receive recognition and keep moving with grace.|Approval hunger; success worn like armor.|Let the accomplishment be visible. Thank the team and remember that applause is a moment, not a compass.|laurel;raised staff;crowd|How can you accept praise without depending on it?|recognition;confidence;gratitude
Seven|Hold your ground with a clear reason.|Defending everything; vigilance without rest.|Your position may need a boundary. Choose what truly warrants the effort and let minor challenges pass.|high ridge;seven staffs;stance|Which principle is worth defending now?|conviction;boundary;resolve
Eight|Act while the opening is clear.|Haste that outruns understanding.|Momentum has arrived. Keep messages simple, check the landing place, and let the useful speed carry the work.|flying staffs;diagonal lines;distant field|What can move quickly once you remove one delay?|speed;message;momentum
Nine|Protect your energy without closing your heart.|Exhaustion; expecting every visitor to be a threat.|Experience has made you watchful. Honor the wound and set a boundary that still lets help through.|bandage;fence of staffs;watchful eye|Where do you need rest before another push?|resilience;wariness;rest
Ten|Set down a burden that no longer belongs to you.|Overload defended as duty.|The goal is near, but the bundle is heavy. Redistribute the work or question which pieces ever needed carrying.|bundle of staffs;road;near town|What responsibility can be shared or released?|burden;limits;completion
Page|Follow a lively question into the field.|A promising idea left untested.|Curiosity is a useful guide when paired with attention. Explore, ask, and bring back one observation worth keeping.|young traveler;staff;small flame|What are you excited to learn firsthand?|curiosity;discovery;play
Knight|Bring bold energy to a worthy pursuit.|Rushing past people or details.|A brave move can break inertia. Let courage travel with a map and enough room for others to respond.|rider;plume;desert wind|Where can boldness become useful action?|adventure;drive;direction
Queen|Lead through warmth, confidence, and invitation.|Performing certainty; neglecting your own fire.|Your presence can make other people braver. Tend your own source of energy as you make room for theirs.|sunflower;black cat;staff|How can you make confidence contagious today?|radiance;leadership;warmth
King|Steward a vision and empower its makers.|Dominating the plan; impatience with process.|See the long arc and set a clear standard. The strongest fire gives others light enough to build beside it.|throne;lion;flame|What vision needs steady leadership rather than force?|vision;stewardship;enterprise
""".strip(),
    "Cups": """
Ace|Open to a feeling that wants honest expression.|Emotional overflow; a heart held shut.|A new emotional current is here. Make a vessel for it through conversation, art, or a quiet act of care.|brimming cup;waterfall;dove|What feeling deserves a safe place to land?|feeling;openness;care
Two|Meet another person in mutual respect.|An imbalance hidden by chemistry.|Connection deepens when each person can be seen. Offer what is true and listen for what the other can truly offer.|two cups;joined hands;bridge|Where could reciprocity become clearer?|partnership;mutuality;trust
Three|Let friendship multiply delight.|Feeling outside the circle; celebration postponed.|Good news grows when shared. Reach for the people who can celebrate freely and make room for their stories too.|three cups;fruit;circle|Who would enjoy this moment with you?|friendship;celebration;support
Four|Look again at an offer before dismissing it.|Apathy; chasing novelty to avoid feeling.|A pause may be needed, but numbness can hide a useful invitation. Check what you need before turning away.|seated figure;offered cup;tree|What have you stopped noticing nearby?|reconsideration;pause;awareness
Five|Honor loss while noticing what remains.|Grief denied; hope used to rush healing.|Something mattered and is gone. Give sorrow its real space, then turn gently toward the cups that still stand.|spilled cups;two standing cups;river|What support remains within reach as you grieve?|loss;grief;remaining gifts
Six|Let memory offer comfort and perspective.|Nostalgia that edits out the whole story.|An old kindness may still nourish you. Enjoy the memory and ask what it teaches your present life.|flower cups;old courtyard;two children|Which memory can guide you without trapping you?|memory;kindness;innocence
Seven|Sort enticing possibilities from living choices.|Fantasy replacing commitment.|Many images compete for your attention. Name the real cost and next step for each before choosing one to pursue.|seven visions;cloud;veils|Which dream can survive a practical question?|imagination;options;discernment
Eight|Leave a familiar vessel when it no longer holds you.|Walking away before speaking honestly.|You may have gathered all this place can give. Depart with care, and carry the learning instead of a silent grievance.|stacked cups;night road;mountain|What would you gain by leaving with clarity?|departure;search;release
Nine|Take pleasure in enoughness.|Indulgence that masks an unmet need.|Satisfaction can be a practice. Notice what is good without making the day prove that everything is perfect.|nine cups;arched shelf;smile|What is already enough for one moment?|contentment;gratitude;pleasure
Ten|Nurture the bonds that make joy durable.|Idealizing harmony; quiet needs left unsaid.|The image of a happy home is built from everyday care. Ask what each person needs and celebrate what already connects you.|rainbow of cups;home;family|What small act would strengthen belonging?|belonging;harmony;shared joy
Page|Welcome a surprising message from the heart.|Mood mistaken for a promise.|A tender thought may arrive in an odd form. Stay curious, then give it a clear and kind expression.|fish in cup;young dreamer;shore|What emotion is trying to speak creatively?|wonder;message;sensitivity
Knight|Offer devotion with both poetry and follow through.|Charm without commitment; idealizing another.|A heartfelt invitation deserves a real path. Say what you mean and let actions confirm the beauty of your words.|rider;cup;river crossing|How can you make a sincere gesture concrete?|romance;offering;integrity
Queen|Hold feeling with empathy and healthy edges.|Absorbing every feeling around you.|Your sensitivity is perceptive. Give it a shore: listen deeply while remembering what belongs to you.|ornate cup;shore;quiet throne|Where does care need a boundary?|empathy;intuition;containment
King|Lead with emotional steadiness.|Control disguised as calm; feelings kept offshore.|You can be moved without being swept away. Make room for emotion and respond from a considered center.|stone throne;open sea;cup|What feeling can you acknowledge before deciding?|composure;care;maturity
""".strip(),
    "Swords": """
Ace|Cut through confusion with a useful truth.|Sharpness without care; certainty before evidence.|A clear idea can open the way. Test it honestly and speak it in a form that others can hear.|upright blade;crown;clear sky|What truth needs a precise, kind sentence?|clarity;truth;insight
Two|Make space to decide what you are avoiding.|False peace; information kept outside the room.|A stalemate can protect you briefly, but it cannot choose for you. Gather one missing fact and loosen the crossed guard.|crossed blades;blindfold;sea|What fact would help you choose?|decision;stalemate;information
Three|Name the hurt and tend it directly.|Pain revisited without care; healing hurried.|Heartbreak is real data about what mattered. Give it words, support, and time instead of asking it to disappear on command.|heart;three blades;rain|What would kind attention to this hurt look like?|heartbreak;truth;care
Four|Rest before your thoughts demand it for you.|Avoiding the issue by retreating indefinitely.|Stillness can repair your ability to think. Set a pause with a return point and let the mind unclench.|resting figure;window;four blades|What kind of rest would restore clarity?|rest;recovery;quiet
Five|Question the cost of winning this exchange.|Defeat made into identity; repeating a cruel contest.|A victory can leave the room poorer. Step back from scorekeeping and decide what respect requires now.|scattered blades;departing figures;wind|Which argument could end without another blow?|conflict;cost;repair
Six|Move toward calmer ground with what you have learned.|Transition resisted; carrying every old fear.|The crossing may feel quiet rather than triumphant. Accept help, take the necessary baggage, and leave the rest on shore.|boat;six blades;far bank|What are you ready to carry across, and what can stay?|transition;passage;relief
Seven|Use strategy with integrity.|Secrecy that erodes trust; a plan exposed.|Privacy and cunning can protect a good purpose, yet evasions accumulate a cost. Check whose trust your tactic asks you to spend.|stepping figure;carried blades;tents|Where would directness simplify the plan?|strategy;secrecy;ethics
Eight|Test the limits that feel absolute.|A new exit ignored; fear of first steps.|Some constraints are real, and some tighten when you stop checking them. Find one safe movement and see what the ground permits.|loose blindfold;blade ring;path|Which restriction could you verify today?|constraint;fear;agency
Nine|Bring a private worry into gentle daylight.|Rumination; seeking certainty from sleeplessness.|Thoughts grow louder in the dark. Write down the specific concern, rest if you can, and invite another perspective.|night bed;nine marks;hands|Who or what could help you carry this worry?|anxiety;night;support
Ten|Acknowledge a hard ending and the dawn beyond it.|Refusing the ending; turning pain into a permanent story.|The old line has reached its limit. Care for the injury, stop asking it to continue, and notice the first light at the edge.|fallen figure;ten blades;dawn|What support helps you close this chapter?|ending;exhaustion;dawn
Page|Ask sharp questions and stay teachable.|Suspicion posing as wisdom.|An alert mind sees patterns quickly. Verify them, welcome correction, and use your voice to learn rather than score.|young scout;raised sword;wind|What question would help more than an assumption?|curiosity;vigilance;learning
Knight|Pursue an idea with disciplined speed.|A rush that cuts past people.|Urgency can clear a path when it knows its target. Check the facts and the people affected before charging ahead.|rider;storm;forward blade|Where does speed need one deliberate check?|urgency;argument;focus
Queen|Speak plainly from earned discernment.|Guardedness; wit used to wound.|Clarity can be both firm and humane. Trust your experience and leave room for evidence that changes your view.|upright sword;open hand;cloud break|What boundary can you state without cruelty?|discernment;independence;honesty
King|Make decisions through reason and responsibility.|Rigid judgment; intellect detached from people.|A sound decision can explain its evidence and its stakes. Use authority to make thought accountable to lived effects.|throne;butterflies;sword|Who bears the outcome of this decision?|reason;authority;judgment
""".strip(),
    "Pentacles": """
Ace|Plant a practical opportunity carefully.|An opening missed; security sought without action.|A tangible seed is in your hands. Give it soil, a modest plan, and time to become more than a promising object.|coin;garden gate;hand|What small investment can you make today?|opportunity;resources;seed
Two|Balance moving demands with a flexible rhythm.|Juggling beyond capacity; a choice deferred.|Life has more than one current. Adjust the rhythm and decide which responsibility needs a firmer place.|two coins;infinity ribbon;waves|What can be simplified to make balance real?|adaptation;priorities;rhythm
Three|Build well with other people's expertise.|Working alone to protect control.|The craft improves when different skills meet. Make the plan visible, listen to the person nearest the work, and honor contribution.|workshop;three coins;blueprint|Whose skill would improve this effort?|craft;teamwork;recognition
Four|Protect resources while keeping them in motion.|Clinging; fear disguised as planning.|A reserve can support freedom, yet a locked hand cannot also receive. Decide what truly needs safeguarding and what can circulate.|four coins;closed gate;city|Where has caution become a grip?|security;stewardship;release
Five|Seek warmth and practical help in a hard season.|Shame that keeps support at a distance.|Scarcity can narrow the view. Look for the lit doorway, name a concrete need, and allow help to reach you.|snow;stained window;door|What help could you ask for plainly?|hardship;support;resilience
Six|Give and receive with attention to power.|Generosity with strings; a need hidden by pride.|An exchange can restore dignity when both sides remain visible. Notice who chooses the terms and make the balance kinder.|scales;open palms;six coins|How can this exchange respect everyone involved?|generosity;exchange;equity
Seven|Assess the growth before changing course.|Impatience; tending a plan past its season.|Work needs intervals of observation. Measure what is growing, change what is failing, and resist digging up the roots each day.|garden;seven coins;leaning staff|What evidence would tell you to persist or pivot?|patience;assessment;growth
Eight|Practice the craft one honest repetition at a time.|Perfectionism; labor without learning.|Skill gathers in the marks of repeated work. Set a useful standard, make one more piece, and inspect what improved.|workbench;row of coins;tool|Which repetition would teach you the most?|practice;skill;attention
Nine|Enjoy a freedom you have cultivated.|Isolation inside success; ease treated as a test.|The garden reflects long care. Let yourself receive its pleasures and share from abundance without losing your independence.|vineyard;falcon;nine coins|What earned ease can you allow yourself?|independence;reward;pleasure
Ten|Think beyond today's gain toward shared legacy.|Family expectations overriding present needs.|Resources can become a shelter across generations. Ask what should be preserved, who belongs, and what needs to change.|archway;ten coins;family|What do you hope your work makes possible for others?|legacy;home;continuity
Page|Study a promising material path.|Endless preparation; losing wonder in details.|A practical lesson has your attention. Start as a learner, record what works, and let a small project become your classroom.|young student;coin;field|What could you learn by making one prototype?|study;potential;practice
Knight|Advance through reliable, thoughtful work.|Routine without purpose; stubborn pace.|Consistency can carry more than a dramatic burst. Check that the destination still matters, then take the next grounded step.|steady horse;plowed field;coin|What dependable action would help most today?|reliability;patience;duty
Queen|Care for the material world generously.|Self-neglect inside caretaking.|Comfort grows from attention to bodies, places, and resources. Make the environment nourishing for you as well as everyone else.|garden throne;rabbit;coin|What practical care do you need yourself?|nurture;home;resourcefulness
King|Manage abundance with integrity and perspective.|Possession mistaken for worth.|Good stewardship turns resources into durable wellbeing. Let success be measured by the life it supports and the trust it earns.|stone throne;vines;coin|What would responsible prosperity look like here?|stewardship;stability;prosperity
""".strip(),
}

RANKS = ["Ace", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Page", "Knight", "Queen", "King"]
ELEMENTS = {"Wands": "Fire", "Cups": "Water", "Swords": "Air", "Pentacles": "Earth"}
ROMAN = ["0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI"]


def parse_records(block: str, width: int) -> list[list[str]]:
    rows = [line.split("|") for line in block.splitlines() if line.strip()]
    for row in rows:
        if len(row) != width:
            raise ValueError(f"Expected {width} columns: {row}")
    return rows


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def make_deck() -> list[dict]:
    cards = []
    for number, row in enumerate(parse_records(MAJORS, 8)):
        title, upright, reversed, interpretation, symbols, reflection, keywords, path = row
        card_id = f"major-{number:02d}-{slug(title)}"
        cards.append({
            "id": card_id, "title": title, "arcana": "major", "suit": None,
            "number": number, "numeral": ROMAN[number], "element": None, "path": path,
            "upright": upright, "reversed": reversed,
            "interpretation": interpretation, "symbols": symbols.split(";"),
            "reflection": reflection, "keywords": keywords.split(";"),
            "art": f"assets/cards/{card_id}.svg",
        })
    for suit, block in MINORS.items():
        rows = parse_records(block, 7)
        if [row[0] for row in rows] != RANKS:
            raise ValueError(f"Wrong ranks for {suit}")
        for number, row in enumerate(rows, 1):
            rank, upright, reversed, interpretation, symbols, reflection, keywords = row
            title = f"{rank} of {suit}"
            card_id = f"{slug(suit)}-{number:02d}-{slug(rank)}"
            cards.append({
                "id": card_id, "title": title, "arcana": "minor", "suit": suit,
                "number": number, "numeral": ROMAN[number] if number <= 10 else rank.upper(), "element": ELEMENTS[suit],
                "path": None, "upright": upright, "reversed": reversed,
                "interpretation": interpretation, "symbols": symbols.split(";"),
                "reflection": reflection, "keywords": keywords.split(";"),
                "art": f"assets/cards/{card_id}.svg",
            })
    if len(cards) != 78 or len({c["id"] for c in cards}) != 78:
        raise ValueError("Deck must contain exactly 78 unique cards")
    return cards


INK = "#232b2d"
GOLD = "#997643"
PAPER = "#f2ebd9"
ACCENTS = {"Wands": "#a65942", "Cups": "#4e777c", "Swords": "#596d78", "Pentacles": "#65704b"}


def _rgb(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError(f"Expected a six-digit hex color: {value!r}")
    return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))


def _hex(channels: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def _mix(first: str, second: str, fraction: float) -> str:
    a, b = _rgb(first), _rgb(second)
    return _hex(tuple(round(x * (1 - fraction) + y * fraction) for x, y in zip(a, b)))


def _luminance(value: str) -> float:
    channels = [channel / 255 for channel in _rgb(value)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
    return sum(a * b for a, b in zip(linear, (.2126, .7152, .0722)))


def _contrast(first: str, second: str) -> float:
    bright, dark = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (bright + .05) / (dark + .05)


def _readable(color: str, paper: str, goal: float, fallback: str) -> str:
    """Keep a theme hue, moving toward high-contrast ink only when required."""
    if _contrast(color, paper) >= goal:
        return color.lower()
    if _contrast(fallback, paper) < goal:
        fallback = "#ffffff" if _luminance(paper) < .18 else "#000000"
    for step in range(1, 101):
        candidate = _mix(color, fallback, step / 100)
        if _contrast(candidate, paper) >= goal:
            return candidate
    return fallback.lower()


def _suit_tone(accent: str, muted: str, hue_shift: float) -> str:
    """A related enamel tone; the four suits remain identifiable in any theme."""
    red, green, blue = (channel / 255 for channel in _rgb(accent))
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    shifted = colorsys.hls_to_rgb((hue + hue_shift / 360) % 1,
                                 min(.76, max(.28, lightness)), max(.22, saturation * .78))
    colored = _hex(tuple(round(channel * 255) for channel in shifted))
    return _mix(colored, muted, .12)


@dataclass(frozen=True)
class DeckPalette:
    paper: str = PAPER
    ink: str = INK
    gold: str = GOLD
    back_fill: str = INK
    back_line: str = PAPER
    accents: Mapping[str, str] = field(default_factory=lambda: ACCENTS.copy())

    @classmethod
    def from_theme(cls, background: str, foreground: str, accent: str, muted: str) -> "DeckPalette":
        # A small foreground veil gives the shell background a printed-paper
        # surface while retaining its hue and its light/dark mode.
        paper = _mix(background, foreground, .06)
        ink = _readable(foreground, paper, 7, "#ffffff" if _luminance(paper) < .18 else "#000000")
        gold = _readable(accent, paper, 4.5, ink)
        shifts = {"Wands": -18, "Cups": 146, "Swords": 203, "Pentacles": 78}
        accents = {
            suit: _readable(_suit_tone(accent, muted, shift), paper, 3, ink)
            for suit, shift in shifts.items()
        }
        return cls(paper=paper, ink=ink, gold=gold,
                   back_fill=_mix(paper, ink, .1), back_line=ink, accents=accents)


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def line(x1, y1, x2, y2, cls="ink", extra=""):
    return f'<path class="{cls}" d="M{x1} {y1}L{x2} {y2}" {extra}/>'


def circle(x, y, r, cls="ink", extra=""):
    return f'<circle class="{cls}" cx="{x}" cy="{y}" r="{r}" {extra}/>'


def path(d, cls="ink", extra=""):
    return f'<path class="{cls}" d="{d}" {extra}/>'


def rect(x, y, w, h, cls="ink", extra=""):
    return f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" {extra}/>'


def text_svg(x, y, content, cls="label", extra=""):
    return f'<text class="{cls}" x="{x}" y="{y}" {extra}>{e(content)}</text>'


def star(x, y, r=8, cls="gold"):
    return path(f"M{x} {y-r}L{x+r*.23:.1f} {y-r*.23:.1f}L{x+r} {y}L{x+r*.23:.1f} {y+r*.23:.1f}L{x} {y+r}L{x-r*.23:.1f} {y+r*.23:.1f}L{x-r} {y}L{x-r*.23:.1f} {y-r*.23:.1f}Z", cls)


def figure(x, y, scale=1, facing=1, cls="ink"):
    """An elongated, faceted human silhouette with printmaking-style folds."""
    return f'<g transform="translate({x} {y}) scale({scale*facing} {scale})">' + (
        path("M-9 -69L-11 -82Q-9 -92 0 -93Q10 -91 12 -81L8 -68L5 -64H-5Z", "paperfill")
        + path("M-10 -79Q-13 -93 -1 -96Q10 -97 13 -83Q6 -88 0 -83Q-6 -78 -10 -79Z", "inkfill")
        + path("M3 -76L8 -75M-3 -66Q2 -63 6 -67", "fine")
        + path("M-5 -64L-6 -58M5 -64L6 -58", "ink")
        + path("M-8 -61Q0 -66 8 -61L18 -51L21 -9Q0 4 -21 -9L-18 -51Z", "wash")
        + path("M-11 -55L-22 -23L-27 -18L-23 -14L-18 -17L-6 -47M11 -55L21 -24L25 -20L22 -15L17 -19L6 -47", "paperfill")
        + path("M-8 -47Q0 -39 8 -47M-15 -14Q0 -20 15 -14M-10 -34L-13 -3M9 -35L12 -3M0 -42V-5", "fine")
        + path("M-18 -8Q0 -2 18 -8M-15 -52Q0 -46 15 -52", "gold")
        + path("M-11 -2L-11 2M11 -2L11 2", cls)
    ) + "</g>"


def hill(y=324, peak=217):
    return path(f"M35 {y}Q83 {peak} 135 {y}Q181 {peak+10} 244 {y}L244 368L35 368Z", "wash") + path(f"M35 {y}Q83 {peak} 135 {y}Q181 {peak+10} 244 {y}", "ink")


def water(y=326):
    return "".join(path(f"M42 {y+n*11} Q69 {y-6+n*11} 96 {y+n*11} T150 {y+n*11} T204 {y+n*11} T238 {y+n*11}", "fine") for n in range(4))


def sun(x=140, y=191, r=36):
    return circle(x, y, r, "sun") + "".join(line(x, y-r-8-i*2, x, y-r-17-i*2, "gold", f'transform="rotate({angle} {x} {y})"') for i, angle in enumerate(range(0, 360, 30)))


def moon(x=141, y=175, r=32):
    return circle(x, y, r, "gold") + circle(x+13, y-8, r-2, "paperfill")


def cup(x, y, s=1):
    return f'<g transform="translate({x} {y}) scale({s})">' + path("M-14 -18 Q-14 4 0 8 Q14 4 14 -18Z", "ink") + path("M-12 -13 Q0 -17 12 -13", "gold") + line(0, 8, 0, 23) + line(-10, 23, 10, 23) + "</g>"


def wand(x, y, s=1, rotation=0):
    return f'<g transform="translate({x} {y}) rotate({rotation}) scale({s})">' + path("M-2 24 L-2 -23 Q0 -29 2 -23 L2 24Z", "ink") + path("M1 -12 Q13 -22 13 -30 M-1 1 Q-13 -7 -11 -17", "vine") + "</g>"


def sword(x, y, s=1, rotation=0):
    return f'<g transform="translate({x} {y}) rotate({rotation}) scale({s})">' + path("M0 -30 L5 12 L0 15 L-5 12Z", "ink") + line(-13, 16, 13, 16, "gold") + line(0, 16, 0, 28) + circle(0, 29, 2, "gold") + "</g>"


def pentacle(x, y, s=1):
    coords = [(0, -12), (11.4, -3.7), (7.1, 9.7), (-7.1, 9.7), (-11.4, -3.7)]
    order = [0, 2, 4, 1, 3, 0]
    points = " ".join(f"{coords[i][0]:.1f},{coords[i][1]:.1f}" for i in order)
    return f'<g transform="translate({x} {y}) scale({s})">' + circle(0, 0, 18, "gold") + f'<polyline class="fine" points="{points}"/>' + "</g>"


def motif(name, x, y, s=1, rotation=0):
    return {"Wands": wand, "Cups": cup, "Swords": sword, "Pentacles": pentacle}[name](x, y, s, rotation) if name in ("Wands", "Swords") else {"Cups": cup, "Pentacles": pentacle}[name](x, y, s)


def major_scene(number: int) -> str:
    """Original emblematic plates; imagery uses shared tarot archetypes only."""
    y = 310
    if number == 0:  # Fool: the threshold
        return sun(196, 168, 23) + path("M37 352L37 287L112 287L143 330L143 352Z", "wash") + path("M37 287L112 287L143 330", "ink") + figure(104, 277, 1.24) + wand(128, 232, 0.8, -20) + star(75, 227, 7)
    if number == 1:
        return sun(140, 165, 23) + figure(140, 280, 1.55) + line(139, 198, 139, 147, "gold") + rect(58, 299, 164, 9, "ink") + cup(79, 289, .55) + sword(117, 286, .5) + wand(166, 287, .5) + pentacle(205, 287, .55)
    if number == 2:
        return moon() + rect(57, 215, 23, 135, "column") + rect(200, 215, 23, 135, "column") + path("M77 211 Q140 169 203 211", "ink") + figure(140, 327, 1.35) + water(329)
    if number == 3:
        return sun(140, 173, 30) + path("M39 353Q60 266 120 276Q175 225 241 352", "vine") + figure(140, 294, 1.4) + "".join(star(x, yy, 5, "vine") for x, yy in [(65,283),(82,315),(210,289),(225,327)])
    if number == 4:
        return hill(340, 205) + rect(94, 253, 92, 61, "column") + rect(102, 235, 76, 22, "column") + figure(140, 307, 1.3) + line(182, 244, 182, 312, "gold")
    if number == 5:
        return path("M70 353V207Q140 136 210 207V353", "ink") + path("M87 350V220Q140 170 193 220V350", "fine") + figure(140, 327, 1.12) + rect(112, 278, 56, 42, "paperfill") + line(140, 278, 140, 320, "gold") + star(140, 179, 10)
    if number == 6:
        return sun(140, 165, 28) + figure(91, 332, 1.45, 1) + figure(189, 332, 1.45, -1) + path("M105 253 Q140 224 175 253", "gold") + star(140, 233, 9) + path("M38 351Q140 326 242 351", "vine")
    if number == 7:
        return star(140, 162, 14) + rect(74, 253, 132, 64, "column") + circle(103, 323, 23, "ink") + circle(177, 323, 23, "ink") + figure(140, 251, 1.1) + path("M40 346Q62 290 85 331M240 346Q218 290 195 331", "ink")
    if number == 8:
        return circle(140, 241, 68, "gold") + path("M91 273Q86 211 116 210Q126 191 151 204Q184 196 188 230Q204 272 172 292Q144 307 118 288Z", "ink") + circle(122, 227, 4, "gold") + path("M125 246Q149 256 170 243", "gold") + figure(184, 331, 1.28) + path("M169 293Q153 278 145 267", "fine")
    if number == 9:
        return hill(344, 218) + figure(144, 291, 1.5) + line(173, 242, 173, 325, "gold") + path("M101 230L117 213L133 230L133 248L101 248Z", "lantern") + star(117, 230, 7)
    if number == 10:
        ring = circle(140, 245, 80, "gold") + circle(140, 245, 58, "ink") + circle(140, 245, 17, "gold")
        ring += "".join(line(140, 169, 140, 321, "fine", f'transform="rotate({a} 140 245)"') for a in range(0, 180, 45))
        return ring + "".join(star(x, yy, 6) for x, yy in [(60,158),(220,158),(60,337),(220,337)])
    if number == 11:
        return figure(140, 329, 1.4) + sword(140, 218, 1.2) + line(68, 228, 212, 228, "gold") + line(78, 228, 78, 271, "fine") + line(202, 228, 202, 271, "fine") + path("M59 271Q78 292 97 271ZM183 271Q202 292 221 271Z", "ink") + star(140, 168, 9)
    if number == 12:
        return path("M57 166L223 166M140 166L140 330", "ink") + circle(140, 292, 31, "gold") + figure(140, 228, 1.55) + path("M100 332Q140 346 180 332", "fine")
    if number == 13:
        return path("M55 352V232Q140 148 225 232V352", "ink") + path("M80 352V241Q140 186 200 241V352", "fine") + sun(140, 252, 22) + path("M140 352L140 301M140 326Q113 312 109 292M140 319Q164 302 175 289", "vine")
    if number == 14:
        return figure(140, 301, 1.5) + cup(91, 285, .9) + cup(189, 285, .9) + path("M104 272Q140 302 176 272", "water") + water(340) + sun(140, 161, 21)
    if number == 15:
        return circle(140, 205, 43, "gold") + path("M109 193L97 165M171 193L183 165", "ink") + figure(140, 302, 1.45) + figure(85, 349, .7) + figure(195, 349, .7) + path("M80 311Q86 286 107 281M200 311Q194 286 173 281", "chain") + star(140, 216, 9)
    if number == 16:
        return rect(98, 215, 84, 139, "column") + rect(87, 208, 106, 18, "column") + path("M180 136L123 216L153 211L118 282", "lightning") + path("M94 282L126 267M174 304L203 286", "ink") + star(75, 185, 7)
    if number == 17:
        return "".join(star(x, yy, rr) for x, yy, rr in [(140,153,14),(68,181,6),(100,200,6),(182,200,6),(212,181,6),(80,236,5),(200,236,5),(140,211,6)]) + figure(139, 319, 1.2) + cup(93, 306, .63) + cup(186, 306, .63) + water(338)
    if number == 18:
        return moon(140, 165, 31) + rect(56, 225, 31, 123, "column") + rect(193, 225, 31, 123, "column") + path("M140 354Q107 318 140 288Q172 259 140 240", "fine") + water(345) + star(110, 198, 5) + star(177, 208, 5)
    if number == 19:
        return sun(140, 173, 48) + path("M63 335Q140 306 217 335", "vine") + path("M113 324Q96 291 107 270Q127 247 163 265Q190 287 162 326", "ink") + figure(145, 261, .85) + "".join(star(x, yy, 7, "vine") for x, yy in [(56,316),(76,282),(219,310),(206,277)])
    if number == 20:
        return sun(140, 173, 24) + path("M104 200L149 215L149 231L104 216Z", "gold") + line(149, 223, 192, 236, "gold") + "".join(figure(x, 332, .8) for x in (80, 140, 200)) + path("M42 351L238 351", "ink")
    if number == 21:
        return circle(140, 245, 84, "vine") + circle(140, 245, 75, "gold") + figure(140, 315, 1.6) + "".join(star(x, yy, 7) for x, yy in [(54,159),(225,159),(54,337),(225,337)])
    raise ValueError(number)


def blossom(x: int, y: int, scale: float = 1) -> str:
    petals = "".join(circle(x + dx * scale, y + dy * scale, 5 * scale, "petal")
                     for dx, dy in ((0, -8), (8, 0), (0, 8), (-8, 0)))
    return petals + circle(x, y, 3 * scale, "gold")


def major_detail(number: int) -> str:
    """Small traditional symbols, newly drawn as accents to the main scene."""
    if number == 0:
        return path("M65 348Q62 321 71 302M70 325Q50 313 47 301M68 318Q81 304 88 296", "vine") + blossom(72, 291, .75)
    if number == 1:
        return path("M113 120C89 100 88 150 113 135C139 117 141 107 163 135C186 154 195 103 166 120C144 137 137 151 113 120Z", "gold")
    if number == 2:
        return path("M84 209Q140 187 196 209M84 217Q140 195 196 217M87 221V310M193 221V310", "arch")
    if number == 3:
        return "".join(path(f"M{x} 353Q{x-5} 328 {x+2} 305M{x} 323L{x-9} 314M{x+1} 317L{x+9} 307", "vine") for x in (55, 70, 207, 222))
    if number == 4:
        return path("M102 287H178M102 296H178M113 257V310M140 257V310M167 257V310", "fine")
    if number == 5:
        return path("M74 343Q105 325 140 339Q175 325 206 343L206 362Q173 347 140 359Q105 347 74 362Z", "paperfill") + path("M140 339V359", "gold")
    if number == 6:
        return path("M50 347V296M230 347V296M50 307Q37 296 40 278M50 305Q64 293 67 279M230 307Q217 296 215 280M230 304Q244 291 241 276", "vine")
    if number == 7:
        return path("M55 298Q40 278 49 265Q64 256 72 279M208 279Q218 258 231 265Q240 278 225 298", "ink")
    if number == 8:
        return path("M119 133C98 118 97 164 121 149C141 137 143 128 161 149C183 165 186 118 163 133C143 150 140 163 119 133Z", "gold")
    if number == 9:
        return path("M41 362Q82 341 100 361Q135 334 165 355Q207 332 240 360", "terrain")
    if number == 10:
        return "".join(path(f"M{x-8} {y}H{x+8}M{x} {y-8}V{y+8}", "gold") for x, y in ((59, 153), (221, 153), (59, 334), (221, 334)))
    if number == 11:
        return path("M61 276H95M185 276H219M78 232V271M202 232V271", "gold")
    if number == 12:
        return path("M66 182L140 343L214 182Z", "ridge") + circle(140, 293, 42, "halo")
    if number == 13:
        return path("M65 360Q72 336 82 324M82 324Q66 312 64 303M82 322Q91 307 101 304M206 360Q211 338 202 325M202 325Q189 315 187 306", "vine")
    if number == 14:
        return path("M106 266Q140 306 174 266M107 277Q140 316 175 277", "water") + circle(140, 320, 6, "gold")
    if number == 15:
        return path("M80 339Q107 349 114 331M200 339Q173 349 166 331", "chain") + path("M130 361Q121 345 139 328Q135 346 151 354Q149 369 130 361Z", "regalia")
    if number == 16:
        return path("M44 354L91 331L113 356M167 354L191 326L240 353", "ridge") + "".join(star(x, y, 5) for x, y in ((61, 242), (215, 270), (208, 178)))
    if number == 17:
        return "".join(path(f"M{x} {y-11}V{y+11}M{x-11} {y}H{x+11}", "gold") for x, y in ((68, 180), (212, 180)))
    if number == 18:
        return path("M124 362Q106 332 142 306Q173 284 140 254", "terrain") + circle(72, 202, 3, "gold") + circle(209, 209, 3, "gold")
    if number == 19:
        return blossom(61, 294, 1.1) + blossom(218, 298, 1.1) + path("M61 306V351M218 310V351", "vine")
    if number == 20:
        return "".join(line(140, 137, 140, 117, "gold", f'transform="rotate({a} 140 179)"') for a in range(-70, 71, 35))
    if number == 21:
        return "".join(path(f"M{x} {y}Q{x+10} {y-16} {x+19} {y-5}Q{x+7} {y+1} {x} {y}", "vine") for x, y in ((61, 203), (57, 264), (64, 321), (201, 196), (209, 252), (202, 312)))
    raise ValueError(number)


def pip_scene(card: dict) -> str:
    suit, number = card["suit"], card["number"]
    if number <= 10:
        return numbered_scene(suit, number)
    rank = RANKS[number-1]
    accent = "gold" if suit in ("Wands", "Pentacles") else "fine"
    base = suit_landscape(suit, number) + circle(140, 224, 69, "halo")
    base += path("M48 352Q140 303 232 352M57 361Q140 321 223 361", "terrain")
    if rank == "Page":
        base += figure(137, 322, 1.72) + path("M113 245Q140 216 167 245", "gold") + star(140, 213, 8)
        base += path("M67 335Q97 288 112 305M202 312Q218 315 231 338", "terrain")
    elif rank == "Knight":
        base += path("M48 328Q65 295 91 294Q111 270 132 299Q160 282 187 302L223 338H62Z", "beast")
        base += path("M58 331L48 349M88 329L84 351M184 329L194 349M210 331L222 347", "ink")
        base += figure(139, 274, 1.45) + path("M74 288Q66 275 71 261M73 289Q88 278 93 279", "ink")
    elif rank == "Queen":
        base += path("M81 336V266Q140 234 199 266V336M91 335V278Q140 254 189 278V335", "column")
        base += figure(140, 320, 1.58) + path("M115 228L127 207L140 221L153 207L165 228Z", "regalia")
        base += path("M80 266Q140 238 200 266", "gold")
    elif rank == "King":
        base += path("M75 340V261L99 247H181L205 261V340M91 335V265H189V335", "column")
        base += figure(140, 323, 1.58) + path("M113 230L117 201L130 220L140 198L150 220L163 201L167 230Z", "regalia")
        base += path("M78 267H202M100 248H180", "gold")
    return base + motif(suit, 204, 269, 1.05, -12) + star(66, 189, 7, accent) + star(214, 189, 7, accent)


def suit_landscape(suit: str, number: int) -> str:
    """Four illustrated worlds. The extra geometry is clean ink, never noise."""
    if suit == "Wands":
        return (sun(198, 153, 22) + path("M35 345Q84 277 129 317Q182 245 245 337V382H35Z", "distant")
                + path("M35 353Q98 314 143 340Q197 295 245 349", "terrain")
                + path("M40 365L77 349M195 351L239 366", "fine"))
    if suit == "Cups":
        return (moon(198, 155, 20) + path("M35 324Q76 300 120 324Q175 291 245 322V380H35Z", "distant")
                + water(323) + path("M43 353Q74 341 106 353T169 353T235 353", "water")
                + circle(72, 205, 2, "water") + circle(226, 234, 2, "water"))
    if suit == "Swords":
        return (circle(195, 151, 22, "halo")
                + path("M36 215Q70 189 106 207T180 205T245 210M36 241Q72 217 103 235T177 230T245 236", "cloud")
                + path("M38 349Q91 319 141 344Q198 311 242 343", "terrain")
                + "".join(line(52+i*26, 158, 68+i*26, 143, "wind") for i in range(7)))
    return (path("M36 351Q84 283 141 328Q187 289 244 345V382H36Z", "distant")
            + path("M44 356Q89 330 142 351Q193 323 238 354", "terrain")
            + "".join(path(f"M{x} 359V{yy}M{x} {yy+8}Q{x-12} {yy-3} {x-18} {yy+9}M{x} {yy+7}Q{x+10} {yy-5} {x+17} {yy+8}", "vine")
                       for x, yy in ((65, 264), (215, 267)))
            + sun(193, 155, 18))


def numbered_scene(suit: str, number: int) -> str:
    """A different pictorial composition for every numeral in each suit."""
    land = suit_landscape(suit, number)
    # These placements are part of each scene rather than a repeating pip grid.
    layouts = {
        1: [(140, 225, 1.65, 0)],
        2: [(91, 242, 1.16, -7), (189, 242, 1.16, 7)],
        3: [(75, 265, .99, -5), (140, 211, 1.12, 0), (205, 265, .99, 5)],
        4: [(91, 211, 1.02, 0), (189, 211, 1.02, 0), (91, 305, 1.02, 0), (189, 305, 1.02, 0)],
        5: [(72, 197, .91, -14), (205, 196, .91, 14), (140, 249, 1.06, 0), (88, 309, .91, 12), (198, 310, .91, -12)],
        6: [(80, 205, .88, 0), (140, 189, .88, 0), (200, 205, .88, 0),
            (80, 310, .88, 0), (140, 326, .88, 0), (200, 310, .88, 0)],
        7: [(140, 166, .84, 0), (86, 218, .84, 0), (140, 227, .84, 0), (194, 218, .84, 0),
            (69, 308, .84, 0), (140, 318, .84, 0), (211, 308, .84, 0)],
        8: [(65, 181, .79, -18), (123, 174, .79, -18), (181, 167, .79, -18), (222, 198, .79, -18),
            (59, 278, .79, -18), (117, 271, .79, -18), (175, 264, .79, -18), (221, 297, .79, -18)],
        9: [(78, 190, .78, 0), (140, 181, .78, 0), (202, 190, .78, 0),
            (78, 255, .78, 0), (140, 248, .78, 0), (202, 255, .78, 0),
            (78, 320, .78, 0), (140, 315, .78, 0), (202, 320, .78, 0)],
        10: [(82, 175, .78, 0), (140, 167, .78, 0), (198, 175, .78, 0),
             (65, 232, .78, 0), (116, 232, .78, 0), (164, 232, .78, 0), (215, 232, .78, 0),
             (82, 312, .78, 0), (140, 323, .78, 0), (198, 312, .78, 0)],
    }
    settings = {
        1: path("M83 327Q109 294 140 298Q171 294 197 327M98 316Q140 344 182 316", "hands") + star(140, 144, 10),
        2: circle(140, 245, 62, "halo") + path("M91 296Q140 325 189 296M91 185Q140 157 189 185", "gold"),
        3: path("M41 339Q140 286 239 339M45 184Q140 139 235 184", "arch") + star(140, 310, 7),
        4: path("M56 173V346M224 173V346M56 173Q140 136 224 173M56 346H224", "arch") + path("M68 270H212", "gold"),
        5: path("M48 359L224 151M50 244L223 337M41 279Q140 186 239 279", "tension"),
        6: path("M43 258Q140 225 237 258M43 269Q140 236 237 269", "bridge") + star(140, 259, 7),
        7: path("M42 351L140 141L238 351M62 351L140 185L218 351", "ridge"),
        8: path("M40 326L226 133M40 348L239 142M46 370L241 158", "motion") + star(222, 145, 8),
        9: path("M46 160Q140 112 234 160V350H46Z", "arch") + path("M57 347H223", "gold"),
        10: path("M43 357V158Q140 118 237 158V357M58 346V170Q140 137 222 170V346", "arch") + star(140, 269, 13),
    }
    scale = .87 if suit == "Pentacles" else 1
    pips = "".join(motif(suit, x, y, size * scale, rotation) for x, y, size, rotation in layouts[number])
    return land + settings[number] + pips


def etched_setting(card: dict) -> str:
    """An architectural frame that stays quiet behind the actual illustration."""
    number = card["number"]
    variant = number % 4
    pieces = [
        path("M32 374V148Q140 94 248 148V374", "ghost"),
        path("M38 374V154Q140 108 242 154V374", "ghost"),
        path("M31 375H249", "ghost"),
        star(140, 114, 4, "gold"),
        path("M34 159H43M237 159H246M31 326H39M241 326H249", "ghost"),
    ]
    if card["arcana"] == "major":
        # Repeated etched contours deepen the flat emblems without competing
        # with their central figures. Every major receives a different horizon.
        rise = [321, 314, 333, 327][variant]
        pieces.extend([
            path(f"M39 {rise+24}Q78 {rise-8} 117 {rise+14}Q167 {rise-20} 241 {rise+25}", "landscape"),
            path(f"M39 {rise+34}Q79 {rise+3} 117 {rise+24}Q166 {rise-8} 241 {rise+35}", "ghost"),
        ])
        if number in (0, 1, 3, 6, 7, 8, 14, 19, 20):
            pieces.append(circle(140, 222, 97, "ghost"))
            pieces.extend(path("M140 115L140 124", "ghost", f'transform="rotate({angle} 140 222)"') for angle in range(0, 360, 30))
        else:
            pieces.append(path("M55 208Q140 149 225 208", "ghost"))
    return "".join(pieces)


def card_svg(card: dict, palette: DeckPalette | None = None) -> str:
    palette = palette or DeckPalette()
    ink, gold, paper = palette.ink, palette.gold, palette.paper
    card_id = card["id"]
    seed = int(hashlib.sha256(card_id.encode()).hexdigest()[:8], 16)
    suit = card["suit"]
    accent = palette.accents.get(suit, gold)
    title = card["title"]
    # The name sits below the image; precise serif forms stay legible at scale.
    title_size = 16 if len(title) > 17 else 18 if len(title) > 13 else 22
    top = "MAJOR ARCANA" if card["arcana"] == "major" else f"{e(suit).upper()} · {e(card['element']).upper()}"
    plate = (major_scene(card["number"]) + major_detail(card["number"])
             if card["arcana"] == "major" else pip_scene(card))
    little_stars = "".join(star(49 + (seed >> (i*4) & 0x7) * 25, 118 + (seed >> (i*6) & 0x3) * 22, 2.4, "faint") for i in range(4))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="280" height="480" viewBox="0 0 280 480" role="img" aria-labelledby="title description">
<title id="title">{e(title)} — Ominity Tarot</title><desc id="description">Original etched tarot plate for {e(title)}.</desc>
<style>
.ink{{fill:none;stroke:{ink};stroke-width:2.3;stroke-linecap:round;stroke-linejoin:round}}
.fine{{fill:none;stroke:{ink};stroke-opacity:.53;stroke-width:1.15;stroke-linecap:round;stroke-linejoin:round}}
.gold{{fill:none;stroke:{gold};stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
.faint{{fill:none;stroke:{gold};stroke-opacity:.66;stroke-width:1.25}}
.inkfill{{fill:{ink};stroke:{ink};stroke-width:1}}
.distant{{fill:{accent};fill-opacity:.13;stroke:{accent};stroke-opacity:.58;stroke-width:1.5;stroke-linejoin:round}}
.terrain{{fill:none;stroke:{accent};stroke-opacity:.76;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}}
.halo{{fill:{gold};fill-opacity:.10;stroke:{gold};stroke-width:1.25}}
.cloud{{fill:none;stroke:{ink};stroke-opacity:.32;stroke-width:1.3;stroke-linecap:round}}
.wind{{fill:none;stroke:{accent};stroke-opacity:.60;stroke-width:1.1;stroke-linecap:round}}
.hands{{fill:none;stroke:{ink};stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}}
.arch{{fill:none;stroke:{gold};stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}}
.tension{{fill:none;stroke:{accent};stroke-opacity:.55;stroke-width:1.5;stroke-linecap:round}}
.bridge{{fill:none;stroke:{gold};stroke-width:2.3;stroke-linecap:round}}
.ridge{{fill:none;stroke:{ink};stroke-opacity:.46;stroke-width:1.6;stroke-linejoin:round}}
.motion{{fill:none;stroke:{accent};stroke-opacity:.54;stroke-width:2;stroke-linecap:round}}
.beast{{fill:{accent};fill-opacity:.23;stroke:{ink};stroke-width:1.8;stroke-linejoin:round}}
.regalia{{fill:{gold};fill-opacity:.25;stroke:{gold};stroke-width:1.6;stroke-linejoin:round}}
.petal{{fill:{paper};stroke:{accent};stroke-width:1.5}}
.wash{{fill:{accent};fill-opacity:.11;stroke:{ink};stroke-width:1.8;stroke-linejoin:round}}
.column{{fill:{paper};stroke:{ink};stroke-width:2.1}}
.sun{{fill:{gold};fill-opacity:.2;stroke:{gold};stroke-width:2}}
.paperfill{{fill:{paper};stroke:{ink};stroke-width:1.8}}
.lantern{{fill:{gold};fill-opacity:.35;stroke:{ink};stroke-width:2}}
.vine{{fill:none;stroke:{accent};stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
.water{{fill:none;stroke:{accent};stroke-width:2;stroke-linecap:round}}
.chain{{fill:none;stroke:{gold};stroke-width:3;stroke-dasharray:4 4}}
.lightning{{fill:none;stroke:{accent};stroke-width:7;stroke-linecap:square;stroke-linejoin:miter}}
.ghost{{fill:none;stroke:{gold};stroke-opacity:.52;stroke-width:1.05;stroke-linecap:round;stroke-linejoin:round}}
.landscape{{fill:none;stroke:{accent};stroke-opacity:.58;stroke-width:1.5;stroke-linecap:round}}
.hatch{{fill:none;stroke:{ink};stroke-opacity:.42;stroke-width:1;stroke-linecap:round}}
</style>
<rect width="280" height="480" fill="{paper}"/>
<rect x="8" y="8" width="264" height="464" fill="none" stroke="{gold}" stroke-width="1.8"/>
<rect x="14" y="14" width="252" height="452" fill="none" stroke="{ink}" stroke-width=".75" opacity=".72"/>
<path d="M23 77H257M23 391H257M25 454H255" stroke="{gold}" stroke-width="1"/>
<path d="M20 20L36 20M20 20L20 36M260 20L244 20M260 20L260 36M20 460L36 460M20 460L20 444M260 460L244 460M260 460L260 444" stroke="{ink}" stroke-width="1.4"/>
<text class="number" x="140" y="42" font-family="Noto Serif" font-size="20" font-weight="400" fill="{gold}" text-anchor="middle">{e(card['numeral'])}</text>
<text class="small" x="140" y="64" font-family="Noto Sans" font-size="8" font-weight="600" letter-spacing="1.7" fill="{gold}" text-anchor="middle">{top}</text>
<g clip-path="url(#window)">{etched_setting(card)}{little_stars}{plate}</g>
<defs><clipPath id="window"><rect x="24" y="79" width="232" height="309"/></clipPath></defs>
<path d="M42 382H79M201 382H238" stroke="{gold}" stroke-width=".9"/>
<circle cx="140" cy="382" r="4" fill="none" stroke="{gold}" stroke-width="1.3"/>
<text class="title" x="140" y="423" font-family="Noto Serif" font-size="{title_size}" font-weight="600" fill="{ink}" text-anchor="middle">{e(title)}</text>
<text class="label" x="140" y="447" font-family="Noto Sans" font-size="9" font-weight="600" letter-spacing="1.8" fill="{ink}" text-anchor="middle">{e(card['keywords'][0].upper())}</text>
</svg>'''


GUIDE = {
    "title": "A living guide to the Ominity Tarot",
    "edition": "Original Ominity plates and reflections, 2026",
    "introduction": "Tarot is a picture language for reflection. A card offers a perspective, not a fixed prediction. Let an image prompt a question, then trust your own context over any printed meaning.",
    "structure": {
        "major_arcana": "Twenty-two cards trace the Fool's journey through beginnings, choices, upheaval, renewal, and completion. A major card often invites attention to a wider life pattern.",
        "minor_arcana": "Fifty-six cards explore ordinary life in four suits. Each suit runs from Ace through Ten, then Page, Knight, Queen, and King.",
        "ranks": "Aces suggest seeds; Two through Ten develop a situation. Pages explore, Knights pursue, Queens tend and interpret, and Kings steward and decide. These court figures describe roles or approaches, not gender or a guaranteed person.",
    },
    "suits": {
        "Wands": {"element": "Fire", "domain": "creative energy, purpose, courage, and action"},
        "Cups": {"element": "Water", "domain": "feeling, intimacy, imagination, and care"},
        "Swords": {"element": "Air", "domain": "thought, language, conflict, and discernment"},
        "Pentacles": {"element": "Earth", "domain": "body, work, resources, and the material world"},
    },
    "reversals": "A reversed card can suggest a blocked, inward, delayed, or overextended version of its theme. It is not automatically bad news. Read the upright and reversed lines together, then ask which fits the actual situation.",
    "daily_reflection": "Take one breath, name the day or a specific question, and draw. Notice the image before reading its words. Keep one useful sentence and one small action; return later to see what changed.",
    "ethics": "The cards cannot establish facts about another person's mind, diagnose illness, or replace professional advice. Use them to clarify your own choices and conversations.",
    "influence": "Ominity nods to the expansive, art-forward spirit of the Starman Tarot by Davide De Angelis, and to traditional visual grammar familiar from Rider–Waite–Smith tarot. Every Ominity plate and reading is newly made; it does not reproduce the art or text of either deck.",
    "influence_sources": [
        {"title": "Starman Tarot — Lo Scarabeo", "url": "https://www.loscarabeo.com/en/products/starman-tarot"},
        {"title": "Starman Tarot Deck — Llewellyn", "url": "https://www.llewellyn.com/product.php?ean=9780738777795"},
    ],
    "art": "Original vector plates pair clean engraved lines with symbolic scenes and exact typography. The active Omarchy palette recolors the full deck without raster textures. The named archetypes and pips are traditional tarot vocabulary.",
}


def card_back_svg(palette: DeckPalette | None = None) -> str:
    """The hidden side of a card: an original compass/eye night plate."""
    palette = palette or DeckPalette()
    ink, gold, paper = palette.back_fill, palette.gold, palette.back_line
    rays = "".join(
        f'<path d="M140 146L140 158" transform="rotate({angle} 140 240)"/>'
        for angle in range(0, 360, 15)
    )
    corners = "".join(
        f'<path d="M{x} {y-7}L{x} {y+7}M{x-7} {y}L{x+7} {y}"/>'
        for x, y in ((43, 59), (237, 59), (43, 421), (237, 421))
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="280" height="480" viewBox="0 0 280 480" role="img" aria-labelledby="title description">
<title id="title">Ominity card back</title><desc id="description">A gold compass and watchful eye engraved on dark ink.</desc>
<rect width="280" height="480" fill="{ink}"/>
<rect x="8" y="8" width="264" height="464" rx="2" fill="none" stroke="{gold}" stroke-width="2"/>
<rect x="16" y="16" width="248" height="448" rx="1" fill="none" stroke="{paper}" stroke-width=".8" opacity=".75"/>
<rect x="25" y="25" width="230" height="430" fill="none" stroke="{gold}" stroke-width=".6" opacity=".55"/>
<g fill="none" stroke="{gold}" stroke-linejoin="round" stroke-linecap="round">
<path d="M140 47L150 72L140 97L130 72Z M140 383L150 408L140 433L130 408Z" stroke-width="1.4"/>
<path d="M140 63L140 84M140 396L140 417" stroke-width=".8"/>
<circle cx="140" cy="240" r="94" stroke-width=".9"/>
<circle cx="140" cy="240" r="82" stroke-width="1.8"/>
<circle cx="140" cy="240" r="69" stroke-width=".7" opacity=".65"/>
<path d="M140 154L152 224L222 240L152 256L140 326L128 256L58 240L128 224Z" stroke-width="1.4"/>
<path d="M140 176L149 229L204 240L149 251L140 304L131 251L76 240L131 229Z" stroke-width=".6"/>
<path d="M78 240Q140 178 202 240Q140 302 78 240Z" fill="{ink}" stroke-width="2"/>
<circle cx="140" cy="240" r="28" stroke="{paper}" stroke-width="1.1"/>
<circle cx="140" cy="240" r="14" stroke-width="1.8"/>
<circle cx="140" cy="240" r="5" fill="{gold}" stroke="none"/>
<path d="M140 113L145 126L140 139L135 126Z M140 341L145 354L140 367L135 354Z" stroke-width="1"/>
<path d="M42 119L55 119M225 119L238 119M42 361L55 361M225 361L238 361" stroke-width=".7"/>
<path d="M32 32L46 32M32 32L32 46M248 32L234 32M248 32L248 46M32 448L46 448M32 448L32 434M248 448L234 448M248 448L248 434" stroke-width="1.2"/>
</g>
<g fill="none" stroke="{paper}" stroke-width=".55" opacity=".67">{rays}</g>
<g fill="none" stroke="{gold}" stroke-width=".8" opacity=".8">{corners}</g>
</svg>'''


def main() -> None:
    cards = make_deck()
    CARD_DIR.mkdir(parents=True, exist_ok=True)
    DECK_DIR.mkdir(parents=True, exist_ok=True)
    (DECK_DIR / "deck.json").write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n")
    (DECK_DIR / "guide.json").write_text(json.dumps(GUIDE, ensure_ascii=False, indent=2) + "\n")
    for card in cards:
        (ROOT / card["art"]).write_text(card_svg(card) + "\n")
    (ROOT / "assets" / "card-back.svg").write_text(card_back_svg() + "\n")
    print(f"Generated {len(cards)} original cards, SVG plates, and card back")


if __name__ == "__main__":
    main()
