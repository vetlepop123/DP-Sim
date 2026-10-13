"""DP-simulator: hold en semisub-rigg på posisjon med fire azimut-thrustere.

Streamlit lager siden og innstillingene. Selve spillet (fysikk, grafikk og
tastatur) kjører i JavaScript i game.html, slik at det går jevnt i sanntid.

Kjør med:
    streamlit run simulator.py
"""

import json
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v2 as components_v2

import leaderboard

GAME_FILE = Path(__file__).with_name("game.html")
GAME_HEIGHT = 780

# Usynlig komponent som tar imot resultatet fra spillet (postMessage fra iframen)
# og sender det videre til Python som en trigger-verdi.
RESULT_BRIDGE_JS = """
export default function(component) {
    const { setTriggerValue } = component;
    const onMessage = (ev) => {
        const d = ev.data;
        if (d && d.type === 'dpsim-result') setTriggerValue('result', d);
    };
    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
}
"""
result_bridge = components_v2.component("dpsim_result_bridge", js=RESULT_BRIDGE_JS)

# Startvær: Orkan. Været blir verre hvert 30. sekund (se LEVEL_TIME i game.html).
# wind [m/s], gust = relativt standardavvik på vindkast, hs = signifikant bølgehøyde [m],
# current [m/s], dir_var = vindretningsstøy [grader], shift = værskifter der vinden dreier 30-90 grader.
WEATHER_NAME = "Orkan"
WEATHER = dict(wind=31, gust=0.22, hs=10.0, current=1.0, dir_var=20, shift=True)
# Riggens ytterste punkt er ca. 69 m fra senter, så radius 100 gir ca. 31 m å gå på.
RADIUS = 100

st.set_page_config(page_title="DP-simulator", page_icon="⚓", layout="wide")

with st.sidebar:
    st.text_input("Spillernavn (til ledertavlen)", key="player_name", max_chars=leaderboard.NAME_MAX,
                  placeholder="Skriv navnet ditt")
    st.header("Innstillinger")
    st.caption(
        f"Starter i {WEATHER_NAME.lower()} (vind {WEATHER['wind']} m/s, Hs {WEATHER['hs']} m, "
        f"strøm {WEATHER['current']} m/s), og været blir verre hvert 30. sekund. "
        f"Sirkelen har radius {RADIUS} m."
    )
    heading_rule = st.checkbox("Kursregel (tap ved kursavvik)", value=False)
    heading_tol = st.slider("Kurstoleranse [± grader]", 5, 20, 10) if heading_rule else 10
    speed = st.slider("Spillhastighet [x sanntid]", 1.0, 3.0, 1.5, step=0.25)
    show_forces = st.checkbox("Vis kraftvektorer (hjelp)", value=True)
    failures = st.checkbox("Tilfeldige thrusterfeil", value=False)
    st.caption("Når du endrer en innstilling, starter spillet på nytt.")

st.title("⚓ DP-simulator: semisub")
st.write(
    "Klikk på spillet for å gi det tastaturfokus. Hold hele riggen innenfor sirkelen så lenge du klarer. "
    "Når runden er over, havner tiden din på ledertavlen under spillet."
)

# Ledertavlen har én liste per kombinasjon av innstillinger som påvirker vanskeligheten
# (Formatet er det samme som før vær, radius og progressivt vær ble låst, så gamle resultater står.)
category = "-".join(
    [WEATHER_NAME.lower(), f"r{RADIUS}", f"x{speed:g}", "prog",
     f"kurs{heading_tol}" if heading_rule else "kursfri"]
    + (["feil"] if failures else [])
)
category_label = " · ".join(
    [f"{speed:g}x fart", f"kurs ±{heading_tol}°" if heading_rule else "uten kursregel"]
    + (["thrusterfeil"] if failures else [])
)

config = {
    "category": category,
    "weather": {
        "name": WEATHER_NAME,
        "wind": WEATHER["wind"],
        "gust": WEATHER["gust"],
        "hs": WEATHER["hs"],
        "current": WEATHER["current"],
        "dirVar": WEATHER["dir_var"],
        "shift": WEATHER["shift"],
    },
    "radius": RADIUS,
    "speed": speed,
    "headingRule": heading_rule,
    "headingTol": heading_tol,
    "showForces": show_forces,
    "failures": failures,
    "height": GAME_HEIGHT,
}


def start_with_name():
    """Kalles fra Start-knappen. Kjøres før neste kjøring, så navnefeltet i menyen kan settes her."""
    name = leaderboard.clean_name(st.session_state.get("name_entry"))
    st.session_state.player_name = name
    st.session_state.name_missing = not name


# Spillet vises først når spilleren har skrevet inn et navn
if leaderboard.clean_name(st.session_state.get("player_name")):
    html = GAME_FILE.read_text(encoding="utf-8").replace("__CONFIG__", json.dumps(config))
    st.iframe(html, height=GAME_HEIGHT)
else:
    with st.form("name_form"):
        st.markdown("#### Skriv inn navnet ditt for å starte")
        st.text_input("Spillernavn", key="name_entry", max_chars=leaderboard.NAME_MAX,
                      placeholder="Navnet som vises på ledertavlen")
        st.form_submit_button("Start", type="primary", on_click=start_with_name)
    if st.session_state.get("name_missing"):
        st.error("Du må skrive inn et navn for å spille.")

# --- Ledertavle --------------------------------------------------------------
# Resultatet fra spillet tas vare på til det er lagret, slik at man kan skrive inn
# navnet etter runden. Hver runde har en unik id, så den lagres bare én gang.
result = result_bridge(key="result_bridge", on_result_change=lambda: None).result
saved_ids = st.session_state.setdefault("saved_ids", set())
if isinstance(result, dict) and result.get("id") not in saved_ids:
    try:
        st.session_state.pending = {
            "id": str(result["id"])[:40],
            "time_s": float(min(max(result["time_s"], 0), 35999)),
            "level": int(min(max(result.get("level", 1), 1), 10000)),
            "category": str(result.get("category", category))[:100],
            # Innstillingene runden ble spilt med (kategorien kommer fra spillet selv)
            "settings": {"weather": WEATHER_NAME, "radius": RADIUS, "speed": speed, "progressive": True,
                         "heading_rule": heading_rule, "heading_tol": heading_tol, "failures": failures,
                         "mode": "direct"},
        }
    except (KeyError, TypeError, ValueError):
        pass

pending = st.session_state.get("pending")
if pending and pending["id"] not in saved_ids:
    name = leaderboard.clean_name(st.session_state.get("player_name"))
    if name:
        try:
            leaderboard.add_score({"name": name, "time_s": pending["time_s"], "level": pending["level"],
                                   "category": pending["category"], **pending["settings"]})
            saved_ids.add(pending["id"])
            st.session_state.pending = None
            mins, secs = divmod(int(pending["time_s"]), 60)
            st.toast(f"Lagret på ledertavlen: {name}, {mins:02d}:{secs:02d}", icon="🏆")
        except Exception as e:
            st.error(f"Kunne ikke lagre resultatet: {e}")
    else:
        mins, secs = divmod(int(pending["time_s"]), 60)
        st.warning(f"Du holdt ut i {mins:02d}:{secs:02d}. Skriv inn navnet ditt, "
                   "så lagres resultatet på ledertavlen.")

st.subheader("🏆 Ledertavle")
st.caption(f"{category_label}. Disse innstillingene har sin egen liste.")
try:
    rows = leaderboard.top_scores(category)
except Exception as e:
    rows = []
    st.error(f"Kunne ikke hente ledertavlen: {e}")
if rows:
    me = leaderboard.clean_name(st.session_state.get("player_name")).lower()
    table = [
        {"#": i + 1,
         "Navn": r["name"] + (" ◀" if me and r["name"].lower() == me else ""),
         "Tid": f"{int(r['time_s']) // 60:02d}:{int(r['time_s']) % 60:02d}",
         "Nivå": r.get("level", 1),
         "Dato": datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")).strftime("%d.%m.%Y")}
        for i, r in enumerate(rows)
    ]
    st.dataframe(table, hide_index=True, width="stretch")
elif not st.session_state.get("pending"):
    st.info("Ingen resultater i denne kategorien ennå. Bli den første!")
if leaderboard.backend_name() != "Supabase":
    st.caption("Resultatene lagres foreløpig i en lokal fil (leaderboard_local.json). "
               "Sett opp Supabase for en felles ledertavle, se README.")

col1, col2 = st.columns(2)
with col1:
    with st.expander("Kontroller", expanded=False):
        st.markdown(
            "Hver thruster har fire taster i en omvendt T, som på tastaturet. "
            "Øverste tast gir mer pådrag, midterste gir mindre, og venstre/høyre roterer.\n\n"
            "| Thruster | Mer / mindre pådrag | Roter mot / med klokka |\n"
            "|---|---|---|\n"
            "| T1 baug babord | W / S | A / D |\n"
            "| T2 baug styrbord | I / K | J / L |\n"
            "| T3 akter babord | T / G | F / H |\n"
            "| T4 akter styrbord | ↑ / ↓ | ← / → |"
        )
        st.markdown(
            "- **Shift**: finjustering\n"
            "- **Mellomrom**: pause / fortsett\n"
            "- **R**: ny runde (når spillet er pauset eller over)"
        )
with col2:
    with st.expander("Om fysikken", expanded=False):
        st.markdown(
            "Riggen er modellert med tre frihetsgrader (nord, øst, kurs). Den har en masse på "
            "omtrent 50 000 tonn inkludert tilleggsmasse, og fire azimut-thrustere på 1,8 MN hver. "
            "Spillhastigheten kjører hele simuleringen raskere enn sanntid, mens tid og rekord teller ekte sekunder.\n\n"
            "- **Vind**: kraften øker med kvadratet av vindhastigheten, og vindkastene varierer tilfeldig.\n"
            "- **Bølger**: middels driftkraft som øker med Hs² og varierer langsomt. "
            "Svingningene fra hver enkelt bølge vises bare visuelt, slik et ekte DP-system filtrerer dem bort.\n"
            "- **Strøm**: riggen dempes mot vannet, så strømmen drar riggen med seg.\n"
            "- **Girmoment**: vind og bølger angriper litt utenfor senter, så kursen driver.\n"
            "- **Thrustere**: pådrag og retning følger det bestilte med begrenset hastighet.\n\n"
            "Konstantene ligger øverst i `game.html` og kan justeres."
        )
