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

        self.timer_frame = Tk.Frame(self.root,  width=360, height=60)
        self.timer_frame.pack_propagate(False)
        self.timer_frame.pack(side=Tk.TOP)

        self.timers = []
        self.init_timers()

        self.options_frame = Tk.Frame(self.root, width=300, height=10, padx=10, pady=10)
        self.options_frame.pack(side=Tk.BOTTOM)

        button_options = dict(
            text="Toggle Borders",
            command=lambda: self.root.overrideredirect(not self.root.overrideredirect()),
            padx=5
        )

        self.toggle_borders = Tk.Button(self.options_frame, **button_options)
        self.toggle_borders.pack()

        self.notification_frame = Tk.Frame(self.root, width=300, height=10)
        self.notification_frame.pack(side=Tk.BOTTOM)

        self.notification = Tk.Label(self.notification_frame, text="")
        self.notification.pack()

    def init_timers(self):
        for i in range(6):
            self.timers.append(Tk.Label(self.timer_frame, text=''))
            self.timers[i].pack(side=Tk.LEFT, expand=True)
