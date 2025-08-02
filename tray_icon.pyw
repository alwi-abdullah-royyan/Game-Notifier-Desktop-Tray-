from pystray import Icon, MenuItem as item, Menu
from PIL import Image
import threading

def start_tray_icon(stop_event):
    def on_exit(icon, item):
        stop_event.set()
        icon.stop()

    def setup():
        icon_image = Image.open('1.ico')
        
        icon = Icon(
            "GameNotifier",
            icon=icon_image,
            menu=Menu(item("Exit", on_exit))
        )
        icon.run()

    # Run the tray icon in a separate thread
    threading.Thread(target=setup, daemon=True).start()

