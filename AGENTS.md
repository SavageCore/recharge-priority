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
  every patched list is listed, including slots that do not move.
- `src/vanilla-chargeby.tsv` is the snapshot of the game's lists that verify
  compares against. Regenerate it after a game update before touching the patch
  table.
- The mod patches `ChargeBy` lists by slot index under the technology `ID`,
  starting at slot 0 with `LINE_OFFSET 1`. A technology whose list changes shape
  makes verify fail rather than ship half patched.
