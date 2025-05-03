import logging
import time
from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key

mouse_controller = mouse.Controller()

# Setup logging to console only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s • %(message)s',
    datefmt='%H:%M:%S'
)

print("[DEBUG] Mouse logger starting. Logging to terminal only.")

# Global variables/state flags:
click_locations = []       # holds the currently recording macro’s click coordinates
macros = {}                # maps user-specified keys to recorded macro lists
recording = False          # indicates if we are recording a macro now
awaiting_assignment = False  # indicates we are waiting for a key to assign the macro

def on_click(x, y, button, pressed):
    global recording
    if pressed and recording:
        click_locations.append((x, y))
        print(f"[INFO] Recorded click location #{len(click_locations)}: ({x}, {y})")
        logging.info(f"Recorded click location #{len(click_locations)}: ({x}, {y})")

def on_press(key):
    global recording, click_locations, macros, awaiting_assignment

    # Handle non-character keys first
    if key == Key.esc:
        if recording:
            # stop current recording and prompt for macro assignment
            recording = False
            awaiting_assignment = True
            print("[INFO] Recording stopped. Please press a key to assign this macro.")
            logging.info("Recording stopped. Awaiting macro assignment.")
        return

    try:
        char = key.char.lower()
    except AttributeError:
        return

    # If we are waiting to assign a macro, assign the current recording to the pressed key
    if awaiting_assignment:
        if char in macros:
            print(f"[INFO] Overwriting existing macro assigned to key '{char}'.")
            logging.info(f"Overwriting macro assigned to key '{char}'.")
        macros[char] = click_locations.copy()  # store a copy of the recorded macro
        print(f"[INFO] Macro assigned to key '{char}' with {len(click_locations)} steps.")
        logging.info(f"Macro assigned to key '{char}' with {len(click_locations)} steps.")
        click_locations.clear()
        awaiting_assignment = False
        return

    # Start recording a new macro
    if char == 's':
        recording = True
        click_locations.clear()  # start fresh recording
        print("[INFO] Recording started. Mouse clicks will now be recorded.")
        logging.info("Recording started.")
        return

    # Check if the pressed key maps to a recorded macro and replay it.
    if char in macros:
        macro = macros[char]
        if not macro:
            print("[WARN] Macro is empty, cannot replay.")
            logging.warning("Macro is empty")
            return
        print(f"[INFO] '{char}' key pressed. Executing assigned macro with {len(macro)} steps.")
        logging.info(f"Executing macro assigned to key '{char}' with {len(macro)} steps.")
        for index, location in enumerate(macro, start=1):
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

if __name__ == "__main__":
    # Start the mouse listener thread
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.daemon = True
    mouse_listener.start()

    # Start the keyboard listener thread to capture when the user presses keys
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
