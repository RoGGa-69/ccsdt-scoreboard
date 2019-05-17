import csdc
import orm
import model
import yaml
import os
from morgues import download_morgues
import logging
import glob
import shlex
import subprocess

CONFIG_FILE = 'config.yml'
if not os.path.isfile(CONFIG_FILE):
    CONFIG_FILE = 'config_default.yml'

CONFIG = yaml.safe_load(open(CONFIG_FILE, encoding='utf8'))

logging_level = logging.NOTSET
if 'logging level' in CONFIG and hasattr(logging, CONFIG['logging level']):
    logging_level = getattr(logging, CONFIG['logging level'])

logging.basicConfig(level=logging.DEBUG)

orm.initialize(CONFIG['db uri'])
model.setup_database()
csdc.initialize_weeks()

GREP_COMMAND = ("grep -i -C4 --ignore-case '|.*cool[[:space:]]*play'")

for wk in csdc.weeks:
    download_morgues(wk, CONFIG['morgue dir'])
    morgueglob = os.path.join(CONFIG['morgue dir'],wk.number, "*.txt")
    cmdline = shlex.split(GREP_COMMAND)
    logging.debug("Executing subprocess: {}".format(cmdline + [morgueglob]))
    morgues = glob.glob(morgueglob)
    if len(morgues) == 0:
        continue
    coolplay = os.path.join(CONFIG['www dir'],"{}-plays.txt".format(wk.number))
    oldmask = os.umask(18)
    with open(coolplay, 'w') as f:
        p = subprocess.run(cmdline + morgues, encoding='utf-8', stdout=f,
        stderr=subprocess.DEVNULL)
    os.umask(oldmask)

