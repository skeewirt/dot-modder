# DoT Modder (MVP)

GUI tool to view and edit The Doors of Trithius loadouts safely.

## Setup
- Windows + Python 3.11+ recommended
- `python -m venv .venv && .\.venv\Scripts\activate`
- `pip install -r requirements.txt`
- Set DOT.jar location:
  `setx DOT_JAR_PATH "C:\Program Files (x86)\Steam\steamapps\common\The Doors of Trithius\DOT.jar"`

## Run
`python -m app.main`

## Dev notes
- We deserialize `modules/loadouts.dat` through a Java helper in `tools/java/DumpLoadouts.java`.
- We never commit game files. The app extracts to `%TEMP%\dotmodder_*`.

## Roadmap
- Writer helper to patch `loadouts.dat`
- Backup/restore UI (per record / type / global) [wire to real backups]
- “Reapply my changes” patch store
