__author__ = 'Dan'

import Tkinter as Tk

import dota_timer

class Overlay(Tk.Frame):
    def update_timer(self):
        for i, time in enumerate(dota_timer.timer_time_left):

            self.timers[i]['text'] = time

        dota_timer.root.after(100, self.update_timer)

    def __init__(self, master=None):
        Tk.Frame.__init__(self, master)
        
        self.timers = []

        for i in range(6):
            self.timers.append(Tk.Label(width=8))
            self.timers[i]['text'] = ''
            self.timers[i].pack({'side': 'left'})
