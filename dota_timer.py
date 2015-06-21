import pythoncom
import pyHook
import sys
import time
import json
from threading import Thread, current_thread
from win32com import client
from Queue import Queue
import ConfigParser
import logging
import curses
import Tkinter as Tk

import test
import gui

logging.basicConfig(filename='log.log', level=logging.DEBUG)

speaker = client.Dispatch("SAPI.SpVoice")

HOTKEYS_FILE = 'hotkeys.ini'
HOTKEYS = {}

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

timer_running = map(lambda i: False, range(6))
timer_time_left = map(lambda i: 0, range(6))

accept_hotkeys = True

voice_msg_queue = Queue()
timer_info_queue = Queue()
notification_queue = Queue()

last_key_pressed = ''


def increment_hero_state(name):
    if heroes[name]['state'] != LEVEL_16:
        heroes[name]['state'] += 1
        notification_queue.put(
            "Hero #{} ({}): Incremented level".format(heroes[name]['index'] + 1, heroes[name]['localized_name']))


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
    for hero_id in map(str, range(1, 106)):
        if hero_id not in HERO_DATA:
            continue

        info = HERO_DATA.get(hero_id)

        names = [
            info.get('name').lower(),
            info.get('localized_name').lower(),
            info.get('name_short').lower()
        ]

        if info.get('aliases') != '':
            for alias in info.get('aliases').split(','):
                names.append(alias)

        if name in names:
            return hero_id
        elif hero_id == '105':
            return None


def run_hero_timer(name):
    logging.debug('Current thread: {}'.format(current_thread().name))

    hero_index = heroes[name]['index']
    localized_name = heroes[name]['localized_name']

    cooldown_time = get_cooldown_time(name)

    notification_queue.put("Hero #{} ({}): Starting ult timer for {} seconds".format(
        hero_index + 1, localized_name,  cooldown_time))

    timer_time_left[heroes[name]['index']] = cooldown_time
    for i in range(cooldown_time):
        time.sleep(1)
        timer_time_left[hero_index] -= 1

    voice_msg_queue.put(ALERT_MESSAGES['HERO'].format(hero_index + 1))
    voice_msg_queue.task_done()

    timer_running[heroes[name]['index']] = False

    notification_queue.put("Hero #{} ({}): Ult is ready!".format(hero_index + 1, localized_name))


def run_roshan_timer():
    logging.debug('Current thread: {}'.format(current_thread().name))

    notification_queue.put("Starting Roshan timer...")

    timer_time_left[5] = 60 * 11

    for i in range(60 * 8):
        time.sleep(1)
        timer_time_left[5] -= 1

    voice_msg_queue.put(ALERT_MESSAGES['ROSHAN']['MAYBE_ALIVE'])
    notification_queue.put("Roshan might be alive...")

    for i in range(60 * 3):
        time.sleep(1)
        timer_time_left[5] -= 1

    voice_msg_queue.put(ALERT_MESSAGES['ROSHAN']['ALIVE'])
    voice_msg_queue.task_done()

    timer_running[5] = False

    notification_queue.put("Roshan is alive!")


def read_hotkeys(filename):
    """
    Reads hotkey info from a config file and returns it as a dictionary
    :param filename: Configuration file with hotkey settings
    :return: A dictionary of hotkey settings
    """
    hotkeys = {}

    try:
        config = ConfigParser.ConfigParser()
        config.read(filename)

        hotkeys['HEROES'] = config.get('hotkeys', 'start_enemy_timer').split(', ')
        hotkeys['ROSHAN'] = config.get('hotkeys', 'roshan')

        return hotkeys
    except ConfigParser.Error:
        logging.exception("Failed to read and parse hotkeys configuration at {}".format(filename))

    sys.exit(1)


def read_hero_data(filename):
    """
    Read hero cooldowns from the specified JSON file.

    :param filename: The JSON file with the hero cooldown information
    :return: A dictionary containing hero information
    """
    try:
        with open(filename) as f:
            return json.load(f)
    except IOError:
        logging.exception(
            "Couldn't open the hero cooldowns file. Make sure it's called {} and in the same folder as the script."
            .format(HERO_DATA_FILE))
    except ValueError:
        logging.exception("Couldn't parse the hero cooldowns file. Make sure it's valid JSON.")

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


def create_heroes(hero_names, hero_ids):
    result = {}

    for i, name in enumerate(hero_names):
        hero_id = hero_ids[i]
        info = HERO_DATA.get(hero_id)
        localized_name = info.get('localized_name')

        if info.get('ultimate') is not None:
            cooldowns = info.get('ultimate').get('cooldown')
            scepter_cooldowns = info.get('ultimate').get('scepter_cooldown')
        else:
            cooldowns = [0]
            scepter_cooldowns = None

        result[name] = {
            'index': i,
            'cooldowns': cooldowns,
            'scepter_cooldowns': scepter_cooldowns,
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
    global last_key_pressed
    last_key_pressed = event.Key

    if event.Key == 'Return':
        global accept_hotkeys
        accept_hotkeys = not accept_hotkeys

    if not accept_hotkeys:
        return True

    if event.Key == HOTKEYS['ROSHAN']:
        if timer_running[5]:
            return True

        thread = Thread(target=run_roshan_timer, name='Roshan Timer')
        thread.start()
        timer_running[5] = True
    elif event.Key in HOTKEYS['HEROES']:
        i = HOTKEYS['HEROES'].index(event.Key)

        if timer_running[i]:
            return True

        name = get_hero_name_by_index(i)

        if event.IsAlt():
            increment_hero_state(name)
        elif last_key_pressed == 'Lshift':
            heroes[name]['has_scepter'] = not heroes[name]['has_scepter']

            localized_name = heroes[name]['localized_name']
            has_scepter = heroes[name]['has_scepter']

            notification_queue.put("{} has Aghanim's Scepter: {}".format(
                localized_name, has_scepter))
        else:
            thread = Thread(target=run_hero_timer, kwargs={'name': name}, name="Hero Timer {}".format(i + 1))
            thread.start()
            timer_running[i] = True

    return True


def watch_timers():
    timers_string = ""
    for i in range(6):
        timers_string += "{:10}"

    while True:
        timer_info_queue.put(timers_string.format(*timer_time_left))

        time.sleep(1)


def listen_for_keys():
    hm = pyHook.HookManager()
    hm.KeyDown = on_key_down
    hm.HookKeyboard()
    pythoncom.PumpMessages()


def update_screen():
    labels = ""
    for i in range(5):
        title = "Hero #{}".format(i + 1)
        labels += "{:>10}".format(title)

    labels += "{:>10}".format("Roshan")

    timer_info = ""
    notification = ""

    window = curses.initscr()

    while True:
        if not timer_info_queue.empty():
            timer_info = timer_info_queue.get()

        if not notification_queue.empty():
            notification = notification_queue.get()

        window.clear()

        window.addstr(labels)
        window.addstr("\n")
        window.addstr(timer_info)
        window.addstr("\n\n")
        window.addstr(notification)

        window.refresh()

        time.sleep(1)


def listen_for_voice_msgs():
    while True:
        if not voice_msg_queue.empty():
            msg = voice_msg_queue.get()
            speaker.Speak(msg)
        else:
            time.sleep(1)


def run_overlay():
    root = Tk.Tk()
    root.overrideredirect(1)
    root.attributes('-alpha', 0.7)
    screen_width = root.winfo_screenwidth()
    top_center = screen_width/2
    root.geometry('360x40+'+str(top_center+90)+'+0')

    root.wm_attributes('-topmost', 1)
    app = gui.Overlay(master=root)

    app.after(100, app.update_timer)

    app.mainloop()
    root.destroy()


def run():
    key_listener = Thread(target=listen_for_keys, name="Key Listener")
    key_listener.start()

    timer_watcher = Thread(target=watch_timers, name="Timer Watcher")
    timer_watcher.start()

    screen_updater = Thread(target=update_screen, name="Screen Updater")
    screen_updater.start()

    overlay_runner = Thread(target=run_overlay, name="Overlay Runner")
    overlay_runner.start()

    listen_for_voice_msgs()  # voice messages have to run on the main thread


def load_configs():
    global HERO_DATA
    HERO_DATA = read_hero_data(HERO_DATA_FILE)
    logging.info("Successfully read HERO_DATA file.")

    global HOTKEYS
    HOTKEYS = read_hotkeys(HOTKEYS_FILE)
    logging.info("Successfully read HOTKEYS file.")


def set_heroes(names, ids):
    global heroes
    heroes = create_heroes(names, ids)


def main():
    load_configs()
    set_heroes(*read_hero_names_and_ids())
    run()


if __name__ == '__main__':
    test.run()
    # main()

