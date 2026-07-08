"""
Epic Seven Story Auto-Progression Tool
=======================================
Exactly mirrors E7SecretShopRefresh.py's window management:
- Resizes emulator window to 906x539 and moves it to (0,0).
- Clicks using fixed percentage-based coordinates relative to the window.
- Uses template matching ONLY for:
  - Detecting the lobby/ready button (1.png) to know when to start/end cycles.
  - Detecting the Skip button (newskip.png) and Confirm Skip (comfirmskipnew.png) during cutscenes.
- Handles battle completion by tapping the center of the screen every 10 seconds.

Press ESC to stop and exit the tool at any time.
"""

import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image, ImageGrab
import os
import sys
import time
import threading
import re

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pyautogui
import pygetwindow as gw
import cv2
import numpy as np
import keyboard

# Disable pyautogui fail-safe
pyautogui.FAILSAFE = False


# ============================================================================
# Configuration
# ============================================================================

STORY_ASSETS_DIR = 'story-assets'

# Template files needed for scanning (matching the user's files)
TEMPLATES = {
    'ready':        {'file': '1.png',               'desc': 'Ready (lobby)'},
    'skip':         {'file': 'newskip.png',         'desc': 'Skip button'},
    'confirm_skip': {'file': 'comfirmskipnew.png',  'desc': 'Confirm Skip popup'},
}

RECOGNIZE_TITLES = {
    'Epic Seven',
    'BlueStacks App Player',
    'LDPlayer',
    'MuMu Player 12',
    'Google Play Games on PC Emulator',
}


# ============================================================================
# Story Progression Engine
# ============================================================================

class StoryProgression:
    def __init__(self, title_name, callback=None, tk_instance=None):
        self.title_name = title_name
        self.callback = callback or (lambda: print('Terminated!'))
        self.tk_instance = tk_instance
        self.loop_active = False
        self.loop_finish = True
        self.mouse_sleep = 0.3
        self.screenshot_sleep = 0.3
        self.match_threshold = 0.70
        self.battle_wait_max = 240  # Maximum time for one full run
        self.cycles_completed = 0

        # Find window
        windows = gw.getWindowsWithTitle(self.title_name)
        self.window = next((w for w in windows if w.title == self.title_name), None)

        # Load templates
        self.template_images = {}
        for key, info in TEMPLATES.items():
            path = os.path.join(STORY_ASSETS_DIR, info['file'])
            if os.path.exists(path):
                img = cv2.imread(path)
                if img is not None:
                    # Convert to RGB (ImageGrab standard)
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    self.template_images[key] = img_rgb
                    print(f'  [OK] Loaded template: {info["desc"]} ({info["file"]})')
                else:
                    print(f'  [FAIL] Cannot read template: {path}')
            else:
                print(f'  [MISS] Template not found: {path}')

    def start(self):
        if self.loop_active or not self.loop_finish:
            return
        self.loop_active = True
        self.loop_finish = False

        # Run listener and main loop in background threads
        kb_thread = threading.Thread(target=self._checkKeyPress, daemon=True)
        main_thread = threading.Thread(target=self._mainLoop, daemon=True)
        kb_thread.start()
        main_thread.start()

    def _checkKeyPress(self):
        """Esc key stops and closes the application."""
        while self.loop_active and not self.loop_finish:
            if keyboard.is_pressed('esc'):
                self.loop_active = False
                print('ESC pressed - exiting application...')
                if self.tk_instance:
                    self.tk_instance.root.after(0, self.tk_instance.close_app)
                sys.exit(0)
            time.sleep(0.1)

    def takeScreenshot(self):
        """Take screenshot of the emulator window."""
        try:
            try:
                self.window.activate()
            except Exception:
                pass

            region = [self.window.left, self.window.top,
                      self.window.width, self.window.height]
            screenshot = ImageGrab.grab(
                bbox=(region[0], region[1],
                      region[2] + region[0], region[3] + region[1]),
                all_screens=True
            )
            screenshot = np.array(screenshot)
            return screenshot
        except Exception as e:
            print(f'Screenshot error: {e}')
            return None

    def findTemplate(self, screenshot, template_key):
        """Find template using template matching."""
        if template_key not in self.template_images:
            return None

        template = self.template_images[template_key]
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= self.match_threshold:
            # Return absolute coordinate center
            x = self.window.left + max_loc[0] + template.shape[1] // 2
            y = self.window.top + max_loc[1] + template.shape[0] // 2
            return (x, y, max_val)
        return None

    def clickAt(self, x, y, desc=''):
        """Move mouse and click."""
        pyautogui.moveTo(x, y)
        pyautogui.click()
        time.sleep(self.mouse_sleep)
        timestamp = time.strftime('%H:%M:%S')
        print(f'[{timestamp}] CLICK ({x},{y}) - {desc}')

    def log(self, text):
        timestamp = time.strftime('%H:%M:%S')
        msg = f'[{timestamp}] {text}'
        print(msg)
        if self.tk_instance:
            # Update status text in the GUI
            self.tk_instance.root.after(0, lambda: self.tk_instance.update_status(text))

    # ============================================================================
    # Coordinates mapping relative to 906x539 window
    # ============================================================================

    def get_coords(self, rx, ry):
        """Map window-relative ratios to screen coordinates."""
        x = self.window.left + int(self.window.width * rx)
        y = self.window.top + int(self.window.height * ry)
        return x, y

    def click_ready(self):
        # Ready / Select Team / Start Quest / End Battle (Bottom right green button)
        x, y = self.get_coords(0.87, 0.91)
        self.clickAt(x, y, 'Green Button (Bottom Right)')

    def click_skip(self):
        # Skip button on top right of cutscenes
        x, y = self.get_coords(0.93, 0.08)
        self.clickAt(x, y, 'Skip Button')

    def click_confirm_skip(self):
        # Confirm Skip button on popup dialog
        x, y = self.get_coords(0.58, 0.65)
        self.clickAt(x, y, 'Confirm Skip')

    def click_cancel_friend(self):
        # Cancel Friend Request button (left popup option)
        x, y = self.get_coords(0.40, 0.62)
        self.clickAt(x, y, 'Cancel Friend Request')

    def click_center(self, desc='Center Tap'):
        # Click center of screen
        x, y = self.get_coords(0.50, 0.50)
        self.clickAt(x, y, desc)

    # ============================================================================
    # Loops
    # ============================================================================

    def _mainLoop(self):
        # Resize window exactly like SecretShopRefresh
        try:
            if self.window.isMaximized or self.window.isMinimized:
                self.window.restore()
            self.window.moveTo(0, 0)
            self.window.resizeTo(906, 539)
            self.log('Resized emulator window to 906x539 at (0,0)')
        except Exception as e:
            self.log(f'Window resizing warning: {e}')

        time.sleep(1.0)

        try:
            self.window.activate()
        except Exception:
            pass

        # Save a debug screenshot to ensure it's correct
        ss = self.takeScreenshot()
        if ss is not None:
            debug_path = os.path.join(STORY_ASSETS_DIR, 'debug_screenshot.png')
            cv2.imwrite(debug_path, cv2.cvtColor(ss, cv2.COLOR_RGB2BGR))
            self.log(f'Debug screenshot saved to {debug_path}')

        start_time = time.time()

        try:
            self._cycleLoop()
        except Exception as e:
            self.log(f'Execution Error: {e}')
            import traceback
            traceback.print_exc()

        elapsed = time.time() - start_time
        mins, secs = int(elapsed // 60), int(elapsed % 60)
        self.log(f'Finished! Cycles: {self.cycles_completed} | Time: {mins}m {secs}s')

        self.loop_active = False
        self.loop_finish = True
        self.callback()

    def _cycleLoop(self):
        while self.loop_active:
            n = self.cycles_completed + 1
            
            # Wait 5 seconds between loops to allow the lobby to load
            if self.cycles_completed > 0:
                self.log('Waiting 5s for the lobby to load before starting the next cycle...')
                time.sleep(5.0)

            self.log(f'=== CYCLE {n} ===')

            # 0. Wait for Ready Button (Lobby detector)
            self.log('Waiting to be in lobby (detecting Ready)...')
            lobby_wait = time.time()
            found_lobby = False
            while self.loop_active and (time.time() - lobby_wait) < 15:
                ss = self.takeScreenshot()
                if ss is not None and self.findTemplate(ss, 'ready') is not None:
                    found_lobby = True
                    break
                time.sleep(1.0)
            
            if not found_lobby:
                self.log('Lobby Ready button (1.png) not found. Proceeding anyway...')

            # 1. Click Ready
            self.log('Step 1: Click Ready')
            self.click_ready()
            time.sleep(1.5)

            # 2. Click Select Team
            if not self.loop_active: break
            self.log('Step 2: Click Select Team')
            self.click_ready()
            time.sleep(1.5)

            # 3. Click Start Quest
            if not self.loop_active: break
            self.log('Step 3: Click Start Quest')
            self.click_ready()
            time.sleep(5.0)  # Wait longer for loading & potential start cutscenes

            # 4. Skip cutscenes and auto-tap every 10 seconds until back to lobby
            if not self.loop_active: break
            self.log('Step 4: Battle & Auto-tap Loop started')
            self._battleLoop()

            self.cycles_completed += 1
            self.log(f'Cycle {n} completed successfully!')

    def _battleLoop(self):
        battle_start = time.time()
        last_10s_click = time.time()
        
        while self.loop_active:
            # Battle timeout safety (e.g. if we get stuck or energy runs out)
            if (time.time() - battle_start) > self.battle_wait_max:
                self.log(f'Battle loop timeout ({self.battle_wait_max}s)')
                break

            ss = self.takeScreenshot()
            if ss is None:
                time.sleep(1.0)
                continue

            # A. Check if we are back in the lobby (meaning battle is finished and cycle is over)
            # We wait at least 20 seconds of battle time before checking lobby to avoid false detections
            if (time.time() - battle_start) > 20:
                if self.findTemplate(ss, 'ready') is not None:
                    self.log('Ready button detected! Back to lobby.')
                    break

            # B. Check if Skip button is visible
            skip_res = self.findTemplate(ss, 'skip')
            if skip_res is not None:
                self.log('Skip button detected! Clicking Skip.')
                self.click_skip()
                time.sleep(0.5)
                self.click_confirm_skip()
                time.sleep(1.0)
                continue

            # C. Check if Confirm Skip popup is visible directly
            confirm_res = self.findTemplate(ss, 'confirm_skip')
            if confirm_res is not None:
                self.log('Confirm Skip popup detected! Clicking Confirm.')
                self.click_confirm_skip()
                time.sleep(1.0)
                continue

            # D. Every 10 seconds: Click center, Cancel Friend, and End Battle Confirm
            # This handles clear stage screens, tap to close, friend requests, and results screen.
            if (time.time() - last_10s_click) >= 10.0:
                self.log('Auto-tapping post-battle screen buttons...')
                self.click_center('Center tap')
                time.sleep(0.8)
                self.click_cancel_friend()
                time.sleep(0.8)
                self.click_ready()  # Clicks End Battle Confirm if it is visible
                last_10s_click = time.time()

            # Wait before scanning again
            time.sleep(1.5)


# ============================================================================
# GUI - matches SecretShopRefresh
# ============================================================================

class AutoStoryGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.bg = '#171717'
        self.fg = '#dddddd'

        self.root.config(bg=self.bg)
        self.root.title('STORY AUTO-PROGRESS')
        self.root.geometry('420x420')
        self.root.minsize(420, 420)

        icon_path = os.path.join('assets', 'gui_icon.ico')
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        self.title_name = ''
        self.lock_start_button = False

        # Bind ESC globally to exit the app
        self.root.bind('<Escape>', lambda e: self.close_app())

        tk.Label(self.root, text='E7 Story Auto-Progression',
                 font=('Helvetica', 20), bg=self.bg, fg=self.fg).pack(pady=(15, 0))

        # Emulator selection
        self.packLabel('Select emulator or type window title:')

        def onSelect(event):
            t = self.combo.get()
            if t not in gw.getAllTitles():
                self.start_btn.config(state=tk.DISABLED)
                return
            self.title_name = t
            if not self.lock_start_button:
                self.start_btn.config(state=tk.NORMAL)

        def onEnter(event):
            t = self.combo.get()
            if t == '' or t not in gw.getAllTitles():
                self.start_btn.config(state=tk.DISABLED)
                return
            self.title_name = t
            if not self.lock_start_button:
                self.start_btn.config(state=tk.NORMAL)

        titles = sorted(RECOGNIZE_TITLES)
        self.combo = ttk.Combobox(self.root, values=titles, width=35)
        self.combo.bind('<<ComboboxSelected>>', onSelect)
        self.combo.bind('<KeyRelease>', onEnter)
        self.combo.pack(pady=5)

        # Auto-detect window
        for t in titles:
            if t in gw.getAllTitles():
                self.title_name = t
                self.combo.set(t)
                break

        if not self.title_name:
            google_play = re.compile(r"^(Epic Seven|에픽세븐).*$", re.UNICODE)
            for t in gw.getAllTitles():
                if google_play.fullmatch(t):
                    self.title_name = t
                    self.combo.set(t)
                    break

        # Settings
        self.packLabel('Settings:', 15, (15, 0))

        sf = tk.Frame(self.root, bg=self.bg)
        sf.pack(pady=5)

        def makeEntry(label, default):
            f = tk.Frame(sf, bg=self.bg, pady=3)
            tk.Label(f, text=label, bg=self.bg, fg=self.fg,
                     font=('Helvetica', 11)).pack(side=tk.LEFT, padx=8)
            e = tk.Entry(f, bg='#333333', fg=self.fg,
                         font=('Helvetica', 11), width=8)
            e.insert(0, str(default))
            e.pack(side=tk.RIGHT, padx=8)
            f.pack(fill=tk.X)
            return e

        self.mouse_speed_entry = makeEntry('Mouse speed (s):', 0.3)
        self.battle_wait_entry = makeEntry('Battle timeout (s):', 240)

        # Status text
        self.status_label = tk.Label(self.root, text='Status: Ready (Press ESC to exit)',
                                     font=('Helvetica', 11), bg=self.bg, fg='#FFBF00',
                                     wraplength=380)
        self.status_label.pack(pady=(15, 5))

        # Start button
        self.start_btn = tk.Button(self.root, text='Start progression',
                                   font=('Helvetica', 14),
                                   state=tk.NORMAL if self.title_name else tk.DISABLED,
                                   command=self.onStart)
        self.start_btn.pack(pady=(10, 0))

        self.root.mainloop()

    def packLabel(self, text, size=13, pady=10):
        tk.Label(self.root, text=text, font=('Helvetica', size),
                 bg=self.bg, fg=self.fg).pack(pady=pady)

    def update_status(self, text):
        self.status_label.config(text=f'Status: {text}')

    def onComplete(self):
        self.status_label.config(text='Status: Terminated')
        self.root.title('STORY AUTO-PROGRESS')
        self.start_btn.config(state=tk.NORMAL)
        self.lock_start_button = False

    def close_app(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def onStart(self):
        self.root.title('Press ESC to exit!')
        self.lock_start_button = True
        self.start_btn.config(state=tk.DISABLED)

        self.sp = StoryProgression(
            title_name=self.title_name,
            callback=self.onComplete,
            tk_instance=self
        )

        try:
            self.sp.mouse_sleep = float(self.mouse_speed_entry.get())
        except ValueError:
            pass
        try:
            self.sp.battle_wait_max = int(self.battle_wait_entry.get())
        except ValueError:
            pass

        self.status_label.config(text='Status: Auto-progression running...')
        self.sp.start()


# ============================================================================
# Main
# ============================================================================

def main():
    if not os.path.isdir(STORY_ASSETS_DIR):
        print(f"[ERROR] '{STORY_ASSETS_DIR}/' not found!")
        sys.exit(1)

    AutoStoryGUI()


if __name__ == '__main__':
    main()
