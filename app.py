"""Fantasy Intel — download current Sleeper fantasy football rosters."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
import streamlit as st

import reports
import sleeper_api
from sleeper_api import API_VERSION, SleeperError

STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Barlow+Condensed:wght@600;700&display=swap');

:root {
  --bg: #0f1a14;
  --ink: #e8f0ea;
  --muted: #8fa396;
  --accent: #3d9a5f;
  --accent-2: #c4a35a;
  --surface: #16241c;
  --line: rgba(232, 240, 234, 0.12);
  --radius: 8px;
}

html, body, [class*="css"] {
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
  color: var(--ink);
}

.stApp {
  background:
    radial-gradient(800px 400px at 90% -10%, rgba(61, 154, 95, 0.22), transparent 55%),
    radial-gradient(600px 360px at 0% 30%, rgba(196, 163, 90, 0.12), transparent 50%),
    var(--bg);
}

.block-container {
  max-width: 880px;
  padding-top: 2.75rem;
  padding-bottom: 4rem;
}

#MainMenu, footer, header { visibility: hidden; height: 0; }

.fi-hero { margin-bottom: 1.75rem; }
.fi-brand {
  font-family: "Barlow Condensed", sans-serif;
  font-weight: 700;
  font-size: clamp(2.75rem, 7vw, 3.75rem);
  letter-spacing: 0.02em;
  line-height: 1;
  color: var(--ink);
  margin: 0 0 0.75rem 0;
  text-transform: uppercase;
}
.fi-brand span { color: var(--accent); }
.fi-lede {
  font-size: 1.08rem;
  line-height: 1.55;
  color: var(--muted);
  max-width: 34rem;
  margin: 0;
}
.fi-rule {
  width: 2.75rem;
  height: 4px;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  margin: 1.15rem 0 0 0;
  border: 0;
  border-radius: 2px;
}

.fi-section { margin: 2rem 0 0.75rem 0; }
.fi-section h2 {
  font-family: "Barlow Condensed", sans-serif;
  font-weight: 700;
  font-size: 1.35rem;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  margin: 0 0 0.3rem 0;
  color: var(--ink);
}
.fi-section p {
  margin: 0;
  color: var(--muted);
  font-size: 0.92rem;
}

.fi-note {
  margin: 1.25rem 0 0 0;
  padding: 0.85rem 1rem;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  color: var(--muted);
  font-size: 0.9rem;
  line-height: 1.5;
}
.fi-note strong {
  color: var(--ink);
  font-weight: 600;
}
.fi-note code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.86em;
  color: var(--accent-2);
}

.fi-meta {
  margin: 0.75rem 0 0 0;
  color: var(--muted);
  font-size: 0.8rem;
  letter-spacing: 0.02em;
}
.fi-meta code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: var(--accent-2);
}
</style>
"""

SAMPLE_LEAGUE_ID = "289646328504385536"


def _season_options(state: dict[str, Any]) -> tuple[list[str], str]:
    current = str(state.get("league_season") or state.get("season") or "2025")
    try:
        year = int(current)
    except ValueError:
        year = 2025
    seasons = [str(y) for y in range(year, year - 6, -1)]
    return seasons, current


def _dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _dataframe_to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="rosters")
    return buffer.getvalue()


def _resolve_league_id() -> str | None:
    lookup_mode = st.radio(
        "How do you want to find your league?",
        ["Username", "League ID"],
        horizontal=True,
    )

    if lookup_mode == "League ID":
        league_id = st.text_input(
            "League ID",
            placeholder="e.g. 289646328504385536",
            help="Find this in the Sleeper app league URL or settings.",
        ).strip()
        if not league_id:
            return None
        try:
            league = sleeper_api.get_league(league_id)
        except SleeperError as exc:
            st.error(str(exc))
            return None
        st.success(f"League: **{league.get('name', league_id)}**")
        return league["league_id"]

    username = st.text_input(
        "Username",
        placeholder="your_sleeper_username",
    ).strip()
    if not username:
        return None

    try:
        user = sleeper_api.get_user(username)
        state = sleeper_api.get_nfl_state()
    except SleeperError as exc:
        st.error(str(exc))
        return None

    seasons, default_season = _season_options(state)
    season = st.selectbox(
        "Season",
        options=seasons,
        index=seasons.index(default_season) if default_season in seasons else 0,
    )

    try:
        leagues = sleeper_api.get_user_leagues(user["user_id"], season)
    except SleeperError as exc:
        st.error(str(exc))
        return None

    if not leagues:
        st.warning(f"No NFL leagues found for @{user.get('username', username)} in {season}.")
        return None

    labels = {
        f"{lg.get('name', 'League')} ({lg['league_id']})": lg["league_id"]
        for lg in leagues
    }
    choice = st.selectbox("League", options=list(labels.keys()))
    return labels[choice]


def main() -> None:
    st.set_page_config(
        page_title="Fantasy Football Intel",
        page_icon="FI",
        layout="centered",
    )
    st.markdown(STYLES, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="fi-hero">
          <h1 class="fi-brand">Fantasy Football <span>Intel</span></h1>
          <p class="fi-lede">
            Pull current rosters for all teams in your fantasy football league and export them to CSV or Excel.
          </p>
          <hr class="fi-rule" />
          <p class="fi-note">
            <strong>Sleeper only for now</strong> — support for more fantasy platforms is in development.
            Want to try it without your own league? Use sample league ID
            <code>{SAMPLE_LEAGUE_ID}</code> (Sleeper Friends League, 2018).
          </p>
          <p class="fi-meta">Sleeper API <code>{API_VERSION}</code></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="fi-section">
          <h2>League</h2>
          <p>Search by username or paste a league ID directly.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    league_id = _resolve_league_id()
    if not league_id:
        st.info("Enter a username or league ID to continue.")
        return

    st.markdown(
        """
        <div class="fi-section">
          <h2>Report</h2>
          <p>Current rosters — one row per player, with starters, bench, taxi, and IR.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    report_type = st.selectbox("Report type", ["Current rosters"])
    export_format = st.selectbox("File format", ["CSV", "XLSX"])

    if not st.button("Generate report", type="primary"):
        return

    if report_type != "Current rosters":
        st.error("Unsupported report type.")
        return

    with st.spinner("Building roster report…"):
        try:
            rosters = sleeper_api.get_rosters(league_id)
            users = sleeper_api.get_league_users(league_id)
            players = sleeper_api.get_players()
            df = reports.build_roster_report(rosters, users, players)
        except SleeperError as exc:
            st.error(str(exc))
            return

    if df.empty:
        st.warning("No roster players found for this league.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)

    safe_name = f"sleeper-rosters-{league_id}"
    if export_format == "CSV":
        st.download_button(
            label="Download CSV",
            data=_dataframe_to_csv_bytes(df),
            file_name=f"{safe_name}.csv",
            mime="text/csv",
            type="primary",
        )
    else:
        st.download_button(
            label="Download Excel",
            data=_dataframe_to_xlsx_bytes(df),
            file_name=f"{safe_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )


if __name__ == "__main__":
    main()
