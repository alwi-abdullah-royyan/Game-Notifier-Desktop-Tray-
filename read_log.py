import os
from tkinter import Tk, messagebox

def read_logs():
    root = Tk()
    root.withdraw()

    log_dir = "logs"
    if not os.path.exists(log_dir):
        messagebox.showinfo("Log Reader", "No logs found.")
        root.destroy()
        return

    log_files = [f for f in os.listdir(log_dir) if f.startswith("log_") and f.endswith(".txt")]
    if not log_files:
        messagebox.showinfo("Log Reader", "No log files to read.")
        root.destroy()
        return

    # Optional: sort so newest logs come first
    log_files.sort(reverse=True)

    logs_combined = []
    for filename in log_files:
        full_path = os.path.join(log_dir, filename)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    logs_combined.append(f"--- {filename} ---\n{content}")
                else:
                    logs_combined.append(f"--- {filename} ---\n(Log file is empty.)")
        except Exception as e:
            logs_combined.append(f"Error reading {filename}: {e}")

    combined_text = "\n\n".join(logs_combined)

    # Show in popup
    messagebox.showinfo("Game Logs", combined_text[:5000])  # Truncate if too long

    root.destroy()
