# Over & Under: Swipe Duel (More or Less Game)

A high-stakes comparison guessing game built with **Godot 4.7** featuring **Tinder-style card swiping**, dynamic streaks, 3D rendered visuals via **Blender**, and an extensible JSON-based category system.

---

## 🎮 Gameplay & Swiping Mechanics

- **Tinder-Style Swiping**:
  - Drag or swipe the comparison card **LEFT** to predict Candidate A has the higher value (shows glowing cyan `👈 PICK [NAME]` badge).
  - Drag or swipe the comparison card **RIGHT** to predict Candidate B has the higher value (shows glowing purple/magenta `PICK [NAME] 👉` badge).
  - The card rotates and tilts dynamically with your gesture, snapping back if released under the swipe threshold, or flying to commit your choice!
- **Accessibility & Controls**:
  - **Touch & Mouse**: Full drag-and-swipe physics with spring physics and rotation.
  - **Keyboard**: Press **Left Arrow** / **A** or **Right Arrow** / **D**.
  - **Buttons**: Dedicated on-screen `👈 PICK LEFT` and `PICK RIGHT 👉` buttons.
- **Dynamic Streaks & Fresh Matchups**:
  - Each round presents **2 brand-new options** to compare, keeping matchups fresh and unpredictable!
  - Streaks are celebrated with audio fanfares and milestone flame badges every 5 wins.
  - Beat your personal best streak for each individual category!

---

## 🗂️ NBA Dataset Categories & Filter System

All categories are generated directly from the NBA database (`data/categories/nba data/nba.sqlite`):

### 🔍 Interactive Filtering in UI
- **Filter Pills**: Switch between **⭐ All**, **💪 Physicals**, **📜 Career & Draft**, and **🏟️ Teams & Arenas** with one tap.
- **Search Bar**: Type any stat, prompt, or keyword to filter categories in real time.

### 🏀 Available Categories
1. **💪 Player Physicals & Draft Combine**:
   - **Player Height (`nba_height.json`)**: "Who is TALLER (Height in Inches)?"
   - **Player Weight (`nba_weight.json`)**: "Who is HEAVIER (Weight in LBS)?"
   - **Combine Wingspan (`nba_wingspan.json`)**: "Who has the LONGER Wingspan (Inches)?"
   - **Combine Max Vertical Leap (`nba_vertical_leap.json`)**: "Who recorded the HIGHER Max Vertical Leap?"
   - **Combine Bench Press (`nba_bench_press.json`)**: "Who benched MORE Reps (185 lbs) at the Combine?"

2. **📜 Career, Draft & Scoring**:
   - **Scoring Averages (`nba_ppg.json`)**: "Who has the HIGHER Career Regular Season PPG?"
   - **Seasons Played (`nba_seasons_played.json`)**: "Who played MORE Seasons in the NBA?"
   - **Overall Draft Pick (`nba_draft_pick.json`)**: "Who had the HIGHER Overall Draft Pick Number?"

3. **🏟️ Teams, Arenas & Franchises**:
   - **All-Time Regular Season Wins (`nba_franchise_wins.json`)**: "Which franchise has MORE All-Time Wins?" (Calculated from 65,698 regular-season games).
   - **All-Time Win % (`nba_franchise_win_pct.json`)**: "Which franchise has the HIGHER All-Time Win %?"
   - **Arena Seating Capacity (`nba_arena_capacity.json`)**: "Which NBA team plays in the LARGER Arena?"
   - **Franchise Age (`nba_franchise_founded.json`)**: "Which franchise is OLDER (More Years Established)?"

---

## 🛠️ Adding New Categories (Extensibility)

You can add unlimited new categories in two ways:

### Option 1: In-Game Custom Creator
Click the **`+ CUSTOM`** button in the category select screen. You can paste or type JSON directly into the editor and hit **SAVE & ADD**—it instantly hot-loads and persists into your local user categories!

### Option 2: Drop a `.json` into `data/categories/`
Create a new file (e.g. `data/categories/spotify_streams.json`) following this structure:

```json
{
  "id": "spotify_streams",
  "title": "Most Streamed Songs on Spotify",
  "prompt": "Which track has MORE lifetime streams (Billions)?",
  "unit": "B",
  "value_format": "{value} Billion Streams",
  "items": [
    {
      "name": "Blinding Lights",
      "subtext": "The Weeknd • 2019",
      "value": 4.5,
      "image": "res://assets/images/music/blinding_lights.png"
    },
    {
      "name": "Shape of You",
      "subtext": "Ed Sheeran • 2017",
      "value": 3.9,
      "image": "res://assets/images/music/shape_of_you.png"
    }
  ]
}
```

The game automatically discovers and loads all `.json` files in the directory on startup!

---

## 🎨 Asset Pipeline (Real Internet Photos, Blender 3D & Procedural Audio)

- **Real Reference Photos (`tools/fetch_real_images.py`)**:
  - Automatically fetches high-resolution photos and official posters from Wikipedia / Wikimedia Commons.
  - Automatically crops and centers each picture to standard card dimensions (`480x600`) with rounded corners and bottom gradient scrims for optimal text readability.
- **Blender 3D Renders (`tools/render_3d_assets.py`)**:
  - Gold Trophy emblem (`assets/icons/trophy.png`)
  - Streak Fire flame (`assets/icons/flame.png`)
  - Versus badge (`assets/icons/vs_badge.png`)
  - Neon swipe indicators (`assets/icons/swipe_left.png`, `swipe_right.png`)
- **Audio Synthesizer (`tools/generate_sfx.py`)**:
  - Polyphonic sound effects: card swoosh, button clicks, correct chime arpeggio, streak victory fanfare, and buzzer.

---

## 🚀 Running the Game

Open Godot 4 and load `/run/media/system/Games/Workbench/Over and Under Game/project.godot`, or run via terminal:

```bash
flatpak run org.godotengine.Godot
```
