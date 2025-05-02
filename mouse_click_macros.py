#!/usr/bin/env python3

import logging
import time
from pynput import mouse, keyboard
from pynput.mouse import Button

mouse_controller = mouse.Controller()

# Setup logging to console only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s • %(message)s',
    datefmt='%H:%M:%S'
)

print("[DEBUG] Mouse logger starting. Logging to terminal only.")

# Global list to store click locations
click_locations = []

def on_click(x, y, button, pressed):
    if pressed:
        click_locations.append((x, y))
        print(f"[INFO] Recorded click location #{len(click_locations)}: ({x}, {y})")
        logging.info(f"Recorded click location #{len(click_locations)}: ({x}, {y})")

def on_press(key):
    try:
        if key.char.lower() == 'l':
            if not click_locations:
                print("[WARN] No click locations have been recorded yet.")
                logging.warning("No click locations have been recorded yet.")
                return
            print("[INFO] 'l' key pressed. Executing pre-recorded clicks sequence.")
            logging.info("Executing pre-recorded clicks sequence.")

            for index, location in enumerate(click_locations, start=1):
                mouse_controller.position = location
                mouse_controller.click(Button.left)
                print(f"[INFO] Clicked at {location} (Step {index}/{len(click_locations)})")
                logging.info(f"Clicked at {location} (Step {index}/{len(click_locations)})")
                time.sleep(0.5)  # delay between clicks

            # Move back to the first location
            mouse_controller.position = click_locations[0]
            # Clear the list for new sequence recording
            click_locations.clear()
    except AttributeError:
        # Ignore special keys without a char attribute
        pass

if __name__ == "__main__":
    # Start the mouse listener thread
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.daemon = True
    mouse_listener.start()

    # Start a keyboard listener thread to capture when the user presses "l"
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.daemon = True
    keyboard_listener.start()

    print("[TIP] Ensure your OS allows Python to monitor input events.\n")

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mouse_listener.stop()
        keyboard_listener.stop()
        print("\nStopped.")
