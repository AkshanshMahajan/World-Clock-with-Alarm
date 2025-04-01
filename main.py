from datetime import datetime
import pytz
from tkinter import *
from tkinter import ttk, messagebox
import winsound
import uuid  # For unique alarm IDs

# Create the main window
root = Tk()
root.title("World Clock with Alarm")
root.geometry("880x600")
root.resizable(False, False)
root.configure(bg="#2C3E50")

# Custom Fonts
font_large = ("Arial", 24, "bold")
font_medium = ("Arial", 18)
font_small = ("Arial", 14)

# Add a Frame for cleaner layout
main_frame = Frame(root, bg="#34495E", bd=10, relief=RAISED, width=960, height=550)
main_frame.pack_propagate(False)
main_frame.grid(row=0, column=0, padx=20, pady=20)

# Configure grid for proper alignment
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=3)
main_frame.columnconfigure(2, weight=1)

# Time Zone Selection
time_zones = pytz.all_timezones
selected_timezone = StringVar()
selected_timezone.set("Asia/Kolkata")

# Time Display
time_label = Label(main_frame, text="", bg="#34495E", fg="white", font=font_large)
time_label.grid(row=0, column=0, columnspan=3, pady=10)

# City Label
city_label = Label(main_frame, text="", bg="#34495E", fg="lightgrey", font=font_medium)
city_label.grid(row=1, column=0, columnspan=3, pady=5)

# Timezone Dropdown with Autocomplete
timezone_label = Label(main_frame, text="Select Timezone:", bg="#34495E", fg="white", font=font_small)
timezone_label.grid(row=2, column=0, padx=10, pady=5, sticky=W)

timezone_menu = ttk.Combobox(main_frame, values=time_zones, textvariable=selected_timezone,
                            state="normal", font=font_small, width=30)
timezone_menu.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

def update_timezone():
    global current_timezone
    current_timezone = selected_timezone.get()
    update_time()

update_button = Button(main_frame, text="Update Timezone", bg="#3498DB", fg="white",
                       font=font_small, command=update_timezone, relief=SOLID, bd=2, width=15)
update_button.grid(row=2, column=2, padx=(10, 20), pady=5, sticky=E)

# Autocomplete with Debounce
debounce_timer = None

def update_timezone_suggestions(event):
    global debounce_timer
    if debounce_timer:
        root.after_cancel(debounce_timer)
    debounce_timer = root.after(300, filter_timezones)

def filter_timezones():
    search_term = timezone_menu.get().lower()
    if search_term == "":
        timezone_menu['values'] = time_zones
    else:
        filtered_timezones = [tz for tz in time_zones if search_term in tz.lower()]
        timezone_menu['values'] = filtered_timezones[:20]

timezone_menu.bind('<KeyRelease>', update_timezone_suggestions)
timezone_menu['state'] = 'normal'

# Alarm Section
alarm_frame = Frame(main_frame, bg="#1ABC9C", bd=5, relief=GROOVE)
alarm_frame.grid(row=3, column=0, columnspan=3, pady=15, sticky="ew")

# Alarm Inputs
Label(alarm_frame, text="Set Alarm (HH:MM:SS AM/PM):", bg="#1ABC9C", fg="white", font=font_small).grid(row=0, column=0, padx=10, pady=5)

hour_var = StringVar()
minute_var = StringVar()
second_var = StringVar()
ampm_var = StringVar()
ampm_var.set("AM")

hour_entry = Entry(alarm_frame, textvariable=hour_var, width=5, font=font_small, justify="center")
minute_entry = Entry(alarm_frame, textvariable=minute_var, width=5, font=font_small, justify="center")
second_entry = Entry(alarm_frame, textvariable=second_var, width=5, font=font_small, justify="center")
ampm_menu = ttk.Combobox(alarm_frame, textvariable=ampm_var, values=["AM", "PM"], state="readonly", width=5, font=font_small)

hour_entry.grid(row=0, column=1, padx=5, pady=5)
minute_entry.grid(row=0, column=2, padx=5, pady=5)
second_entry.grid(row=0, column=3, padx=5, pady=5)
ampm_menu.grid(row=0, column=4, padx=(5, 20), pady=5)

# Alarm Control Variables
alarms_data = {}
alarm_stop_flags = {}
alarm_timers = {}

def cancel_alarm(alarm_id):
    global alarms_data, alarm_stop_flags, alarm_timers
    if alarm_id in alarms_data:
        alarm_stop_flags[alarm_id] = True
        if alarm_id in alarm_timers:
            root.after_cancel(alarm_timers[alarm_id])
            del alarm_timers[alarm_id]
        alarms_data[alarm_id]['label'].destroy()
        alarms_data[alarm_id]['button'].destroy()
        del alarms_data[alarm_id]
        del alarm_stop_flags[alarm_id]
        
        for idx, (alarm_id, data) in enumerate(alarms_data.items()):
            data['label'].grid(row=4 + idx, column=0, columnspan=2, pady=5, sticky="w")
            data['button'].grid(row=4 + idx, column=2, padx=(10, 20), pady=5, sticky="w")

def show_alarm_popup(alarm_id):
    popup = Toplevel(root)
    popup.title("⏰ Alarm Ringing!")
    popup.geometry("300x150")
    popup.configure(bg="#E74C3C")
    popup.transient(root)
    popup.grab_set()

    label = Label(popup, text="⏰ Alarm Time!", bg="#E74C3C", fg="white", font=("Arial", 18, "bold"))
    label.pack(pady=20)

    stop_button = Button(popup, text="Stop Alarm", bg="#3498DB", fg="white", font=("Arial", 14),
                         command=lambda: stop_alarm(alarm_id, popup), relief=SOLID, bd=2, width=15)
    stop_button.pack(pady=10)

    popup.attributes('-topmost', True)

def set_alarm():
    global alarms_data, alarm_stop_flags, alarm_timers
    if len(alarms_data) >= 5:
        messagebox.showwarning("Maximum Alarms Reached", "You can set a maximum of 5 alarms.")
        return

    try:
        alarm_hour = int(hour_var.get())
        alarm_minute = int(minute_var.get())
        alarm_second = int(second_var.get())
        alarm_ampm = ampm_var.get()

        alarm_time = f"{alarm_hour:02d}:{alarm_minute:02d}:{alarm_second:02d}"
        alarm_id = str(uuid.uuid4())

        if alarm_ampm == "PM" and alarm_hour != 12:
            alarm_hour += 12
        if alarm_ampm == "AM" and alarm_hour == 12:
            alarm_hour = 0

        alarm_label = Label(main_frame, text=f"Alarm: {alarm_time} ({alarm_ampm})", bg="#1ABC9C", fg="white", font=font_small)
        alarm_time = f"{alarm_hour:02d}:{alarm_minute:02d}:{alarm_second:02d}"
        alarm_label.grid(row=4 + len(alarms_data), column=0, columnspan=2, pady=5, sticky="w")

        cancel_button = Button(main_frame, text="Cancel", bg="#E74C3C", fg="white", font=font_small,
                               command=lambda: cancel_alarm(alarm_id), relief=SOLID, bd=2, width=15)
        cancel_button.grid(row=4 + len(alarms_data), column=2, padx=(10, 20), pady=5, sticky="w")

        alarms_data[alarm_id] = {'label': alarm_label, 'button': cancel_button}
        alarm_stop_flags[alarm_id] = False

        def alarm_loop():
            tz = pytz.timezone(selected_timezone.get())
            def check_alarm():
                if not alarm_stop_flags[alarm_id]:
                    current_time = datetime.now(tz).strftime("%H:%M:%S")
                    if current_time == alarm_time:
                        winsound.PlaySound("resources/alarm.wav", winsound.SND_ASYNC)
                        alarm_timers[alarm_id] = root.after(10000, stop_alarm, alarm_id)
                        show_alarm_popup(alarm_id)
                    else:
                        alarm_timers[alarm_id] = root.after(1000, check_alarm)
                else:
                    cancel_alarm(alarm_id)

            check_alarm()

        alarm_loop()

    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numbers for hours, minutes, and seconds.")

def stop_alarm(alarm_id, popup=None):
    winsound.PlaySound(None, winsound.SND_ASYNC)
    alarm_stop_flags[alarm_id] = True
    cancel_alarm(alarm_id)
    if popup:
        popup.destroy()  # Close the popup window

Button(alarm_frame, text="Set Alarm", bg="#E74C3C", fg="white",
       font=font_small, command=set_alarm, relief=SOLID, bd=2, width=15).grid(row=0, column=5, padx=(10, 20), pady=5)

# Auto-Update Time
current_timezone = selected_timezone.get()

def update_time():
    try:
        tz = pytz.timezone(current_timezone)
        current_time = datetime.now(tz).strftime("%I:%M:%S %p")
        time_label.config(text=current_time)
        city_label.config(text=current_timezone.split("/")[-1])
    except Exception as e:
        print(f"Error updating time: {e}")
        city_label.config(text="Invalid Timezone")
    root.after(1000, update_time)

# Initialize Time
update_time()

# Run the App
root.mainloop()
