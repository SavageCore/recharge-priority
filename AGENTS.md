# AGENTS.md

## Versioning

- The mod version is `VERSION` in the `Makefile`. An unreleased build stays at
  `0.0.0`; the first public release bumps it in the same commit that publishes
  it.
- The version-bump commit touches only the version line, and its message is the
  version and nothing else.
- Release tags are `v`-prefixed (`v0.1.0`), applied to the bump commit when it
  is pushed, never later.

## Fuel lists

- `src/patches.tsv` is the single source for the recharge order. Every slot of
  every patched list is listed, including slots that do not move. The `SCOPE`
  column tags which installer variants carry the row: `suit` rows ship in
  `full` and `suit-only`, `terrain` rows in `full` and `terrain-only`.
- `src/vanilla-chargeby.tsv` is the snapshot of the game's lists that verify
  compares against. Regenerate it after a game update before touching the patch
  table.
- The mod patches `ChargeBy` lists by slot index under the technology `ID`,
  starting at slot 0 with `LINE_OFFSET 1`. A technology whose list changes shape
  makes verify fail rather than ship half patched.
- A row with an empty `BASE` is written, not reordered: the game ships no slot
  there, and the render emits a `REPLACEatLINE` block swapping the empty
  `ChargeBy` head for the full list. TERRAINEDITOR is the case: it charges by
  substance category (`Metal`), so the mod gives it an explicit ordered list
  with Silicate Powder first. All four `Metal` substances are listed, so the
  fallback set is exactly what the category offered.
- One install step, `SelectExactlyOne`, three prebuilt variants (`full`,
  `suit-only`, `terrain-only`). Separate toggles are not offered: both options
  ship the same EXML path, so two folders would overwrite each other.
