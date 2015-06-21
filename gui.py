__author__ = 'Dan'

import Tkinter as Tk

import dota_timer

class Overlay(Tk.Frame):
    def update_info(self):
        for i, time in enumerate(dota_timer.timer_time_left):
            self.timers[i]['text'] = time

        if not dota_timer.notification_queue.empty():
            self.notification['text'] = dota_timer.notification_queue.get()

        self.root.after(100, self.update_info)

    def __init__(self):
        self.root = Tk.Tk()

        self.root.attributes('-alpha', 0.7)
        self.root.wm_attributes('-topmost', 1)  # always on top

        Tk.Frame.__init__(self, master=self.root)

        self.left_side = Tk.Frame(self.root,  width=360, height=40)
        self.left_side.pack_propagate(False)
        self.left_side.pack(side=Tk.LEFT)
        
        self.timers_time = Tk.Frame(self.left_side,  width=360)
        self.timers_time.pack(side=Tk.BOTTOM)

        self.timers = []
        self.init_timers()

        self.right_side = Tk.Frame(self.root, height=40, padx=8)
        self.right_side.pack(side=Tk.RIGHT)

        button_options = dict(
            text="Toggle Borders",
            command=lambda: self.root.overrideredirect(not self.root.overrideredirect()),
            padx=5
        )

        self.toggle_borders = Tk.Button(self.right_side, **button_options)
        self.toggle_borders.pack()

        self.notification_frame = Tk.Frame(self.left_side, height=8)
        self.notification_frame.pack(side=Tk.TOP)

        self.notification = Tk.Label(self.notification_frame, text="")
        self.notification.pack()

    def init_timers(self):
        for i in range(6):
            self.timers.append(Tk.Label(self.timers_time, text='', width=8))
            self.timers[i].pack(side=Tk.LEFT)
