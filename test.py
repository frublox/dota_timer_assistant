__author__ = 'Dan'

import dota_timer as dt
from threading import Thread


def run():
    dt.hero_names = get_names()
    print str(dt.hero_names)

    dt.hero_ids = get_ids()
    print str(dt.hero_ids)

    dt.hero_info = read_info()
    timers()


def get_ids():
    ids = []

    for name in dt.hero_names:
        hero_id = str(dt.get_hero_id(name))
        assert hero_id != '-1'
        ids.append(hero_id)

    return ids


def get_names():
    names = dt.read_hero_names()

    assert len(names) == 5

    return names


def read_info():
    info = dt.read_hero_info(dt.cooldowns_file)

    assert info.get('1') is not None
    assert info.get('105') is not None

    return info


def timers():
    for i in range(5):
        t = Thread(target=dt.run_hero_timer, args=i)
        t.start()
        print "Started thread #{}".format(i + 1)