# ─── Standard Library ─────────────────────────────────────────────
import os
import sys
import time
import json
import gzip
import shutil
import threading
import logging
from datetime import datetime
from tkinter import Tk, messagebox
from logging.handlers import RotatingFileHandler

# ─── Third-Party Libraries ────────────────────────────────────────
import requests
from PIL import Image
from pystray import Icon, MenuItem, Menu
from win10toast import ToastNotifier

# ─── Local Modules ────────────────────────────────────────────────
from read_log import read_logs
from analyze import analyze_upload_frequencies

log_handler = RotatingFileHandler(
    'error.log',            # File name
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3              # Keep 3 backups: error.log.1, error.log.2, etc.
)
log_handler.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(message)s')
log_handler.setFormatter(log_formatter)
# Set up the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
# Optional: Remove default stderr logging if not needed
logger.propagate = False

with open("config.json", "r") as f:
    config = json.load(f)

API_URL = config["API_URL"]

DATA_FILE = 'prev_data.json'
RUNNING = True
toaster = ToastNotifier()
missed_games = 0
icon_ref = None  # So main thread can access the tray icon
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

def compress_old_logs():
    for i in range(1, 4):  # Adjust range to match backupCount
        file_name = f'error.log.{i}'
        compressed_file = file_name + '.gz'
        
        # Only compress if the uncompressed file exists and compressed version doesn't
        if os.path.exists(file_name) and not os.path.exists(compressed_file):
            try:
                with open(file_name, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(file_name)  # Delete the original after compression
                print(f"Compressed {file_name} → {compressed_file}")
            except Exception as e:
                print(f"Failed to compress {file_name}: {e}")

def load_previous_ids():
    try:
        with open(DATA_FILE, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_current_ids(ids_set):
    with open(DATA_FILE, 'w') as f:
        json.dump(list(ids_set), f)

def show_notification(title, message):
    global missed_games
    missed_games += 1
    toaster.show_toast(title, message, duration=10, threaded=True)
    update_tray_icon()

def update_tray_icon():
    global icon_ref, missed_games
    if icon_ref:
        try:
            icon_image = Image.open("1_alert.ico" if missed_games else "1.ico")
            icon_ref.icon = icon_image
            icon_ref.menu = Menu(
                MenuItem(lambda text: f"New games: {missed_games}", None, enabled=False),
                MenuItem("read log", read_logs),
                MenuItem("Clear notification", clear_notifications),
                MenuItem("read update/upload pattern", analyze),
                MenuItem('Quit', on_quit)
            )
            
            icon_ref.update_menu()
        except Exception as e:
            logging.error("Tray update failed", exc_info=True)

        
def clear_notifications(icon, item):
    global missed_games
    missed_games = 0
    update_tray_icon()
    if os.path.exists(log_dir):
        for file in os.listdir(log_dir):
            if file.startswith("log_"):
                os.remove(os.path.join(log_dir, file))

def analyze():
    root = Tk()
    root.withdraw()  # Hide empty root window

    try:
        info = analyze_upload_frequencies()
        messagebox.showinfo("Upload Pattern", info)
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        root.destroy()

def log_new_games(games):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{log_dir}/log_{now}.txt"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"[{now}] {len(games)} new game(s) detected:\n")
        for game in games:
            f.write(f" - {game['title']} by {game['creator']} (ID: {game['thread_id']})\n")
        f.write("\n")
        
def log_upload_timestamps(new_games, log_path="upload_timestamps.log"):
    with open(log_path, "a", encoding="utf-8") as f:
        for game in new_games:
            ts = game["ts"]
            dt = datetime.fromtimestamp(ts)
            hour = dt.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts},{hour}\n")
            
def check_games_loop():
    known_ids = load_previous_ids()
    retries = 5
    attempt = 0 
    consecutive_failures = 0
    while RUNNING:
        try:
            retry = False
            timestamp = int(time.time() * 1000) - (attempt * 60000)  # Decrease by 60 seconds per retry
            print(f"Attempt {attempt + 1}: Trying timestamp {timestamp}")
            
            response = requests.get(f"{API_URL}{timestamp}")
            response.raise_for_status()
            
            data = response.json()
            game_list = data["msg"]["data"]
            current_ids = set(game["thread_id"] for game in game_list)

            new_ids = current_ids - known_ids
            new_games = [game for game in game_list if game["thread_id"] in new_ids]

            if new_games:
                log_new_games(new_games)
                log_upload_timestamps(new_games)
                show_notification("New Game Alert!", f"There are {len(new_games)} new game(s) available!")
                known_ids.update(new_ids)
                save_current_ids(known_ids)
            
            # Reset attempts after success
            consecutive_failures = 0
        except Exception as e:
            retry = True
            print(f"Error: {e}")
            if consecutive_failures >= 5:
                logger.error("Exception in check_games_loop", exc_info=True)
                show_notification("Game Notifier Error", "Too many failed attempts to fetch new games. Check your internet or the API.")
                consecutive_failures = 0
                compress_old_logs()
                
        if retry and retries > 0:
            retries -= 1
            attempt += 1
            time.sleep(1)
            continue

        consecutive_failures += 1
        retries = 5
        attempt = 0 
        time.sleep(60)



def on_quit(icon, item):
    global RUNNING
    RUNNING = False
    icon.stop()

def setup_tray():
    global icon_ref
    image = Image.open("1.ico")
    icon_ref = Icon("GameNotifier", icon=image, title="Game Notifier")

    icon_ref.menu = Menu(
        MenuItem(lambda text: f"New games: {missed_games}", None, enabled=False),
        MenuItem("read log", read_logs),
        MenuItem("Clear notification", clear_notifications),
        MenuItem("read update/upload pattern", analyze),
        MenuItem('Quit', on_quit)
    )
    icon_ref.run()


# Start tray icon in a separate thread
def start_tray_icon():
    tray_thread = threading.Thread(target=setup_tray, daemon=True)
    tray_thread.start()

if __name__ == '__main__':
    # Start the tray icon
    start_tray_icon()

    # Start checker in a separate thread
    checker_thread = threading.Thread(target=check_games_loop, daemon=True)
    checker_thread.start()

    # Wait for threads to complete
    while RUNNING:
        time.sleep(1)  # Keep the main thread alive while the other threads run