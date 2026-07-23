"""Thin Sleeper API client (read-only, no auth)."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests
import streamlit as st

BASE_URL = "https://api.sleeper.app/v1"
API_VERSION = "v1"
TIMEOUT = 30


class SleeperError(Exception):
    """Raised when the Sleeper API returns an error or empty result."""


def _path_segment(value: str) -> str:
    """Encode an untrusted value as one URL path segment."""
    return quote(value, safe="")


def _league_id(value: str) -> str:
    """Validate a Sleeper snowflake before putting it in an API path."""
    cleaned = value.strip()
    if not cleaned or not cleaned.isascii() or not cleaned.isdecimal():
        raise SleeperError("Enter a numeric Sleeper league ID.")
    return cleaned


def _get(path: str) -> Any:
    url = f"{BASE_URL}{path}"
    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise SleeperError(f"Network error calling Sleeper: {exc}") from exc

    if response.status_code == 404:
        raise SleeperError("Not found. Check the username or league ID.")
    if response.status_code != 200:
        raise SleeperError(
            f"Sleeper API error ({response.status_code}) for {path}."
        )

    if not response.content:
        return None

    data = response.json()
    if data is None:
        raise SleeperError("Not found. Check the username or league ID.")
    return data


@st.cache_data(ttl=3600, show_spinner=False)
def get_user(username: str) -> dict[str, Any]:
    cleaned = username.strip().lstrip("@")
    if not cleaned:
        raise SleeperError("Enter a Sleeper username.")
    data = _get(f"/user/{_path_segment(cleaned)}")
    if not isinstance(data, dict) or "user_id" not in data:
        raise SleeperError(f"User '{cleaned}' not found.")
    return data


@st.cache_data(ttl=3600, show_spinner=False)
def get_nfl_state() -> dict[str, Any]:
    data = _get("/state/nfl")
    if not isinstance(data, dict):
        raise SleeperError("Could not load NFL state.")
    return data


@st.cache_data(ttl=600, show_spinner=False)
def get_user_leagues(user_id: str, season: str) -> list[dict[str, Any]]:
    data = _get(
        f"/user/{_path_segment(user_id)}/leagues/nfl/{_path_segment(season)}"
    )
    if data is None:
        return []
    if not isinstance(data, list):
        raise SleeperError("Unexpected leagues response.")
    return data


@st.cache_data(ttl=600, show_spinner=False)
def get_league(league_id: str) -> dict[str, Any]:
    cleaned = _league_id(league_id)
    data = _get(f"/league/{cleaned}")
    if not isinstance(data, dict) or "league_id" not in data:
        raise SleeperError(f"League '{cleaned}' not found.")
    return data


@st.cache_data(ttl=300, show_spinner=False)
def get_rosters(league_id: str) -> list[dict[str, Any]]:
    data = _get(f"/league/{_league_id(league_id)}/rosters")
    if data is None:
        return []
    if not isinstance(data, list):
        raise SleeperError("Unexpected rosters response.")
    return data


@st.cache_data(ttl=300, show_spinner=False)
def get_league_users(league_id: str) -> list[dict[str, Any]]:
    data = _get(f"/league/{_league_id(league_id)}/users")
    if data is None:
        return []
    if not isinstance(data, list):
        raise SleeperError("Unexpected users response.")
    return data


@st.cache_data(ttl=86400, show_spinner="Loading NFL player map (once per day)…")
def get_players() -> dict[str, Any]:
    """Full NFL player map (~5MB). Cached for 24 hours per Sleeper guidance."""
    data = _get("/players/nfl")
    if not isinstance(data, dict):
        raise SleeperError("Could not load player map.")
    return data
