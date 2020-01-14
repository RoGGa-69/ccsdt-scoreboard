from calendar import timegm

import characteristic

import sqlalchemy
from sqlalchemy import (
    Table,
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import enum
import json

Base = declarative_base()

@characteristic.with_repr(["name"])  # pylint: disable=too-few-public-methods
class Server(Base):
    """A DCSS server -- a source of logfiles/milestones.

    Columns:
        name: Server's short name (eg CAO, CPO).
    """

    __tablename__ = "servers"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(4), nullable=False, index=True, unique=True)  # type: str

@characteristic.with_repr(["name", "server"])  # pylint: disable=too-few-public-methods
class Account(Base):
    """An account -- a single username on a single server.

    Columns:
        name: name of the account on the server
        blacklisted: if the account has been blacklisted. Accounts started as
            streak griefers/etc are blacklisted.
    """

    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), nullable=False, index=True)  # type: str
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)  # type: int
    server = relationship("Server")
    blacklisted = Column(Boolean, nullable=False, default=False)  # type: bool
    player_id = Column(
        Integer, ForeignKey("players.id"), nullable=False, index=True
    )  # type: int
    player = relationship("Player", back_populates="accounts")

    @property
    def canonical_name(self) -> str:
        """Canonical name.

        Crawl names are case-insensitive, we preserve the account's
        preferred capitalisation, but store them uniquely using the canonical
        name.
        """
        return self.name.lower()

    __table_args__ = (UniqueConstraint("name", "server_id", name="name-server_id"),)

@characteristic.with_repr(["name"])  # pylint: disable=too-few-public-methods
class Player(Base):
    """A player -- a collection of accounts with shared metadata.

    Columns:
        name: Player's name. For now, this is the same as the accounts that
            make up the player. In future, it could be changed so that
            differently-named accounts can make up a single player (eg
            Sequell nick mapping).
    """

    __tablename__ = "players"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), unique=True, nullable=False)  # type: str
    accounts = relationship("Account", back_populates="player")  # type: list

    @property
    def url_name(self):
        return self.name.lower()

@characteristic.with_repr(["short"])  # pylint: disable=too-few-public-methods
class Species(Base):
    """A DCSS player species.

    Columns:
        short: short species name, eg 'HO', 'Mi'.
        name: long species name, eg 'Hill Orc', 'Minotaur'.
        playable: if the species is playable in the current version.
            Not quite sure what to do in the case of a mismatch between stable
            and trunk...
    """

    __tablename__ = "species"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    short = Column(String(2), nullable=False, index=True, unique=True)  # type: str
    name = Column(String(15), nullable=False, unique=True)  # type: str


@characteristic.with_repr(["short"])  # pylint: disable=too-few-public-methods
class Background(Base):
    """A DCSS player background.

    Columns:
        short: short background name, eg 'En', 'Be'.
        name: long background name, eg 'Enchanter', 'Berserker'.
        playable: if the background is playable in the current version.
            Not quite sure what to do in the case of a mismatch between stable
            and trunk...
    """

    __tablename__ = "backgrounds"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    short = Column(String(2), nullable=False, index=True, unique=True)  # type: str
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str


@characteristic.with_repr(["name"])  # pylint: disable=too-few-public-methods
class God(Base):
    """A DCSS god.

    Columns:
        name: full god name, eg 'Nemelex Xobeh', 'Trog'.
        playable: if the god is playable in the current version.
            Not quite sure what to do in the case of a mismatch between stable
            and trunk...
    """

    __tablename__ = "gods"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str


@characteristic.with_repr(["v"])  # pylint: disable=too-few-public-methods
class Version(Base):
    """A DCSS version.

    Columns:
        v: version string, eg '0.17', '0.18'.
    """

    __tablename__ = "versions"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    v = Column(String(10), nullable=False, index=True, unique=True)  # type: str


@characteristic.with_repr(["short"])  # pylint: disable=too-few-public-methods
class Branch(Base):
    """A DCSS Branch (Dungeon, Lair, etc).

    Columns:
        short: short code, eg 'D', 'Wizlab'.
        name: full name, eg 'Dungeon', 'Wizard\'s Laboratory'.
        multilevel: Is the branch multi-level? Note: Pandemonium is not
            considered multilevel, since its levels are not numbered ingame.
        playable: Is it playable in the current version?
            Not quite sure what to do in the case of a mismatch between stable
            and trunk...
    """

    __tablename__ = "branches"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    short = Column(String(10), nullable=False, index=True, unique=True)  # type: str
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str
    multilevel = Column(Boolean, nullable=False)  # type: bool


@characteristic.with_repr(["branch", "level"])  # pylint: disable=too-few-public-methods
class Place(Base):
    """A DCSS Place (D:8, Pan:1, etc).

    Note that single-level branches have a single place with level=1 (eg
        Temple:1, Pan:1).
    """

    __tablename__ = "places"
    id = Column("id", Integer, primary_key=True, nullable=False)  # type: int
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)  # type: int
    branch = relationship("Branch")
    level = Column(Integer, nullable=False, index=True)  # type: int

    @property
    def as_string(self) -> str:
        """Return the Place with a pretty name, like D:15 or Temple."""
        # TODO: should specify name in 'normal' form eg 'Gehenna' etc
        if self.branch.multilevel:
            return "%s:%s" % (self.branch.short, self.level)
        else:
            return "%s" % self.branch.short

    __table_args__ = (UniqueConstraint("branch_id", "level", name="branch_id-level"),)


@characteristic.with_repr(["name"])  # pylint: disable=too-few-public-methods
class Ktyp(Base):
    """A DCSS ktyp (mon, beam, etc)."""

    __tablename__ = "ktyps"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str


@characteristic.with_repr(["name"])  # pylint: disable=too-few-public-methods
class Verb(Base):
    """A DCSS milestone verb (rune, orb, etc)."""

    __tablename__ = "verbs"
    id = Column(Integer, primary_key=True, nullable=False)  # type: int
    name = Column(String(20), nullable=False, index=True, unique=True)  # type: str


@characteristic.with_repr(["name"])
class Skill(Base):
    """A DCSS Skill."""

    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, nullable=False) #type: int
    name = Column(String(20), nullable=False, index=True, unique=True)


@characteristic.with_repr(["gid"])  # pylint: disable=too-few-public-methods
class Game(Base):
    """A single DCSS game.

    Columns (most are self-explanatory):
        gid: unique id for the game, comprised of "name:server:start". For
            compatibility with sequell.
        account_id
        account
        player_id: denormalised and set on game creation
        version_id
        version
        species_id
        species
        background_id
        background
        milestones: list of Milestone objects for the game's milestones in
            reverse chronological order, so that milestones[0] is the latest.

        start: start time for the game (in UTC)
        end: end time for the game (in UTC). Null for an ongoing game. The
            following fields are also null for ongoing games

        ktyp: dcss Ktype.
        dam
        sdam
        tdam
        score
    """

    __tablename__ = "games"
    gid = Column(String(50), primary_key=True, nullable=False)  # type: str

    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)  # type: int
    account = relationship("Account")

    # Denormalised data. Set on game record insertion
    player_id = Column(Integer, nullable=False, index=True)  # type: int

    version_id = Column(Integer, ForeignKey("versions.id"), nullable=False)  # type: int
    version = relationship("Version")

    species_id = Column(Integer, ForeignKey("species.id"), nullable=False)  # type: int
    species = relationship("Species")

    background_id = Column(
        Integer, ForeignKey("backgrounds.id"), nullable=False
    )  # type: int
    background = relationship("Background")

    start = Column(DateTime, nullable=False, index=True)  # type: DateTime
    end = Column(DateTime, nullable=True, index=True)  # type: DateTime

    dam = Column(Integer, nullable=True)  # type: int
    sdam = Column(Integer, nullable=True)  # type: int
    tdam = Column(Integer, nullable=True)  # type: int
    score = Column(Integer, nullable=True)  # type: int

    ktyp_id = Column(Integer, ForeignKey("ktyps.id"), nullable=True)  # type: int
    ktyp = relationship("Ktyp")

    milestones = relationship("Milestone", back_populates="game",
            uselist=True, order_by="desc(Milestone.time)")

    __table_args__ = (
            Index("ix_games_player_start", player_id, start),
        )

    @property
    def player(self) -> Player:
        """Convenience shortcut."""
        return self.account.player

    @property
    def alive(self) -> bool:
        """Is this game still ongoing?"""
        return self.end == None

    @property
    def latestmilestone(self):
        """shortcut"""
        return self.milestones[0]

    @property
    def won(self) -> bool:
        """Was this game won."""
        return self.ktyp != None and self.ktyp.name == "winning"

    @property
    def quit(self) -> bool:
        """Was this game quit."""
        return self.ktyp != None and self.ktyp.name == "quitting"

    @property
    def boring(self) -> bool:
        """Was this game was quit, left, or wizmoded."""
        return self.ktyp != None and self.ktyp.name in ("quitting", "leaving", "wizmode")

    @property
    def char(self) -> str:
        """Character code eg 'MiFi'."""
        return "{}{}".format(self.species.short, self.background.short)

    def as_dict(self) -> dict:
        """Convert to a dict, for public consumption."""
        return {
            "gid": self.gid,
            "account_name": self.account.name,
            "player_name": self.player.name,
            "server_name": self.account.server.name,
            "version": self.version.v,
            "species": self.species.name,
            "background": self.background.name,
            "char": self.char,
            "tmsg": self.tmsg,
            "score": self.score,
            "start": self.start.timestamp(),
            "end": self.end.timestamp(),
        }

@characteristic.with_repr(["gid"])  # pylint: disable=too-few-public-methods
class Milestone(Base):
    """A single DCSS game.

    Columns (most are self-explanatory):
        gid: unique id for the game, comprised of "name:server:start". For
            compatibility with sequell.
        xl
        place_id where the player is now
        oplace_id where the player was when this was triggered
        god_id
        turn
        time
        dur
        runes
        potionsused
        scrollsused
        skill_id
        sklev
        verb_id
    """

    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True, nullable=False)
    gid = Column(String(50), ForeignKey("games.gid"), nullable=False) # type: str
    game = relationship(Game, back_populates="milestones", lazy=False)

    place_id = Column(Integer, ForeignKey("places.id"), nullable=True)  # type: int
    place = relationship("Place", foreign_keys=place_id)
    oplace_id = Column(Integer, ForeignKey("places.id"), nullable=True)  # type: int
    oplace = relationship("Place", foreign_keys=oplace_id)

    god_id = Column(Integer, ForeignKey("gods.id"), nullable=True)  # type: int
    god = relationship("God")

    xl = Column(Integer, nullable=True)  # type: int
    turn = Column(Integer, nullable=True)  # type: int
    dur = Column(Integer, nullable=True)  # type: int
    runes = Column(Integer, nullable=True)  # type: int
    time = Column(DateTime, nullable=False, index=True)  # type: DateTime
    potionsused = Column(Integer, nullable=True)  # type: int
    scrollsused = Column(Integer, nullable=True)  # type: int
    status = Column(String(1000), nullable=True) # type: str

    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)
    skill = relationship("Skill")
    sklev = Column(Integer, nullable=True)

    verb_id = Column(Integer, ForeignKey("verbs.id"), nullable=True)  # type: int
    verb = relationship("Verb")

    msg = Column(String(1000), nullable=True) # type:str

    __table_args__ = (
            # Used to get milestones in order (and find the latest ones)
            Index("ix_milestones_gid_time", gid, time),
        )

    def as_dict(self) -> dict:
        """Convert to a dict, for public consumption."""
        return {
            "gid": self.gid,
            "account_name": self.game.account.name,
            "player_name": self.game.player.name,
            "server_name": self.game.account.server.name,
            "place": self.place.as_string,
            "god": self.god.name,
            "xl": self.xl,
            "turn": self.turn,
            "dur": self.dur,
            "runes": self.runes,
            "verb" : self.verb.name,
            "noun" : self.noun,
            "time" : self.time.timestamp(),
            "potionsused" : self.potionsused,
            "scrollsused" : self.scrollsused
        }

class Logfile(Base):
    """Logfile import progress.

    Columns:
        source_url: logfile source url
        current_key: the key of the next logfile event to import.
    """
    __tablename__ = 'logfile'
    source_url = Column(String(1000), primary_key=True)
    current_key = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return "<Logfile(source_url={logfile.source_url}, offset={logfile.current_key})>".format(logfile=self)


class CsdcContestant(Base):
    """CSDC Contestant"""

    __tablename__ = 'contestants'
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False,
            unique=True, primary_key=True)
    player = relationship("Player")
    division = Column(Integer, nullable=False)

# End Object defs

session_factory = None

def initialize(uri):
    engine = create_engine(uri)
    global session_factory 
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, autocommit=False)
    Base.metadata.create_all(engine)

@contextmanager
def get_session():
    global session_factory
    Session = scoped_session(session_factory)
    yield Session()
    Session.remove()
