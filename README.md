# برا السالفة — Bara Al-Salfa

A party spy game on one phone. Word lists are updated from your PC over Wi-Fi,
and the app keeps working offline from its saved copy.

**Current state: Stages 1–4** — PC server, phone sync, game rules with tests, and
all six game screens. A full game is playable on desktop right now. Stage 5 adds
the Arabic font and polish; Stage 6 builds the APK.

## Run it

```powershell
cd C:\work\bara_alsalfa
.\.venv\Scripts\python.exe server.py     # terminal 1: the PC server
.\.venv\Scripts\python.exe app.py        # terminal 2: the app
```

In VS Code, `F5` with **Run BOTH (server + app)** does the same thing.

The server prints the address to type in the app, e.g. `192.168.1.5:8000`.

## Test the rules

```powershell
.\.venv\Scripts\python.exe test_game.py
```

## Files

| File | Role |
|---|---|
| `server.py` | PC: answers `/version` and `/data` |
| `words.json` | your categories and words (bump `version` when you edit) |
| `app.py` | phone: syncs, saves locally, and the six game screens |
| `game.py` | the rules: spy, word, pairs, scoring — no UI |
| `test_game.py` | seven tests, one per rule |
| `local_words.json` | created by the app — the copy kept on the phone |
| `pc_address.txt` | created by the app — the last PC address |
