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

## Current file structure

```
internal_jira_he_releases/
│
├── config.ini.example       # credential template
├── requirements.txt
│
├── jira_client.py           # connect_jira()
│
└── tests/
    └── test_jira_client.py
```

---

## Running tests

```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```
