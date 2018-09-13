import os
import sources
import logging
import yaml
import subprocess
import orm
import model
import time

SOURCES_DIR = './sources'
CONFIG_FILE = 'config.yml'
if not os.path.isfile(CONFIG_FILE):
    CONFIG_FILE = 'config_default.yml'

CONFIG = yaml.safe_load(open(CONFIG_FILE, encoding='utf8'))

logging_level = logging.NOTSET
if 'logging level' in CONFIG and hasattr(logging, CONFIG['logging level']):
    logging_level = getattr(logging, CONFIG['logging level'])

logging.basicConfig(level=logging_level)

orm.initialize(CONFIG['db uri'])
model.setup_database()

t_i = time.time()
#sources.download_rcfiles(CONFIG['sources file'], SOURCES_DIR)
logging.info("Fetched rcfiles in {} seconds.".format(time.time() - t_i))

with orm.get_session() as s:
	for p in sources.contestant_list(CONFIG['sources file'], SOURCES_DIR):
		#try:
			model.add_contestant(s, p)
		#except BaseException as e:
		#    logging.warning("Bad player {}. Exception: {}.".format(p, repr(e)))
