#!/usr/bin/env python3
"""Write the vanilla charge lists snapshot from a decompiled technology table.

Usage:
  python3 src/dump_vanilla.py path/to/NMS_REALITY_GCTECHNOLOGYTABLE.MXML \
      > src/vanilla-chargeby.tsv

The snapshot is what verify compares every technology the mod does not patch
against, so it has to be regenerated whenever a game update changes the
table. See the README for how to extract and decompile the table.
"""

import sys
import xml.etree.ElementTree as ET


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: dump_vanilla.py <decompiled GCTECHNOLOGYTABLE MXML>")

    root = ET.parse(sys.argv[1]).getroot()
    outer = None
    for child in root:
        if child.tag == "Property" and child.get("name") == "Table":
            outer = child
            break
    if outer is None:
        raise SystemExit("no Table section")

    rows = []
    for entry_el in outer:
        if entry_el.tag != "Property" or entry_el.get("name") != "Table":
            continue
        entry = entry_el.get("_id")
        if not entry:
            continue
        for child in entry_el:
            if child.tag != "Property" or child.get("name") != "ChargeBy":
                continue
            for item in child:
                if item.tag != "Property" or item.get("name") != "ChargeBy":
                    raise SystemExit("%s: unexpected %r inside ChargeBy" % (entry, item.get("name")))
                rows.append((entry, int(item.get("_index")), item.get("value")))

    for entry, index, value in rows:
        print("%s\t%d\t%s" % (entry, index, value))


if __name__ == "__main__":
    main()
