import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
from datetime import datetime, timedelta
from stravalib.client import Client
import os
from dotenv import load_dotenv
import requests

class RunningCalendar:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Load Strava credentials
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.access_token = os.getenv('STRAVA_ACCESS_TOKEN')
        self.refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')

        if not all([self.client_id, self.client_secret, self.access_token, self.refresh_token]):
            raise ValueError("""Missing required Strava credentials in .env file.
Please ensure your .env file contains:
STRAVA_CLIENT_ID=your_actual_client_id
STRAVA_CLIENT_SECRET=your_actual_client_secret
STRAVA_ACCESS_TOKEN=your_actual_access_token
STRAVA_REFRESH_TOKEN=your_actual_refresh_token""")

        # Refresh access token if needed
        self.refresh_strava_token()

        # Initialize Strava client
        self.client = Client(access_token=self.access_token)

        # Create main window
        self.root = tk.Tk()
        self.root.title("Running Calendar")
        self.root.geometry("800x600")

        # Header
        ttk.Label(self.root, text="Running Calendar", font=('Arial', 16, 'bold')).pack(pady=10)

        # Calendar widget
        self.cal = Calendar(
            self.root,
            selectmode='day',
            year=datetime.now().year,
            month=datetime.now().month
        )
        self.cal.pack(pady=20)

        # Text box for activity details
        self.activity_text = tk.Text(self.root, height=10, width=70)
        self.activity_text.pack(pady=10)

        # Buttons
        ttk.Button(self.root, text="Refresh Activities", command=self.fetch_activities).pack(pady=10)

        # Store activities by date
        self.activities = {}

        # Bind calendar date selection
        self.cal.bind('<<CalendarSelected>>', self.show_activities)

    def refresh_strava_token(self):
        """Refresh the Strava access token if expired"""
        try:
            response = requests.post(
                'https://www.strava.com/oauth/token',
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'refresh_token': self.refresh_token,
                    'grant_type': 'refresh_token'
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                self.refresh_token = data['refresh_token']

                # Update .env file
                with open('.env', 'r') as f:
                    lines = f.readlines()

                with open('.env', 'w') as f:
                    for line in lines:
                        if line.startswith('STRAVA_ACCESS_TOKEN='):
                            f.write(f'STRAVA_ACCESS_TOKEN={self.access_token}\n')
                        elif line.startswith('STRAVA_REFRESH_TOKEN='):
                            f.write(f'STRAVA_REFRESH_TOKEN={self.refresh_token}\n')
                        else:
                            f.write(line)
            else:
                raise ValueError(f"Failed to refresh token: {response.text}")

        except Exception as e:
            print(f"Error refreshing token: {str(e)}")

    def fetch_activities(self):
        """Fetch authenticated user's running activities"""
        try:
            after = datetime.now() - timedelta(days=365)
            self.activity_text.delete('1.0', tk.END)
            self.activity_text.insert(tk.END, "Fetching your Strava activities...\n")
            self.root.update()

            activities = list(self.client.get_activities(after=after))
            if not activities:
                self.activity_text.insert(tk.END, "No activities found in the past year.\n")
                return

            self.activities.clear()
            run_count = 0

            for activity in activities:
                if activity.type == 'Run':
                    run_count += 1
                    date = activity.start_date_local.date()

                    if date not in self.activities:
                        self.activities[date] = []

                    if activity.moving_time and activity.distance:
                        pace_minutes = (activity.moving_time.total_seconds() / 60) / activity.distance.get_km()
                        pace = f"{int(pace_minutes)}:{int((pace_minutes % 1) * 60):02d}"
                    else:
                        pace = "N/A"

                    self.activities[date].append({
                        'name': activity.name,
                        'distance': f"{activity.distance.get_km():.2f} km",
                        'duration': str(activity.moving_time).split('.')[0],
                        'pace': f"{pace}/km"
                    })

            self.activity_text.delete('1.0', tk.END)
            self.activity_text.insert(tk.END, f"Processed {run_count} runs in the past year.\n")
            self.show_activities(None)

        except Exception as e:
            self.activity_text.delete('1.0', tk.END)
            self.activity_text.insert(tk.END, f"Error fetching activities: {str(e)}\n")
            self.activity_text.insert(tk.END, "Please check your Strava tokens or re-authorize the app.\n")

    def show_activities(self, event):
        """Display runs for the selected date"""
        selected_date = datetime.strptime(self.cal.get_date(), "%m/%d/%y").date()
        self.activity_text.delete('1.0', tk.END)

        if selected_date in self.activities:
            for activity in self.activities[selected_date]:
                self.activity_text.insert(
                    tk.END,
                    f"Run: {activity['name']}\n"
                    f"Distance: {activity['distance']}\n"
                    f"Duration: {activity['duration']}\n"
                    f"Pace: {activity['pace']}\n"
                    f"------------------------\n"
                )
        else:
            self.activity_text.insert(tk.END, "No runs logged on this date.\n")

    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = RunningCalendar()
    app.run()
