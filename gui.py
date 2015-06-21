__author__ = 'Dan'

import Tkinter as Tk

import dota_timer

class Overlay(Tk.Frame):
    def update_timer(self):
        for i, time in enumerate(dota_timer.timer_time_left):
            self.timers[i]['text'] = time

        self.root.after(100, self.update_timer)

    def __init__(self):
        self.root = Tk.Tk()

        self.root.overrideredirect(0)
        self.root.attributes('-alpha', 0.7)

        self.root.wm_attributes('-topmost', 1)  # always on top
        self.root.resizable(False, False)

        Tk.Frame.__init__(self, master=self.root)

        frame_options = dict(
            width=360,
            height=50,
            borderwidth=4,
            relief=Tk.RAISED
        )

        self.frame = Tk.Frame(self.root, **frame_options)
        self.frame.pack_propagate(False)
        self.frame.pack()

        self.timers = []

        for i in range(6):
            self.timers.append(Tk.Label(self.frame, padx=16))
            self.timers[i]['text'] = ''
            self.timers[i].pack({'side': 'left'})

        def toggle_borders():
            self.root.overrideredirect(not self.root.overrideredirect())

        button_options = dict(
            text="Toggle Borders",
            command=toggle_borders
        )

        self.toggle_borders = Tk.Button(self.frame, **button_options)
        self.toggle_borders.pack()
