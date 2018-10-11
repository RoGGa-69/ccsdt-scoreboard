import csdc
import orm
import model
import yaml
import os

CONFIG_FILE = 'config.yml'
if not os.path.isfile(CONFIG_FILE):
    CONFIG_FILE = 'config_default.yml'

CONFIG = yaml.safe_load(open(CONFIG_FILE, encoding='utf8'))

orm.initialize(CONFIG['db uri'])
model.setup_database()
print("!nick -rm csdc22")
with orm.get_session() as s:
    buf = "";
    for p in s.query(orm.CsdcContestant).all():
        if len(buf + " " + p.player.name) > 275:
            print("!nick csdc22 " + buf)
            buf = p.player.name
        else: 
            buf = buf + " " + p.player.name
    print("!nick csdc22 " + buf)
