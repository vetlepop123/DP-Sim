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
- With progressive weather (on by default), wind, waves and current get stronger every 30 seconds. Your score is how long you survive.
- The small blue arrow on each thruster shows its jet (the rig is pushed the opposite way). The large blue arrow in the middle is the total thruster force on the rig, and the orange arrow is the environmental force.

### Controls

Each thruster has four keys in an inverted T, like on the keyboard. The top key gives more thrust, the middle key less, and left/right rotate the thruster.

| Thruster | Keys |
|---|---|
| T1 bow port | W A S D |
| T2 bow starboard | I J K L |
| T3 stern port | T F G H |
| T4 stern starboard | ↑ ← ↓ → |

Shift gives fine adjustment, Space pauses and R starts a new round. There is also a select mode (choose thrusters with 1–4, steer with the arrow keys).

### Settings (sidebar)

Weather (Storm or Orkan), progressive weather, circle radius, heading rule, game speed, force vectors and random thruster failures.

## Files

- `simulator.py`: the Streamlit page with settings and weather levels.
- `game.html`: the game itself (physics, graphics and keyboard) in JavaScript. The physical constants are at the top of the file.

## Physics

The rig is modelled in three degrees of freedom (north, east, heading), with about 50 000 t mass including added mass and four 1.8 MN azimuth thrusters. Wind force grows with the square of wind speed and has random gusts, wave drift grows with Hs², and current drags the rig along through damping relative to the water. Wind and waves act slightly off-centre, so the heading drifts. Thruster thrust and direction follow the ordered values at a limited rate.
