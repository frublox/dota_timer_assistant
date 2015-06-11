__author__ = 'Dan'

import Tkinter as Tk

import dota_timer


class Overlay(Tk.Frame):
    def update_timer(self):
        timer_text = ""

        for i, time in enumerate(dota_timer.timer_time_left):
            timer_text += "Hero {}: {}s\n".format(i + 1, time)

        self.timer['text'] = timer_text
        self.timer.pack({'side': 'left'})

        dota_timer.root.after(100, self.update_timer)

    def __init__(self, master=None):
        Tk.Frame.__init__(self, master)

        self.timer = Tk.Label()
        self.timer['text'] = 'Timer 1: 0'
        self.timer.pack({'side': 'left'})