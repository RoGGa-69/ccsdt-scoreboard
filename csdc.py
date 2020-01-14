import datetime
import constants
from collections import namedtuple
from model import (
    latestmilestones,
    get_species,
    get_background,
    get_place,
    get_branch,
    get_place_from_string,
    get_god,
    get_ktyp,
    get_verb
)
from modelutils import morgue_url
from orm import (
    Logfile,
    Server,
    Player,
    Species,
    Background,
    God,
    Version,
    Branch,
    Place,
    Game,
    Milestone,
    Account,
    Ktyp,
    Verb,
    Skill,
    CsdcContestant,
    get_session,
)

from sqlalchemy import asc, desc, func, type_coerce, Integer, literal, case
from sqlalchemy.sql import and_, or_
from sqlalchemy.orm.query import (
    aliased,
    Query
)

CsdcBonus = namedtuple("CsdcBonus", ["name", "description", "query", "pts"])
# The query here must be a scalar query, see no bonus for the example.

NoBonus = CsdcBonus("NoBonus","No bonus",[literal(False)], "0")

def _champion_god(milestones, god):
    """Query if the supplied god get championed in the provided milestone set"""
    with get_session() as s:
        worship_id = get_verb(s, "god.worship").id
        champ_id = get_verb(s, "god.maxpiety").id
    maxpiety = milestones.filter(
                Milestone.god_id == god.id,
                Milestone.verb_id == champ_id
            ).exists()
    worship = milestones.filter(
                Milestone.god_id == god.id,
                Milestone.verb_id == worship_id
            ).exists()
    neverworship = ~milestones.filter(
                Milestone.verb_id == worship_id
            ).exists()

    champion_conditions = {
        "GOD_NO_GOD" : neverworship,
        "Xom" : worship,
        "Gozag" : worship
    }

    return champion_conditions.get(god.name, maxpiety)


class CsdcWeek:
    """A csdc week

    This object generates the queries needed to score a csdc week"""

    def _valid_games(self, alias):
        """Query the gids in an alias for the Games table for the valid ones

        There are a lot of games but not that many in a given time window,
        there is a good index for this filter, so even if it is implied one
        should endavour to use it.
 
        add_columns can specify further columns, but as-is this is hit by a
        covering index"""
        return Query(alias.gid).join(Account,
            alias.account_id == Account.id).filter(
                ~Account.blacklisted,
                alias.species_id == self.species.id,
                alias.background_id == self.background.id,
                alias.start >= self.start,
                alias.start < self.end
            )


    def __init__(self, **kwargs):
        with get_session() as s:
            self.number = kwargs["number"]
            self.species = get_species(s, kwargs["species"])
            self.background = get_background(s, kwargs["background"])
            self.char = self.species.short + self.background.short
            self.gods = [ get_god(s, g) for g in kwargs["gods"] ]
            self.start = kwargs["start"]
            self.end = kwargs["end"]
            self.tier1 = kwargs.get("bonus1", NoBonus)
            self.tier2 = kwargs.get("bonus2", NoBonus)

        g1 = aliased(Game)
        g2 = aliased(Game)
        possiblegames = self._valid_games(g1).add_columns(
                g1.player_id,
                g1.start,
                g1.end
            ).filter(g1.gid.in_(
                self._valid_games(g2).filter(
                    g2.player_id == g1.player_id
                ).order_by(g2.start).limit(2))
            ).join(latestmilestones, g1.gid == latestmilestones.c.gid
            ).add_column(latestmilestones.c.xl).cte()
        pg2 = possiblegames.alias()
        self.gids = Query(possiblegames.c.gid.label("gid")).outerjoin(pg2,
                and_(pg2.c.player_id == possiblegames.c.player_id,
                    possiblegames.c.start > pg2.c.start)
                ).filter(or_(pg2.c.gid == None,
                    and_(pg2.c.end != None, pg2.c.xl < 5, 
                    possiblegames.c.start > pg2.c.end)))


    def _valid_milestone(self):
        return Query(Milestone).filter(Milestone.gid == Game.gid,
                Milestone.time <= self.end);

    def _uniq(self):
        with get_session() as s:
            verb_ids = [ get_verb(s, u).id for u in ["uniq", "uniq.ban",
            "uniq.pac", "uniq.slime"]]

        return self._valid_milestone().filter(Milestone.verb_id.in_(verb_ids)).exists()

    def _brenter(self):
        with get_session() as s:
            verb_id = get_verb(s, "br.enter").id
            d_id = get_branch(s, "D").id
            multilevel_places = Query(Place.id).join(Branch).filter(
                    Branch.id != d_id, Branch.multilevel)

        return self._valid_milestone().filter(
            Milestone.place_id.in_(multilevel_places),
            Milestone.verb_id == verb_id
        ).exists()

    def _brend(self):
        with get_session() as s:
            verb_id = get_verb(s, "br.end").id
            multilevel_places = Query(Place.id).join(Branch).filter(Branch.multilevel)

        return self._valid_milestone().filter(
            Milestone.place_id.in_(multilevel_places),
            Milestone.verb_id == verb_id
        ).exists()

    def _god(self):
        with get_session() as s:
            worship_id = get_verb(s, "god.worship").id
            champ_id = get_verb(s, "god.maxpiety").id
            abandon_id = get_verb(s, "god.renounce").id
        god_ids = [g.id for g in self.gods]
        return and_(
            or_(*[_champion_god(self._valid_milestone(), g) for g in
                self.gods]),
            ~self._valid_milestone().filter(
                Milestone.verb_id == abandon_id
            ).exists())

    def _rune(self, n):
        return self._valid_milestone().filter(
            Milestone.runes >= n
        ).exists()

    def _orb(self, n):
        with get_session() as s:
            verb_id = get_verb(s, "orb").id

        return self._valid_milestone().filter(
            Milestone.verb_id == verb_id
        ).exists()

    def _win(self):
        with get_session() as s:
            ktyp_id = get_ktyp(s, "winning").id

        return type_coerce(and_(Game.ktyp_id != None, 
            Game.ktyp_id == ktyp_id,
            Game.end <= self.end), Integer)

    def _fifteenrune(self):
        with get_session() as s:
            ktyp_id = get_ktyp(s, "winning").id

        return type_coerce(and_(
            Game.ktyp_id != None,
            Game.ktyp_id == ktyp_id,
            Game.end <= self.end,
            self._rune(15)), Integer)

    def _sub40k(self):
        with get_session() as s:
            ktyp_id = get_ktyp(s, "winning").id

        return type_coerce(func.ifnull(and_(
            Game.ktyp_id == ktyp_id,
            Game.end <= self.end,
            ~self._valid_milestone().filter(
                Milestone.turn >= 40000).exists()
        ), 0), Integer)
     
    def _zig(self):
        with get_session() as s: 
            zexit = get_verb(s, "zig.exit").id
            zplace = get_place_from_string(s, "Zig:27").id

        return self._valid_milestone().filter(
                Milestone.verb_id == zexit,
                Milestone.oplace_id == zplace).exists()

    def _lowxlzot(self):
        with get_session() as s:
            verb_id = get_verb(s, "br.enter").id
            place = get_place_from_string(s, "Zot:1").id

        return self._valid_milestone().filter(
            Milestone.xl <= 20,
            Milestone.verb_id == verb_id,
            Milestone.place_id == place).exists()
    
    def _nolairwin(self):
        with get_session() as s:
            ktyp_id = get_ktyp(s, "winning").id
            brenter = get_verb(s, "br.enter").id
            lair = get_place_from_string(s, "Lair:1").id

        return type_coerce(and_(Game.ktyp_id != None, 
            Game.ktyp_id == ktyp_id,
            Game.end <= self.end,
            ~self._valid_milestone().filter(
                Milestone.verb_id == brenter,
                Milestone.place_id == lair).exists()), Integer)

    def _asceticrune(self):
        with get_session() as s:
            verb_id = get_verb(s, "rune").id

        return self._valid_milestone().filter(
            Milestone.verb_id == verb_id,
            Milestone.potionsused == 0,
            Milestone.scrollsused == 0).exists()

    def _bonus(self, bonus):
        """in principle we support more than two bonuses"""
        return type_coerce(self._valid_milestone().filter(
                *bonus.query
            ).exists(), Integer).__mul__(bonus.pts)

    def scorecard(self):
        sc = Query([Game.gid,
            Game.player_id,
            type_coerce(self._uniq(), Integer).label("uniq"),
            type_coerce(self._brenter(), Integer).label("brenter"),
            type_coerce(self._brend(), Integer).label("brend"),
            type_coerce(self._god(), Integer).label("god"),
            type_coerce(self._rune(1), Integer).label("rune"),
            type_coerce(self._rune(3), Integer).label("threerune"),
            type_coerce(self._orb(), Integer).).label("orb"),
            self._win().label("win"),
            self._bonus(self.tier1).label("bonusone"),
            self._bonus(self.tier2).label("bonustwo"),
        ]).filter(Game.gid.in_(self.gids)).subquery()

        return Query( [Player, Game]).select_from(CsdcContestant).join(Player
                ).outerjoin(sc, CsdcContestant.player_id ==
                        sc.c.player_id).outerjoin(Game,
                Game.gid == sc.c.gid).add_columns(
                    sc.c.player_id.label("player_id"),
                    sc.c.uniq,
                    sc.c.brenter,
                    sc.c.brend,
                    sc.c.god,
                    sc.c.rune,
                    sc.c.threerune,
                    sc.c.orb,
                    sc.c.win,
                    sc.c.bonusone.label("bonusone"),
                    sc.c.bonustwo.label("bonustwo"),
                    (sc.c.bonusone + sc.c.bonustwo).label("bonus"),
                    func.max(
                        sc.c.uniq
                        + sc.c.brenter
                        + sc.c.brend
                        + sc.c.god
                        + sc.c.rune
                        + sc.c.threerune
                        + sc.c.win
                        + sc.c.orb
                        + sc.c.bonusone
                        + sc.c.bonustwo
                    ).label("total")
            )

    def onetimes(self):
        return Query([Game.gid,
            Game.account_id.label("account_id"), 
            Game.player_id.label("player_id"),
            Game.score.label("score"),
            type_coerce(self._fifteenrune(), Integer).label("fifteenrune"),
            type_coerce(self._sub40k(), Integer).label("sub40k"),
            type_coerce(self._zig(), Integer).label("zig"),
            type_coerce(self._lowxlzot(), Integer).label("lowxlzot"),
            type_coerce(self._nolairwin(), Integer).label("nolairwin"),
            type_coerce(self._asceticrune(), Integer).label("asceticrune"),
        ]).filter(Game.gid.in_(self.gids))


    def sortedscorecard(self):
        return self.scorecard().group_by(CsdcContestant.player_id).order_by(desc("total"), desc("bonus"),
        desc(Game.score), Game.start)

weeks = []

def initialize_weeks():
    with get_session() as s:
        m2 = aliased(Milestone)
        runebranchlowskill = CsdcBonus("RuneBranchLowSkill",
            "Enter a rune branch with all base skills < 11.",
            [ or_(
                and_(Milestone.sklev < 11,
                    Milestone.id.in_(Query(m2.id).filter(
                        Milestone.gid == m2.gid,
                        m2.verb_id == get_verb(s, "br.enter").id,
                        m2.place_id.in_([ get_place(s, get_branch(s, b), 1).id for b in constants.RUNE_BRANCHES]))
                    )),
                and_(Milestone.sklev < 11,
                    Milestone.id.in_(Query(m2.id).filter(
                        Milestone.gid == m2.gid,
                        m2.verb_id == get_verb(s, "abyss.enter").id)))) ],
            1)
        runelowskill = CsdcBonus("RuneLowSkill",
            "Collect a rune with all base skills < 11.",
            [ Milestone.sklev < 11,
                Milestone.id.in_(Query(m2.id).filter(
                    Milestone.gid == m2.gid,
                    m2.verb_id == get_verb(s, "rune").id
                ))],
            "1")

        slimefirst = CsdcBonus("EnterSlime2nd",
            "Enter Slime as your second multi-level branch (don't get banished).",
            [ Milestone.verb_id == get_verb(s, "br.enter").id,
              Milestone.place_id == get_place_from_string(s, "Slime:1").id,
              Query(func.count(m2.id)).filter(
                  Milestone.gid == m2.gid,
                  m2.turn < Milestone.turn, 
                  m2.verb_id == get_verb(s, "br.enter").id,
                  m2.place_id.in_([ get_place(s, get_branch(s, b), 1).id for b in constants.MULTI_LEVEL_BRANCHES])
              ).as_scalar() < 2],
            "1")

        slimerunefirst = CsdcBonus("GetTheSlimyRuneFirst",
            "Get the slimy rune without entering any multi-level branch other than Lair, Slime, and D (don't get banished).",
            [ Milestone.verb_id == get_verb(s, "rune").id,
              Milestone.place_id  == get_place_from_string(s, "Slime:5").id,
              Query(func.count(m2.id)).filter(
                  Milestone.gid == m2.gid,
                  m2.turn < Milestone.turn,
                  m2.verb_id == get_verb(s, "br.enter").id,
                  m2.place_id.in_([ get_place(s, get_branch(s, b), 1).id for b in constants.MULTI_LEVEL_BRANCHES])
              ).as_scalar() <= 2],
            "1")

        temple4k = CsdcBonus("TempleIn4kTurn",
            "Enter the Temple in less than 4,000 turns.",
            [ Milestone.verb_id == get_verb(s, "br.enter").id,
              Milestone.place_id == get_place_from_string(s, "Temple").id,
              Milestone.turn < 4000 ],
            "1")

        rune15k = CsdcBonus("RuneIn15kTurn",
            "Collect a rune in less than 15,000 turns.",
            [ Milestone.verb_id == get_verb(s, "rune").id,
              Milestone.turn < 15000 ],
            "1")

        lairendxl12 = CsdcBonus("LairEndXL12",
            "Reach the end of Lair at XL &leq; 12.",
            [ Milestone.verb_id == get_verb(s, "br.end").id,
              Milestone.place_id == get_place_from_string(s, "Lair:6").id,
              Milestone.xl <= 12 ],
            "1")

        vaultendxl18 = CsdcBonus("VaultEndXL18",
            "Reach the end of the Vaults at XL &leq; 18.",
            [ Milestone.verb_id == get_verb(s, "br.end").id,
              Milestone.place_id == get_place_from_string(s, "Vaults:5").id,
              Milestone.xl <= 18 ],
            "1")

        elfbeforerune = CsdcBonus("Elf3BeforeRunes",
            "Reach the end of Elf before entering a rune branch.",
            [ Milestone.verb_id == get_verb(s, "br.end").id,
              Milestone.place_id == get_place_from_string(s, "Elf:3").id,
              ~Query(m2).filter( 
                  m2.gid == Milestone.gid,
                  m2.turn < Milestone.turn,
                  m2.verb_id == get_verb(s, "br.enter").id,
			      m2.place_id.in_([ get_place(s, get_branch(s, b), 1).id for b in constants.RUNE_BRANCHES ]),
			  ).exists() ],
			"1")

        depthsbeforerune = CsdcBonus("Depths5BeforeRunes",
            "Reach the end of the Depths before entering a rune branch.",
            [ Milestone.verb_id == get_verb(s, "br.end").id,
              Milestone.place_id == get_place_from_string(s, "Depths:5").id,
              ~Query(m2).filter( 
                  m2.gid == Milestone.gid,
                  m2.turn < Milestone.turn,
                  m2.verb_id == get_verb(s, "br.enter").id,
			      m2.place_id.in_([ get_place(s, get_branch(s, b), 1).id for b in constants.RUNE_BRANCHES ]),
			  ).exists() ],
			"1")

        geryonbeforerune = CsdcBonus("GeryonBeforeRune",
            "Kill or slimify Geryon before entering a rune branch (excluding the Abyss).",
            [ or_( Milestone.verb_id == get_verb(s, "uniq").id,
                   Milestone.verb_id == get_verb(s, "uniq.slime").id),
              Milestone.msg.like("%Geryon%"),
              ~Query(m2).filter( 
                  m2.gid == Milestone.gid,
                  m2.turn < Milestone.turn,
                  m2.verb_id == get_verb(s, "br.enter").id,
                  m2.place_id.in_([ get_place(s, get_branch(s, b), 1).id for b in set(constants.RUNE_BRANCHES) - set(("Abyss",))]),
              ).exists() ],
            "1")

        hellpanrunefirst = CsdcBonus("HellPanRuneFirst",
            "Get a rune from Hell or Pan before entering any other rune branch (excluding the Abyss).",
            [ Milestone.verb_id == get_verb(s, "rune").id,
              ~Milestone.msg.like("%byssal%"),
              ~Query(m2).filter( 
                  m2.gid == Milestone.gid,
                  m2.turn < Milestone.turn,
                  m2.verb_id == get_verb(s, "br.enter").id,
                  m2.place_id.in_([ get_place(s, get_branch(s, b), 1).id 
                      for b in set(constants.RUNE_BRANCHES) - set(("Abyss", "Coc", "Geh", "Dis", "Tar", "Pan"))]),
              ).exists() ],
            "1")

        goldenrune = CsdcBonus("GoldenRune",
            "Collect the golden rune.",
            [ Milestone.verb_id == get_verb(s, "rune").id,
              Milestone.place_id == get_place_from_string(s, "Tomb:3").id ],
            "1")

        vowofcourage = CsdcBonus("VowOfCourage",
            "Collect at least 5 runes before entering the Depths.",
            [ Milestone.verb_id == get_verb(s, "rune").id,
              Milestone.runes >= 5,
              ~Query(m2).filter(
                  m2.gid == Milestone.gid,
                  m2.turn < Milestone.turn,
                  m2.verb_id == get_verb(s, "br.enter").id,
                  m2.place_id == get_place_from_string(s, "Depths:1").id).exists() ],
            "1")

        runenosbranch = CsdcBonus("RuneNoSBranch",
            "Collect a rune before entering Shoals, Snake, Spider, or Swamp.",
            [Milestone.verb_id == get_verb(s, "rune").id,
             ~Query(m2).filter(
             m2.gid == Milestone.gid,
             m2.turn < Milestone.turn,
             m2.verb_id == get_verb(
             s, "br.enter").id,
             m2.place_id.in_([ get_place(s, get_branch(s, b), 1).id for b in ("Shoals", "Snake", "Spider", "Swamp")] )
             ).exists() ],
            "1")

        runenolair = CsdcBonus("RuneNoLair",
            "Collect a rune before entering Lair.",
            [Milestone.verb_id == get_verb(s, "rune").id,
             ~Query(m2).filter(
             m2.gid == Milestone.gid,
             m2.turn < Milestone.turn,
             m2.verb_id == get_verb(
                 s, "br.enter").id,
             m2.place_id == get_place_from_string(
                 s, "Lair:1").id,
             ).exists() ],
            "1")

        runedontdie = CsdcBonus("RuneDontDie",
            "Collect a rune without dying.",
            [Milestone.verb_id == get_verb(s, "rune").id,
             ~Query(m2).filter(
             m2.gid == Milestone.gid,
             m2.turn < Milestone.turn,
             m2.verb_id == get_verb(s, "death").id).exists()],
            "1")

        tworunedontdie = CsdcBonus("2RuneDont2Die",
            "Collect two runes without dying twice.",
            [Milestone.verb_id == get_verb(s, "rune").id,
             Query(func.count(m2.id)).filter(
             m2.gid == Milestone.gid,
             m2.turn < Milestone.turn,
             m2.verb_id == get_verb(s, "death").id).as_scalar() < 2],
            "1")

        weeks.append(CsdcWeek(
                number = "1",
                species = "DD",
                background = "Fi",
                gods = ("Makhleb", "Trog", "Okawaru"),
                start = datetime.datetime(2018,10,4, tzinfo=datetime.timezone.utc),
                end = datetime.datetime(2018,10,11, tzinfo=datetime.timezone.utc)))
        weeks.append(CsdcWeek(
                number = "2",
                species = "DD",
                background = "Fi",
                gods = ("Makhleb", "Trog", "Okawaru"),
                start = datetime.datetime(2018,10,11, tzinfo=datetime.timezone.utc),
                end = datetime.datetime(2018,10,18, tzinfo=datetime.timezone.utc)))
        weeks.append(CsdcWeek(
                number = "3",
                species = "DD",
                background = "Fi",
                gods = ("Makhleb", "Trog", "Okawaru"),
                start = datetime.datetime(2018,10,18, tzinfo=datetime.timezone.utc),
                end = datetime.datetime(2018,10,25, tzinfo=datetime.timezone.utc)))
        weeks.append(CsdcWeek(
                number = "4",
                species = "DD",
                background = "Fi",
                gods = ("Makhleb", "Trog", "Okawaru"),
                start = datetime.datetime(2018,10,25, tzinfo=datetime.timezone.utc),
                end = datetime.datetime(2018,11,1, tzinfo=datetime.timezone.utc)))
        weeks.append(CsdcWeek(
                number = "5",
                species = "DD",
                background = "Fi",
                gods = ("Makhleb", "Trog", "Okawaru"),
                start = datetime.datetime(2018,11,8, tzinfo=datetime.timezone.utc),
                end = datetime.datetime(2018,11,15, tzinfo=datetime.timezone.utc)))
        weeks.append(CsdcWeek(
                number = "6",
                species = "DD",
                background = "Fi",
                gods = ("Makhleb", "Trog", "Okawaru"),
                start = datetime.datetime(2018,11,15, tzinfo=datetime.timezone.utc),
                end = datetime.datetime(2018,11,22, tzinfo=datetime.timezone.utc)))
        weeks.append(CsdcWeek(
                number = "7",
                species = "DD",
                background = "Fi",
                gods = ("Makhleb", "Trog", "Okawaru"),
                start = datetime.datetime(2018,11,22, tzinfo=datetime.timezone.utc),
                end = datetime.datetime(2018,11,29, tzinfo=datetime.timezone.utc)))

def all_games():
    allgids = weeks[0].gids.union_all(*[ wk.gids for wk in weeks[1:]]).subquery()
    return Query(Game).filter(Game.gid.in_(allgids))

def onetimescorecard():
    sc = weeks[0].onetimes().union_all(*[wk.onetimes() for wk in weeks[1:]]).subquery()

    return Query([sc.c.player_id.label("player_id"),
        func.min(sc.c.account_id).label("account_id"),
        type_coerce((func.sum(sc.c.fifteenrune) > 0) * 3, Integer).label("fifteenrune"),
        type_coerce((func.sum(sc.c.lowxlzot) > 0) * 3, Integer).label("lowxlzot"),
        type_coerce((func.sum(sc.c.zig) > 0) * 3, Integer).label("zig"),
        type_coerce((func.sum(sc.c.sub40k) > 0) * 6, Integer).label("sub40k"),
        type_coerce((func.sum(sc.c.nolairwin) > 0) * 6, Integer).label("nolairwin"),
        type_coerce((func.sum(sc.c.asceticrune) > 0) * 6, Integer).label("asceticrune"),
        func.max(sc.c.score).label("hiscore")]).group_by(sc.c.player_id)

def overview():
    q = Query(CsdcContestant)
    sc = onetimescorecard().subquery()
    q = q.outerjoin(sc, CsdcContestant.player_id == sc.c.player_id)
    totalcols = []
    wktotal = []
    wkbonuses = []
    for col in ("fifteenrune", "sub40k", "zig", "lowxlzot", "nolairwin", "asceticrune"):
        totalcols.append(func.ifnull(getattr(sc.c, col), 0))
        q = q.add_column(getattr(sc.c, col).label(col))
    for wk in weeks:
        a = wk.sortedscorecard().subquery()
        totalcols.append(func.ifnull(a.c.total, 0))
        wktotal.append(a.c.total)
        wkbonuses.append(func.ifnull(a.c.bonusone, 0) + func.ifnull(a.c.bonustwo, 0))
        q = q.outerjoin(a, CsdcContestant.player_id == a.c.player_id
                ).add_column( a.c.total.label("wk" + wk.number))

    return q.add_columns(
            sc.c.account_id.label("account_id"),
            sum(totalcols).label("grandtotal"),
            sum(wkbonuses).label("tiebreak"),
            sc.c.hiscore.label("hiscore"),
            (func.coalesce(*wktotal) != None).label("played")
        ).order_by(desc("grandtotal"),desc("tiebreak"),desc("hiscore"),desc("played"))

def current_week():
    now = datetime.datetime.now(datetime.timezone.utc)
    for wk in weeks:
        if wk.start <= now and now < wk.end:
            return wk
    return None

divisions = [1]
