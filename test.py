__author__ = 'Dan'

import dota_timer as dt
from threading import Thread


def run():
    dt.HERO_DATA = dt.read_hero_data(dt.HERO_DATA_FILE)

    hero_names = ['sven', 'pudge', 'witch doctor', 'wr', 'pugna']

    dt.heroes = dt.get_heroes(hero_names, [dt.get_hero_id(name) for name in hero_names])

    for name in hero_names:
        dt.heroes[name]['cooldowns'] = [10]

    dt.HOTKEYS = dt.read_hotkeys(dt.HOTKEYS_FILE)
    dt.listen()


def cooldowns(name):
    cooldown_time = dt.get_cooldown_time(name)

    if dt.heroes[name]['has_scepter']:
        assert cooldown_time in dt.heroes[name]['scepter_cooldowns']
    else:
        assert cooldown_time in dt.heroes[name]['cooldowns']
