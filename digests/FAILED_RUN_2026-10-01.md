# Failed nightly run 2026-10-01

- Schema migration, news sourcing, YouTube sourcing: OK (YouTube transcript fetches blocked by cloud IP; non-fatal).
- Digest generation: FAILED. `generate_digest.py` line 76, `build_digest`: `TypeError: '<' not supported between instances of 'int' and 'str'` in the sorted() over top_substance (mixed int/str score values in the data).
- No digest generated for 2026-10-01; writeup and docx steps skipped (0 items).
- `pip install --upgrade pip` failed (Debian-managed pip); requirements installed fine.
- Nothing fixed automatically; data changes not committed.
