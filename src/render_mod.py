#!/usr/bin/env python3
"""Render one Recharge Priority installer variant and its expected lists.

Reads the patch rows in src/patches.tsv, keeps the rows in the asked
variant's scopes, writes the rendered Lua script and the expected values
that verify checks the built EXML against.

The table drives both, so a slot can never be patched without also being
checked, and the two can never drift apart.

Suit rows reorder a list the game already ships: one VALUE_CHANGE_TABLE
block walking the slots. Terrain rows write a list the game leaves empty:
the row's BASE column is empty and the block is a REPLACEatLINE that swaps
the empty ChargeBy head for the full list. A technology is one or the
other, never mixed.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def read_table(path):
    """Return the patch rows as (file, entry, index, base, value, scope)."""
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 6:
                raise SystemExit("bad patch row (need 6 tab separated fields): %r" % line)
            file_path, entry, index, base, value, scope = parts
            rows.append(
                (
                    file_path.strip(),
                    entry.strip(),
                    int(index),
                    base.strip(),
                    value.strip(),
                    scope.strip(),
                )
            )
    return rows


def check_groups(rows):
    """Every entry's slots must be contiguous from 0 and hold distinct fuels."""
    groups = {}
    for file_path, entry, index, base, value, _scope in rows:
        groups.setdefault((file_path, entry), []).append((index, base, value))
    for (file_path, entry), slots in groups.items():
        slots.sort()
        indices = [index for index, _, _ in slots]
        if indices != list(range(len(slots))):
            raise SystemExit(
                "%s: %s slots are %r, want 0..%d"
                % (file_path, entry, indices, len(slots) - 1)
            )
        values = [value for _, _, value in slots]
        if len(set(values)) != len(values):
            raise SystemExit(
                "%s: %s would list a fuel twice: %r" % (file_path, entry, values)
            )
        emptiness = {base == "" for _, base, _ in slots}
        if len(emptiness) != 1:
            raise SystemExit(
                "%s: %s mixes written and reordered slots" % (file_path, entry)
            )
    return groups


def vct_block(entry, slots):
    """A reorder block: walk the list one line at a time from slot 0."""
    lines = [
        "                {",
        '                    ["SPECIAL_KEY_WORDS"]   = {"ID", "%s"},' % entry,
        '                    ["PRECEDING_KEY_WORDS"] = {"ChargeBy"},',
        '                    ["LINE_OFFSET"]         = 1,',
        '                    ["VALUE_CHANGE_TABLE"]  = {',
    ]
    for _index, _base, value in sorted(slots):
        lines.append('                        {"ChargeBy", "%s"},' % value)
    lines += [
        "                    },",
        "                },",
    ]
    return "\n".join(lines)


def add_block(entry, slots):
    """A write block: swap the empty ChargeBy head for the full list."""
    lines = [
        "                {",
        '                    ["SPECIAL_KEY_WORDS"]   = {"ID", "%s"},' % entry,
        '                    ["PRECEDING_KEY_WORDS"] = {"ChargeBy"},',
        '                    ["ADD_OPTION"]          = "REPLACEatLINE",',
        '                    ["ADD"]                 = [[',
        '                        <Property name="ChargeBy" value="GcTechnologyChargeBy.xml">',
    ]
    for index, _base, value in sorted(slots):
        lines.append(
            '                        <Property name="ChargeBy" value="%s" _index="%d" />'
            % (value, index)
        )
    lines += [
        "                        </Property>]],",
        "                },",
    ]
    return "\n".join(lines)


def lua_value(text):
    """Quote a value for the rendered Lua script."""
    return '"%s"' % text.replace("\\", "\\\\").replace('"', '\\"')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", required=True)
    parser.add_argument("--desc", required=True)
    parser.add_argument("--scopes", required=True)
    parser.add_argument("--table", default=os.path.join(HERE, "patches.tsv"))
    parser.add_argument("--template", default=os.path.join(HERE, "recharge.lua.in"))
    parser.add_argument("--out-script", required=True)
    parser.add_argument("--out-expected", required=True)
    args = parser.parse_args()

    wanted_scopes = set(args.scopes.split())
    rows = [
        row for row in read_table(args.table) if row[5] in wanted_scopes
    ]
    if not rows:
        raise SystemExit("no patch rows for variant %r" % args.variant)
    groups = check_groups(rows)

    # Keep the table's order, one group per technology per file.
    order = []
    files = {}
    for file_path, entry, index, base, value, _scope in rows:
        key = (file_path, entry)
        if key not in files:
            files[key] = []
            order.append(key)
        files[key].append((index, base, value))

    blocks = []
    expected_lines = []
    file_order = []
    by_file = {}
    for key in order:
        file_path, entry = key
        slots = sorted(files[key])
        written = all(base == "" for _, base, _ in slots)
        if written:
            blocks.append(add_block(entry, slots))
        else:
            blocks.append(vct_block(entry, slots))
        for index, base, value in slots:
            expected_lines.append(
                "%s\t%s\t%d\t%s\t%s" % (file_path, entry, index, base, value)
            )
        if file_path not in by_file:
            by_file[file_path] = []
            file_order.append(file_path)
        by_file[file_path].append(blocks[-1])

    mbin_blocks = []
    for file_path in file_order:
        mbin_blocks.append(
            "            {\n"
            '                ["MBIN_FILE_SOURCE"]  = {%s},\n'
            '                ["MXML_CHANGE_TABLE"] = {\n'
            "%s\n"
            "                },\n"
            "            }," % (lua_value(file_path), "\n".join(by_file[file_path]))
        )

    with open(args.template, encoding="utf-8") as handle:
        template = handle.read()

    rendered = (
        template.replace("@VARIANT_LABEL@", args.variant)
        .replace("@DESC@", args.desc)
        .replace("@MBINBLOCKS@", "\n".join(mbin_blocks))
    )

    if "@" in rendered:
        leftover = [line for line in rendered.split("\n") if "@" in line]
        raise SystemExit("unsubstituted placeholder left in the script: %r" % leftover)

    with open(args.out_script, "w", encoding="utf-8") as handle:
        handle.write(rendered)
    with open(args.out_expected, "w", encoding="utf-8") as handle:
        handle.write("\n".join(expected_lines) + "\n")

    print(
        "rendered %s: %d technologies, %d slots"
        % (args.variant, len(order), len(expected_lines))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
