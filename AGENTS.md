# Project instructions — برا السالفة

Arabic party spy game ("who is out of the loop") played by a group passing **one
phone** around. Flet UI, plain JSON files on disk, no internet required after the
first sync. Everything on screen is Arabic and right-to-left.

The user is learning as we build, so code is written to be read, not to be clever.

## How the user wants this built

- **Smallest code that works.** No abstractions, no "just in case" code. If a
  line is not needed for the current stage, it does not exist.
- **One stage at a time.** Do not build the whole feature at once. The user runs
  and tests each stage, then reports back before the next one starts.
- **Every file gets a note** in `notes/` saying what it does and *why* each
  choice was made, including the choices that were rejected.
- **Rules live in `game.py`.** Screens never re-implement a rule; they ask the
  `Game` object and draw its answer.

## Read this first (local only)

`notes/00-how-we-work.md` — the index of every note, the file table, and the
stage plan. Each note explains one code file end to end.

`notes/` and `specs/` are deliberately **not committed** and are not in the
remote. They exist in a working copy only. Do not add them to git, and do not
treat their absence in a fresh clone as something missing.

## Current state: Stage 5 is done

Stages 1–5 are complete and tested by playing:

1. PC server that serves the word list.
2. Phone-side sync plus an offline saved copy.
3. Game rules in `game.py`, covered by tests.
4. All six screens, including settings — one full game is playable on desktop.
5. Bundled Tajawal font, a scaled reveal animation, vibration on the reveal.

Remaining work:

- **Stage 6** — build the Android APK and run it on a real phone over Wi-Fi.
  Vibration can only be felt there.
- **Stage 7** — optional PC editor, local network discovery, cloud sync.

Ask the user which of these to start; do not assume.

## Careful: `specs/` is not a to-do list

`specs/stage-4-game-screens.md` describes work that is **already implemented**.
Its problem statement lists six bugs (backwards round screen, impossible round
number, typed spy guess, lost vote requests, moving buttons, sync leaving the
home screen) — all six are fixed in the current code, and its last open item
(the vote-request counter, plus its six tests) is done too. Do not re-implement
any of it.

## One test seam

`game.py` plus `test_game.py` is the only automated seam in the project, and that
is deliberate. Tests are plain `assert`s in one file, run directly by the
interpreter — no pytest, no fixtures. Scenarios are made deterministic by forcing
attributes such as `game.spy` or `game.played` after construction.

Screens and layout are verified by playing the game, not by tests. When a rule
bug is only reachable from a screen, the fix is to move that rule into `Game` —
not to add a browser-driven test.

## Run and test

```powershell
cd C:\work\bara_alsalfa
.\.venv\Scripts\python.exe server.py      # PC side; prints its LAN address
.\.venv\Scripts\python.exe app.py         # the game
.\.venv\Scripts\python.exe test_game.py   # 13 rule tests, must end "all tests passed"
```

Dependencies are pinned in `requirements.txt`; the virtual environment is
`.venv` and is not committed. Data files: `words.json` (on the PC, carries a
`version` that must be bumped when words change), `local_words.json` and
`pc_address.txt` (created at runtime by the app, not committed).

## Notes on the environment

- Windows, PowerShell. The console is cp1252 — keep test output ASCII.
- Flet's web preview can stop accepting clicks after the browser window is
  resized. Reloading the page fixes it; it is not an app bug.
- When testing the UI headlessly, the Flet Python session survives a page reload,
  so code changes need a server restart.
