# برا السالفة — Bara Al-Salfa

A party spy game on one phone. Word lists are updated from your PC over Wi-Fi,
and the app keeps working offline from its saved copy.

**Current state: Stages 1–6** — PC server, phone sync, game rules with tests,
all six game screens, the Arabic font with the animated word reveal, and an
Android APK. A full game is playable on desktop, and the APK is ready to install
on a phone.

## Run it

```powershell
cd C:\work\bara_alsalfa
.\.venv\Scripts\python.exe server.py     # terminal 1: the PC server
.\.venv\Scripts\python.exe app.py        # terminal 2: the app
```

In VS Code, `F5` with **Run BOTH (server + app)** does the same thing.

The server prints the address to type in the app, e.g. `192.168.1.5:8000`.

## Word list

`words.json` holds 15 categories / 1,145 words (version 2): the 12 categories
from your PDF word guide plus the original three small lists. When you edit it,
increase `version` by 1 and press مزامنة in the app — a phone that synced before
the edit keeps its old copy until you do. The APK does **not** contain the word
list, so adding words never needs a rebuild.

## Build the Android APK

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\flet.exe build apk --yes --no-rich-output
```

The file appears at `build\apk\bara-alsalfa.apk`. The first build downloads
Flutter and a JDK; later builds reuse them. Copy the APK to the phone, allow
installing unknown apps, and put the phone on the same Wi-Fi as the server.

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
| `test_game.py` | 22 tests, one per rule |
| `pyproject.toml` | what `flet build apk` reads |
| `assets/fonts/` | Tajawal, the Arabic font the app draws with |
| `local_words.json` | created by the app — the copy kept on the phone |
| `pc_address.txt` | created by the app — the last PC address |
