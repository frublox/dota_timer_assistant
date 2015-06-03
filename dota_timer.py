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

from threading import Thread, current_thread
from win32com import client

import json

import test

from Queue import Queue

speaker = client.Dispatch("SAPI.SpVoice")

HOTKEYS = map(str, range(1, 6))  # keys '1' to '5'
SCEPTER_HOTKEYS = ['!', '@', '#', '$', '%']
ROSHAN_TIMER_HK = '6'

ALERT_MESSAGES = {
    'ROSHAN': {
        'MAYBE_ALIVE': 'Roshan might be alive.',
        'ALIVE': 'Roshan is alive!'
    },
    'HERO': "Hero number {} ultimate ability is ready!"
}

LEVEL_6 = 0
LEVEL_11 = 1
LEVEL_16 = 2

HERO_DATA_FILE = "cooldowns.json"
HERO_DATA = {}  # dictionary of Dota hero data, read in from HERO_DATA_FILE

heroes = {}  # dictionary of enemy heroes in the game, addressed by hero name

threads = []

message_queue = Queue()


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

    if hero['has_scepter'] and hero['scepter_cooldowns'] is not None:
        cooldowns = hero['scepter_cooldowns']
    else:
        cooldowns = hero['cooldowns']

    try:
        cooldown_time = cooldowns[hero['state']]
    except IndexError:
        cooldown_time = cooldowns[0]

    return cooldown_time


def get_all_hero_names(hero_id):
    """
    Get all the different names of a hero, including aliases.

    :param hero_id: An id of a hero
    :return: A list of names
    """
    info = HERO_DATA.get(str(hero_id))

    names = [
        info.get('name').lower(),
        info.get('localized_name').lower(),
        info.get('name_short').lower()
    ]

    if info.get('aliases') != '':
        for alias in info.get('aliases').split(';'):
            names.append(alias)

    return names


def get_hero_id(name):
    """
    Looks through each hero's names and alt names to find the right id.

    :param name: A name of a hero. Can be an alias, short name or localised name
    :return: The id of the hero, or None if not found.
    """
    for hero_id in range(1, 106):
        if str(hero_id) not in HERO_DATA:
            # print "Id {} not in HERO_DATA. Moving on...".format(hero_id)
            continue

        info = HERO_DATA.get(str(hero_id))

        names = [
            info.get('name').lower(),
            info.get('localized_name').lower(),
            info.get('name_short').lower()
        ]

        if info.get('aliases') != '':
            for alias in info.get('aliases').split(','):
                names.append(alias)

        if name in names:
            return str(hero_id)
        elif hero_id == 105:
            return None


def run_hero_timer(name):
    cooldown_time = get_cooldown_time(name)

    print "Starting {}'s (#{}) ult timer for {} seconds"\
        .format(heroes[name]['localized_name'], heroes[name]['index'] + 1,  cooldown_time)

    time.sleep(cooldown_time)

    message_queue.put(ALERT_MESSAGES['HERO'].format(heroes[name]['index'] + 1))

    print "{}'s ult is ready!".format(heroes[name]['localized_name'])


def run_roshan_timer():
    print "Starting Roshan timer..."

    time.sleep(60 * 8)  # roshan takes at least 8 minutes to respawn

    message_queue.put(ALERT_MESSAGES['ROSHAN']['MAYBE_ALIVE'])
    print "Roshan might be alive..."

    time.sleep(60 * 3)  # roshan is definitely alive after 11 minutes

    message_queue.put(ALERT_MESSAGES['ROSHAN']['ALIVE'])
    message_queue.task_done()

    print "Roshan is alive!"


def read_hero_data(filename):
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
            .format(HERO_DATA_FILE)
        print str(e)
        print "Exiting..."
        sys.exit(1)
    except ValueError as e:
        print "Couldn't parse the hero cooldowns file. Make sure it's valid JSON."
        print str(e)
        print "Exiting..."
        sys.exit(1)


def read_hero_names_and_ids():
    """
    Prompt input for the names of each hero on the enemy's team.
    After each name is read, it's id is retrieved and validated.
    If the id wasn't found, the user is reprompted until it is found.

    :return: A tuple containing lists of the names and ids of each enemy hero
    """
    names = []
    ids = []

    for i in range(5):
        while True:
            name = raw_input("Enter name of enemy hero #{}: ".format(i + 1))
            name = name.strip()

            hero_id = get_hero_id(name)

            if hero_id is None:
                print "Invalid hero name. Please try again."
            elif hero_id in ids:
                print "Hero was already entered. Please try again."
            else:
                names.append(name)
                ids.append(hero_id)
                break

    return names, ids


def get_heroes(hero_names, hero_ids):
    result = {}

    for i, name in enumerate(hero_names):
        hero_id = hero_ids[i]
        info = HERO_DATA.get(hero_id)
        localized_name = info.get('localized_name')

        result[name] = {
            'index': i,
            'cooldowns': info.get('ultimate').get('cooldown'),
            'scepter_cooldowns': info.get('ultimate').get('scepter_cooldown'),
            'names': get_all_hero_names(hero_id),
            'has_scepter': False,
            'state': LEVEL_6,
            'localized_name': localized_name
        }

    return result


def get_hero_name_by_index(i):
    for hero in heroes:
        if heroes[hero]['index'] == i:
            return hero


def on_key_down(event):
    if event.Key == ROSHAN_TIMER_HK:
        thread = Thread(target=run_roshan_timer)
        threads.append(Thread)
        thread.start()
    elif event.Key in HOTKEYS:
        i = HOTKEYS.index(event.Key)

        name = get_hero_name_by_index(i)

        if event.IsAlt():
            increment_hero_state(name)
        else:
            thread = Thread(target=run_hero_timer, kwargs={'name': name})
            threads.append(thread)
            thread.start()
    elif event.Key in SCEPTER_HOTKEYS:
        i = SCEPTER_HOTKEYS.index(event.Key)

        name = get_hero_name_by_index(i)

        print "{} now has Aghanim's scepter!".format(name)
        heroes[name]['has_scepter'] = True

    return True


def listen_for_keys():
    hm = pyHook.HookManager()
    hm.KeyDown = on_key_down
    hm.HookKeyboard()
    pythoncom.PumpMessages()


def listen_for_messages():
    while True:
        if not message_queue.empty():
            message = message_queue.get()
            speaker.Speak(message)
            message_queue.task_done()


def listen():
    thread = Thread(target=listen_for_keys)
    thread.start()
    listen_for_messages()


def main():
    global HERO_DATA
    HERO_DATA = read_hero_data(HERO_DATA_FILE)

    names_and_ids = read_hero_names_and_ids()

    global heroes
    heroes = get_heroes(names_and_ids[0], names_and_ids[1])

    listen()


if __name__ == '__main__':
    test.run()
    # main()
