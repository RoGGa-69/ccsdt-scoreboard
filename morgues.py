import multiprocessing
import os
import sys
import subprocess
import logging
import shlex

import csdc
import orm
from modelutils import morgue_url

SIMULTANEOUS_DOWNLOADS = 10
WGET_NAME = 'wget'
WGET_MORGUE_CMDLINE = ("%s --no-verbose --timestamping -P '{prefix}' '{url}'" % WGET_NAME)

def download_morgue_file(url: str, dest: str) -> None:
   logging.debug("Downloading morgues")
   cmdline = shlex.split(WGET_MORGUE_CMDLINE.format(prefix=dest, url=url))
   logging.debug("Executing subprocess: {}".format(cmdline))
   p = subprocess.run(cmdline,
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE)
   if p.returncode:
       logging.warning("Couldon't download {}. Error: {}".format(url, p.stderr))

def download_morgues(week, morguedir) -> None:
    dest = os.path.join(morguedir, week.number)

    if not os.path.exists(dest):
        os.mkdir(dest)

    urls = []
    with orm.get_session() as s:
        for g in week.sortedscorecard().with_session(s).all():
            if g.Game is not None and g.Game.ktyp is not None:
                urls.append(morgue_url(g.Game))
	
    p = multiprocessing.Pool(SIMULTANEOUS_DOWNLOADS)
    jobs = []
    for url in urls:
        jobs.append(p.apply_async(download_morgue_file, (url, dest)))
    for job in jobs:
        job.get()
    p.close()
    p.join()
