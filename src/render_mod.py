#!/usr/bin/env python3
"""Render the Recharge Priority Lua script and its expected charge lists.

Reads the patch table in src/patches.tsv, writes the rendered Lua script and
the expected values that verify checks the built EXML against.

The table drives both, so a value can never be patched without also being
checked, and the two can never drift apart.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def read_table(path):
    """Return the patch rows as (file, entry, index, base, value) tuples."""
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 5:
                raise SystemExit("bad patch row (need 5 tab separated fields): %r" % line)
            file_path, entry, index, base, value = parts
            rows.append(
                (
                    file_path.strip(),
                    entry.strip(),
                    int(index),
                    base.strip(),
                    value.strip(),
                )
            )
    return rows


def check_groups(rows):
    """Every entry's slots must be contiguous from 0 and hold distinct fuels."""
    groups = {}
    for file_path, entry, index, _base, value in rows:
        groups.setdefault((file_path, entry), []).append((index, value))
    for (file_path, entry), slots in groups.items():
        slots.sort()
        indices = [index for index, _ in slots]
        if indices != list(range(len(slots))):
            raise SystemExit(
                "%s: %s slots are %r, want 0..%d"
                % (file_path, entry, indices, len(slots) - 1)
            )
        values = [value for _, value in slots]
        if len(set(values)) != len(values):
            raise SystemExit(
                "%s: %s would list a fuel twice: %r" % (file_path, entry, values)
            )
    return groups


def lua_value(text):
    """Quote a value for the rendered Lua script."""
    return '"%s"' % text.replace("\\", "\\\\").replace('"', '\\"')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", default=os.path.join(HERE, "patches.tsv"))
    parser.add_argument("--template", default=os.path.join(HERE, "recharge.lua.in"))
    parser.add_argument("--out-script", required=True)
    parser.add_argument("--out-expected", required=True)
    args = parser.parse_args()

    rows = read_table(args.table)
    if not rows:
        raise SystemExit("no patch rows in %s" % args.table)
    check_groups(rows)

    # Keep the table's order, and one group per technology.
    order = []
    groups = {}
    for file_path, entry, index, base, value in rows:
        key = (file_path, entry)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append((index, base, value))

    patch_lines = []
    expected_lines = []
    for key in order:
        file_path, entry = key
        slots = sorted(groups[key])
        for index, _base, value in slots:
            patch_lines.append(
                "    { file = %s, entry = %s, index = %d, value = %s },"
                % (lua_value(file_path), lua_value(entry), index, lua_value(value))
            )
        for index, base, value in slots:
            expected_lines.append(
                "%s\t%s\t%d\t%s\t%s" % (file_path, entry, index, base, value)
            )

    with open(args.template, encoding="utf-8") as handle:
        template = handle.read()

    rendered = template.replace("@PATCHES@", "\n".join(patch_lines))

    if "@" in rendered:
        leftover = [line for line in rendered.split("\n") if "@" in line]
        raise SystemExit("unsubstituted placeholder left in the script: %r" % leftover)

    with open(args.out_script, "w", encoding="utf-8") as handle:
        handle.write(rendered)
    with open(args.out_expected, "w", encoding="utf-8") as handle:
        handle.write("\n".join(expected_lines) + "\n")

    print(
        "rendered: %d technologies, %d slots"
        % (len(order), len(expected_lines))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
