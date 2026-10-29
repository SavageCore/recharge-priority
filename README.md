# Recharge Priority

The quick menu spends the first recharge fuel it can find in a technology's
fuel list. This mod makes that an Ion Battery or a Life Support Gel, so
recharging stops eating oxygen, sodium and dioxite while the crafted fuels
sit unused in the inventory.

## Recharge order

| Technology | Order after this mod |
|---|---|
| Life Support | Life Support Gel, Oxygen, Dioxite |
| Hazard Protection | Ion Battery, Sodium, Sodium Nitrate |
| Thermal shield | Ion Battery, Phosphorus |
| Cold shield | Ion Battery, Dioxite |
| Radiation shield | Ion Battery, Uranium |
| Toxic shield | Ion Battery, Ammonia |
| Underwater shield | Life Support Gel, Oxygen |

Nothing is removed. If the batteries or the gel run out, the game falls back
down the list exactly as it does now.

## Install

Single zip, no installer options. Copy the `Recharge Priority` folder inside
the zip into `GAMEDATA/MODS/`, or import the zip with Amethyst or Vortex.
The `recharge.lua` in the folder is the AMUMSS script, for merging with a
larger AMUMSS build.

## Compatibility

Built for Forsaken. It edits
`METADATA/REALITY/TABLES/NMS_REALITY_GCTECHNOLOGYTABLE.MBIN` as EXML line
replacements, so it works alongside mods that change other lines of that
table. Another mod that rewrites these same seven fuel lists will conflict.

## Re-deriving on a game update

The fuel order lives in the `ChargeBy` list of each technology in the
technology table. After a game update:

1. Fetch the latest MBINCompiler (`AMUMSS_HOME`, see the Makefile).
2. Extract and decompile the table from the installed PAKs:

   ```
   hgpaktool -U -O /tmp/gt -f "METADATA/REALITY/TABLES/NMS_REALITY_GCTECHNOLOGYTABLE.MBIN" \
       "$HOME/.steam/steam/steamapps/common/No Man's Sky/GAMEDATA/PCBANKS/NMSARC.Precache.pak"
   "$HOME/AMUMSS/MODBUILDER/MBINCompiler-linux" /tmp/gt/metadata/reality/tables/nms_reality_gctechnologytable.mbin
   python3 src/dump_vanilla.py /tmp/gt/metadata/reality/tables/nms_reality_gctechnologytable.MXML \
       > src/vanilla-chargeby.tsv
   ```

3. Compare the 16 rows in `src/patches.tsv` against the new snapshot. Every
   `BASE` value must still match the slot it replaces, and each of the seven
   lists must still have the same number of slots.
4. `make release`. The verify step fails loudly if a slot moved.

## Build

```
make release
```

Needs the AMUMSS Linux port and `MBINCompiler-linux`
(`AMUMSS_HOME`, default `~/AMUMSS`). `make release` verifies the built table,
then packs `dist/Recharge Priority.zip`.
