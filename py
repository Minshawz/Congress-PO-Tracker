import tkinter as tk
from tkinter import ttk
from datetime import datetime

class POTracker:
    def __init__(self, root):
        root.title("Congress PO Tracker")

        # ---------------- Top Controls ----------------
        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Total Competitors:").pack(side="left")
        self.total_var = tk.IntVar(value=16)
        ttk.Entry(top, textvariable=self.total_var, width=5).pack(side="left", padx=5)
        ttk.Button(top, text="Update", command=self.update_majorities).pack(side="left", padx=5)
        self.majority_label = ttk.Label(top)
        self.majority_label.pack(side="left", padx=10)
        self.update_majorities()

        self.round_var = tk.IntVar(value=1)
        ttk.Label(top, text="Round:").pack(side="left", padx=(20,5))
        ttk.Label(top, textvariable=self.round_var, width=3).pack(side="left")
        ttk.Button(top, text="Next Round", command=self.next_round).pack(side="left", padx=5)
        ttk.Button(top, text="Undo Last", command=self.undo_last).pack(side="left", padx=10)

        self.history = []

        # ---------------- Middle Frame ----------------
        mid = ttk.Frame(root, padding=10)
        mid.pack(fill="both", expand=True)

        # --- Auto-fill lists ---
        self.speaker_names = []
        self.bill_numbers = []

        # ----- Timer -----
        self.timer_running = False
        self.seconds = 0
        self.timer_label = tk.Label(
            mid,
            text="0:00",
            font=("Arial", 36, "bold"),
            fg="black")
        self.timer_label.grid(row=0, column=0, columnspan=5, pady=(0,10))
        ttk.Button(mid, text="Start Timer", command=self.start_timer).grid(row=1, column=0)
        ttk.Button(mid, text="Stop & Use Time", command=self.stop_timer).grid(row=1, column=1)

        # ----- Speech Entry -----
        ttk.Label(mid, text="Add Speech").grid(row=2, column=0, columnspan=5, pady=(10,4))
        self.speaker = ttk.Combobox(mid, values=self.speaker_names, width=15)
        self.bill = ttk.Combobox(mid, values=self.bill_numbers, width=8)
        self.time_spoken = tk.Entry(mid, width=6)
        self.aff_neg = tk.StringVar(value="Aff")
        side_box = ttk.Combobox(mid, textvariable=self.aff_neg,
                                values=["Aff","Neg"], width=5, state="readonly")
        for idx, txt in enumerate(["Speaker","Bill","Time","Side"]):
            ttk.Label(mid, text=txt).grid(row=3, column=idx)
        self.speaker.grid(row=4, column=0)
        self.bill.grid(row=4, column=1)
        self.time_spoken.grid(row=4, column=2)
        side_box.grid(row=4, column=3)
        ttk.Button(mid, text="Add Speech", command=self.add_speech).grid(row=4, column=4, padx=5)

        self.speech_tree = ttk.Treeview(
            mid,
            columns=("Speaker","Bill","Side","Time","Stamp","Round"),
            show="headings", height=7)
        for col,w in zip(("Speaker","Bill","Side","Time","Stamp","Round"),
                         [120,60,60,60,80,50]):
            self.speech_tree.heading(col, text=col)
            self.speech_tree.column(col, width=w)
        self.speech_tree.grid(row=5, column=0, columnspan=5, sticky="nsew", pady=5)
        mid.rowconfigure(5, weight=1)

        # ----- Question Entry -----
        ttk.Label(mid, text="Add Question").grid(row=6, column=0, columnspan=5, pady=(15,4))
        self.q_name = ttk.Combobox(mid, values=self.speaker_names, width=15)
        ttk.Label(mid, text="Questioner").grid(row=7, column=0)
        self.q_name.grid(row=8, column=0)
        ttk.Button(mid, text="Add Question", command=self.add_question).grid(row=8, column=1, padx=5)

        self.q_tree = ttk.Treeview(
            mid,
            columns=("Questioner","Round","Stamp"),
            show="headings", height=5)
        for col,w in zip(("Questioner","Round","Stamp"),[120,50,80]):
            self.q_tree.heading(col, text=col)
            self.q_tree.column(col, width=w)
        self.q_tree.grid(row=9, column=0, columnspan=5, sticky="nsew", pady=5)

        # ---------------- Bottom Frame ----------------
        bot = ttk.Frame(root, padding=10)
        bot.pack(fill="both", expand=True)
        ttk.Label(bot, text="Presidency Ranking (current round)").pack()
        self.rank_tree = ttk.Treeview(
            bot,
            columns=("Speaker","Score","Speeches","Questions"),
            show="headings", height=6)
        for col,w in zip(("Speaker","Score","Speeches","Questions"),[120,60,80,80]):
            self.rank_tree.heading(col, text=col)
            self.rank_tree.column(col, width=w)
        self.rank_tree.pack(fill="both", expand=True)

        # Small footer text
        footer = tk.Label(root, text="Made by Minhaz Abedin",
                          font=("Arial", 8), fg="gray")
        footer.pack(side="bottom", pady=4)

        self.stats = {}

    # -------- Timer --------
    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.tick()

    def tick(self):
        if self.timer_running:
            self.seconds += 1
            mins, secs = divmod(self.seconds, 60)
            time_text = f"{mins}:{secs:02d}"
            if time_text in ("2:00","2:30","3:00"):
                self.timer_label.config(fg="red")
            else:
                self.timer_label.config(fg="black")
            self.timer_label.config(text=time_text)
            self.timer_label.after(1000, self.tick)

    def stop_timer(self):
        if self.timer_running:
            self.timer_running = False
            mins, secs = divmod(self.seconds, 60)
            self.time_spoken.delete(0, tk.END)
            self.time_spoken.insert(0, f"{mins}:{secs:02d}")
            self.seconds = 0
            self.timer_label.config(text="0:00", fg="black")

    # -------- Data Updates --------
    def update_majorities(self):
        total = max(1, self.total_var.get())
        maj = total // 2 + 1
        two_thirds = (total * 2) // 3 + 1
        self.majority_label.config(text=f"Majority: {maj}   2/3: {two_thirds}")

    def add_speech(self):
        speaker = self.speaker.get().strip()
        bill = self.bill.get().strip()
        t = self.time_spoken.get().strip()
        side = self.aff_neg.get()
        if speaker and bill:
            if speaker not in self.speaker_names:
                self.speaker_names.append(speaker)
                self.speaker.config(values=self.speaker_names)
                self.q_name.config(values=self.speaker_names)
            if bill not in self.bill_numbers:
                self.bill_numbers.append(bill)
                self.bill.config(values=self.bill_numbers)

            round_num = self.round_var.get()
            rid = self.speech_tree.insert(
                "", "end",
                values=(speaker,bill,side,t,
                        datetime.now().strftime("%H:%M:%S"), round_num))
            self.update_stats(speaker, speech=1)
            self.history.append(("speech", rid, speaker))
            self.speaker.set("")
            self.bill.set("")
            self.time_spoken.delete(0, tk.END)

    def add_question(self):
        name = self.q_name.get().strip()
        if name:
            if name not in self.speaker_names:
                self.speaker_names.append(name)
                self.speaker.config(values=self.speaker_names)
                self.q_name.config(values=self.speaker_names)

            round_num = self.round_var.get()
            rid = self.q_tree.insert(
                "", "end",
                values=(name, round_num,
                        datetime.now().strftime("%H:%M:%S")))
            self.update_stats(name, question=1)
            self.history.append(("question", rid, name))
            self.q_name.set("")

    def update_stats(self, person, speech=0, question=0):
        d = self.stats.setdefault(person, {"speeches":0,"questions":0})
        d["speeches"] += speech
        d["questions"] += question
        self.refresh_rank()

    def refresh_rank(self):
        for r in self.rank_tree.get_children():
            self.rank_tree.delete(r)
        data = []
        for name,vals in self.stats.items():
            score = vals["speeches"] + 0.5*vals["questions"]
            data.append((name, score, vals["speeches"], vals["questions"]))
        data.sort(key=lambda x:x[1], reverse=True)
        for row in data:
            self.rank_tree.insert("", "end", values=row)

    def next_round(self):
        self.stats.clear()
        self.refresh_rank()
        self.round_var.set(self.round_var.get()+1)

    def undo_last(self):
        if not self.history:
            return
        kind, rid, person = self.history.pop()
        if kind == "speech":
            if rid in self.speech_tree.get_children():
                self.speech_tree.delete(rid)
                self.stats[person]["speeches"] -= 1
        else:
            if rid in self.q_tree.get_children():
                self.q_tree.delete(rid)
                self.stats[person]["questions"] -= 1
        if person in self.stats and \
           self.stats[person]["speeches"] == 0 and \
           self.stats[person]["questions"] == 0:
            del self.stats[person]
        self.refresh_rank()

if __name__ == "__main__":
    root = tk.Tk()
    POTracker(root)
    root.mainloop()
