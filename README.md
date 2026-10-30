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
| Terrain Manipulator | Silicate Powder, Ferrite Dust, Pure Ferrite, Magnetised Ferrite |

Nothing is removed. If the batteries or the gel run out, the game falls back
down the list exactly as it does now. The Terrain Manipulator ships no fuel
list at all, only a substance category, so its row is written rather than
reordered: Silicate Powder first, the three ferrites behind it in refinery
order, cheapest first.

## Install

The zip is a FOMOD installer: import it with Amethyst or Vortex and pick
suit and Terrain Manipulator, suit only, or Terrain Manipulator only. Each
option's folder also carries its AMUMSS `.lua` script, for merging with a
larger AMUMSS build.

## Compatibility

Built for Forsaken. It edits
`METADATA/REALITY/TABLES/NMS_REALITY_GCTECHNOLOGYTABLE.MBIN` as EXML line
replacements, so it works alongside mods that change other lines of that
table. Another mod that rewrites these same eight fuel lists will conflict.

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

3. Compare the 20 rows in `src/patches.tsv` against the new snapshot. Every
   `BASE` value must still match the slot it replaces, and each of the eight
   lists must still have the same number of slots. The four TERRAINEDITOR
   rows carry an empty `BASE`: the game must still ship no list there.
4. `make release`. The verify step fails loudly if a slot moved.

## Build

```
make release
```

Needs the AMUMSS Linux port and `MBINCompiler-linux`
(`AMUMSS_HOME`, default `~/AMUMSS`). `make release` verifies the built table,
then packs `dist/Recharge Priority.zip`.
