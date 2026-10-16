# Failed nightly run — 2026-10-16

No digest was generated, so nothing from this run was committed (DB changes discarded).

- First attempt: News, YouTube, writeups, docx steps failed with `ModuleNotFoundError` (`requests`, `docx`). `pip` (/usr/bin/pip) installs to a different interpreter than `python3` (/usr/local/bin/python3), and `pip install --upgrade pip` failed (Debian-managed). Second attempt used `python3 -m pip install -r requirements.txt` and sourcing steps then succeeded.
- Second attempt: `generate_digest.py` crashed at line 76 (`build_digest`, `top_substance` sort):
  `TypeError: '<' not supported between instances of 'int' and 'str'`.
  Cause: a row has a non-numeric `substance_score` (str) mixed with ints; `trend_score` is handled by `is_numeric_trend` but `substance_score` is not. Likely introduced by newly sourced data.
- Consequence: no `digests/2026-10-16.md`; writeup and docx steps had 0 items.
- Not fixed per routine rules (no script changes). Needs owner review.
