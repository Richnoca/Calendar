import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime, timedelta, date
from garminconnect import Garmin
import json
import csv
import os
from getpass import getpass


YEAR_LOOKBACK = 365  # how many days back I fetch the data
GARMIN_CONFIG = "garmin_config.json" # login detail storage
EVALS_FILE = "run_evals.json" # run evaluation storage

# CSV plans live
PLANS_FOLDER = "plans"

# default run plan
DEFAULT_PLAN_FILENAME = "halhigdon_intermediate_10k.csv"

# RUNNING CALENDAR CLASS
# ---------------------------
class RunningCalendar:
    def __init__(self):
        self.activities = {}           # Garmin runs by date
        self.training_plan = {}        # Training plan run sby date
        self.run_evals = {}            # Self evals
        self.plan_rows = []            # CSV rows for selected plan
        self.training_event_ids = []   # event IDs for training plans
        self.current_plan_file = None   # current plan filename
        self.current_plan_start_date = None

        if not os.path.exists(PLANS_FOLDER):
            os.makedirs(PLANS_FOLDER)

        # Loads past run evals into Calendar
        if os.path.exists(EVALS_FILE):
            try:
                with open(EVALS_FILE) as f:
                    self.run_evals = json.load(f)
            except Exception:
                self.run_evals = {}

        # Garmin login
        # ---------------------------
        if os.path.exists(GARMIN_CONFIG):
            try:
                with open(GARMIN_CONFIG) as f:
                    creds = json.load(f)
                self.email = creds.get("email")
                self.password = creds.get("password")
                if not self.email or not self.password:
                    raise ValueError("Invalid credentials")
            except Exception:
                self.get_garmin_credentials()
        else:
            self.get_garmin_credentials()

        # GUI Setup and layout
        # Still ugly but works, change later
        # ---------------------------
        self.root = tk.Tk()
        self.root.title("Running Calendar")
        self.root.geometry("980x760")

        # Load label
        self.loading_label = tk.Label(self.root, text="", font=('Arial', 14, 'bold'), bg='lightgray')
        self.loading_label.place(relx=0.5, rely=0.5, anchor='center')
        self.loading_label.lower()

        # dropdown + apply + clear + refresh training for plans
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill='x', pady=8)

        ttk.Label(top_frame, text="Select Training Plan:", font=('Arial', 11)).pack(side='left', padx=(10, 6))
        self.plan_var = tk.StringVar()
        self.plan_dropdown = ttk.Combobox(top_frame, textvariable=self.plan_var, state="readonly", width=48)
        self.plan_dropdown.pack(side='left')
        ttk.Button(top_frame, text="Start Plan", command=self.apply_plan_from_selected_date).pack(side='left', padx=6)
        ttk.Button(top_frame, text="Clear Plan", command=self.clear_training_plan).pack(side='left', padx=6)
        ttk.Button(top_frame, text="Refresh Plans", command=self.refresh_plan_list).pack(side='left', padx=6)

        # Calendar widget mods can change colors/fonts
        ttk.Label(self.root, text="Running Calendar", font=('Arial', 16, 'bold')).pack(pady=6)
        self.cal = Calendar(
            self.root,
            selectmode='day',
            year=datetime.now().year,
            month=datetime.now().month,
            firstweekday='sunday',
            background='white',
            foreground='black',
            selectbackground='orange',
            selectforeground='white',
            disabledbackground='gray',
            weekendbackground='lightyellow',
            othermonthwebackground='lightgray',
            othermonthbackground='lightgray',
            font=('Arial', 11, 'bold')
        )
        self.cal.pack(pady=8, fill='x')
        self.cal.bind('<<CalendarSelected>>', self.show_activities)

        # Run detail scroll box to view run stats
        self.details_frame = tk.Frame(self.root, height=220, width=800)
        self.details_frame.pack(pady=8)
        self.details_canvas = tk.Canvas(self.details_frame, height=220, width=800)
        self.scrollbar = ttk.Scrollbar(self.details_frame, orient="vertical", command=self.details_canvas.yview)
        self.scrollable_frame = tk.Frame(self.details_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))
        )
        self.details_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="n", width=800)
        self.details_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.details_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Self Evals
        ttk.Label(self.root, text="Self-Evaluation:", font=('Arial', 12, 'bold')).pack(pady=6)
        self.eval_text = tk.Text(self.root, height=3, width=80)
        self.eval_text.pack(pady=4)
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=6)
        ttk.Button(btn_frame, text="Save Self-Evaluation", command=self.save_evaluation).pack(side='left', padx=6)
        ttk.Button(btn_frame, text="Refresh Activities (Garmin)", command=self.fetch_activities).pack(side='left', padx=6)

        # plans dropdown menu
        self.refresh_plan_list()

        # Load default if exists
        default_path = os.path.join(PLANS_FOLDER, DEFAULT_PLAN_FILENAME)
        if os.path.exists(default_path):
            try:
                idx = self.plan_dropdown['values'].index(DEFAULT_PLAN_FILENAME)
                self.plan_dropdown.current(idx)
                self.load_plan_rows(DEFAULT_PLAN_FILENAME)
            except Exception:
                pass

        # fetch Garmin
        self.fetch_activities()
        self.cal.selection_set(date.today())
        self.show_activities()

    # Garmin Credentials
    # ---------------------------
    def get_garmin_credentials(self):
        self.email = input("Enter your Garmin email: ").strip()
        self.password = getpass("Enter your Garmin password: ")
        try:
            with open(GARMIN_CONFIG, "w") as f:
                json.dump({"email": self.email, "password": self.password}, f)
        except Exception as e:
            print("Failed to save Garmin config:", e)

    # Loading overla
    # ---------------------------
    def show_loading(self, message="Loading..."):
        self.loading_label.config(text=message)
        self.loading_label.lift()
        self.root.update()

    def hide_loading(self):
        self.loading_label.lower()
        self.root.update()

    # Plans: refresh, load CSV
    # ---------------------------
    def refresh_plan_list(self):
        files = [f for f in os.listdir(PLANS_FOLDER) if f.lower().endswith(".csv")]
        files.sort()
        self.plan_dropdown["values"] = files
        if files and not self.plan_var.get():
            self.plan_dropdown.current(0)
            self.load_plan_rows(files[0])

    def load_plan_rows(self, filename):
        self.plan_rows = []
        path = os.path.join(PLANS_FOLDER, filename)
        if not os.path.exists(path):
            messagebox.showerror("Plan load error", f"Plan file not found: {path}")
            return
        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    norm = {}
                    for k, v in row.items():
                        if k is None:
                            continue
                        key = k.strip().capitalize()[:3]
                        norm[key] = (v or "").strip()
                    complete = {wd: norm.get(wd, "").strip() for wd in ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]}
                    self.plan_rows.append(complete)
            self.current_plan_file = filename
        except Exception as e:
            messagebox.showerror("Plan load error", f"Failed to load plan '{filename}': {e}")
            self.plan_rows = []
            self.current_plan_file = None

    # Apply the plan into calendar on highlighted day
    # ---------------------------
    def apply_training_plan_to_calendar(self, start_date):
        # remove old plan events
        for ev_id in list(self.training_event_ids):
            try:
                self.cal.calevent_remove(ev_id)
            except Exception:
                pass
        self.training_event_ids.clear()
        self.training_plan.clear()

        if not self.plan_rows:
            return

        current = start_date
        for week in self.plan_rows:
            for weekday in ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]:
                workout = (week.get(weekday) or "").strip()
                if workout and workout.lower() != "rest":
                    if current not in self.training_plan:
                        self.training_plan[current] = []
                    self.training_plan[current].append(workout)
                    try:
                        ev_id = self.cal.calevent_create(current, workout, "training_plan")
                        self.training_event_ids.append(ev_id)
                    except Exception:
                        pass
                current += timedelta(days=1)

        self.current_plan_start_date = start_date
        try:
            self.cal.tag_config("training_plan", background="lightblue", foreground="black")
        except Exception:
            pass

    # Apply plan button
    # ---------------------------
    def apply_plan_from_selected_date(self):
        if not self.plan_var.get():
            messagebox.showerror("No plan selected", "Please select a training plan.")
            return
        selected_file = self.plan_var.get()
        if selected_file != self.current_plan_file:
            self.load_plan_rows(selected_file)
        try:
            start_date = self.cal.selection_get()
        except Exception:
            messagebox.showerror("Invalid date", "Please select a start date first.")
            return

        # Remove all training plan events first
        for ev in list(self.cal.get_calevents()):
            try:
                self.cal.calevent_remove(ev)
            except Exception:
                pass

        # Apply training plan
        self.apply_training_plan_to_calendar(start_date)

        # Re add Garmin runs
        for run_date in self.activities:
            try:
                self.cal.calevent_create(run_date, "Run", "run_day")
            except Exception:
                pass

        # Style tags
        try:
            self.cal.tag_config("run_day", background="lightgreen", foreground="black")
        except Exception:
            pass

        self.show_activities()

    # Clear training plan button
    # ---------------------------
    def clear_training_plan(self):
        for ev_id in list(self.training_event_ids):
            try:
                self.cal.calevent_remove(ev_id)
            except Exception:
                pass
        self.training_event_ids.clear()
        self.training_plan.clear()
        self.current_plan_start_date = None
        self.current_plan_file = None
        self.show_activities()
        messagebox.showinfo("Training Plan Cleared", "The training plan has been cleared from the calendar.")

    # Garmin fetch
    # ---------------------------
    def fetch_garmin_activities(self):
        try:
            client = Garmin(self.email, self.password)
            client.login()
        except Exception as e:
            print("Garmin login failed:", e)
            return

        cutoff_date = date.today() - timedelta(days=YEAR_LOOKBACK)
        start = 0
        while True:
            try:
                acts = client.get_activities(start=start, limit=50)
                if not acts:
                    break
            except Exception as e:
                print("Failed to fetch activities:", e)
                break

            for act in acts:
                if act.get("activityType", {}).get("typeKey") != "running":
                    continue
                run_date = datetime.fromisoformat(act["startTimeLocal"]).date()
                if run_date < cutoff_date:
                    continue
                if run_date not in self.activities:
                    self.activities[run_date] = []
                miles = round(act.get("distance",0)/1609.34,2)
                dur = round(act.get("duration",0))
                self.activities[run_date].append({
                    "name": act.get("activityName","Run"),
                    "distance_miles": miles,
                    "duration_sec": dur,
                    "pace_mph": round(miles/(dur/3600) if dur else 0,2),
                    "max_hr": act.get("maxHR"),
                    "avg_hr": act.get("avgHR"),
                })
            if len(acts) < 50:
                break
            start += 50
        print(f"Total running activities loaded: {sum(len(v) for v in self.activities.values())}")

    def fetch_activities(self):
        self.activities.clear()
        self.clear_details()
        self.eval_text.delete("1.0", tk.END)
        self.show_loading("Fetching Garmin runs...")
        self.fetch_garmin_activities()

        # Remove all events and reapply current plan + runs
        for ev in list(self.cal.get_calevents()):
            try:
                self.cal.calevent_remove(ev)
            except Exception:
                pass

        if self.current_plan_file and self.current_plan_start_date:
            self.apply_training_plan_to_calendar(self.current_plan_start_date)

        for run_date in self.activities:
            try:
                self.cal.calevent_create(run_date, "Run", "run_day")
            except Exception:
                pass

        # Tag style
        try:
            self.cal.tag_config("run_day", background="lightgreen", foreground="black")
            self.cal.tag_config("training_plan", background="lightblue", foreground="black")
        except Exception:
            pass

        self.hide_loading()
        self.show_activities()

    # Show runs for selected date
    # ---------------------------
    def clear_details(self):
        for w in self.scrollable_frame.winfo_children():
            w.destroy()

    def show_activities(self, event=None):
        self.clear_details()
        selected = self.cal.selection_get()
        self.eval_text.delete("1.0", tk.END)

        outer = tk.Frame(self.scrollable_frame, width=780)
        outer.pack(anchor="n", pady=5)
        inner = tk.Frame(outer)
        inner.pack(anchor="center")

        if selected in self.training_plan:
            for w in self.training_plan[selected]:
                ttk.Label(inner, text=f"Training Plan: {w}", justify="left", anchor="w", foreground="blue").pack(anchor="w", pady=2)

        if selected in self.activities:
            for idx, run in enumerate(self.activities[selected], start=1):
                dur = run.get('duration_sec',0)
                metrics = (
                    f"Garmin Run {idx}: {run.get('name','Run')}\n"
                    f"Distance: {run.get('distance_miles','0')} mi\n"
                    f"Duration: {dur//60}m {dur%60}s\n"
                    f"Pace: {run.get('pace_mph','0')} mph\n"
                    f"Max HR: {run.get('max_hr','N/A')}\n"
                    f"Avg HR: {run.get('avg_hr','N/A')}\n"
                )
                ttk.Label(inner, text=metrics, justify="left", anchor="w").pack(anchor="w", pady=2)

        if selected not in self.training_plan and selected not in self.activities:
            ttk.Label(inner, text="No runs or workouts on this date.", anchor="center").pack(anchor="center")

        eval_text = self.run_evals.get(str(selected),"")
        if eval_text:
            self.eval_text.insert("1.0", eval_text)

    # Save self evalsuation
    # ---------------------------
    def save_evaluation(self):
        selected = self.cal.selection_get()
        text = self.eval_text.get("1.0", tk.END).strip()
        self.run_evals[str(selected)] = text
        try:
            with open(EVALS_FILE,"w") as f:
                json.dump(self.run_evals, f, indent=2)
            print(f"Saved self-evaluation for {selected}: {text}")
        except Exception as e:
            print("Failed to save evaluation:", e)
        self.show_activities()

    # Run GUI
    # ---------------------------
    def run(self):
        self.root.mainloop()

# MAIN
if __name__ == "__main__":
    app = RunningCalendar()
    app.run()
