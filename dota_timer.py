__author__ = 'Dan'

# INSTRUCTIONS

# After a hero uses their ult, press the number of the hero on the keyboard.
# Example: if Sven just used his ult and he's the first player on the enemy team, press 1

# If a hero levels up to 11 or 16, press the number of the hero and ALT.
# Example: if Sven just levelled up to 11, and he's the first player on the enemy team, press ALT+1

# If Roshan dies, press the 6 key.

# If a hero gets Aghanim's sceptre, press the number of the hero and SHIFT.
# Example: if Sven just got Aghanim's Scepter, and he's the first player on the enemy team, press SHIFT+1

import pythoncom
import pyHook
import sys
import time

from threading import Thread
from win32com import client

import json

import test

cooldowns_file = "cooldowns.json"

HOTKEYS = map(str, range(1, 6))  # keys '1' to '5'
SCEPTER_HOTKEYS = ['!', '@', '#', '$', '%']
ROSHAN_TIMER_HK = '6'

ALERT_MESSAGES = {
    'ROSHAN': {
        'MAYBE_ALIVE': 'Roshan might be alive.',
        'ALIVE': 'Roshan is alive!'
    },
    'HERO': "Hero number {}'s ultimate ability is ready!"
}

NO_ULT = -1
LEVEL_6 = 0
LEVEL_11 = 1
LEVEL_16 = 2

heroes = {}  # dictionary of enemy heroes in the game, addressed by hero name

threads = []


def increment_hero_state(name):
    if heroes[name]['state'] != LEVEL_16:
        heroes[name]['state'] += 1
        print "Incremented hero {}'s level.".format(name)


def get_cooldown_time(name):
    """
    Returns the appropriate ult cooldown based on the hero's level and if they have the Aghanim's Scepter.

    :param name: A hero's name
    :return: A cooldown time, in seconds
    """
    hero = heroes[name]

    if hero['has_scepter'] and hero.get('scepter_cooldowns') is not None:
        cooldowns = hero['scepter_cooldowns']
    else:
        cooldowns = hero['cooldowns']

    if len(cooldowns) == 1:
        return cooldowns[0]
    elif len(cooldowns) == 2:
        if hero['state'] == LEVEL_6:
            return cooldowns[0]
        else:
            return cooldowns[1]
    else:
        return cooldowns[hero['state']]


def get_all_hero_names(hero_info, hero_id):
    """
    Get all the names of a hero.

    :param hero_info: A dictionary of Dota heroes with their info
    :param hero_id: An id of a hero
    :return: A list of all the different names of a hero
    """
    print "try id: ", hero_id
    info = hero_info.get(str(hero_id))

    names = [
        info.get('name').lower(),
        info.get('localized_name').lower(),
        info.get('name_short').lower()
    ]

    if info.get('aliases') != '':
        for alias in info.get('aliases').split(';'):
            names.append(alias)

    return names


def get_hero_id(hero_info, name):
    """
    Looks through each hero's names and alt names to find the right id.

    :param hero_info: A dictionary of Dota heroes with their info
    :param name: A name of a hero. Can be an alias, short name or localised name
    :return: The id of the hero, or -1 if not found.
    """
    for hero_id in range(1, 106):
        if str(hero_id) not in hero_info:
            # print "Id {} not in hero_info. Moving on...".format(hero_id)
            continue

        info = hero_info.get(str(hero_id))

        names = [
            info.get('name').lower(),
            info.get('localized_name').lower(),
            info.get('name_short').lower()
        ]

        if info.get('aliases') != '':
            for alias in info.get('aliases').split(','):
                names.append(alias)

        # print "Names: ", names
        # print "searching for: ", name

        if name in names:
            # print 'Returning {}...'.format(hero_id)
            return str(hero_id)
        elif hero_id == 105:
            print "Could not find hero {}'s id! A name was probably entered wrong.".format(name)
            sys.exit(1)


def run_hero_timer(name):
    cooldown_time = get_cooldown_time(name)

    print "Starting ult timer for {}...\nCooldown time: {}".format(name, cooldown_time)

    time.sleep(cooldown_time)

    speaker = client.Dispatch("SAPI.SpVoice")
    speaker.Speak(ALERT_MESSAGES['HERO'].format(heroes[name]['index']))

    print "{}'s ult is ready!".format(name)


def run__roshan_timer():
    print "Starting Roshan timer..."
    time.sleep(60 * 8)  # roshan takes at least 8 minutes to respawn

    speaker = client.Dispatch("SAPI.SpVoice")
    speaker.Speak(ALERT_MESSAGES['ROSHAN']['MAYBE_ALIVE'])

    time.sleep(60 * 8)  # roshan is definitely alive after 11 minutes

    speaker.Speak(ALERT_MESSAGES['ROSHAN']['ALIVE'])

    print "Roshan is alive!"


def read_hero_info(filename):
    """
    Read hero cooldowns from the specified JSON file.

    :param filename: The JSON file with the hero cooldown information
    :return: A dictionary containing hero information
    """
    try:
        with open(filename) as f:
            return json.load(f)
    except IOError as e:
        print "Couldn't open the hero cooldowns file. Make sure it's called {} and in the same folder as the script."\
            .format(cooldowns_file)
        print str(e)
        print "Exiting..."
        sys.exit(1)
    except ValueError as e:
        print "Couldn't parse the hero cooldowns file. Make sure it's valid JSON."
        print str(e)
        print "Exiting..."
        sys.exit(1)


def read_hero_names():
    """
    Prompt input for the names of each hero on the enemy's team.
    :return: A list of the names of each enemy hero
    """
    names = []

    for i in range(5):
        name = raw_input("Enter name of enemy hero #{}: ".format(i + 1))
        names.append(name.strip())

    return names


def get_heroes(hero_info, hero_names):
    result = {}

    for i, name in enumerate(hero_names):
        hero_id = str(get_hero_id(hero_info, name))
        info = hero_info.get(hero_id)

        result[name] = {
            'index': i,
            'cooldowns': info.get('ultimate').get('cooldown'),
            'scepter_cooldowns': info.get('ultimate').get('scepter_cooldown'),
            'names': get_all_hero_names(hero_info, hero_id),
            'has_scepter': False,
            'state': NO_ULT
        }

    return result


def on_key_down(event):
    print 'Key: ', event.Key

    if event.Key == ROSHAN_TIMER_HK:
        thread = Thread(target=run__roshan_timer)
        threads.append(Thread)
        thread.start()
    elif event.Key in HOTKEYS:
        i = HOTKEYS.index(event.Key)

        name = ''

        for hero, info in heroes.iteritems():
            if info['index'] == int(i):
                name = hero

        print name

        if event.IsAlt():
            increment_hero_state(name)
        elif heroes[name]['state'] != NO_ULT:
            thread = Thread(target=run_hero_timer, args=name)
            threads.append(Thread)
            thread.start()
    elif event.Ascii in SCEPTER_HOTKEYS:
        i = SCEPTER_HOTKEYS.index(event.Key)

        name = ''

        for hero, info in heroes.iteritems():
            if info['index'] == int(i):
                name = hero

        print "{} now has Aghanim's scepter!".format(name)
        heroes[name]['has_scepter'] = True


def listen():
    hm = pyHook.HookManager()
    hm.KeyDown = on_key_down
    hm.HookKeyboard()
    pythoncom.PumpMessages()


def main():
    hero_info = read_hero_info(cooldowns_file)
    print 'Successfully read hero info from {}'.format(cooldowns_file)

    # hero_names = read_hero_names()

    hero_names = ['sven', 'br', 'dk', 'dirge', 'windrunner']

    global heroes
    heroes = get_heroes(hero_info, hero_names)

    listen()


if __name__ == '__main__':
    # test.run()
    main()
