# internal_jira_he_releases

Fetch Jira release epics and build a visual timeline for each release's child work items.

---

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy the example config and fill in your credentials:

```bash
cp config.ini.example config.ini
```

`config.ini` is git-ignored and must never be committed.

---

## Usage

```bash
# Console output
python main.py --release 2025.8.0

# Explicit output format
python main.py --release 2025.8.0 --output console
```

---

## File structure

```
internal_jira_he_releases/
│
├── config.ini.example       # credential template
├── requirements.txt
├── main.py                  # CLI entry point
│
├── jira_client.py           # connect_jira(), search_jql(), fetch_changelog()
├── jira_fetch.py            # fetch_release_epics(), fetch_children()
├── models.py                # Epic, ChildIssue dataclasses
├── utils.py                 # extract_version(), fmt_date(), parse_date(), esc()
│
├── renderers/
│   ├── console.py           # print_timeline()  (--output console)
│   └── html/                # HTML renderer (planned)
│
└── tests/
```

---

## Running tests

```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```
