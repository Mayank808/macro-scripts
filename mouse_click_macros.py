import time
import logging
import threading
import json
import os
from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key

# Setup logging to console only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s • %(message)s',
    datefmt='%H:%M:%S'
)

print("[DEBUG] Mouse logger starting. Logging to terminal only.")

# Global variables/state flags:
macros = {}                # maps user-specified keys to recorded macro lists
recording = False          # indicates if we are recording a macro now
click_locations = []       # holds the currently recording macro’s click coordinates
recording_key_bind = '`'       # key to start recording
macros_file = "macros.json" # file to save macros
awaiting_assignment = False  # indicates we are waiting for a key to assign the macro
stop_event = threading.Event() # event to stop the script
mouse_controller = mouse.Controller() # mouse controller instance

# Function to load macros from a JSON file
def load_macros():
    print("[DEBUG] Loading macros from file.")
    if os.path.exists(macros_file):
        try:
            with open(macros_file, "r") as f:
                loaded = json.load(f)
                # Convert each coordinate list back to tuples for compatibility
                for key, value in loaded.items():
                    loaded[key] = [tuple(coord) for coord in value]
                return loaded
        except Exception as e:
            logging.error(f"Error loading macros: {e}")
    return {}

# Function to save macros to a JSON file
def save_macros():
    try:
        with open(macros_file, "w") as f:
            json.dump(macros, f)
            logging.info("Macros saved successfully.")
    except Exception as e:
        logging.error(f"Error saving macros: {e}")

# Function to handle mouse clicks
def on_click(x, y, button, pressed):
    if pressed and recording:
        click_locations.append((x, y))
        print(f"[INFO] Recorded click location #{len(click_locations)}: ({x}, {y})")
        logging.info(f"Recorded click location #{len(click_locations)}: ({x}, {y})")

# Function to handle keyboard events
def on_press(key):
    global recording, click_locations, macros, awaiting_assignment

    # Handle non-character keys first
    if key == Key.esc:
        if recording:
            # Stop recording and prompt for macro assignment
            recording = False
            awaiting_assignment = True
            print("[INFO] Recording stopped. Please press a key to assign this macro.")
            logging.info("Recording stopped. Awaiting macro assignment.")
            return
        elif awaiting_assignment:
            # Cancel macro assignment
            awaiting_assignment = False
            print("[INFO] Macro assignment cancelled.")
            logging.info("Macro assignment cancelled.")
            return

    try:
        char = key.char.lower()
    except AttributeError:
        return

    print(f"[DEBUG] Key pressed: {char}")
    print(f"[DEBUG] Is macro key: {char in macros}")
    # Assign macro when awaiting assignment
    if awaiting_assignment:
        if char in macros:
            print(f"[INFO] Overwriting existing macro assigned to key '{char}'.")
            logging.info(f"Overwriting macro assigned to key '{char}'.")
        # Convert each coordinate tuple to a list for JSON compatibility
        macros[char] = click_locations.copy()
        print(f"[INFO] Macro assigned to key '{char}' with {len(click_locations)} steps.")
        logging.info(f"Macro assigned to key '{char}' with {len(click_locations)} steps.")
        click_locations.clear()
        awaiting_assignment = False
        save_macros()
        return

    # Start recording a new macro
    if char == recording_key_bind:
        recording = True
        click_locations.clear()  # start fresh recording
        print("[INFO] Recording started. Mouse clicks will now be recorded.")
        logging.info("Recording started.")
        return

    # Replay a macro if the key is mapped
    if char in macros:
        # Convert stored list of lists back to tuples
        macro = macros[char]
        if not macro:
            print("[WARN] Macro is empty, cannot replay.")
            logging.warning("Macro is empty")
            return
        print(f"[INFO] '{char}' key pressed. Executing assigned macro with {len(macro)} steps.")
        logging.info(f"Executing macro assigned to key '{char}' with {len(macro)} steps.")
        for index, location in enumerate(macro):
            mouse_controller.position = location
            time.sleep(0.001)
            mouse_controller.click(Button.left)
            time.sleep(0.001)  # delay between clicks
            print(f"[INFO] Clicked at {location} (Step {index}/{len(macro)})")
            logging.info(f"Clicked at {location} (Step {index}/{len(macro)})")
            time.sleep(0.5)  # delay between clicks
        # Move back to the first location
        mouse_controller.position = macro[0]
        return

def main():
    global macros, stop_event
    # Load existing macros and print available key bindings.
    macros = load_macros()
    if macros:
        print("[INFO] Available macros loaded:")
        for keybind, locs in macros.items():
            print(f"{keybind} -> Steps {len(locs)} ")
    else:
        print(f"[INFO] No macros found. Start recording by pressing {recording_key_bind}.")

    # Start the mouse listener thread
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.daemon = True
    mouse_listener.start()

    # Start the keyboard listener thread to capture keystrokes
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.daemon = True
    keyboard_listener.start()

    print("[TIP] Ensure your OS allows Python to monitor input events.\n")
    
    # Keep the main thread alive
    try:
        stop_event.wait()
    except KeyboardInterrupt:
        mouse_listener.stop()
        keyboard_listener.stop()
        stop_event.set()
        print("\nStopped Program.")


if __name__ == "__main__":
    main()