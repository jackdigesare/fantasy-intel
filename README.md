# Fantasy Intel

Streamlit app that downloads current Sleeper fantasy football rosters as CSV or Excel.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No API keys required — the Sleeper API is public and read-only.

## Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

## Usage

1. Enter a Sleeper username (and pick season + league), **or** paste a league ID.
2. Choose **Current rosters** and CSV or XLSX.
3. Generate and download the file.

## Notes

- Player names come from Sleeper’s full NFL player map (~5MB), cached for 24 hours.
- v1 supports current rosters only (starters, bench, taxi, IR).
