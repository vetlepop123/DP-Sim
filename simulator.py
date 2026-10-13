"""DP-simulator: hold en semisub-rigg på posisjon med fire azimut-thrustere.

Streamlit lager siden og innstillingene. Selve spillet (fysikk, grafikk og
tastatur) kjører i JavaScript i game.html, slik at det går jevnt i sanntid.

Kjør med:
    streamlit run simulator.py
"""

import json
from pathlib import Path

import streamlit as st

GAME_FILE = Path(__file__).with_name("game.html")
GAME_HEIGHT = 780

# Værnivåer. wind [m/s], gust = relativt standardavvik på vindkast,
# hs = signifikant bølgehøyde [m], current [m/s], dir_var = vindretningsstøy [grader],
# shift = tilfeldige værskifter der vinden dreier 30-90 grader.
WEATHER = {
    "Storm": dict(wind=25, gust=0.20, hs=8.0, current=0.9, dir_var=16, shift=True,
                  desc="Full storm, høy sjø og sterk strøm. Thrusterne må jobbe hardt."),
    "Orkan": dict(wind=31, gust=0.22, hs=10.0, current=1.0, dir_var=20, shift=True,
                  desc="Ekstremvær. Vindkastene kan bli sterkere enn thrusterne. Hvor lenge holder du?"),
}

CONTROL_MODES = {
    "Direkte (4 taster per thruster)": "direct",
    "Velg thruster (1–4 + piltaster)": "select",
}

st.set_page_config(page_title="DP-simulator", page_icon="⚓", layout="wide")

with st.sidebar:
    st.header("Innstillinger")
    level = st.radio("Vær", list(WEATHER), index=list(WEATHER).index("Orkan"), horizontal=True)
    w = WEATHER[level]
    st.caption(w["desc"])
    progressive = st.checkbox("Progressivt vær (blir verre hvert 30. sekund)", value=True)
    st.caption(
        f"Vind {w['wind']} m/s · Hs {w['hs']} m · strøm {w['current']} m/s"
        + (" · værskifter" if w["shift"] else "")
    )
    mode_label = st.radio("Kontrollmodus", list(CONTROL_MODES))
    # Riggens ytterste punkt er ca. 69 m fra senter, så radius 100 gir ca. 31 m å gå på.
    radius = st.slider("Sirkelradius [m]", 80, 220, 100, step=10)
    heading_rule = st.checkbox("Kursregel (tap ved kursavvik)", value=False)
    heading_tol = st.slider("Kurstoleranse [± grader]", 5, 20, 10) if heading_rule else 10
    speed = st.slider("Spillhastighet [x sanntid]", 1.0, 3.0, 1.5, step=0.25)
    show_forces = st.checkbox("Vis kraftvektorer (hjelp)", value=True)
    failures = st.checkbox("Tilfeldige thrusterfeil", value=False)
    st.caption("Når du endrer en innstilling, starter spillet på nytt.")

st.title("⚓ DP-simulator: semisub")
st.write(
    "Klikk på spillet for å gi det tastaturfokus. Hold hele riggen innenfor sirkelen så lenge du klarer. "
    "Rekorden lagres i nettleseren for hver kombinasjon av vær, radius og kurstoleranse."
)

config = {
    "weather": {
        "name": level,
        "wind": w["wind"],
        "gust": w["gust"],
        "hs": w["hs"],
        "current": w["current"],
        "dirVar": w["dir_var"],
        "shift": w["shift"],
    },
    "mode": CONTROL_MODES[mode_label],
    "radius": radius,
    "speed": speed,
    "progressive": progressive,
    "headingRule": heading_rule,
    "headingTol": heading_tol,
    "showForces": show_forces,
    "failures": failures,
    "height": GAME_HEIGHT,
}

html = GAME_FILE.read_text(encoding="utf-8").replace("__CONFIG__", json.dumps(config))
st.iframe(html, height=GAME_HEIGHT)

col1, col2 = st.columns(2)
with col1:
    with st.expander("Kontroller", expanded=False):
        if config["mode"] == "direct":
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
        else:
            st.markdown(
                "- **1–4**: velg eller fjern en thruster (flere kan være valgt samtidig), **5**: alle\n"
                "- **↑ / ↓** eller **W / S**: pådrag for valgte thrustere\n"
                "- **← / →** eller **A / D**: roter valgte thrustere"
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
