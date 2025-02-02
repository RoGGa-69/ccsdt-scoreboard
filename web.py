import datetime
from orm import get_session, Account
from modelutils import morgue_url
from model import get_game
import csdc

TIMEFMT = "%H:%M %Z"
DATEFMT = "%Y-%m-%d"
DATETIMEFMT = DATEFMT + " " + TIMEFMT

def updated():
    now = datetime.datetime.now(datetime.timezone.utc).strftime(DATETIMEFMT)
    return '<span id="updated"><span class="label">Updates every 5 mins. Last Update: </span>{}</span></div>'.format(now)


def head(static, title):
    refresh = '<meta http-equiv="refresh" content="240">' if not static else ""
    return """<title>{0}</title>
    <?php $this->layout = 'ccsdt'; ?>
    {1}""".format(title, refresh)


version = '0.32'

def logoblock(subhead):
    sh = "<h2>{}</h2>".format(subhead) if subhead != None else ""
    return """<div id="title">
    <h2 id="sdc"><center>CCSDT for DCSS v{}</center></h2>
    {}</div>""".format(version, sh)


def mainmenu():
    return ('<span class="menu"><a href="../ccsdt.html">Overview</a> - </span>' +
        '<span class="menu"><a href="../about_ccsdt.html">Details</a> - </span>' + 
        '<span class="menu"><a href="standings.html">Standings</a></span>' +
        '<span class="menuspacer"></span>')

def serverflag(src):
    return ''.format(src)

def wkmenu(wk):
    sp = ""
    for w in csdc.weeks:
        menuitem = ""
        if ((wk is None or 
            w.number != wk.number)
            and w.start <= datetime.datetime.now(datetime.timezone.utc)):
            menuitem += wkurl(w)
        else:
            menuitem += '{}'
        sp += '<span class="menu">{} - </span>'.format(menuitem.format("Week " +
            w.number))
    return sp


def wkinfo(wk):
    sp = ""
    sp += '<div id="times"><span class="label">Week of '
    sp += wk.start.strftime(DATEFMT) + '</span></div>'
    sp += ('<div id="combo"><span class="label">Character: </span>' +
            '{0} {1}</div>\n'.format(wk.species.name, wk.background.name))
    sp += ('<div id="bonus"><span class="label">Bonus 1: </span>'
            + wk.tier1.description + '<br/>\n'
            + '<span class="label">Bonus 2: </span>'
            + wk.tier2.description +'</div>\n')
    sp += ('<div id="gods"><span class="label">Gods: </span>')
    sp += ", ".join([ g.name for g in wk.gods])
    sp += '</div>'

    return sp


def wkurl(wk):
    return '<a href="'+ wk.number + '.html">{}</a>'


def description(wk, url):
    s = ""

    if wk.start > datetime.datetime.now(datetime.timezone.utc):
        s += "Week {0}"
    else:
        s += "Week {0} &mdash; {1}{2}"

    if url and wk.start <= datetime.datetime.now(datetime.timezone.utc):
        s = wkurl(wk).format(s)

    return s.format(wk.number, wk.species.short,
                wk.background.short)



def scoretable(wk, div):
    sp = ""
    sp += ("""<div class="card"><table><tr class="head">
    <th>Player</th>
    <th>Unique Kill</th>
    <th>Branch Enter</th>
    <th>Branch End</th>
    <th>Champion God</th>
    <th>Collect a Rune</th>
    <th>Collect 3 Runes</th>
    <th>Obtain the Orb</th>
    <th>Win</th>
    <th>Bonus 1</th>
    <th>Bonus 2</th>
    <th>Total</th>
    </tr>""")

    with get_session() as s:
        for g in wk.sortedscorecard().with_session(s).all():
            if g.Game == None:
                sp += """<tr class="{}"><td class="name">{}</td>
                <td colspan="10"></td><td class="total">0</td></tr>""".format(
                        "none", g.Player.name)
                continue

            sp += ('<tr class="{}">'.format(
                "won" if g.Game.won and g.Game.end.replace(tzinfo=datetime.timezone.utc) <= wk.end else
                "alive" if g.Game.alive else
                "dead"))
            namestr = '<td class="name">{flag}<a href="{url}">{name}</a></td>' if not g.Game.alive else '<td class="name">{flag}{name}</td>'
            sp += (namestr.format(
                url = morgue_url(g.Game), name = g.Game.player.name,
                flag = serverflag(g.Game.account.server.name)))
            sp += ( (('<td class="pt">{}</td>' * 10) 
                + '<td class="total">{}</td>').format(
                g.uniq,
                g.brenter,
                g.brend,
                g.god,
                g.rune,
                g.threerune,
                g.orb,
                g.win,
                g.bonusone,
                g.bonustwo,
                g.total))
            sp += ('</tr>\n')

    sp += '</table></div>'

    return sp

def game_status(gid):
    with get_session() as s:
        game = get_game(s,gid=gid)
        if game == None:
            return "none"
        elif game.alive:
            return "alive"
        elif game.won:
            return "won"
        else:
            return "dead"

def _ifnone(x, d):
    """this should be a language builtin like it is in sql"""
    return x if x is not None else d


def standingstable():
    with get_session() as s:
        sp = '<div class="card"><table>'
        sp += '<tr class="head"><th></th><th>Player</th>'
        sp += ''.join(['<th>' + description(wk, True) +'</th>' for wk in csdc.weeks
            ])
        sp +='<th>15 Rune Win</th><th>Full Zig</th><th>Zot <= XL20</th>'
        sp +='<th>Win &lt;40k Turns</th><th>No Lair Win</th><th>Ascetic Rune</th>'
        sp += '<th>Total Score</th><th>Weekly Bonuses</th><th>Game High Score</th></tr>'
        place = 1
        for p in csdc.overview().with_session(s).all():
            acct = s.query(Account).filter_by(id = p.account_id).first();
            sp += '<tr>'
            sp += '<td class="total">{}.</td>'.format(place)
            place += 1
            sp += '<td class="name">{}{}</td>'.format(
            serverflag(acct.server.name) if acct else "", p.CsdcContestant.player.name)
            for wk in csdc.weeks:
                sp += '<td class="pt{}">{}</td>'.format(game_status(getattr(p,"wk" + wk.number + "gid")),
                                                        _ifnone(getattr(p, "wk" + wk.number), ""))
            for c in ("fifteenrune", "zig", "lowxlzot", "sub40k", "nolairwin", "asceticrune"):
                sp += ('<td class="pt">{}</td>').format(_ifnone(getattr(p, c), ""))
            sp += '<td class="total">{}</td>'.format(p.grandtotal)
            sp += '<td class="pt">{}</td><td class="hs">{}</td>'.format(p.tiebreak, _ifnone(p.hiscore, ""))
            sp += '</tr>'
        sp += '</table></div>'

        return sp


def scorepage(wk):
    return page( static=False, subhead = description(wk, False),
            content = wkinfo(wk) + 
            " ".join([ scoretable(wk, d) for d in csdc.divisions]),
            menu = wkmenu(wk))


def standingspage():
    return page( static=False,
            subhead = "Standings",
            content = standingstable())

def standingsplchold():
    return page( static=True,
            subhead = "Registrations are not yet being processed. Check back soon.",
            content = "" )

def overviewpage():
    pagestr = """
    <pre id="cover">
_You are suddenly pulled into a different region of the Abyss!
_A floating eye, a glowing orange brain, 4 small abominations and 8 large abominations come into view.</pre>
<p>The Crawl Cosplay Sudden Death Tournament (CCSTD) is a competition that aims to fill a
Crawl niche not currently filled by the version release tournament and the other 3 Crawl Cosplay initiatives.
The idea is for players to compete by trying to do as well as possible in a
game of Crawl with one attempt only; if you die, that week's challenge is over (thus
"sudden death". This competition is a lower time commitment event that aims to challenge players while
simultaneously encouraging unusual characters and play styles that you might not normally consider.</p>

<h2>Competition Format</h2>

<ul>
<li>Each challenge consists of playing a randomly chosen Crawl combo.</li>
<li>You get <em>one</em> attempt to play each combo.</li>
<li>The goal is to advance as far as possible (and win!) in each game, scoring
points by reaching various in-game milestones.</li>
<li>Only games played and milestones scored between 00:00 UTC on the start and end dates count.</li>
<li>Details on rules and scoring are available on the <a
href="rules.html">rules page</a>.</li>
</ul>

<h2>Schedule</h2>

{}

{}

<h2>Credits</h2>

<p>Original CSDC rules and organization by <a href="http://crawl.akrasiac.org/scoring/players/walkerboh.html">WalkerBoh</a> and 
<a href="http://crawl.akrasiac.org/scoring/players/ebering.html">ebering</a>.
Thank you to scrubbdaddy for python assistance. I am your host, RoGGa."""

    wklist = '<ul id="schedule">'
    for wk in csdc.weeks:
        wklist += '<li><span class="label">{}:</span> {} to {}'.format(description(wk,True),
                wk.start.strftime(DATEFMT),
                wk.end.strftime(DATEFMT))
    wklist += "</ul>"

    signup = ""
    if datetime.datetime.now(datetime.timezone.utc) <= csdc.weeks[0].end:
        signup ="""
<h2>Sign Up</h2>

<p>In order to sign up, set the first line of your 0.32 rcfile to</p> <pre
id="rc"># csdc</pre><p>on <a
href="https://crawl.develz.org/play.htm">any of the official online servers</a>
before the end of the first week. Your name will appear in the standings once
you've done this correctly and started at least one 0.32 game (though it may take about 20 minutes before it does).</p>"""
    else:
        signup = "<h2>Sign Up</h2> <p>Sign ups are now closed. See you in 0.33.</p>"

    return page( static = True, title="Crawl Cosplay Sudden Death Tournament", content = pagestr.format(wklist,signup))

def rulespage():
    pagestr ="""
    <ol>
<li>Each challenge consists of playing a randomly chosen Crawl race/class combo
(e.g. MiBe). The combo for each week of the competition will be announced at
00:00 UTC on the Friday starting that week. All players have one week to
finish a game using that combo. Only milestones recorded during the week (from
00:00 UTC on the start date until 00:00 UTC on the end date) will count for
scoring.</li>
<li>Your first {} game started on an official server during the week will count
for scoring. This is the only allowed attempt, subject to rule 3 below.</li>
<li>One redo per week is allowed if your first game ended in death with player
XL < 5 (i.e., no redo once you hit XL 5). The redo game must be started after
the end of the first game (no startscumming!).  The highest CSDC score of the
two games is counted towards your score.</li>
<li>Each challenge has 2 optional bonus challenges in addition to the
race/class combo.</li>
<li>Each challenge includes a list of gods. A point can be earned upon
reaching ****** piety (or on worship with Gozag or Xom) with one of the listed
gods. The point is lost if you ever abandon your god or are excommunicated. If
the combo for the week is a zealot background, god points are only for sticking
with the starting god. If the combo for the week is a demigod, the god point is automatically awarded.</li>
<li>The season consists of 5 challenges total (i.e., 5 different combos). Each
race and background will be selected at most once during the competition.</li>
<li>The final rankings will be tallied at the end of week 5 and represent the
final outcome. The player with the highest CSDC score is the champion.</li>
<li>Tiebreakers are (in order): number of weekly bonus points, highest in-game
score.</li>
<li>Don't play on more than one account. That misses the point.</li>
</ol>

<h2>Scoring</h2>

<p>Scoring is divided into two parts, weekly points assigned to each game
played, and one-time points awarded once per season regardless of how many
games achieve them.</p>

<table class="info"><tr class="head"><th>Weekly points (can be earned each
week)</th><th></th></tr>
<tr><td class="name">Kill a unique:</td><td class="pt">1</td></tr>
<tr><td class="name">Enter a multi-level branch of the dungeon:</td><td class="pt">1</td></tr>
<tr><td class="name">Reach the end of a multi-level branch (including D):</td><td class="pt">1</td></tr>
<tr><td class="name">Champion a listed god:</td><td class="pt">1</td></tr>
<tr><td class="name">Collect a rune:</td><td class="pt">1</td></tr>
<tr><td class="name">Collect 3 or more runes:</td><td class="pt">1</td></tr>
<tr><td class="name">Collect the Orb of Zot:</td><td class="pt">1</td></tr>
<tr><td class="name">Win:</td><td class="pt">1</td></tr>
<tr><td class="name">Complete Bonus 1:</td><td class="pt">1</td></tr>
<tr><td class="name">Complete Bonus 2:</td><td class="pt">1</td></tr>
<tr class="head" id="onetime"><th>One-time points (earned once during the tournament)</th><th></th></tr>
<tr><td class="name">Win a game with 15 runes:</td><td class="pt">3</td></tr>
<tr><td class="name">Clear a Ziggurat:</td><td class="pt">3</td></tr>
<tr><td class="name">Enter Zot at XL 20 or lower:</td><td class="pt">3</td></tr>
<tr><td class="name">Win a game in under 40,000 turns:</td><td class="pt">6</td></tr>
<tr><td class="name">Win a game without entering lair:</td><td class="pt">6</td></tr>
<tr><td class="name">Get a rune without using potions or scrolls:</td><td class="pt">6</td></tr>
</table>

<p class="notes"> Unless specified, a bonus or one time point does not
require you to win to earn the point.</p>

"""
    return page(static=True, subhead="Rules", content = pagestr.format("0.32"))


def page(**kwargs):
    """static, title, subhead, content"""
    return """{}{}<div id="content">{}</div>
    <div id="bottomtext">{}""".format(
            head(kwargs["static"],kwargs.get("title",kwargs.get("subhead",""))),
            logoblock(kwargs.get("subhead","")),
            kwargs["content"],
            mainmenu() + kwargs.get("menu", wkmenu(None)) + (updated() if not kwargs["static"] else
                ""))
