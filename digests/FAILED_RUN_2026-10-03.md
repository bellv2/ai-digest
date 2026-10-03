# Failed nightly run 2026-10-03

- Schema migration, news sourcing, YouTube sourcing: OK
- Digest generation: FAILED. `generate_digest.py` line 76 (`build_digest`) raised
  `TypeError: '<' not supported between instances of 'str' and 'int'` while sorting
  top_substance (a score column appears to hold a string value in at least one row).
- No digest file was produced for 2026-10-03, so writeups and docx were skipped (0 items).
- Per routine rules, no data changes were committed. Not fixed automatically.
