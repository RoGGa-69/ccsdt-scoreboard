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
    return '<span id="updated"><span class="label">Updates every 10 mins. Last Update: </span>{}</span></div>'.format(now)


def head(static, title):
    refresh = '<meta http-equiv="refresh" content="240">' if not static else ""
    return """<title>{0}</title>
    <?php $this->layout = 'ccsdt'; ?>
    {1}""".format(title, refresh)


version = '0.34'

def logoblock(subhead):
    sh = "<h2>{}</h2>".format(subhead) if subhead != None else ""
    return """<div id="title">
    <h2 id="sdc"><center>CCSDT#3 for DCSS v{}</center></h2>
    {}</div>""".format(version, sh)

def mainmenu():
    return ('<span class="menu">CCSDT for v0.34</a> : </span>' +
            '<span class="menu"><img src="/img/animated-arrow.gif" width="40" height="10"></span>' +
            '<span class="menu"><a href="index.html">Overview</a> - </span>' +
            '<span class="menu"><a href="rules.html">Details</a> - </span>' + 
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
    sp += '<div id="times"><span class="label">Week of: </span>'
    sp += wk.start.strftime(DATEFMT) + ' (ends at start of ' + wk.end.strftime(DATEFMT) + ' 00:00 UTC)</div>'
    sp += ('<div id="combo"><span class="label">Character: </span>' 
            + '{0} {1}</div>\n'.format(wk.species.name, wk.background.name))
    sp += ('<div id="bonus"><span class="label">Bonus 1: </span>'
            + wk.tier1.description + '<br/>\n'
            + '<span class="label">Bonus 2: </span>'
            + wk.tier2.description +'</div>\n')
    sp += ('<div id="gods"><span class="label">Gods: </span>')
    sp += ", ".join([ g.name for g in wk.gods])
    sp += '</div>'
    sp += '<br><pre>LEGEND<br>------<br>Green = Won<br>Red   = Died<br>Grey  = ongoing or did not finish<br>        before end of the week</right></pre>'
    sp += '<pre>SPECIAL NOTE<br>------------<br>None</pre>'

    return sp

def wkurl(wk):
    return '<a href="'+ wk.number + '.html">{}</a>'


def description(wk, url):
    s = ""

    if wk.start > datetime.datetime.now(datetime.timezone.utc):
        s += "Week {0}"
    else:
        s += "Week {0} &mdash; {1} ({2}{3})"

    if url and wk.start <= datetime.datetime.now(datetime.timezone.utc):
        s = wkurl(wk).format(s)

    return s.format(wk.number, wk.uniques, wk.species.short,
                wk.background.short)



def scoretable(wk, div):
    sp = ""
    sp += ("""<div class="card"><table><tr class="head">
    <th>Player</th>
    <th>Reach XL5</th>
    <th>Kill a Unique</th>
    <th>Worship a Valid God</th>
    <th>Reach XL10</th>
    <th>Branch Enter</th>
    <th>Branch End</th>
    <th>Champion a Valid God</th>
    <th><abbr title="Does not need to stay intact">Collect 1 Gem</abbr></th>
    <th>Collect 1 Rune</th>
    <th>Collect 2 Runes</th>
    <th>Collect 3 Runes</th>
    <th>Obtain Orb of Zot</th>
    <th>Win</th>
    <th>Bonus #1</th>
    <th>Bonus #2</th>
    <th>Week's Total (max=15)</th>
    </tr>""")

    with get_session() as s:
        for g in wk.sortedscorecard().with_session(s).all():
            if g.Game == None:
                sp += """<tr class="{}"><td class="name">{}</td>
                <td colspan="15"></td><td class="total">0</td></tr>""".format(
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
            sp += ( (('<td class="pt">{}</td>' * 15) 
                + '<td class="total">{}</td>').format(
                g.xl5,
                g.uniq,
                g.worship,
                g.xl10,
                g.brenter,
                g.brend,
                g.god,
                g.gem,
                g.rune,
                g.tworune,
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
        sp = '<pre>LEGEND<br>------<br>Green = Won<br>Red   = Died<br>White = ongoing or did not finish <br>        before the end of the week</right></pre>'
        sp += '<pre>SPECIAL NOTE<br>------------<br>None</pre>'
        sp += '<div class="card"><table>'
        sp += '<tr class="head"><th></th><th>Player</th>'
        sp += ''.join(['<th>' + description(wk, True) +'</th>' for wk in csdc.weeks
            ])
#       sp +='<th>Win &lt;40k Turns</th>'
        sp +='<th>15 Rune Win</th><th>Full Zig</th><th>Zot <= XL20</th>'
        sp +='<th>No Lair Win</th><th><abbr title="Get a rune without using potions or scrolls">Ascetic Rune</abbr></th>'
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
            for c in ("fifteenrune", "zig", "lowxlzot", "nolairwin", "asceticrune"):
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
_A floating eye, a glowing orange brain and 8 large abominations come into view.</pre>
<p>The Crawl Cosplay Sudden Death Tournament (CCSTD) is a competition 
that aims to fill a
Crawl niche not currently filled by the <a href="https://crawl.develz.org/tournament/0.34/" target="_blank">DCSS new version release tournament</a> 
and the other <a href="https://www.crawlcosplay.org" target="_blank">four Crawl Cosplay initiatives</a>.
The idea is for players to compete by trying to do as well as possible in a
game of Crawl with one attempt only; if you die, that week's challenge is over (thus
"sudden death".)* 
This competition is a lower time commitment event that aims to challenge players while
simultaneously encouraging unusual characters and play styles that you might not normally consider.</p>

<h2>Competition Format</h2>

<ul>
<li>Each challenge consists of playing a randomly chosen Crawl combo.</li>
<li>You get <em>one</em> attempt to play each combo.*</li>
<li>The goal is to advance as far as possible (and win!) in each game, scoring
points by reaching various in-game milestones.</li>
<li>Only games played and milestones scored between 00:00 UTC on the start and end dates count.</li>
<li>Details on rules and scoring are available on the 
<a href="rules.html">Details page</a>.</li>
</ul>

<p>* There is 1 caveat detailed on the <a href="rules.html">Details page</a> at item 4.</p>

<h2>Schedule</h2>

{}

{}

<h2>Credits</h2>

<p>Original CSDC rules and organization by <a href="http://crawl.akrasiac.org/scoring/players/walkerboh.html">WalkerBoh</a> and 
<a href="http://crawl.akrasiac.org/scoring/players/ebering.html">ebering</a>.<br>
Thank you to scrubbdaddy/scrubbuddy (CCSDT#1&3), grumposus (CCSDT#2) & agentchuck (CCSDT#3) for python assistance.</p>
<p>I am your host,</p>
<p>RoGGa ;-p</p>"""

    wklist = '<ul id="schedule">'
    for wk in csdc.weeks:
        wklist += '<li><span class="label">{}:</span> {} to {}'.format(description(wk,True),
                wk.start.strftime(DATEFMT),
                wk.end.strftime(DATEFMT))
    wklist += "</ul>"

    signup = ""
#    if datetime.datetime.now(datetime.timezone.utc) <= csdc.weeks[0].end:
    signup ="""
<h2>Sign Up</h2>

<p>In order to sign up, set the first line of your DCSS 0.34 RC file to</p>
<pre id="rc"># ccsdt</pre>
<p>on <a href="https://www.dungeoncrawlcentral.org/online_servers.html" target="_blank">any of the DCSS online servers</a> 
 at any point during tournament. Your name will appear in the standings once
you've done this correctly and started at least one 0.34 game (though it may take about 10-15 minutes before it does).</p>

<p>NOTE:<br>
Adding the above entry to your RC file adds your player name to the tournament's system, if you remove the entry later and start a run it will be still counted as part of the tournament.<br>
If you want to do practice runs play under Trunk or v0.33!</p>"""
#    else:
#        signup = "<h2>Sign Up</h2> <p>Sign ups are now closed.</p>"

    return page( static = True, title="Crawl Cosplay Sudden Death Tournament", content = pagestr.format(wklist,signup))

def rulespage():
    pagestr ="""
<h3>Rules</h3>
        <ol>
<li>Each weekly challenge consists of playing a randomly chosen 
Crawl Unqiue's starting combo (e.g. Snorg, a TrBe). 
The chosen combo for each week of the competition will streamed on 
Twitch.tv by RoGGa ( <a href="https://www.twitch.tv/rogga_likes_dcss" target="_blank">www.twitch.tv/rogga_likes_dcss</a> ) 30 minutes before 
the start of the new week. A spin-the-wheel format will be used to 
make the choices random.</li>
<li>Participants have one week to finish a game using that combo. 
Only milestones recorded during the week (from 00:00 UTC on the 
start date until 00:00 UTC on the end date) will count for scoring.</li>
<li>Your first DCSS v{} game started on an <a href="https://www.dungeoncrawlcentral.org/online_servers.html" target="_blank">DCSS Webtiles server</a>  
during the week will count for scoring. This is the only allowed attempt, subject to rule 4 below.
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
<li><b>CLARIFICATION</b>: If you worship another god before one of the 3 gods, you lose out on the 2 god points.</li>
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

<table class="info"><tr class="head"><th>15 Weekly Points (can be earned each
week)</th><th>Points</th></tr>
<tr><td class="name"> 1. Reach XL 5 ¹</td><td class="pt">1</td></tr>
<tr><td class="name"> 2. Kill a unique</td><td class="pt">1</td></tr>
<tr><td class="name"> 3. Worship one of three gods ¹</td><td class="pt">1</td></tr>
<tr><td class="name"> 4. Reach XL 10 ¹</td><td class="pt">1</td></tr>
<tr><td class="name"> 5. Enter a multi-level branch of the dungeon</td><td class="pt">1</td></tr>
<tr><td class="name"> 6. Reach the end of a multi-level branch (including D)</td><td class="pt">1</td></tr>
<tr><td class="name"> 7. Champion a listed god</td><td class="pt">1</td></tr>
<tr><td class="name"> 8. Collect 1 gem ² (does not need to stay intact) ¹</td><td class="pt">1</td></tr>
<tr><td class="name"> 9. Collect 1 rune</td><td class="pt">1</td></tr>
<tr><td class="name">10. Collect 2 runes ¹</td><td class="pt">1</td></tr>
<tr><td class="name">11. Collect 3 runes</td><td class="pt">1</td></tr>
<tr><td class="name">12. Collect the Orb of Zot</td><td class="pt">1</td></tr>
<tr><td class="name">13. Win</td><td class="pt">1</td></tr>
<tr><td class="name">14. Complete Bonus #1</td><td class="pt">1</td></tr>
<tr><td class="name">15. Complete Bonus #2</td><td class="pt">1</td></tr>
<tr class="head" id="onetime"><th>One-time points (earned once during the tournament)</th><th>Points</th></tr>
<!-- <tr><td class="name">Win a game in under 40,000 turns:</td><td class="pt">2</td></tr> -->
<tr><td class="name">1. Win a game with 15 runes</td><td class="pt">3</td></tr>
<tr><td class="name">2. Clear a Ziggurat</td><td class="pt">4</td></tr>
<tr><td class="name">3. Enter Zot at XL 20 or lower</td><td class="pt">5</td></tr>
<tr><td class="name">4. Win a game without entering lair</td><td class="pt">6</td></tr>
<tr><td class="name">5. Get a rune without using potions or scrolls (ascetic rune)</td><td class="pt">7</td></tr>
</table>
<p>¹ 5 new milestones were created for CCSDT#3 along with 
the removal of 1 one-time point: Win a game in under 40,000 turns</p>
<p>² add the following to your DCSS v0.34 RC file:</p>
<pre>always_show_gems = true
more_gem_info = true</pre>

<h2>Bonuses</h2>
<h3>Bonus 1 list</h3>
<ol>
   <li>Enter a rune branch with all base skills < 11.</li>
   <li>Enter Slime as your second multi-level branch (don't get banished).</li>
   <li>Enter the Temple in less than 4,000 turns.</li>
   <li>Reach the end of Lair at XL &leq; 12.</li>
   <li>Reach the end of Elf before entering a rune branch (excluding getting banished to the Abyss).</li>
   <li>Reach the end of the Depths before entering a rune branch (excluding getting banished to the Abyss).</li>
   <li>Collect a rune before entering Shoals, Snake, Spider, or Swamp.</li>
   <li>Collect a rune before entering Lair.</li>
   <li>Collect a rune before reaching XL17.</li>
   <li><b>NEW</b>: Enter Elf:3 in under 12,000 turns.</li>
   <li><b>NEW</b>: Reach the 10th floor of a Ziggurat.</li>
   <li><b>NEW</b>: Enter the bottom floor of the Orcish Mines before XL11.</li>
   <li><b>NEW</b>: Kill a unique in tree form (using lignification potion).</li>
   <li><b>NEW</b>: Pickup the gem in Crypt:3. (it doesn't need to stay intact)</li>
   <li>Collect two runes without dying twice (felids).</li>
</ol>

<h3>Bonus 2 list</h3>
<ol>
   <li>Collect the golden rune.</li>
   <li>Collect a rune with all base skills < 11.</li>
   <li><s>Get the slimy rune without entering any multi-level branch other than Lair, Slime, and Dungeon (don't get banished).</s><br>
       <b>REPLACED BY</b>: Pickup the rune in Slime:5.</li>
   <li>Collect a rune in less than 15,000 turns.</li>
   <li>Reach the end of the Vaults at XL &leq; 18.</li>
   <li>Kill or slimify Geryon before entering a rune branch (excluding the Abyss).</li>
   <li>Get a rune from Pan before entering any other rune branch (excluding the Abyss).</li>
   <li>Get a rune from Hell before entering any other rune branch (excluding the Abyss).</li>
   <li>Collect at least 5 runes before entering the Depths.</li>
   <li><b>NEW</b>: Collect at least 3 gems. (they don't need to stay intact)</li>
   <li><b>NEW</b>: Exit the Abyss in under 27,000 turns.</li>
   <li><b>NEW</b>: Reach the last level of the Depths without having entered the Lair.</li>
   <li><b>NEW</b>: Kill a non-random Pan Lord unique. (Cerebov, Mnoleg, Lom Lobon, or Gloorx Vloq).</li>
   <li><b>NEW</b>: Kill a Hell Lord unique. (Geryon does not count)</li>
   <li><b>NEW</b>: Pickup the gem in Slime:5. (it doesn't need to stay intact)</li>
   <li>Collect a rune without dying (felids).</li>
</ol>

"""
    return page(static=True, 
                subhead="<h2 style='color:rgb(69, 136, 5);'>" +
                        "Details for CCSDT#3</h2>", content = pagestr.format("0.34"))


def page(**kwargs):
    """static, title, subhead, content"""
    return """{}{}<div id="content">{}</div>
    <div id="bottomtext">{}""".format(
            head(kwargs["static"],kwargs.get("title",kwargs.get("subhead",""))),
            logoblock(kwargs.get("subhead","")),
            kwargs["content"],
            mainmenu() + kwargs.get("menu", wkmenu(None)) + (updated() if not kwargs["static"] else
                """</div>"""))
