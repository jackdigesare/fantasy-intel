"""Build exportable fantasy football reports from Sleeper data."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _owner_label(user: dict[str, Any] | None, owner_id: str | None) -> str:
    if not user:
        return owner_id or "Unknown"
    meta = user.get("metadata") or {}
    team_name = (meta.get("team_name") or "").strip()
    display = (user.get("display_name") or user.get("username") or "").strip()
    if team_name and display:
        return f"{team_name} ({display})"
    return team_name or display or owner_id or "Unknown"


def _player_info(players: dict[str, Any], player_id: str) -> dict[str, str]:
    # Defense / special teams IDs are team abbreviations (e.g. "DET").
    if player_id.isalpha() and len(player_id) <= 3:
        return {
            "player_name": f"{player_id} DEF",
            "position": "DEF",
            "nfl_team": player_id,
        }

    info = players.get(player_id) or {}
    first = (info.get("first_name") or "").strip()
    last = (info.get("last_name") or "").strip()
    full = (info.get("full_name") or "").strip()
    name = full or " ".join(p for p in (first, last) if p) or player_id
    fantasy_positions = info.get("fantasy_positions")
    if isinstance(fantasy_positions, list) and fantasy_positions:
        position = str(fantasy_positions[0])
    else:
        position = info.get("position") or ""
    return {
        "player_name": name,
        "position": position,
        "nfl_team": info.get("team") or "",
    }


def _slot_for_player(
    player_id: str,
    starters: set[str],
    reserve: set[str],
    taxi: set[str],
) -> str:
    if player_id in starters:
        return "starter"
    if player_id in reserve:
        return "IR"
    if player_id in taxi:
        return "taxi"
    return "bench"


def build_roster_report(
    rosters: list[dict[str, Any]],
    users: list[dict[str, Any]],
    players: dict[str, Any],
) -> pd.DataFrame:
    """One row per player currently on a roster."""
    users_by_id = {u["user_id"]: u for u in users if "user_id" in u}
    rows: list[dict[str, Any]] = []

    for roster in rosters:
        roster_id = roster.get("roster_id")
        owner_id = roster.get("owner_id")
        owner = users_by_id.get(owner_id) if owner_id else None
        team = _owner_label(owner, owner_id)

        starters = set(roster.get("starters") or [])
        reserve = set(roster.get("reserve") or [])
        taxi = set(roster.get("taxi") or [])
        player_ids = roster.get("players") or []

        for player_id in player_ids:
            if not player_id:
                continue
            info = _player_info(players, str(player_id))
            rows.append(
                {
                    "team": team,
                    "roster_id": roster_id,
                    "slot": _slot_for_player(
                        str(player_id), starters, reserve, taxi
                    ),
                    "player_name": info["player_name"],
                    "position": info["position"],
                    "nfl_team": info["nfl_team"],
                    "player_id": str(player_id),
                }
            )

    df = pd.DataFrame(
        rows,
        columns=[
            "team",
            "roster_id",
            "slot",
            "player_name",
            "position",
            "nfl_team",
            "player_id",
        ],
    )
    if df.empty:
        return df

    slot_order = {"starter": 0, "bench": 1, "taxi": 2, "IR": 3}
    df["_slot_rank"] = df["slot"].map(lambda s: slot_order.get(s, 9))
    df = (
        df.sort_values(["team", "roster_id", "_slot_rank", "position", "player_name"])
        .drop(columns=["_slot_rank"])
        .reset_index(drop=True)
    )
    return df
