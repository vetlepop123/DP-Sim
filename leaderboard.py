"""Ledertavle for DP-simulatoren.

Resultatene lagres i Supabase når nøklene ligger i Streamlit-secrets:

    [supabase]
    url = "https://<prosjekt>.supabase.co"
    key = "<anon- eller publishable-nøkkel>"

Uten secrets lagres de i en lokal JSON-fil, slik at alt kan testes lokalt.
Tabellen opprettes med supabase_setup.sql.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import requests
import streamlit as st

TABLE = "scores"
LOCAL_FILE = Path(__file__).with_name("leaderboard_local.json")
NAME_MAX = 20
_local_lock = threading.Lock()


def _supabase():
    """(url, key) fra secrets, eller None hvis Supabase ikke er satt opp."""
    try:
        sb = st.secrets["supabase"]
        return sb["url"].rstrip("/"), sb["key"]
    except Exception:
        return None


def backend_name():
    return "Supabase" if _supabase() else "lokal fil"


def _headers(key):
    headers = {"apikey": key, "Content-Type": "application/json"}
    # Eldre anon-nøkler er JWT-er og må også sendes som Bearer-token.
    # De nye publishable-nøklene (sb_publishable_...) skal bare i apikey.
    if key.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {key}"
    return headers


def add_score(entry):
    """Lagrer ett resultat. entry: name, time_s, level, category + innstillingene."""
    sb = _supabase()
    if sb:
        url, key = sb
        r = requests.post(f"{url}/rest/v1/{TABLE}", json=entry,
                          headers={**_headers(key), "Prefer": "return=minimal"}, timeout=10)
        r.raise_for_status()
    else:
        with _local_lock:
            rows = json.loads(LOCAL_FILE.read_text(encoding="utf-8")) if LOCAL_FILE.exists() else []
            rows.append({**entry, "created_at": datetime.now(timezone.utc).isoformat()})
            LOCAL_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    top_scores.clear()


@st.cache_data(ttl=20, show_spinner=False)
def top_scores(category, limit=20):
    """De beste resultatene i en kategori, sortert på lengst tid."""
    sb = _supabase()
    if sb:
        url, key = sb
        r = requests.get(
            f"{url}/rest/v1/{TABLE}",
            params={"select": "name,time_s,level,created_at", "category": f"eq.{category}",
                    "order": "time_s.desc", "limit": str(limit)},
            headers=_headers(key), timeout=10,
        )
        r.raise_for_status()
        return r.json()
    if not LOCAL_FILE.exists():
        return []
    rows = [r for r in json.loads(LOCAL_FILE.read_text(encoding="utf-8")) if r["category"] == category]
    return sorted(rows, key=lambda r: r["time_s"], reverse=True)[:limit]


def clean_name(name):
    return " ".join((name or "").split())[:NAME_MAX]
