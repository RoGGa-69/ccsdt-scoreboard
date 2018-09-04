"""Defines useful constants."""

import re
from collections import namedtuple

Species = namedtuple("Species", ["short", "full"])
Background = namedtuple("Background", ["short", "full"])
God = namedtuple("God", ["name"])

SPECIES = {
    Species("Ba", "Barachian"),
    Species("Ce", "Centaur"),
    Species("DD", "Deep Dwarf"),
    Species("DE", "Deep Elf"),
    Species("Dg", "Demigod"),
    Species("Dr", "Draconian"),
    Species("Ds", "Demonspawn"),
    Species("Fe", "Felid"),
    Species("Fo", "Formicid"),
    Species("Gh", "Ghoul"),
    Species("Gn", "Gnoll"),
    Species("Gr", "Gargoyle"),
    Species("HO", "Hill Orc"),
    Species("Ha", "Halfling"),
    Species("Hu", "Human"),
    Species("Ko", "Kobold"),
    Species("Mf", "Merfolk"),
    Species("Mi", "Minotaur"),
    Species("Mu", "Mummy"),
    Species("Na", "Naga"),
    Species("Op", "Octopode"),
    Species("Og", "Ogre"),
    Species("Sp", "Spriggan"),
    Species("Te", "Tengu"),
    Species("Tr", "Troll"),
    Species("VS", "Vine Stalker"),
    Species("Vp", "Vampire"),
}

BACKGROUNDS = {
    Background("AE", "Air Elementalist"),
    Background("AK", "Abyssal Knight"),
    Background("AM", "Arcane Marksman"),
    Background("Ar", "Artificer"),
    Background("As", "Assassin"),
    Background("Be", "Berserker"),
    Background("CK", "Chaos Knight"),
    Background("Cj", "Conjurer"),
    Background("EE", "Earth Elementalist"),
    Background("En", "Enchanter"),
    Background("FE", "Fire Elementalist"),
    Background("Fi", "Fighter"),
    Background("Gl", "Gladiator"),
    Background("Hu", "Hunter"),
    Background("IE", "Ice Elementalist"),
    Background("Mo", "Monk"),
    Background("Ne", "Necromancer"),
    Background("Sk", "Skald"),
    Background("Su", "Summoner"),
    Background("Tm", "Transmuter"),
    Background("VM", "Venom Mage"),
    Background("Wn", "Wanderer"),
    Background("Wr", "Warper"),
    Background("Wz", "Wizard"),
}

GODS = {
    God("Ashenzari"),
    God("Atheist"),
    God("Beogh"),
    God("Cheibriados"),
    God("Dithmenos"),
    God("Elyvilon"),
    God("Fedhas"),
    God("Gozag"),
    God("Hepliaklqana"),
    God("Jiyva"),
    God("Kikubaaqudgha"),
    God("Lugonu"),
    God("Makhleb"),
    God("Nemelex Xobeh"),
    God("Okawaru"),
    God("Qazlal"),
    God("Ru"),
    God("Sif Muna"),
    God("The Shining One"),
    God("Trog"),
    God("Uskayaw"),
    God("Vehumet"),
    God("Xom"),
    God("Yredelemnul"),
    God("Zin"),
    God("Wu Jian"),
}

NONPLAYABLE_COMBOS = [
    "FeGl",
    "FeAs",
    "FeHu",
    "FeAM",
    "DgBe",
    "DgCK",
    "DgAK",
    "GhTm",
    "MuTm",
]
PLAYABLE_COMBOS = (
    "%s%s" % (rc.short, bg.short)
    for rc in SPECIES
    for bg in BACKGROUNDS
    if "%s%s" % (rc, bg) not in NONPLAYABLE_COMBOS
)
GOD_NAME_FIXUPS = {
    # Actually, the ingame name is 'the Shining One', but that looks
    # ugly since the capitalisation is wrong.
    "the Shining One": "The Shining One",
}
SPECIES_NAME_FIXUPS = {
    "Yellow Draconian": "Draconian",
    "Grey Draconian": "Draconian",
    "White Draconian": "Draconian",
    "Green Draconian": "Draconian",
    "Purple Draconian": "Draconian",
    "Mottled Draconian": "Draconian",
    "Black Draconian": "Draconian",
    "Red Draconian": "Draconian",
    "Pale Draconian": "Draconian",
}

Branch = namedtuple("Branch", ["short", "full", "multilevel"])
BRANCHES = {
    Branch("D", "Dungeon", True),
    Branch("Lair", "Lair of the Beasts", True),
    Branch("Temple", "Ecumenical Temple", False),
    Branch("Orc", "Orcish Mines", True),
    Branch("Vaults", "Vaults", True),
    Branch("Snake", "Snake Pit", True),
    Branch("Swamp", "Swamp", True),
    Branch("Shoals", "Shoals", True),
    Branch("Spider", "Spider Nest", True),
    Branch("Elf", "Elven Halls", True),
    Branch("Zig", "Ziggurat", True),
    Branch("Depths", "Depths", True),
    Branch("Abyss", "Abyss", True),
    Branch("Sewer", "Sewer", False),
    Branch("Pan", "Pandemonium", False),
    Branch("Crypt", "Crypt", True),
    Branch("Slime", "Slime Pits", True),
    Branch("Zot", "Realm of Zot", True),
    Branch("Ossuary", "Ossuary", False),
    Branch("IceCv", "Ice Cave", False),
    Branch("Hell", "Vestibule of Hell", False),
    Branch("Lab", "Labyrinth", False),
    Branch("Bailey", "Bailey", False),
    Branch("Volcano", "Volcano", False),
    Branch("Tomb", "Tomb of the Ancients", True),
    Branch("Dis", "Iron City of Dis", True),
    Branch("Tar", "Tartarus", True),
    Branch("Geh", "Gehenna", True),
    Branch("Coc", "Cocytus", True),
    Branch("Bazaar", "Bazaar", False),
    Branch("WizLab", "Wizard's Laboratory", False),
    Branch("Trove", "Treasure Trove", False),
    Branch("Desolation", "Desolation of Salt", False),
}

BLACKLISTS = {
    "griefers": {},
    "bots": {
        "autorobin",
        "xw",
        "auto7hm",
        "rw",
        "qw",
        "ow",
        "qwrobin",
        "gw",
        "notqw",
        "jw",
        "parabodrick",
        "hyperqwbe",
        "cashybrid",
        "tstbtto",
        "parabolic",
        "oppbolic",
        "ew",
        "rushxxi",
        "gaubot",
        "cojitobot",
        "paulcdejean",
        "otabotab",
        "nakatomy",
        "testingqw",
        "beemell",
        "beem",
        "drasked",
        "phybot",
        "khrogbot",
        "jwbot",
        "autocrawlbot",
        "swippen",
        "cotteux",
    },
}

LOGFILE_REGEX = re.compile("(logfile|allgames)")
MILESTONE_REGEX = re.compile("milestone")
KTYPS = (
    "mon",
    "beam",
    "quitting",
    "leaving",
    "pois",
    "winning",
    "acid",
    "cloud",
    "disintegration",
    "wild_magic",
    "starvation",
    "trap",
    "spore",
    "burning",
    "targeting",
    "draining",
    "water",
    "rotting",
    "something",
    "curare",
    "stupidity",
    "bounce",
    "targetting",
    "self_aimed",
    "spines",
    "rolling",
    "lava",
    "barbs",
    "falling_down_stairs",
    "divine_wrath",
    "xom",
    "weakness",
    "clumsiness",
    "being_thrown",
    "wizmode",
    "beogh_smiting",
    "headbutt",
    "mirror_damage",
    "freezing",
    "reflect",
    "collision",
    "petrification",
    "tso_smiting",
    "falling_through_gate",
)
KTYP_FIXUPS = {
    # Renames
    "divine wrath": "divine_wrath",
    "wild magic": "wild_magic",
    "self aimed": "self_aimed",
    "falling down stairs": "falling_down_stairs",
}

VERBS = (
    "begin",
    "br.enter",
    "br.end",
    "br.exit",
    "abyss.enter",
    "abyss.exit",
    "zig",
    "zig.enter",
    "zig.exit",
    "shaft",
    "rune",
    "orb",
    "uniq",
    "uniq.ban",
    "uniq.ens",
    "uniq.pac",
    "uniq.slime",
    "ghost",
    "ghost.ban",
    "god.worship",
    "god.maxpiety",
    "god.ecumenical",
    "god.renounce",
    "sacrifice",
    "ancestor.class",
    "death", #felids
    "death.final", #all others
    "monstrous",
)

