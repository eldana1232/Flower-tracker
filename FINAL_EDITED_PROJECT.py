from plyer import notification
from tkinter import messagebox
from PIL import Image, ImageTk
import tkinter as tk
import os
import random
import datetime
import sqlite3
import threading
import time
# ------------------------- Ge'ez Numeral Converter -------------------------
def to_geez(num):
    """Convert any number 1–9999 to Ge'ez numerals"""
    if not isinstance(num, int) or num < 1 or num > 9999:
        return str(num)

    ones = ["", "፩", "፪", "፫", "፬", "፭", "፮", "፯", "፰", "፱"]
    tens = ["", "፲", "፳", "፴", "፵", "፶", "፷", "፸", "፹", "፺"]
    hundreds = ["", "፻", "፳፻", "፴፻", "፵፻", "፶፻", "፷፻", "፸፻", "፹፻", "፺፻"]
    thousands = ["", "፻፻", "፪፻፻", "፫፻፻", "፬፻፻", "፭፻፻", "፮፻፻", "፯፻፻", "፰፻፻", "፱፻፻"]

    t = num // 1000
    remainder = num % 1000
    h = remainder // 100
    remainder = remainder % 100
    te = remainder // 10
    o = remainder % 10

    result = ""
    if t > 0:
        result += thousands[t]
    if h > 0:
        result += hundreds[h]
    if te > 0:
        result += tens[te]
    if o > 0:
        result += ones[o]

    return result if result else "፩"
# ------------------------- Ethiopian Calendar conversion functions -------------------------
def is_gregorian_leap(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def meskerem1_gregorian_for_gregorian_year(y):
    if is_gregorian_leap(y + 1):
        return datetime.date(y, 9, 12)
    return datetime.date(y, 9, 11)

def gregorian_to_ethiopic(g_date):
    y = g_date.year
    mesk_current = meskerem1_gregorian_for_gregorian_year(y)
    if g_date >= mesk_current:
        eth_year = y - 7
        mesk = mesk_current
    else:
        eth_year = y - 8
        mesk = meskerem1_gregorian_for_gregorian_year(y - 1)
    delta = (g_date - mesk).days
    eth_month = delta // 30 + 1
    eth_day = delta % 30 + 1
    return eth_year, eth_month, eth_day

def meskerem1_gregorian_for_eth_year(e):
    return meskerem1_gregorian_for_gregorian_year(e + 7)

def ethiopic_to_gregorian(ey, em, ed):
    mesk = meskerem1_gregorian_for_eth_year(ey)
    days = (em - 1) * 30 + (ed - 1)
    gdate = mesk + datetime.timedelta(days=days)
    return gdate.year, gdate.month, gdate.day

# ------------------------- Ethiopian calendar labels -------------------------
ethiopian_months = [
    "መስከረም", "ጥቅምት", "ኅዳር", "ታህሳስ", "ጥር", "የካቲት",
    "መጋቢት", "ሚያዝያ", "ግንቦት", "ሰኔ", "ሐምሌ", "ነሐሴ", "ጳጉሜን"
]
amharic_days = ["ሰኞ", "ማክሰኞ", "ረቡዕ", "ሐሙስ", "ዓርብ", "ቅዳሜ", "እሑድ"]

class FlowerTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flower Tracker Login System")
        self.root.geometry("1350x700+0+0")

        # Database and current user/profile
        self.db_path = "flowertracker.db"
        self.current_user = None
        self.profile = {}
        self.current_year = 2018
        self.current_month = 1

        # Notification settings
        self.notifications_enabled = True
        self.water_reminder_active = False
        self.period_reminder_active = False
        self.water_count = 0
        self.water_goal = 8

        # init DB
        self.init_db()

        # Load login background image
        login_bg_path = "download.png"
        if os.path.exists(login_bg_path):
            self.login_bg_img = Image.open(login_bg_path)
            self.login_bg_img = self.login_bg_img.resize((1350, 700), Image.LANCZOS)
            self.login_bg_photo = ImageTk.PhotoImage(self.login_bg_img)
            self.login_bg_label = tk.Label(self.root, image=self.login_bg_photo)
            self.login_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            print(f"Warning: {login_bg_path} not found.")

        # Login Title
        title = tk.Label(self.root,
                         text="እንኳን ወደ ውቢት's የወር አበባ መከታተያ በሰላም መጡ",
                         font=("Impact", 24, "bold"),
                         fg="grey",
                         bg="#FFC0CB")
        title.place(x=465, y=180)

        # Username label & entry
        lbl_user = tk.Label(self.root,
                            text="User name",
                            font=("Goudy old style", 15, "bold"),
                            fg="grey", bg="#FFC0CB")
        lbl_user.place(x=490, y=240)
        self.user_name = tk.Entry(self.root,
                                  font=("Goudy old style", 15),
                                  bg="#E7E6E6")
        self.user_name.place(x=490, y=270, width=350, height=35)

        # Password label & entry
        lbl_pass = tk.Label(self.root,
                            text="Enter password",
                            font=("Goudy old style", 15, "bold"),
                            fg="grey", bg="#FFC0CB")
        lbl_pass.place(x=490, y=310)
        self.password = tk.Entry(self.root,
                                 font=("Goudy old style", 15),
                                 bg="#E7E6E6", show="*")
        self.password.place(x=490, y=340, width=350, height=35)

        # Login button
        login_btn = tk.Button(self.root,
                              text="Login\nለነባር መለያ",
                              bd=0,
                              font=("Goudy old style", 15),
                              fg="white",
                              bg="purple",
                              command=self.login_function)
        login_btn.place(x=490, y=420, width=180, height=40)

        # Register button
        register_btn = tk.Button(self.root,
                                 text="Register New Account\nለአዲስ አካውንት",
                                 bd=0,
                                 font=("Goudy old style", 15),
                                 fg="white",
                                 bg="blue",
                                 command=self.show_register_window)
        register_btn.place(x=660, y=420, width=180, height=40)

    # ------------------------- NOTIFICATION SYSTEM -------------------------
    def send_notification(self, title, message, timeout=5):
        """Generic notification sender"""
        if not self.notifications_enabled:
            return
        try:
            notification.notify(
                title=title,
                message=message,
                timeout=timeout
            )
        except Exception as e:
            print(f"Notification error: {e}")

    def test_notification(self):
        """Test notification function"""
        self.send_notification(
            "ሰላም\nHello 🎉",
            "ማስታወሻዎች በጥሩ ሁኔታ እየሰሩ ይገኛሉ\nNotifications are working perfectly! 🌸"
        )

    def start_water_reminder(self):
        """Start water reminder notifications"""
        def notify_water():
            while self.water_reminder_active:
                self.send_notification(
                    "💧የውሃ ማስታወሻ\n Water Reminder", 
                    "ውሃ መጠጣት እንዳትረሺ\nTime to drink water! Stay hydrated!\n 💧"
                )
                time.sleep(3600)  # Every hour
        
        if not self.water_reminder_active:
            self.water_reminder_active = True
            reminder_thread = threading.Thread(target=notify_water, daemon=True)
            reminder_thread.start()
            self.send_notification("የውሃ ማስታወሻ ጀምሯል\nWater Reminder Started", "በየሰዓቱ ማስታወሻ\nWater reminders every hour! 💧")

    def stop_water_reminder(self):
        """የውሃ ማስታወሻ ለማቆም\nStop water reminder notifications"""
        self.water_reminder_active = False
        self.send_notification("የውሃ ማስታወሻ አቁሟል\nWater Reminder Stopped", "No more water reminders.")

    def start_period_reminder(self):
        """የወር አበባ ማስታወሻ ለማስጀመር\nStart period reminder notifications"""
        def check_period():
            while self.period_reminder_active:
                self.send_notification(
                    "🌸የወር አበባ ማስታወሻ ጀምሯል\n Period Reminder", 
                    "የወር አበባ ኡደትሽን መመዝገብ እንዳትረሺ\nDon't forget to track your cycle! 🌸"
                )
                time.sleep(86400)  # Daily check
        
        if not self.period_reminder_active:
            self.period_reminder_active = True
            period_thread = threading.Thread(target=check_period, daemon=True)
            period_thread.start()
            self.send_notification("🌸የወር አበባ ማስታወሻ ጀምሯል\nPeriod Reminders Started🌸")

    def stop_period_reminder(self):
        """የወር አበባ ማስታወሻ ለማቆም\nStop period reminder notifications"""
        self.period_reminder_active = False
        self.send_notification("የወር አበባ ማስታወሻ ቆሟል\nPeriod Reminders Stopped", "No more period reminders.")

    def check_predicted_period_reminders(self):
        """Check if we need to send reminders for predicted periods"""
        if not self.current_user or not self.notifications_enabled:
            return
        
        # Get period and cycle length from profile
        period_length = self.profile.get('period_days', 5)
        cycle_length = self.profile.get('cycle_days', 28)
        
        if not period_length or not cycle_length:
            return
        
        # Get the most recent period start
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT start_date FROM period_starts WHERE username = ? ORDER BY start_date DESC LIMIT 1", (self.current_user,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return
        
        try:
            last_period_start = datetime.datetime.strptime(result[0], "%Y-%m-%d").date()
            next_predicted_start = last_period_start + datetime.timedelta(days=cycle_length)
            today = datetime.date.today()
            
            # Calculate days until next predicted period
            days_until = (next_predicted_start - today).days
            
            # Send reminders 3 days before
            if days_until == 3:
                self.send_notification(
                    "🌸 Period Reminder - 3 Days!", 
                    f"የወር አበባሽ ከ፫ ቀን በኋላ ይጀምራል\nYour period is predicted to start in 3 days ({next_predicted_start.strftime('%B %d')})! ተዘጋጂ\nTime to prepare! 🌸"
                )
            # Send reminders 1 day before
            elif days_until == 1:
                self.send_notification(
                    "የወር አበባሽ  ነገ ይጀምራል\n🌸 Period Reminder - Tomorrow!", 
                    f"Your period is predicted to start tomorrow ({next_predicted_start.strftime('%B %d')})! Get ready! 🌸"
                )
            # Send reminder on the predicted day
            elif days_until == 0:
                self.send_notification(
                    "የወር አበባሽ ጀምሯል\n🌸 Period Day Arrived!", 
                    f"Your period is predicted to start today! Don't forget to track it in the calendar! 🌸"
                )
                
        except Exception as e:
            print(f"Error checking predicted period reminders: {e}")

    def start_predicted_period_reminders(self):
        """Start automatic predicted period reminder system"""
        def check_reminders():
            while self.period_reminder_active:
                self.check_predicted_period_reminders()
                time.sleep(86400)  # Check once per day
        
        if not self.period_reminder_active:
            self.period_reminder_active = True
            reminder_thread = threading.Thread(target=check_reminders, daemon=True)
            reminder_thread.start()
            self.send_notification("የወር አበባ ትንበያ ጀምሯል\n🌸 Period Prediction Reminders Started!", "የወር አበባሽ ከመምጣቱ ፫ ቀን በፊት ማስታወሻ ታገኛለሽ!\nYou'll get notified 3 days before your predicted period! 🌸")

    def stop_predicted_period_reminders(self):
        """Stop predicted period reminder notifications"""
        self.period_reminder_active = False
        self.send_notification("የወር አበባ ማስታወሻ አቁሟል\n🌸 Period Prediction Reminders Stopped", "No more period prediction reminders.")

    def toggle_notifications(self):
        """Toggle notification system on/off"""
        self.notifications_enabled = not self.notifications_enabled
        status = "enabled" if self.notifications_enabled else "disabled"
        messagebox.showinfo("Notifications", f"Notifications {status}")
        if self.notifications_enabled:
            self.send_notification("ማስታወቂያ በርቷል\nNotifications Enabled", "አሁን መልክቶች ይደርስሻል\nYou'll now receive notifications! 🔔")

    # ------------------------- NEW NOTIFICATION WINDOW -------------------------
    def show_notifications(self):
        """Show dedicated notification management window"""
        notification_window = tk.Toplevel(self.root)
        notification_window.title("🔔የማስታወቂያ ማዕከል\nNotification Center")
        notification_window.geometry("500x600")
        notification_window.config(bg="#F0F8FF")

        # Title
        title = tk.Label(notification_window, 
                        text="🔔የማስታወቂያ ማዕከልNotification Center", 
                        font=("Impact", 20, "bold"), 
                        fg="#4169E1", 
                        bg="#F0F8FF")
        title.pack(pady=20)

        # Status Frame
        status_frame = tk.LabelFrame(notification_window, 
                                   text="አሁን ያለበት ሁኔታ Current Status", 
                                   font=("Arial", 14, "bold"),
                                   bg="#E6F3FF", 
                                   fg="#2E8B57")
        status_frame.pack(pady=10, padx=20, fill="x")

        # Notification status
        notif_status = "ON" if self.notifications_enabled else "OFF"
        tk.Label(status_frame, 
                text=f"🔔ማስታወሻዎች Notifications: {notif_status}", 
                font=("Arial", 12), 
                bg="#E6F3FF").pack(pady=5)

        # Water reminder status
        water_status = "ACTIVE" if self.water_reminder_active else "INACTIVE"
        tk.Label(status_frame, 
                text=f"💧የውሃ ማስታወሻ Water Reminders: {water_status}", 
                font=("Arial", 12), 
                bg="#E6F3FF").pack(pady=5)

        # Period reminder status
        period_status = "ACTIVE" if self.period_reminder_active else "INACTIVE"
        tk.Label(status_frame, 
                text=f"🌸 የወር አበባ ማስታወሻ Period Reminders: {period_status}", 
                font=("Arial", 12), 
                bg="#E6F3FF").pack(pady=5)

        # Predicted period reminder status
        predicted_status = "ACTIVE" if self.period_reminder_active else "INACTIVE"
        tk.Label(status_frame, 
                text=f"🔮 የትንበያ ማስታወሻ Prediction Reminders: {predicted_status}", 
                font=("Arial", 12), 
                bg="#E6F3FF").pack(pady=5)

        # Water tracking
        tk.Label(status_frame, 
                text=f"💧 የውሃ ግብ Water Goal: {self.water_count}/{self.water_goal} glasses", 
                font=("Arial", 12), 
                bg="#E6F3FF").pack(pady=5)

        # Control Buttons Frame
        control_frame = tk.LabelFrame(notification_window, 
                                    text="Controls", 
                                    font=("Arial", 14, "bold"),
                                    bg="#FFE4E1", 
                                    fg="#DC143C")
        control_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Test notification
        tk.Button(control_frame, 
                 text="🔔 ማስታወሻን ለመሞከር Test Notification",
                 command=self.test_notification,
                 bg="#FF69B4", fg="white", 
                 font=("Arial", 12, "bold"),
                 relief="raised").pack(pady=10, fill="x", padx=10)

        # Water reminder controls
        water_frame = tk.Frame(control_frame, bg="#FFE4E1")
        water_frame.pack(pady=10, fill="x", padx=10)

        tk.Button(water_frame, 
                 text="💧 የውሃ ማስታወሻ ለማስጀመር Start Water Reminders",
                 command=self.start_water_reminder,
                 bg="#00BFFF", fg="white", 
                 font=("Arial", 11)).pack(side="left", padx=5, fill="x", expand=True)

        tk.Button(water_frame, 
                 text="💧 የውሃ ማስታወሻ ለማስቆም Stop Water Reminders",
                 command=self.stop_water_reminder,
                 bg="#FF6347", fg="white", 
                 font=("Arial", 11)).pack(side="right", padx=5, fill="x", expand=True)

        # Period reminder controls
        period_frame = tk.Frame(control_frame, bg="#FFE4E1")
        period_frame.pack(pady=10, fill="x", padx=10)

        tk.Button(period_frame, 
                 text="🌸 የወር አበባ ማስታወሻ ለማስጀመር Start Period Reminders",
                 command=self.start_period_reminder,
                 bg="#DDA0DD", fg="white", 
                 font=("Arial", 11)).pack(side="left", padx=5, fill="x", expand=True)

        tk.Button(period_frame, 
                 text="🌸 የወር አበባ ማስታወሻ ለማስቆም Stop Period Reminders",
                 command=self.stop_period_reminder,
                 bg="#DC143C", fg="white", 
                 font=("Arial", 11)).pack(side="right", padx=5, fill="x", expand=True)

        # Predicted period reminder controls
        predicted_frame = tk.Frame(control_frame, bg="#FFE4E1")
        predicted_frame.pack(pady=10, fill="x", padx=10)

        tk.Button(predicted_frame, 
                 text="🔮 የወር አበባ ትንበያ ለማስጀመር Start Prediction Reminders",
                 command=self.start_predicted_period_reminders,
                 bg="#9370DB", fg="white", 
                 font=("Arial", 11)).pack(side="left", padx=5, fill="x", expand=True)

        tk.Button(predicted_frame, 
                 text="🔮 የወር አበባ ትንበያ ለማስቆም Stop Prediction Reminders",
                 command=self.stop_predicted_period_reminders,
                 bg="#8B0000", fg="white", 
                 font=("Arial", 11)).pack(side="right", padx=5, fill="x", expand=True)

        # Water tracking controls
        water_track_frame = tk.Frame(control_frame, bg="#FFE4E1")
        water_track_frame.pack(pady=10, fill="x", padx=10)

        tk.Button(water_track_frame, 
                 text="+1 ብርጭቆ +1💧 +1 Glass",
                 command=self.add_glass_from_notification,
                 bg="#20B2AA", fg="white", 
                 font=("Arial", 11)).pack(side="left", padx=5, fill="x", expand=True)

        tk.Button(water_track_frame, 
                 text="🔄 የውሃ እቅድን ከእንደገና ለማስጀመር Reset Water Count",
                 command=self.reset_glasses,
                 bg="#FF8C00", fg="white", 
                 font=("Arial", 11)).pack(side="right", padx=5, fill="x", expand=True)

        # Toggle notifications
        tk.Button(control_frame, 
                 text="🔕 ሁሉንም ማስታወሻዎች ለማጥፋት Toggle All Notifications",
                 command=lambda: [self.toggle_notifications(), notification_window.destroy(), self.show_notifications()],
                 bg="#8A2BE2", fg="white", 
                 font=("Arial", 12, "bold"),
                 relief="raised").pack(pady=15, fill="x", padx=10)

        # Close button
        tk.Button(control_frame, 
                 text="✖ Close",
                 command=notification_window.destroy,
                 bg="#696969", fg="white", 
                 font=("Arial", 12)).pack(pady=10, fill="x", padx=10)

    def add_glass_from_notification(self):
        """Add glass from notification window and update display"""
        if self.water_count < self.water_goal:
            self.water_count += 1
            if self.water_count == self.water_goal:
                self.send_notification(
                    "የውሀ ግብሽን  ተሳክተሻል\n🎉 Water Goal Achieved!", 
                    "እንኳን ደስ አለሽ \nCongratulations!\nእለታዊ የውሀ ግቡን አሳክተሻል \nYou reached your daily water goal! 💧"
                )
                messagebox.showinfo("እንኳን ደስ አለሽ\nCongrats!", "🎉 የውሀ ግብሽን  ተሳክተሻል\nYou reached your daily water goal!")
        else:
            messagebox.showinfo("አለቀ\nDone", "እለታዊ የውሀ ግቡን አሳክተሻል\nYou already reached your daily goal!")

    # ------------------------- Database helpers -------------------------
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   username TEXT PRIMARY KEY,
                   password TEXT,
                   name TEXT,
                   age INTEGER,
                   period_days INTEGER,
                   cycle_days INTEGER
               )"""
        )
        # Create period_logs table for tracking symptoms/mood/flow
        c.execute(
            """CREATE TABLE IF NOT EXISTS period_logs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT,
                   log_date TEXT,
                   symptoms TEXT,
                   mood TEXT,
                   flow TEXT,
                   FOREIGN KEY (username) REFERENCES users (username)
               )"""
        )
        # Create period_starts table for tracking period start dates
        c.execute(
            """CREATE TABLE IF NOT EXISTS period_starts (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT,
                   start_date TEXT,
                   end_date TEXT,
                   FOREIGN KEY (username) REFERENCES users (username)
               )"""
        )
        c.execute("INSERT OR IGNORE INTO users(username, password) VALUES (?, ?)", ("admin", "1234"))
        conn.commit()
        conn.close()

    def load_user_profile(self):
        if not self.current_user:
            self.profile = {}
            return
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT name, age, period_days, cycle_days FROM users WHERE username = ?", (self.current_user,))
        row = c.fetchone()
        conn.close()
        if row:
            name, age, pdays, cdays = row
            self.profile = {'name': name, 'age': age, 'period_days': pdays, 'cycle_days': cdays}
        else:
            self.profile = {}

    def save_user_profile(self, name, age):
        if not self.current_user:
            messagebox.showerror("Error", "No logged in user to save profile for.")
            return
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE users SET name = ?, age = ? WHERE username = ?", (name, age, self.current_user))
        if c.rowcount == 0:
            c.execute("INSERT INTO users(username, name, age) VALUES (?, ?, ?)", (self.current_user, name, age))
        conn.commit()
        conn.close()
        self.profile['name'] = name
        self.profile['age'] = age
        self.update_profile_label()
        self.send_notification("ገፅታሽ ተመዝግቧል\nProfile Saved! ✅", f"እንኳን ደና መጣሽ\nWelcome {name}! ገፅታሽ በተሳካ ሁኔታ ተሻሽሏል\nProfile updated successfully.")
        messagebox.showinfo("Saved(ተመዝግቧል)", "ገፅታሽ በተሳካ ሁኔታ ተመዝግቧል\nProfile saved successfully.")

    def save_period_details(self, period_days, cycle_days):
        """Save period details to database"""
        if not self.current_user:
            return
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE users SET period_days = ?, cycle_days = ? WHERE username = ?", 
                  (period_days, cycle_days, self.current_user))
        conn.commit()
        conn.close()
        self.profile['period_days'] = period_days
        self.profile['cycle_days'] = cycle_days

    # ------------------------- MERGED SAVE LOG FUNCTION -------------------------
    def save_log(self, date, popup):
        """Save symptoms, mood, and flow data to database"""
        selected_symptoms = [s for s, var in self.symptom_vars.items() if var.get()]
        selected_moods = [m for m, var in self.mood_vars.items() if var.get()]
        flow = ["ቀላል \nLight", "መካከለኛ \nMedium", "ከባድ \nHeavy", "በጣም ከባድ \nDisaster"][self.flow_var.get()-1] if self.flow_var.get() else ""
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO period_logs (username, log_date, symptoms, mood, flow) VALUES (?, ?, ?, ?, ?)",
                  (self.current_user, date, ",".join(selected_symptoms), ",".join(selected_moods), flow))
        conn.commit()
        conn.close()
        
        popup.destroy()
        self.send_notification("Symptoms Saved! 📝", "Your daily symptoms and mood have been recorded. 🌸")
        messagebox.showinfo("Saved", "Mood/Symptoms/Flow saved successfully!")

    # ------------------------- Register window -------------------------
    def show_register_window(self):
        register_win = tk.Toplevel(self.root)
        register_win.title("Register New User")
        register_win.geometry("400x300")
        
        tk.Label(register_win, text="Username:").pack(pady=5)
        username_entry = tk.Entry(register_win)
        username_entry.pack(pady=5)
        
        tk.Label(register_win, text="Password:").pack(pady=5)
        password_entry = tk.Entry(register_win, show="*")
        password_entry.pack(pady=5)
        
        tk.Label(register_win, text="Name:").pack(pady=5)
        name_entry = tk.Entry(register_win)
        name_entry.pack(pady=5)
        
        tk.Label(register_win, text="Age:").pack(pady=5)
        age_entry = tk.Entry(register_win)
        age_entry.pack(pady=5)
        
        def register_user():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            name = name_entry.get().strip()
            age_text = age_entry.get().strip()
            if not username or not password or not name or not age_text:
                messagebox.showerror("Error", "All fields are required!")
                return
            try:
                age = int(age_text)
            except ValueError:
                messagebox.showerror("Error", "Age must be a number!")
                return
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users(username, password, name, age) VALUES (?, ?, ?, ?)",
                          (username, password, name, age))
                conn.commit()
                self.send_notification("Registration Successful! 🎉", f"እንኳን ደና መጣሽ\nWelcome {name}! Account created successfully.")
                messagebox.showinfo("Success", "User registered successfully!")
                register_win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists!")
            finally:
                conn.close()
        
        tk.Button(register_win, text="Register\nክፈት", bg="green", fg="white", command=register_user).pack(pady=10)

    # ------------------------- Login -------------------------
    def login_function(self):
        user = self.user_name.get().strip()
        pwd = self.password.get().strip()
        if user == "" or pwd == "":
            messagebox.showerror("Error", "All fields are required", parent=self.root)
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (user,))
        row = c.fetchone()
        conn.close()
        
        if row and row[0] == pwd:
            self.current_user = user
            self.load_user_profile()
            welcome_name = self.profile.get('name', user)
            self.send_notification(f"Hello {welcome_name}! 🎉", "Welcome back to Flower Tracker! 🌸")
            messagebox.showinfo("Success", f"Welcome back, {user}!", parent=self.root)
            self.show_home_page()
        else:
            if user == "admin" and pwd == "1234":
                self.current_user = user
                self.load_user_profile()
                self.send_notification("Welcome Admin! 🎉", "Welcome to Flower Tracker! 🌸")
                messagebox.showinfo("Success", "Welcome to Flower Tracker!", parent=self.root)
                self.show_home_page()
            else:
                messagebox.showerror("Error", "Invalid username or password", parent=self.root)

    # ------------------------- Home Page -------------------------
    def show_home_page(self):
        self.hide_all_pages()
        self.home_page = tk.Frame(self.root)
        self.home_page.place(x=0, y=0, width=1350, height=700)

        home_bg_path = "try.png"
        if os.path.exists(home_bg_path):
            self.home_bg_img = Image.open(home_bg_path)
            self.home_bg_img = self.home_bg_img.resize((1350, 700), Image.LANCZOS)
            self.home_bg_photo = ImageTk.PhotoImage(self.home_bg_img)
            self.home_bg_label = tk.Label(self.home_page, image=self.home_bg_photo)
            self.home_bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        title = tk.Label(self.home_page,
                         text="🌸 Welcome to Flower Tracker 🌸\nእንኳን ወደ ውቢት's የወር አበባ መከታተያ በሰላም መጡ",
                         font=("Comic Sans MS", 22, "bold"),
                         fg="#FF69B4")
        title.place(relx=0.5, y=50, anchor="center")

        # Profile summary label removed per user request
        # Title is now centered and styled cutely

        # Primary buttons (Left side)
        tk.Button(self.home_page, text="Set Period Details🌸\nየወርአበባ ዝርዝር ለማስቀመጥ",
                  font=("Arial", 14), fg="white", bg="#FFB6C1",
                  command=self.show_period_details).place(x=100, y=100, width=200, height=50)

        tk.Button(self.home_page, text="View Calendar\nየቀን መቁጠሪያ📅",
                  font=("Arial", 14), fg="white", bg="#FFB6C1",
                  command=self.show_calendar).place(x=100, y=200, width=200, height=50)

        tk.Button(self.home_page, text="TALK FLORA:\nእህትአለም💬",
                  font=("Arial", 14), fg="white", bg="#FFB6C1",
                  command=self.show_ai_chat).place(x=100, y=300, width=200, height=50)

        tk.Button(self.home_page, text="View Reports\nውጤት ለመመልከት 📝",
                  font=("Arial", 14), fg="white", bg="#FFB6C1",
                  command=self.show_reports).place(x=100, y=400, width=200, height=50)

        tk.Button(self.home_page, text="Settings\nማስተካከያ⚙️",
                  font=("Arial", 14), fg="white", bg="#FFB6C1",
                  command=self.show_settings).place(x=100, y=500, width=200, height=50)

        tk.Button(self.home_page, text="Health Tips\nየጤና ምክሮች💡",
                  font=("Arial", 14), fg="white", bg="#98FB98",
                  command=self.show_health_tips).place(x=100, y=570, width=200, height=50)

        # NEW DEDICATED NOTIFICATION BUTTON (Right side - lower position)
        tk.Button(self.home_page, text="🔔 NOTIFICATIONS\nማሳወቂያዎች",
                  font=("Arial", 16, "bold"), fg="white", bg="#FFB6DE",
                  command=self.show_notifications).place(x=1100, y=300, width=200, height=80)

        # Water tracking shortcut
        tk.Button(self.home_page, text="💧 Water Tracker\nየውሃ መከታተያ",
                  font=("Arial", 12), fg="white", bg="#B8E6B8",
                  command=self.show_water_reminder).place(x=1100, y=400, width=200, height=50)

    def update_profile_label(self):
        # Profile label removed per user request
        pass
              # ------------------------- UTILITY FUNCTIONS -------------------------
    def hide_all_pages(self):
        """Hide all page frames"""
        for frame in ['home_page', 'calendar_page', 'period_page', 'ai_page', 'reports_page', 'settings_page', 'water_page']:
            if hasattr(self, frame):
                getattr(self, frame).place_forget()

    def reset_glasses(self):
        """Reset water glass counter"""
        self.water_count = 0
        if hasattr(self, 'status_label'):
            self.status_label.config(text=f"Glasses Drunk: {self.water_count}/{self.water_goal}")

    # ------------------------- SETTINGS PAGE -------------------------
    def show_settings(self):
        """Show settings page with profile and notifications"""
        self.hide_all_pages()
        self.settings_page = tk.Frame(self.root, bg="white")
        self.settings_page.place(x=0, y=0, width=1350, height=700)

        title = tk.Label(self.settings_page, text="Settings", font=("Impact", 24, "bold"), fg="grey", bg="white")
        title.place(x=600, y=20)

        tk.Button(self.settings_page, text="Back 🏠", font=("Arial", 14), fg="white", bg="#FFB6C1",
                  command=self.show_home_page).place(x=100, y=100)
        
        # Quick access to notification center
        tk.Button(self.settings_page, text="🔔 Notification Center", 
                  font=("Arial", 12), fg="white", bg="#FF69B4",
                  command=self.show_notifications).place(x=100, y=560, width=180, height=40)

        # Profile frame
        profile_frame = tk.LabelFrame(
            self.settings_page,
            text="Profile",
            font=("Comic Sans MS", 14),
            padx=10,
            pady=10,
            bg="#FFEBF0"
        )
        profile_frame.place(x=100, y=150, width=420, height=200)

        tk.Label(profile_frame, text="Name:", bg="#FFEBF0", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=8)
        name_entry = tk.Entry(profile_frame, font=("Arial", 12), width=28)
        name_entry.grid(row=0, column=1, pady=8)

        tk.Label(profile_frame, text="Age:", bg="#FFEBF0", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=8)
        age_entry = tk.Entry(profile_frame, font=("Arial", 12), width=28)
        age_entry.grid(row=1, column=1, pady=8)

        self.load_user_profile()
        if self.profile.get('name'):
            name_entry.insert(0, self.profile.get('name'))
        if self.profile.get('age'):
            age_entry.insert(0, str(self.profile.get('age')))

        def on_save_profile():
            name = name_entry.get().strip()
            age_text = age_entry.get().strip()
            if name == "" or age_text == "":
                messagebox.showerror("Error", "Please enter both name and age.")
                return
            try:
                age = int(age_text)
            except ValueError:
                messagebox.showerror("Error", "Age must be a number.")
                return
            self.save_user_profile(name, age)

        tk.Button(profile_frame, text="Save Profile", font=("Arial", 12), bg="#D6336C", fg="white", command=on_save_profile).grid(row=2, column=0, columnspan=2, pady=15)

        # User Guide frame
        guide_frame = tk.LabelFrame(
            self.settings_page,
            text="የተጠቃሚ መምሪያ User Guide 📚",
            font=("Comic Sans MS", 14),
            padx=10,
            pady=10,
            bg="#F0F8FF"
        )
        guide_frame.place(x=550, y=150, width=420, height=400)

        # Create scrollable text widget for guide
        guide_text = tk.Text(guide_frame, 
                            height=20, 
                            width=45, 
                            wrap=tk.WORD, 
                            bg="#FFFAF0", 
                            fg="#333333",
                            font=("Arial", 10),
                            relief="sunken",
                            bd=2)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(guide_frame, orient="vertical", command=guide_text.yview)
        guide_text.configure(yscrollcommand=scrollbar.set)
        
        # User guide content
        guide_content = """🌸 FLOWER TRACKER USER GUIDE 🌸

🏠 HOME PAGE:ዋና ገፅ
• Set Period Details:(የወር አበባ ዝርዝሮች ) Configure your period length & cycle\nየወር አበባ ቆይታ እና ዑደት አዋቅር
• View Calendar:( ቀን መቁጠሪያ ለመመልከት) Ethiopian calendar with period tracking\nከወር አበባ ክትትል ጋር የተያያዘ የኢትዮጵያ ቀን መቁጠሪያ
• Talk Flora:(እህታለም) AI chat for period advice:\n(በሌላ ስሟ እህታለም ሲሆን ለጥያቄዎችሽ መልስ አዘጋጅታ ትጠብቅሻለች)
• View Reports:(ዘገባ) See your period history & logs:\n(የወር አበባ ዘገባችን እና ዳታ ያስምጣል)
• Notifications:(ማስታወቂያ) Manage all reminder settings\nሁሉን ማስታወሻዎችሽን በአንድ ይዞ ይቆጣጠራል
• Water Tracker:(የውሃ ማስታወሻ) Track daily hydration goals\nእለታዊ የውሀ አወሳሰድሽን ይቆጣጠራል

📅 CALENDAR FEATURES:የቀን መቁጠሪያ
• Click any day to mark period start\n(የወር አበባ የጀመረበን ቀን ለመመግገብ የፈለጉት ቀን ይጫኑ)
• 🌸 Pink: Period start days\n(ሮዝ ቀለም የወር አበባ የጀመረበትን ቀን ለማመልከት)
• 🔴 Red: Period days (based on your length):(ቀይ ቀለም የወር አበባ ቀናትን)
• 🟢 Green: Predicted future periods:(አረንጓዴ ቀለም የወደፊት የወር አበባ ትንበያዎች)
• 🌟 Purple: Today's date(ሀምራዊ ቀለም የዛሬን ቀን ለማመልከት)
• Navigate months with ← → buttons( ← → እነዚህን ቁልፍ በመጫን ወርን  ወደፊት ወደኋላ ማየት ትቺያለሽ)

🔔 NOTIFICATIONS: ማስታወሻዎች
• Water Reminders: Hourly hydration alerts\n የውሃ ማስታወሻ ፡ በየሰአቱ የውሃ አስታዋሽ
• Period Reminders: Daily tracking reminders\nየወር አበባ አስታዋሽ፡ ዕለታዊ የክትትል አስታዋሽ
• Prediction Reminders: 3-day advance warnings\nየትንበያ አስታዋሽ፡ በቀድሞ 3 ቀናት የሚሰጡ ማስታወሻዎች
• Test notifications to check if working\nማስታወሻዎች በትክክል እየሰሩ እንደሆነ ለማረጋገጥ መፈተኛ

💧 WATER TRACKING:ውሃ ማስታወሻ
• Set daily goal (default: 8 glasses)\nዕለታዊ ግብ ማዘጋጃ(ቋሚ፡ 8 ብርጭቆ)
• Click "+1 Glass" when you drink water\nውሃ ሲጠጡ “+1 ብርጭቆ” ይንኩ
• Visual progress with glass emojis(የየቀን ሂደት በብርጭቆ ኢሞጂ)
• Reset counter daily\nቆጠራው በየቀኑ እንዳዲስ ይጀመራል 

📝 SYMPTOM TRACKING:የምልክት ክትትል
• Track daily symptoms, mood & flow\n ዕለታዊ ምልክቶች፣ ስሜት እና ፍሰት ይከታተሉ
• Access from calendar "Add Note" button\nከቀን መቁጠሪያ “ማስታወሻ ጨምር” አዝራር ይጠቀሙ
• Data saved for reports and patterns\nመረጃው ለሪፖርትና ለንድፈ ስርዓት ይቀመጣል

🤖 AI CHAT (FLORA):እህትአለም
• Ask questions about periods, symptoms\nስለ ወር አበባ እና ምልክቶች ጥያቄዎችን ይጠይቁ
• Get personalized advice and tips\nየግል ምክርና ጠቃሚ ምክሮች ያግኙ
• Available 24/7 for support\n24/7 በፈለጉት ሰዓት መጠቀም ይችላሉ

📊 REPORTS:ምዝገባዎች
• View all logged symptoms and moods\nየተመዘገቡ ምልክቶችንና ስሜቶችን ይመልከቱ
• Track period patterns over time\nየወር አበባ ንድፎችን በጊዜ ይከታተሉ
• Cycle statistics and predictions\nየዑደት ስታቲስቲክስ እና ትንበያዎች

⚙️ SETTINGS:ማስተካከያዎች
• Update your name and age\nም እና ዕድሜ ማስተካከል ይችላሉ 
• Set period length (e.g., 5 days)\nየወር አበባ ቆይታ ማዘጋጃ (ምሳሌ፡ 5 ቀን)
• Set cycle length (e.g., 28 days)\nየዑደት ርዝመት ማዘጋጃ (ምሳሌ፡ 28 ቀን)
• These settings affect predictions!\nእነዚህ ማስተካከያዎች ትንበያዎችን ያድርጋሉ!

🌟 TIPS:ምክሮች
• Set your period details first for accurate predictions\nየወር አበባ ዝርዝሮችሽን በመጀመሪያ በመሙላት ትክክለኛ ትንበያ እንዲኖሮት ያድርጉ 
• Mark period starts regularly for better tracking\nየወር አበባ መጀመሪያ ቀኖችን በመደበኛ ምልክት አድርጊ
• Enable notifications for helpful reminders\n
• Use water tracker for better health\nየውሃ ክትትል ተጠቀሚ ለጤናሽ ጠቃሚ ነው 
• Check reports monthly for patterns\nንድፎችን ለማየት በየወሩ የተመዘገቡትን መረጃዎች ተመልከቺ

🌸 Happy tracking! \n🌸 መልካም ክትትል! 🌸🌸"""
        
        guide_text.insert(tk.END, guide_content)
        guide_text.config(state=tk.DISABLED)  # Make read-only
        
        guide_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

    # ------------------------- HEALTH TIPS PAGE -------------------------
    def show_health_tips(self):
        """Show health tips page with quotes, food, medicine, and drink suggestions"""
        self.hide_all_pages()
        self.health_tips_page = tk.Frame(self.root)
        self.health_tips_page.place(x=0, y=0, width=1350, height=700)
        bg_path = "health_bg.png"
        if os.path.exists(bg_path):
            self.health_bg_img = Image.open(bg_path)
            self.health_bg_img = self.health_bg_img.resize((1350, 700), Image.LANCZOS)
            self.health_bg_photo = ImageTk.PhotoImage(self.health_bg_img)
            bg_label = tk.Label(self.health_tips_page, image=self.health_bg_photo)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Title
        title = tk.Label(self.health_tips_page, 
                        text="🌸 Health Tips & Wellness Guide 🌸", 
                        font=("Comic Sans MS", 24, "bold"), 
                        fg="#FF69B4", bg="#F0FFF0")
        title.pack(pady=20)

        # Back button
        tk.Button(self.health_tips_page, text="Back 🏠", 
                  font=("Arial", 14), fg="white", bg="#FFB6C1",
                  command=self.show_home_page).place(x=50, y=50)

        # Create scrollable frame
        canvas = tk.Canvas(self.health_tips_page, bg="#F0FFF0")
        scrollbar = tk.Scrollbar(self.health_tips_page, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#F0FFF0")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        #-------helper fun-------
        def create_item(parent, text, image_name, bg):
            frame = tk.Frame(parent, bg=bg)
            frame.pack(fill="x", pady=5, padx=10)
        # Image placeholder (X)
            if os.path.exists(image_name):
                img = Image.open(image_name)
                img = img.resize((50, 50), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                image_label = tk.Label(frame, image=photo, bg="#F0FFFF")
                image_label.image = photo  # keep reference
            else:
                image_label = tk.Label(frame, text="?",font=("Arial",16,"bold"),
                                       bg="#CCCCCC", width=4, height=2)
            image_label.pack(side="left", padx=(0, 15))
            tk.Label(frame, text=text, font=("Arial", 11), bg=bg,
                 wraplength=600, justify="left").pack(side="left", anchor="w")


        # Food Suggestions Section
        foods = [
        ("እንጀራ/ገንፎ፡የደም እጥረት ከመከሰት ይከላከላል፣ ሀይል ይሰጣል፣ አጥንትን ያጠናክራል", "injera.png"),
        ("ሽሮ ደምን ይጨምራል፣ ድካምን ያሳንሳል", "shiro.png"),
        ("ጎመን የህመም መቀነሻ፣ ደም ይጨምራል፣ ጡንቻን ያሳርፋል", "gomen.png"),
        ("ጥቁር ቸኮላት፣በተፈጥሮ ስሜትን የማነቃቃት እና ማግኒዢየም አለው", "coco.png"),
        ("ማር  ኃይል ይሰጣል፣  ድካምን ያሳንሳል", "honey.png"),
        ("አሳ  ህመምን ያሳንሳል", "fish.png"),
        ("ቆሎ ኃይል ይሰጣል፣ ድካም ከመከሰት ይከላከላል፣ የምግብ መፈጨትን ያግዛል", "kolo.png"),
        ("ድንች ጭንቀትን ያሳንሳል፣ የጡንቻ ህመምን ይቀንሳል፣ ኃይል ይሰጣል", "potato.png")
        ]
        food_frame = tk.LabelFrame(scrollable_frame, 
                                 text="🍎 Nourishing Foods for Your Cycle", 
                                 font=("Comic Sans MS", 16, "bold"),
                                 bg="#F0FFFF", fg="#008B8B", padx=20, pady=15)
        food_frame.pack(fill="x", padx=20, pady=10)

        for text, img in foods:
           create_item(food_frame,text,img,"#FFFFFF")
            
        # Drink Suggestions Section
        drinks = [
        ("ሻይ፡የዝንጅብል የቀረፋ እና የቅንፋድ ሻይ ለሆድ ቁርጠተሰ እና ለመፍታታት ፍቱን መፍትሄ ነው", "tea.png"),
        ("የዝንጅብል ሻይ: ", "ginger.png"),
        ("ቅርንፉድ ሻይ – የደም ዝውውርን ያሻሽላል፣ ቁርጠትን ይቀንሳል።", "clove.png"),
        ("ናና ሻይ – ለሆድ መፈጨት፣ ራስ ህመም እና ማቅለሽለሽን ይቀንሳል።", "nana.png"),
        ("ብርቱካን ጭማቂ፡ቪታሚን C ይሰጣል፣ በወር አበባ ጊዜ የሚቀንስ ብረትን ይረዳ እንዲቀበል ያግዛል", "orange.png"),
        ("ኮካ፡አንቲ ኦክሲዳንት ባህሪ አለው", "coca.png"),
    ]
        drinks_frame = tk.LabelFrame(scrollable_frame, text="🍵 Healing Drinks & Teas",
                                 font=("Comic Sans MS", 16, "bold"),
                                 bg="#FFF8DC", fg="#DAA520", padx=20, pady=15)
        drinks_frame.pack(fill="x", padx=20, pady=10)
        for text, img in drinks:
            create_item(drinks_frame, text, img, "#FFF8DC")

        # Natural Remedies Section
        remedies = [
        ("Heat Therapy: Heating pad or warm bath for cramp relief", "heat.png"),
        ("Gentle Yoga: Child's pose, cat-cow stretches", "yoga.png"),
        ("Epsom Salt Bath: Magnesium absorption", "bath.png"),
    ]
        remedies_frame = tk.LabelFrame(scrollable_frame, text="🌿 Remedies & Self-Care",
                                   font=("Comic Sans MS", 16, "bold"),
                                   bg="#E6E6FA", fg="#9370DB", padx=20, pady=15)
        remedies_frame.pack(fill="x", padx=20, pady=10)
        for text, img in remedies:
            create_item(remedies_frame, text, img, "#E6E6FA")

        # Ethiopian Traditional Remedies
        traditional = [
        ("Ethiopian Coffee: Rich in antioxidants", "coffee.png"),
        ("Rue (Tena Adam): Digestive comfort", "rue.png"),
        ("Ethiopian Honey: Natural energy", "honey.png"),
    ]
        traditional_frame = tk.LabelFrame(scrollable_frame, text="🇪🇹 Ethiopian Traditional Wisdom",
                                      font=("Comic Sans MS", 16, "bold"),
                                      bg="#FFFACD", fg="#B8860B", padx=20, pady=15)
        traditional_frame.pack(fill="x", padx=20, pady=10)
        for text, img in traditional:
            create_item(traditional_frame, text, img, "#FFFACD")

        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")

        # Add mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # ------------------------- PERIOD DETAILS PAGE -------------------------
    def show_period_details(self):
        """Show period details configuration page"""
        self.hide_all_pages()
        self.period_page = tk.Frame(self.root)
        bg_path = "eldu.png"   # your image file
        if os.path.exists(bg_path):
            self.period_bg_img = Image.open(bg_path)
            self.period_bg_img = self.period_bg_img.resize((1350, 700), Image.LANCZOS)
            self.period_bg_photo = ImageTk.PhotoImage(self.period_bg_img)
            bg_label = tk.Label(self.period_page, image=self.period_bg_photo)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.period_page.place(x=0, y=0, width=1350, height=700)

        title = tk.Label(self.period_page, text="Set Period Details", font=("Impact", 24, "bold"), fg="grey", bg="white")
        title.place(x=500, y=30)

        input_frame = tk.Frame(self.period_page, bg="white")
        input_frame.place(x=400, y=150, width=500, height=300)

        self.create_period_cycle_inputs(input_frame)

        tk.Button(self.period_page, text="Back 🏠",
                  font=("Arial", 14), fg="white", bg="pink",
                  command=self.show_home_page).place(x=100, y=100)

    def create_period_cycle_inputs(self, parent_frame):
        """Create period and cycle input widgets"""
        period_length_label = tk.Label(parent_frame, text="How many days does your period last\nየወር አበባሽ ስንት ቀን ይቆያል?", font=("Arial", 14))
        period_length_label.pack(pady=10)

        self.period_length_var = tk.IntVar()
        period_length_entry = tk.Entry(parent_frame, textvariable=self.period_length_var, width=5, font=("Arial", 14))
        period_length_entry.pack(pady=5)

        cycle_length_label = tk.Label(parent_frame, text="How many days is your cycle\ \n የወር አበባሽ የስንት ቀኑ ይመጣል?", font=("Arial", 14))
        cycle_length_label.pack(pady=10)

        self.cycle_length_var = tk.IntVar()
        cycle_length_entry = tk.Entry(parent_frame, textvariable=self.cycle_length_var, width=5, font=("Arial", 14))
        cycle_length_entry.pack(pady=5)

        set_details_button = tk.Button(parent_frame, text="Set Period Details", font=("Arial", 14), fg="#ffffff", bg="#FFB6C1", command=self.set_period_details)
        set_details_button.pack(pady=20)

    def set_period_details(self):
        """Save period details"""
        period_length = self.period_length_var.get()
        cycle_length = self.cycle_length_var.get()
        if period_length and cycle_length:
            self.save_period_details(period_length, cycle_length)
            self.send_notification(
                "Period Details Saved! 🌸",
                f"Period: {period_length} days, Cycle: {cycle_length} days"
            )
            messagebox.showinfo("Details Set", f"Your period length: {period_length} days\nYour cycle length: {cycle_length} days")
        else:
            messagebox.showwarning("Missing Information", "Please fill in both fields!")

    # ------------------------- WATER REMINDER PAGE -------------------------
    def show_water_reminder(self):
        """Show cute water tracking page"""
        self.hide_all_pages()
        self.water_page = tk.Frame(self.root, bg="#E6F7FF")
        self.water_page.place(x=0, y=0, width=1350, height=700)

        # Back button at top
        top_frame = tk.Frame(self.water_page, bg="#E6F7FF")
        top_frame.pack(fill="x", padx=20, pady=10)
        
        back_btn = tk.Button(top_frame, text="🏠 Back to Home", 
                           command=self.show_home_page, 
                           font=("Comic Sans MS", 14, "bold"), 
                           bg="#9370DB", fg="white",
                           relief="raised", bd=4,
                           width=15, height=1)
        back_btn.pack(side="left")

        # Reset button at top-right
        reset_btn = tk.Button(top_frame, text="🔄 Reset Day", 
                            command=self.reset_water_now, 
                            font=("Comic Sans MS", 12, "bold"), 
                            bg="#FF6347", fg="white",
                            relief="raised", bd=3,
                            width=12, height=1)
        reset_btn.pack(side="right")

        # Title
        title = tk.Label(self.water_page, text="💧✨ Hydration Station ✨💧", 
                        font=("Comic Sans MS", 28, "bold"), 
                        fg="#6A9BCD", bg="#E6F7FF")
        title.pack(pady=15)
        
        subtitle = tk.Label(self.water_page, text="Stay cute, stay hydrated! 🌸💦", 
                           font=("Comic Sans MS", 16), 
                           fg="#FF69B4", bg="#E6F7FF")
        subtitle.pack(pady=5)

        # Visual glasses display
        glasses_frame = tk.Frame(self.water_page, bg="#E6F7FF")
        glasses_frame.pack(pady=30)

        self.glass_labels = []
        for i in range(self.water_goal):
            if i < self.water_count:
                glass_emoji = "🥛"
                color = "#00BFFF"
            else:
                glass_emoji = "🥃"
                color = "#D3D3D3"
            
            glass_label = tk.Label(glasses_frame, text=glass_emoji, 
                                 font=("Arial", 30), fg=color, bg="#E6F7FF")
            glass_label.pack(side="left", padx=8)
            self.glass_labels.append(glass_label)

        # Progress status
        self.water_status_label = tk.Label(self.water_page, 
                                         text=f"💧 {self.water_count}/{self.water_goal} glasses completed! 💧", 
                                         font=("Comic Sans MS", 20, "bold"), 
                                         fg="#4169E1", bg="#E6F7FF")
        self.water_status_label.pack(pady=20)

        # Motivational message
        messages = ["በርቺቺቺ\nYou're doing amazing! 🌟", "ቀጥዪበት ደርሰሻል\nKeep going, ውቢት\nbeautiful! 💖", "ውሀ መጠጣት እራስሽን ለመጠበቅ ነው ✨\nHydration is self-care!", "Your skin will thank you! 🌸", "Almost there ደርሰሻል\n, superstar! 🎉"]
        progress_percent = (self.water_count / self.water_goal) * 100
        if progress_percent == 100:
            motivation = " GOAL ACHIEVED!\nግብሽን አሳክተሻል🎉\n ጀግኒት አሳክተሸዋል👑 You're a hydration queen! "
        elif progress_percent >= 75:
            motivation = messages[4]
        elif progress_percent >= 50:
            motivation = messages[3]
        elif progress_percent >= 25:
            motivation = messages[2]
        else:
            motivation = messages[0]

        self.water_motivation_label = tk.Label(self.water_page, text=motivation, 
                                             font=("Comic Sans MS", 16), 
                                             fg="#FF1493", bg="#E6F7FF")
        self.water_motivation_label.pack(pady=10)

        # Buttons
        button_frame = tk.Frame(self.water_page, bg="#E6F7FF")
        button_frame.pack(pady=30)

        # Drink water button
        drink_btn = tk.Button(button_frame, text="💧 Drink Water! 💧", 
                            command=self.drink_water_now, 
                            font=("Comic Sans MS", 18, "bold"), 
                            bg="#00CED1", fg="white",
                            relief="raised", bd=5,
                            width=20, height=2)
        drink_btn.pack(pady=15)

        # Reset button
        reset_btn = tk.Button(button_frame, text="🔄 Reset Day", 
                            command=self.reset_water_now, 
                            font=("Comic Sans MS", 14), 
                            bg="#FF6347", fg="white",
                            relief="raised", bd=3,
                            width=15)
        reset_btn.pack(pady=10)


        # Tips
        tips_frame = tk.LabelFrame(self.water_page, text="💡 Hydration Tips", 
                                 font=("Comic Sans MS", 14, "bold"),
                                 bg="#FFFACD", fg="#8B4513")
        tips_frame.pack(pady=20, fill="x", padx=100)

        tips = ["💧 Start your day with a glass of water!", "🍋 Add lemon for extra vitamin C!", "⏰ Set reminders every hour!", "🌿 Herbal teas count towards hydration!", "🥒 Eat water-rich foods like cucumber!"]
        
        import random
        daily_tip = random.choice(tips)
        tip_label = tk.Label(tips_frame, text=daily_tip, 
                           font=("Comic Sans MS", 12), 
                           fg="#2E8B57", bg="#FFFACD")
        tip_label.pack(pady=15)

    def drink_water_now(self):
        """Add a glass of water with visual updates"""
        if self.water_count < self.water_goal:
            self.water_count += 1
            
            # Update visual glasses
            for i, glass_label in enumerate(self.glass_labels):
                if i < self.water_count:
                    glass_label.config(text="🥛", fg="#00BFFF")
                else:
                    glass_label.config(text="🥃", fg="#D3D3D3")
            
            # Update status
            self.water_status_label.config(text=f"💧 {self.water_count}/{self.water_goal} glasses completed! 💧")
            
            # Update motivation
            progress_percent = (self.water_count / self.water_goal) * 100
            if progress_percent == 100:
                motivation = "🎉 GOAL ACHIEVED! You're a hydration queen! 👑"
                self.send_notification("🎉 Hydration Queen! 👑", "Amazing! You've reached your daily water goal! You're glowing! ✨💧")
                messagebox.showinfo("🎉 Congratulations! 🎉", "You're officially a hydration queen! 👑✨\nYour skin is going to be glowing! 🌟")
            elif progress_percent >= 75:
                motivation = "Almost there\nደርሰሻል, superstar! 🎉"
            elif progress_percent >= 50:
                motivation = "Your skin will thank you!\nጀግኒት 🌸"
            elif progress_percent >= 25:
                motivation = "Hydration is self-care! ✨"
            else:
                motivation = "You're doing amazing! 🌟\nአሪፍ ላይ ነሽ"
            
            self.water_motivation_label.config(text=motivation)
        else:
            messagebox.showinfo("💧 Already Perfect! 💧", "You've already achieved your hydration goal today! 🎉\nYou're a water-drinking superstar! ⭐")

    def reset_water_now(self):
        """Reset water counter with confirmation"""
        if self.water_count > 0:
            result = messagebox.askyesno("🔄 Reset Hydration", "Are you sure you want to reset your water progress? 💧\n\nThis will start your hydration journey over! 🌟")
            if result:
                self.water_count = 0
                
                # Update visual glasses
                for glass_label in self.glass_labels:
                    glass_label.config(text="🥃", fg="#D3D3D3")
                
                # Update status
                self.water_status_label.config(text=f"💧 {self.water_count}/{self.water_goal} glasses completed! 💧")
                
                # Reset motivation
                self.water_motivation_label.config(text="You're doing amazing! 🌟")
                
                self.send_notification("🔄 Fresh Start! 🔄", "Your hydration counter has been reset! Time for a fresh start! 💧✨")
        else:
            messagebox.showinfo("💧 Nothing to Reset! 💧", "Your hydration counter is already at zero! 🌟\nTime to start drinking some water! 💦")

     # ------------------------- ETHIOPIAN CALENDAR PAGE -------------------------
    def show_calendar(self):
        """Show Ethiopian calendar with mood/symptom tracking"""
        self.hide_all_pages()
        self.calendar_page = tk.Frame(self.root)
        self.calendar_page.place(x=0, y=0, width=1350, height=700)
        bg_path = "eldu.png"
        if os.path.exists(bg_path):
            self.calendar_bg_img = Image.open(bg_path)
            self.calendar_bg_img = self.calendar_bg_img.resize((1350, 700), Image.LANCZOS)
            self.calendar_bg_photo = ImageTk.PhotoImage(self.calendar_bg_img)
            bg_label = tk.Label(self.calendar_page, image=self.calendar_bg_photo)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.title_var = tk.StringVar()
        title_label = tk.Label(self.calendar_page, textvariable=self.title_var,
                               font=("Comic Sans MS", 18, "bold"), fg="#D6336C", bg="white")
        title_label.grid(row=0, column=0, columnspan=5, pady=10)

        btn_prev = tk.Button(self.calendar_page, text="←ቀዳሚ", command=self.prev_month,
                             font=("Comic Sans MS", 12), bg="#B6D1FF", fg="white", relief="flat")
        btn_prev.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        btn_today = tk.Button(self.calendar_page, text="ዛሬ 📅", command=self.go_today,
                              font=("Comic Sans MS", 12), bg="#B6D1FF", fg="white", relief="flat")
        btn_today.grid(row=1, column=1, pady=5)

        btn_next = tk.Button(self.calendar_page, text="ቀጣይ →", command=self.next_month,
                             font=("Comic Sans MS", 12), bg="#B6D1FF", fg="white", relief="flat")
        btn_next.grid(row=1, column=2, padx=10, pady=5, sticky="e")

        btn_add_note = tk.Button(self.calendar_page, text="💖 Add Note 💖", command=self.show_symptom_mood_flow,
                                 font=("Comic Sans MS", 12), bg="#FFB6DE", fg="white", relief="flat")
        btn_add_note.grid(row=1, column=3, padx=5, pady=5)

        btn_period_start = tk.Button(self.calendar_page, text="🌸 Mark Period Start 🌸", command=self.mark_period_start,
                                    font=("Comic Sans MS", 12), bg="#FF69B4", fg="white", relief="flat")
        btn_period_start.grid(row=1, column=4, padx=5, pady=5)

        tk.Button(self.calendar_page, text="Back 🏠", font=("Arial", 14), fg="white", bg="#FFB6C1",
                  command=self.show_home_page).grid(row=1, column=5, padx=20, pady=5, sticky="e")

        self.calendar_frame = tk.Frame(self.calendar_page, bg="white")
        self.calendar_frame.grid(row=2, column=0, columnspan=5, padx=10, pady=10)

        self.go_today()

    def mark_period_start(self):
        """Open date picker to mark any date as period start"""
        self.show_period_date_picker()

    def show_period_date_picker(self):
        """Show date picker dialog for selecting period start date"""
        self.hide_all_pages()
        self.date_picker_page = tk.Frame(self.root, bg="#FFE4E1")
        self.date_picker_page.place(x=0, y=0, width=1350, height=700)

        # Title
        title = tk.Label(self.date_picker_page, text="🌸 Select Period Start Date 🌸", 
                        font=("Comic Sans MS", 24, "bold"), 
                        fg="#FF1493", bg="#FFE4E1")
        title.pack(pady=30)

        # Date selection frame
        date_frame = tk.Frame(self.date_picker_page, bg="#FFE4E1")
        date_frame.pack(pady=20)

        # Year selection
        year_label = tk.Label(date_frame, text="Year:", font=("Comic Sans MS", 14, "bold"), 
                             fg="#FF1493", bg="#FFE4E1")
        year_label.grid(row=0, column=0, padx=10, pady=10)
        
        current_year = datetime.date.today().year
        self.year_var = tk.StringVar(value=str(current_year))
        year_spinbox = tk.Spinbox(date_frame, from_=current_year-5, to=current_year+1, 
                                 textvariable=self.year_var, width=10, font=("Comic Sans MS", 12))
        year_spinbox.grid(row=0, column=1, padx=10, pady=10)

        # Month selection
        month_label = tk.Label(date_frame, text="Month:", font=("Comic Sans MS", 14, "bold"), 
                              fg="#FF1493", bg="#FFE4E1")
        month_label.grid(row=0, column=2, padx=10, pady=10)
        
        months = ["January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November", "December"]
        self.month_var = tk.StringVar(value=months[datetime.date.today().month-1])
        month_combo = tk.ttk.Combobox(date_frame, textvariable=self.month_var, values=months, 
                                     width=12, font=("Comic Sans MS", 12), state="readonly")
        month_combo.grid(row=0, column=3, padx=10, pady=10)

        # Day selection
        day_label = tk.Label(date_frame, text="Day:", font=("Comic Sans MS", 14, "bold"), 
                            fg="#FF1493", bg="#FFE4E1")
        day_label.grid(row=0, column=4, padx=10, pady=10)
        
        self.day_var = tk.StringVar(value=str(datetime.date.today().day))
        day_spinbox = tk.Spinbox(date_frame, from_=1, to=31, textvariable=self.day_var, 
                                width=5, font=("Comic Sans MS", 12))
        day_spinbox.grid(row=0, column=5, padx=10, pady=10)

        # Buttons frame
        button_frame = tk.Frame(self.date_picker_page, bg="#FFE4E1")
        button_frame.pack(pady=40)

        # Mark date button
        mark_btn = tk.Button(button_frame, text="🌸 Mark This Date 🌸", 
                           command=self.save_selected_period_date,
                           font=("Comic Sans MS", 16, "bold"), 
                           bg="#FF1493", fg="white",
                           relief="raised", bd=5, width=20, height=2)
        mark_btn.pack(side="left", padx=20)

        # Cancel button
        cancel_btn = tk.Button(button_frame, text="❌ Cancel", 
                             command=self.show_calendar,
                             font=("Comic Sans MS", 16, "bold"), 
                             bg="#808080", fg="white",
                             relief="raised", bd=5, width=15, height=2)
        cancel_btn.pack(side="left", padx=20)

        # Instructions
        instructions = tk.Label(self.date_picker_page, 
                               text="💡 Select any date when your period started\n🌸 This will help track your cycle and generate reports",
                               font=("Comic Sans MS", 12), fg="#FF69B4", bg="#FFE4E1")
        instructions.pack(pady=20)

    def save_selected_period_date(self):
        """Save the selected date as period start"""
        try:
            year = int(self.year_var.get())
            month = self.month_var.get()
            day = int(self.day_var.get())
            
            # Convert month name to number
            months = ["January", "February", "March", "April", "May", "June",
                     "July", "August", "September", "October", "November", "December"]
            month_num = months.index(month) + 1
            
            # Create date object
            selected_date = datetime.date(year, month_num, day)
            
            # Check if this date already exists
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT * FROM period_starts WHERE username = ? AND start_date = ?", 
                      (self.current_user, selected_date.strftime("%Y-%m-%d")))
            existing = c.fetchone()
            
            if existing:
                result = messagebox.askyesno("🌸 Period Start", 
                                           f"You already marked {selected_date.strftime('%B %d, %Y')} as a period start date.\n\nDo you want to remove this marking?")
                if result:
                    c.execute("DELETE FROM period_starts WHERE username = ? AND start_date = ?", 
                             (self.current_user, selected_date.strftime("%Y-%m-%d")))
                    conn.commit()
                    self.send_notification("🌸 Period Start Removed", "Period start date has been removed from your calendar.")
                    messagebox.showinfo("Removed", "Period start date removed from your calendar! 🌸")
            else:
                c.execute("INSERT INTO period_starts (username, start_date) VALUES (?, ?)", 
                         (self.current_user, selected_date.strftime("%Y-%m-%d")))
                conn.commit()
                self.send_notification("🌸 Period Start Marked! 🌸", "Your period start date has been added to the calendar!")
                messagebox.showinfo("Marked! 🌸", f"Period start marked for {selected_date.strftime('%B %d, %Y')}! 🌸\nThis will help track your cycle and generate reports!")
            
            conn.close()
            # Go back to calendar and refresh
            self.show_calendar()
            
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter a valid date!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def get_period_starts_for_month(self, year, month):
        """Get all period start dates for a specific month"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT start_date FROM period_starts WHERE username = ?", (self.current_user,))
        dates = c.fetchall()
        conn.close()
        
        period_dates = set()
        for date_str in dates:
            try:
                date_obj = datetime.datetime.strptime(date_str[0], "%Y-%m-%d").date()
                ey, em, ed = gregorian_to_ethiopic(date_obj)
                if ey == year and em == month:
                    period_dates.add(ed)
            except:
                continue
        
        return period_dates

    def get_all_period_starts(self):
        """Get all period start dates for the current user (for reports)"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT start_date FROM period_starts WHERE username = ? ORDER BY start_date", 
                  (self.current_user,))
        dates = c.fetchall()
        conn.close()
        
        period_dates = []
        for date_str in dates:
            try:
                date_obj = datetime.datetime.strptime(date_str[0], "%Y-%m-%d").date()
                period_dates.append(date_obj)
            except:
                continue
        
        return period_dates

    def calculate_cycle_stats(self):
        """Calculate cycle statistics from period start dates"""
        period_dates = self.get_all_period_starts()
        
        if len(period_dates) < 2:
            return {
                'average_cycle': 'Not enough data',
                'last_period': period_dates[0] if period_dates else 'No data',
                'next_predicted': 'Not enough data',
                'total_periods': len(period_dates)
            }
        
        # Calculate cycle lengths
        cycle_lengths = []
        for i in range(1, len(period_dates)):
            cycle_length = (period_dates[i] - period_dates[i-1]).days
            cycle_lengths.append(cycle_length)
        
        average_cycle = sum(cycle_lengths) / len(cycle_lengths)
        last_period = period_dates[-1]
        next_predicted = last_period + datetime.timedelta(days=int(average_cycle))
        
        return {
            'average_cycle': f"{average_cycle:.1f} days",
            'last_period': last_period.strftime("%B %d, %Y"),
            'next_predicted': next_predicted.strftime("%B %d, %Y"),
            'total_periods': len(period_dates),
            'cycle_lengths': cycle_lengths
        }

    def show_month(self):
        """Display current month in Ethiopian calendar"""
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        ey = self.current_year
        em = self.current_month

        days_in_month = 30 if em <= 12 else (6 if (ey % 4) == 3 else 5)

        gy, gm, gd = ethiopic_to_gregorian(ey, em, 1)
        first_g = datetime.date(gy, gm, gd)
        start_weekday = first_g.weekday()

        self.title_var.set(f"{ethiopian_months[em-1]} {to_geez(ey)} E.C.")

        for i, wd in enumerate(amharic_days):
            lbl = tk.Label(self.calendar_frame, text=wd, width=10, height=3,
                           font=("Comic Sans MS", 14, "bold"),
                           borderwidth=1, relief="solid", bg="#FFB6C1", fg="#D6336C")
            lbl.grid(row=0, column=i, sticky="nsew")

        row = 1
        col = start_weekday

        today_g = datetime.date.today()
        today_eth = gregorian_to_ethiopic(today_g)
        
        # Get period start dates, period days, and predicted period days for this month
        period_starts = self.get_period_starts_for_month(ey, em)
        period_days = self.get_period_days_for_month(ey, em)
        predicted_days = self.get_predicted_period_days_for_month(ey, em)

        for d in range(1, days_in_month + 1):
            gy, gm, gd = ethiopic_to_gregorian(ey, em, d)
            geez_day = to_geez(d)
            geez_month = to_geez(gm)
            geez_gday = to_geez(gd)
            text = f"{geez_day}\n{geez_month}/{geez_gday}"

            # Color coding: today = purple, period start = bright pink, period days = red, predicted = light green, normal = light pink
            if (ey, em, d) == today_eth:
                bg_color = "#D44CB2"
                text = f"🌟{geez_day}🌟\n{geez_month}/{geez_gday}"
            elif d in period_starts:
                bg_color = "#FF1493"  # Deep pink for period start
                text = f"🌸{geez_day}🌸\n{geez_month}/{geez_gday}"
            elif d in period_days:
                bg_color = "#DC143C"  # Red for period days
                text = f"🔴{geez_day}🔴\n{geez_month}/{geez_gday}"
            elif d in predicted_days:
                bg_color = "#90EE90"  # Light green for predicted period days
                text = f"🟢{geez_day}🟢\n{geez_month}/{geez_gday}"
            else:
                bg_color = "#FFE0E0"

            lbl = tk.Label(self.calendar_frame, text=text, width=10, height=4,
                           font=("Arial", 12, "bold"),
                           borderwidth=1, relief="solid",
                           bg=bg_color, fg="white" if d in period_starts or d in period_days or (ey, em, d) == today_eth else "#D6336C",
                           padx=5, pady=5, anchor="center", cursor="hand2")
            lbl.grid(row=row, column=col, sticky="nsew")
            
            # Make each day clickable for period start selection
            lbl.bind("<Button-1>", lambda event, day=d: self.on_day_click(day))

            col += 1
            if col > 6:
                col = 0
                row += 1

    def prev_month(self):
        """Navigate to previous month"""
        if self.current_month == 1:
            self.current_month = 13
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.show_month()

    def next_month(self):
        """Navigate to next month"""
        if self.current_month == 13:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.show_month()

    def go_today(self):
        """Navigate to current month"""
        today = datetime.date.today()
        ey, em, ed = gregorian_to_ethiopic(today)
        self.current_year, self.current_month = ey, em
        self.show_month()

    def on_day_click(self, day):
        """Handle clicking on a calendar day to mark period start"""
        result = messagebox.askyesno(
            "🌸 Period Start", 
            f"Mark day {to_geez(day)} as your period start date?\n\nThis will automatically mark your period days based on your saved period length."
        )
        
        if result:
            # Convert Ethiopian date to Gregorian
            gy, gm, gd = ethiopic_to_gregorian(self.current_year, self.current_month, day)
            selected_date = datetime.date(gy, gm, gd)
            
            # Check if this date already exists
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT * FROM period_starts WHERE username = ? AND start_date = ?", 
                      (self.current_user, selected_date.strftime("%Y-%m-%d")))
            existing = c.fetchone()
            
            if existing:
                # Remove existing period start
                c.execute("DELETE FROM period_starts WHERE username = ? AND start_date = ?", 
                         (self.current_user, selected_date.strftime("%Y-%m-%d")))
                conn.commit()
                self.send_notification("🌸 Period Start Removed", "Period start date has been removed from your calendar.")
                messagebox.showinfo("Removed", "Period start date removed! 🌸")
            else:
                # Add new period start
                c.execute("INSERT INTO period_starts (username, start_date) VALUES (?, ?)", 
                         (self.current_user, selected_date.strftime("%Y-%m-%d")))
                conn.commit()
                self.send_notification("🌸 Period Start Marked! 🌸", "Your period start date has been added to the calendar!")
                messagebox.showinfo("Marked! 🌸", f"Period start marked for {selected_date.strftime('%B %d, %Y')}! 🌸")
            
            conn.close()
            # Refresh the calendar display
            self.show_month()

    def get_period_days_for_month(self, year, month):
        """Get all period days (not just starts) for a specific month based on period length"""
        period_days = set()
        
        # Get period length from profile
        period_length = self.profile.get('period_days', 5)  # Default to 5 days
        
        # Get all period start dates
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT start_date FROM period_starts WHERE username = ?", (self.current_user,))
        dates = c.fetchall()
        conn.close()
        
        for date_str in dates:
            try:
                start_date = datetime.datetime.strptime(date_str[0], "%Y-%m-%d").date()
                
                # Add each day of the period
                for i in range(period_length):
                    period_date = start_date + datetime.timedelta(days=i)
                    ey, em, ed = gregorian_to_ethiopic(period_date)
                    if ey == year and em == month:
                        period_days.add(ed)
            except:
                continue
        
        return period_days

    def get_predicted_period_days_for_month(self, year, month):
        """Get predicted period days for a specific month based on cycle length - calculates for entire year"""
        predicted_days = set()
        
        # Get period and cycle length from profile
        period_length = self.profile.get('period_days', 5)  # Default to 5 days
        cycle_length = self.profile.get('cycle_days', 28)  # Default to 28 days
        
        # Get all period start dates
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT start_date FROM period_starts WHERE username = ? ORDER BY start_date DESC", (self.current_user,))
        dates = c.fetchall()
        conn.close()
        
        if not dates:
            return predicted_days
        
        # Get the most recent period start
        try:
            last_period_start = datetime.datetime.strptime(dates[0][0], "%Y-%m-%d").date()
            
            # Calculate multiple predicted periods for the entire year
            # Start from the next predicted period after the last actual period
            next_predicted_start = last_period_start + datetime.timedelta(days=cycle_length)
            
            # Generate predictions for up to 2 years ahead to cover all possible months
            for cycle_num in range(24):  # 24 cycles = ~2 years of predictions
                predicted_start = next_predicted_start + datetime.timedelta(days=cycle_length * cycle_num)
                
                # Add predicted period days for this cycle
                for i in range(period_length):
                    predicted_date = predicted_start + datetime.timedelta(days=i)
                    ey, em, ed = gregorian_to_ethiopic(predicted_date)
                    
                    # Only add days that match the requested month/year
                    if ey == year and em == month:
                        predicted_days.add(ed)
                
                # Convert to Gregorian to check if we've gone too far
                predicted_gregorian = predicted_start
                if predicted_gregorian.year > datetime.date.today().year + 2:
                    break
                    
        except:
            pass
        
        return predicted_days

    def show_symptom_mood_flow(self):
        """Show symptom, mood, and flow selection window"""
        symptom_window = tk.Toplevel(self.root)
        symptom_window.title("📝 Track Your Day - Symptoms, Mood & Flow")
        symptom_window.geometry("800x650")
        symptom_window.config(bg="#FFFEEB")
        symptom_window.resizable(True, True)

        # Configure grid weights for proper scaling
        symptom_window.grid_columnconfigure(0, weight=1)
        symptom_window.grid_columnconfigure(1, weight=1)
        symptom_window.grid_rowconfigure(1, weight=1)

        # Title
        title_label = tk.Label(symptom_window, text="📝 How are you feeling today?", 
                              font=("Comic Sans MS", 16, "bold"), 
                              fg="#D6336C", bg="#FFFEEB")
        title_label.grid(row=0, column=0, columnspan=2, pady=15, sticky="ew")

        # Main content frame with scrollable capability
        main_frame = tk.Frame(symptom_window, bg="#FFFEEB")
        main_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        symptoms_frame = tk.LabelFrame(main_frame, text="🩺 Symptoms", font=("Comic Sans MS", 12, "bold"),
                                       padx=5, pady=5, bg="#FFEBF0", fg="#D6336C")
        symptoms_frame.grid(row=0, column=0, padx=5, pady=5, sticky="new")

        self.symptom_vars = {}
        symptoms = ['Feeling Good', 'Cramps', 'Lower Pain', 'Bloating', 'Acne',
                    'Nausea', 'Headache', 'Diarrhea', 'Constipation', 'Gas']
        for i, symptom in enumerate(symptoms):
            var = tk.BooleanVar()
            self.symptom_vars[symptom] = var
            checkbutton = tk.Checkbutton(symptoms_frame, text=symptom, variable=var,
                                         font=("Comic Sans MS", 9), bg="#FFEBF0", fg="#D6336C",
                                         activebackground="#FFE4E1")
            checkbutton.grid(row=i, column=0, sticky='w', pady=0)

        moods_frame = tk.LabelFrame(main_frame, text="😊 Mood", font=("Comic Sans MS", 12, "bold"),
                                    padx=5, pady=5, bg="#FFEBF0", fg="#D6336C")
        moods_frame.grid(row=0, column=1, padx=5, pady=5, sticky="new")

        self.mood_vars = {}
        moods = ['Normal🙂', 'Happy😁', 'Sad😭', 'Angry😡', 'Exhausted😓', 'Depressed😔', 'Emotional🫥', 'Anxious😨']
        for i, mood in enumerate(moods):
            var = tk.BooleanVar()
            self.mood_vars[mood] = var
            checkbutton = tk.Checkbutton(moods_frame, text=mood, variable=var,
                                         font=("Comic Sans MS", 9), bg="#FFEBF0", fg="#D6336C",
                                         activebackground="#FFE4E1")
            checkbutton.grid(row=i, column=0, sticky='w', pady=0)

        # Flow section - now more prominent with space freed up
        flow_frame = tk.LabelFrame(main_frame, text="🌊 Flow Intensity", font=("Comic Sans MS", 14, "bold"),
                                   padx=15, pady=10, bg="#FFEBF0", fg="#D6336C")
        flow_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=15, sticky="ew")

        self.flow_var = tk.IntVar()
        flows = ['Light 💧', 'Medium 💧💧', 'Heavy 💧💧💧', 'Disaster 🌊']
        
        # Create a prominent horizontal layout for flow options
        flow_inner_frame = tk.Frame(flow_frame, bg="#FFEBF0")
        flow_inner_frame.pack(pady=10)
        
        for i, flow in enumerate(flows):
            radiobutton = tk.Radiobutton(flow_inner_frame, text=flow, variable=self.flow_var, value=i+1,
                                         font=("Comic Sans MS", 12, "bold"), bg="#FFEBF0", fg="#D6336C",
                                         activebackground="#FFE4E1", selectcolor="#FFB6C1")
            radiobutton.pack(side="left", padx=25, pady=5)

        # Button frame - fixed at bottom
        button_frame = tk.Frame(symptom_window, bg="#FFFEEB")
        button_frame.grid(row=2, column=0, columnspan=2, pady=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        # Save button - more prominent
        save_button = tk.Button(button_frame, text="💾 Save My Day",
                                command=lambda: self.save_log(datetime.date.today().strftime("%Y-%m-%d"), symptom_window),
                                font=("Comic Sans MS", 14, "bold"), bg="#FF69B4", fg="white",
                                relief="raised", width=18, height=2,
                                activebackground="#FF1493", cursor="hand2")
        save_button.grid(row=0, column=0, padx=20, pady=10)

        # Cancel button
        cancel_button = tk.Button(button_frame, text="❌ Cancel",
                                 command=symptom_window.destroy,
                                 font=("Comic Sans MS", 12), bg="#DC143C", fg="white",
                                 relief="raised", width=15, height=2,
                                 activebackground="#B22222", cursor="hand2")
        cancel_button.grid(row=0, column=1, padx=20, pady=10)

    # ------------------------- AI CHAT PAGE -------------------------
    def show_ai_chat(self):
        """Show AI chat interface"""
        self.hide_all_pages()
        self.ai_page = tk.Frame(self.root)
        self.ai_page.place(x=0, y=0, width=1350, height=700)

        ai_bg_path = "elda.png"
        if os.path.exists(ai_bg_path):
            self.ai_bg_img = Image.open(ai_bg_path)
            self.ai_bg_img = self.ai_bg_img.resize((1350, 700), Image.LANCZOS)
            self.ai_bg_photo = ImageTk.PhotoImage(self.ai_bg_img)
            self.ai_bg_label = tk.Label(self.ai_page, image=self.ai_bg_photo)
            self.ai_bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        title = tk.Label(self.ai_page, text="AI Chat - Talk to Flora", font=("Impact", 24, "bold"), fg="grey", bg="white")
        title.place(x=500, y=30)

        self.chat_log = tk.Text(self.ai_page, height=15, width=50, state=tk.DISABLED, bg="#FFEBF0", fg="#D6336C", font=("Arial", 12))
        self.chat_log.pack(pady=20)

        self.entry = tk.Entry(self.ai_page, width=40, font=("Arial", 14))
        self.entry.pack(pady=10)
        self.entry.bind('<Return>', lambda event: self.send_message())

        tk.Button(self.ai_page, text="Send ✨", font=("Arial", 14), fg="white", bg="#FFB6C1", command=self.send_message).pack()
        tk.Button(self.ai_page, text="Back 🏠", font=("Arial", 14), fg="white", bg="#FFB6C1", command=self.show_home_page).pack(pady=20)

    def send_message(self):
        """Send message to AI chat"""
        user_input = self.entry.get()
        if user_input.strip() == "":
            return
        if user_input.lower() == "exit":
            self.show_home_page()
            return
        response = self.get_response(user_input)
        self.chat_log.config(state=tk.NORMAL)
        self.chat_log.insert(tk.END, f"You: {user_input}\nFlora: {response}\n\n")
        self.chat_log.config(state=tk.DISABLED)
        self.chat_log.see(tk.END)
        self.entry.delete(0, tk.END)

    def get_response(self, user_input):
        """Get AI response based on user input"""
        responses = {
            'hello': ['Hello, beautiful! 🌸', 'Hey girl, how can I help today?'],
            'hi': ['Hello, beautiful! 🌸', 'Hey girl, how can I help today?'],
            'hey': ['Hey lovely! 🌺'],
            'how are you': ['I am fine thank you, how about you?'],
            'not good': ['Im sorry to hear that. Remember, after the rain comes the rainbow! 🌈'],
            'good': ['Thats great to hear! Keep shining'],
            'great': ['Awesome! Keep that positive energy going! 🌟'],
            'okay': ['Hope things get even better! You got this! 💪'],
            'fine': ['Glad to hear that! 😊 keep shining girlll'],
            'pain': ['Im sorry to hear that. Try using a warm compress or taking a warm bath 🛁'],
            'bloating': ['Tummy troubles? Try some light exercise or peppermint tea 🍵'],
            'nausea': ['Ginger tea or peppermint can help soothe nausea 🤢'],
            'cramps': ['I am sorry your in pain. Period cramps can be really tough. Want me to suggest some ways to ease them?'],
            'yeah': ['Sure! Here are some tips to help with cramps:\n1. Use a heating pad on your lower abdomen.\n2. Try gentle yoga or stretching.\n3. Drink plenty of water and herbal teas.\n4. Over-the-counter pain relievers can help if needed.\n5. Rest and relax as much as possible. Hope you feel better soon! 🌸'],
            'periods': ['Your period starts in 7 days. Stay hydrated and take care 🌺!'],
            'fertile': ['Your fertile window is from Day 12 to Day 16 of your cycle!'],
            'mood': ['If youre feeling stressed, try listening to some calming music 🎶!', 'Remember to breathe deeply and relax 🌿'],
            'tired': ['It sounds like you might need some rest. Take it easy today 💆‍♀️.'],
            'headache': ['Try drinking water, resting in a dark room, and using a cold compress on your forehead 🧊.'],
            'hunger': ['I recommend a healthy snack! How about some fruits or a smoothie? 🍎🥭'],
            'exercise': ['How about some light stretches or a short walk? A little movement can boost your mood! 🧘‍♀️'],
            'sleep': ['Good sleep is so important! Try to relax before bed, maybe a nice warm bath? 🛁'],
            'happy': ['Im glad to hear youre feeling happy! 😄', 'Spread that joy, girl! 🌟'],
            'sad': ['Im sorry youre feeling sad. Its okay to have these days. 💕'],
            'thank you': ['Youre welcome, lovely!'],
            'thanks': ['Youre welcome, lovely!'],
            'bye': ['Goodbye! Take care and stay fabulous! 🌸'],
        }
        user_input = user_input.lower()
        for keyword in responses:
            if keyword in user_input:
                return random.choice(responses[keyword])
        return "Sorry, I didn't catch that. Can you ask something else? 🌸"

    # ------------------------- REPORTS PAGE (MERGED SHOW_REPORT) -------------------------
    def show_reports(self):
        """Show period reports and logs"""
        self.hide_all_pages()
        self.reports_page = tk.Frame(self.root, bg="white")
        self.reports_page.place(x=0, y=0, width=1350, height=700)
        bg_path = "reports_bg.png"
        if os.path.exists(bg_path):
            self.reports_bg_img = Image.open(bg_path)
            self.reports_bg_img = self.reports_bg_img.resize((1350, 700), Image.LANCZOS)
            self.reports_bg_photo = ImageTk.PhotoImage(self.reports_bg_img)
            bg_label = tk.Label(self.reports_page, image=self.reports_bg_photo)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        title = tk.Label(self.reports_page, text="Period Reports & Logs", font=("Impact", 24, "bold"), fg="grey", bg="white")
        title.pack(pady=20)

        # Create scrollable frame for reports
        canvas = tk.Canvas(self.reports_page, bg="white")
        scrollbar = tk.Scrollbar(self.reports_page, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Get period logs from database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT log_date, symptoms, mood, flow FROM period_logs WHERE username=? ORDER BY log_date DESC", (self.current_user,))
        logs = c.fetchall()
        conn.close()

        if logs:
            for i, log in enumerate(logs):
                log_frame = tk.Frame(scrollable_frame, bg="#FFE4E1", relief="raised", bd=2)
                log_frame.pack(fill="x", padx=20, pady=5)
                
                date_label = tk.Label(log_frame, text=f"📅 ቀን\nDate: {log[0]}", font=("Arial", 12, "bold"), bg="#FFE4E1")
                date_label.pack(anchor="w", padx=10, pady=2)
                
                if log[1]:  # symptoms
                    symptoms_label = tk.Label(log_frame, text=f"🩺 ምልክቶች\nSymptoms: {log[1]}", font=("Arial", 10), bg="#FFE4E1", wraplength=800)
                    symptoms_label.pack(anchor="w", padx=10, pady=1)
                
                if log[2]:  # mood
                    mood_label = tk.Label(log_frame, text=f"😊 ስሜት\nMood: {log[2]}", font=("Arial", 10), bg="#FFE4E1", wraplength=800)
                    mood_label.pack(anchor="w", padx=10, pady=1)
                
                if log[3]:  # flow
                    flow_label = tk.Label(log_frame, text=f"🌊 ፍሰት\nFlow: {log[3]}", font=("Arial", 10), bg="#FFE4E1")
                    flow_label.pack(anchor="w", padx=10, pady=1)
        else:
            no_data_label = tk.Label(scrollable_frame, text="No period logs found. Start tracking your symptoms in the calendar! 🌸", 
                                   font=("Arial", 14), bg="white", fg="grey")
            no_data_label.pack(pady=50)

        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")
        
        tk.Button(self.reports_page, text="Back 🏠", font=("Arial", 14), fg="white", bg="#FFB6C1", command=self.show_home_page).pack(pady=20)


# ------------------------- STARTUP FUNCTIONS -------------------------
def show_splash_screen():
    """Show splash screen on startup"""
    splash_root = tk.Tk()
    splash_root.title("Flower Tracker")

    width = 700
    height = 600
    screen_width = splash_root.winfo_screenwidth()
    screen_height = splash_root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    splash_root.geometry(f"{width}x{height}+{x}+{y}")
    splash_root.overrideredirect(True)

    image_path = "eldu.png"
    if os.path.exists(image_path):
        bg_image = Image.open(image_path)
        bg_image = bg_image.resize((width, height), Image.LANCZOS)
        bg_photo = ImageTk.PhotoImage(bg_image)
        bg_label = tk.Label(splash_root, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        animated_bg = "#F09CC6"
    else:
        splash_root.configure(bg="black")
        animated_bg = "black"

    full_text = "እንኳን ወደ ውቢት's የወር አበባ መከታተያ በሰላም መጡ\nWelcome to Flower Tracker. Enjoy! 🌸"
    animated_label = tk.Label(splash_root, text="", font=("Comic Sans MS", 18, "bold"), fg="#B1769F", bg=animated_bg)
    animated_label.place(relx=0.5, rely=0.9, anchor="center")

    def animate_text(index=0):
        if index < len(full_text):
            animated_label.config(text=full_text[:index + 1])
            splash_root.after(100, animate_text, index + 1)

    animate_text()
    splash_root.after(4000, lambda: [splash_root.destroy(), show_login_window()])
    splash_root.mainloop()

def show_login_window():
    """Show main login window"""
    root = tk.Tk()
    app = FlowerTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    show_splash_screen()


