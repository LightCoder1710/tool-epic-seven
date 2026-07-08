# Epic Seven Automation Tools (with GUI)

A suite of automation tools for Epic Seven, containing both an **Auto Secret Shop Refresher** and an **Auto Story Progression Bot**. Both tools feature a clean Tkinter GUI, automatic window sizing, and global hotkey control.

---

## 🛠️ Included Tools

### 1. Auto Secret Shop Refresher (`e7refresh.py`)
Automatically refreshes the secret shop in the lobby to purchase Covenant and Mystic Bookmarks.
*   **GUI Control:** Easily select your emulator, configure mouse/screenshot speeds, and set a Skystone budget.
*   **Safe Clicks:** Uses percentage-based coordinates on a resized `906x539` window to ensure precise clicks.
*   **Stats Tracking:** Displays a live counter of bookmarks purchased and saves history logs.

### 2. Auto Story Progression Bot (`e7story.py`)
Automatically cycles through campaign stages to clear story chapters.
*   **Sequential Stage Loop:** Enters lobby -> Ready -> Select Team -> Starts Quest.
*   **Automatic Cutscene Skipping:** Detects and clicks "Skip" and "Confirm Skip" during story cutscenes.
*   **Auto-Battle Transitions:** Clicks screen center, cancels friend requests, and confirms end battle screens automatically every 10 seconds.
*   **Lobby Detection:** Detects the lobby Ready button to safely start the next cycle.

---

## 🚀 Getting Started

### ⚠️ Critical Requirements (Read First!)
1.  **Run as Administrator:** You **must** open your terminal (PowerShell / Command Prompt) as **Administrator** to run these tools. Windows UAC blocks mouse clicks sent to emulator processes running at higher privilege levels.
2.  **Display Active:** Keep your monitor turned on while the tool is running; the script relies on display capture to scan screen regions.
3.  **Instant Exit:** Press the **`ESC`** key at any time to immediately stop the macro and close the application.

---

### How to Install & Run

1.  **Install Python:** Download and install Python (v3.10+ recommended).
2.  **Download Source:** Clone or download this repository.
3.  **Install Dependencies:** Open your terminal (as Administrator) in the folder and run:
    ```bash
    pip install -r requirements.txt
    ```

#### Running the Shop Refresher:
1.  Open Epic Seven to the Secret Shop screen.
2.  Run the command:
    ```bash
    python e7refresh.py
    ```
3.  Select your emulator from the GUI dropdown list and click **Start Refresh**.

#### Running the Story Progression Bot:
1.  Open Epic Seven to the chapter stage selection lobby (where the green **Ready** button is visible).
2.  Run the command:
    ```bash
    python e7story.py
    ```
3.  Select your emulator, input your desired mouse speed, and click **Start progression**.

---

## 📸 Image Assets Configuration for Story Mode

The Story bot relies on 3 key images inside the `story-assets/` folder to scan the game state. 

*   Since the tool resizes your emulator window to `906x539` at startup, you should crop these image snippets from your emulator **at that exact size** (`906x539`) for optimal template matching:

1.  **`1.png`**: A cropped snippet of the green **Ready** button in the lobby.
2.  **`newskip.png`**: A cropped snippet of the **Skip >** button that appears in the top-right corner of cutscenes.
3.  **`comfirmskipnew.png`**: A cropped snippet of the **Confirm** button that appears on the skip confirmation dialog popup.

---

## 💻 Compile to Executable (`.exe`)

You can compile these scripts into standalone executables using `PyInstaller`:

```bash
# Compile Shop Refresher
python -m PyInstaller -F --noconsole -i assets/icon.ico e7refresh.py

# Compile Story Progression
python -m PyInstaller -F --noconsole -i assets/gui_icon.ico e7story.py
```
The compiled files will appear inside the `dist/` directory.
