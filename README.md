# DP-Sim

A retro dynamic positioning (DP) game. You control a semi-submersible drilling rig from above with four azimuth thrusters, and try to keep the whole rig inside a circle while the weather gets progressively worse.

## Run

```
pip install -r requirements.txt
streamlit run simulator.py
```

Click the game to give it keyboard focus.

## How to play

- Keep every part of the rig (pontoons and deck) inside the circle. If part of the rig is over the line for more than 10 seconds, the game is over.
- Wind, waves and current get stronger every 30 seconds. Your score is how long you survive.
- The small blue arrow on each thruster shows its jet (the rig is pushed the opposite way). The large blue arrow in the middle is the total thruster force on the rig, and the orange arrow is the environmental force.

### Controls

Each thruster has four keys in an inverted T, like on the keyboard. The top key gives more thrust, the middle key less, and left/right rotate the thruster.

| Thruster | Keys |
|---|---|
| T1 bow port | W A S D |
| T2 bow starboard | I J K L |
| T3 stern port | T F G H |
| T4 stern starboard | ↑ ← ↓ → |

Shift gives fine adjustment, Space pauses and R starts a new round.

### Settings (sidebar)

Every round starts in hurricane-force weather (Orkan) that gets worse every 30 seconds, with a fixed 100 m circle. The sidebar has the heading rule, game speed, force vectors and random thruster failures.

## Leaderboard

You have to enter a name before the game appears; you can change it later in the sidebar. When a round ends, your time is saved to the leaderboard under the game. Each combination of the settings that affect difficulty (game speed, heading rule, thruster failures) has its own list.

Without any setup, results are stored in a local file (`leaderboard_local.json`), which is fine for testing on one PC. For a shared leaderboard online, set up Supabase and Streamlit Community Cloud:

1. **Supabase database (free):** create a project at [supabase.com](https://supabase.com). Open **SQL Editor → New query**, paste the contents of `supabase_setup.sql` and click **Run**. This creates the `scores` table. Anyone can add and read scores, but nobody can edit or delete them through the API.
2. **Keys:** in Supabase, open **Project Settings → API** and copy the **Project URL** and the **anon** (or **publishable**) key.
3. **Deploy:** go to [share.streamlit.io](https://share.streamlit.io), click **Create app**, and choose the repo `vetlepop123/DP-Sim`, branch `main`, main file `simulator.py`.
4. **Secrets:** under **Advanced settings → Secrets** (or later under **App settings → Secrets**), paste:

   ```toml
   [supabase]
   url = "https://YOUR-PROJECT.supabase.co"
   key = "YOUR-ANON-OR-PUBLISHABLE-KEY"
   ```

5. Share the app link. Everyone who plays there writes to the same leaderboard.

To use Supabase when running locally, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in the same values. That file is in `.gitignore` and is never committed.

## Files

- `simulator.py`: the Streamlit page with settings, the starting weather and the leaderboard.
- `game.html`: the game itself (physics, graphics and keyboard) in JavaScript. The physical constants are at the top of the file.
- `leaderboard.py`: saves and reads results (Supabase, or a local JSON file when no secrets are set).
- `supabase_setup.sql`: creates the leaderboard table in Supabase.

## Physics

The rig is modelled in three degrees of freedom (north, east, heading), with about 50 000 t mass including added mass and four 1.8 MN azimuth thrusters. Wind force grows with the square of wind speed and has random gusts, wave drift grows with Hs², and current drags the rig along through damping relative to the water. Wind and waves act slightly off-centre, so the heading drifts. Thruster thrust and direction follow the ordered values at a limited rate.
