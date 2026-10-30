#!/usr/bin/env python3
"""Check the built Recharge Priority installer variants.

For every variant this asserts:

  1. the built EXML exists and was produced by this run, not carried over
     from a previous one
  2. every patched technology carries exactly the charge list the patch
     table asks for, slot by slot and with no slot left over
  3. the EXML patches those technologies and no others, and carries
     nothing but the charge list for each of them
  4. the patch table's BASE column still matches the vanilla snapshot in
     src/vanilla-chargeby.tsv - or, for a written list, is still absent
     from it, so a game update that ships its own list fails here loudly
     instead of silently doubling one
  5. there are no AMUMSS marker attributes or marker tags left behind,
     which would leave the patch visibly annotated in game

Job 1 covers the failure mode the others cannot see. The build copies out
of the AMUMSS CreatedMODS directory, which is a persistent directory this
mod does not own. When a script changes nothing AMUMSS creates nothing and
leaves the previous build's file sitting there, and the copy then succeeds
and the other jobs happily validate last week's output.
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET

TABLE_REL = "METADATA/REALITY/TABLES/NMS_REALITY_GCTECHNOLOGYTABLE.EXML"


def read_expected(path):
    """Return the expected rows as {entry: [value by slot]} plus the bases."""
    lists = {}
    bases = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) != 5:
                raise SystemExit("bad expected row (need 5 fields): %r" % line)
            _file_path, entry, index, base, value = parts
            index = int(index)
            lists.setdefault(entry, {})[index] = value
            bases[(entry, index)] = base
    return lists, bases


def read_vanilla(path):
    """Return the vanilla charge lists as {entry: [value by slot]}."""
    lists = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            entry, index, value = line.split("\t")
            lists.setdefault(entry, {})[int(index)] = value
    return lists


def ordered(slots, entry, where):
    """Turn a slot map into a list, insisting the slots are 0..n-1."""
    indices = sorted(slots)
    if indices != list(range(len(indices))):
        raise SystemExit("%s: %s slots are %r, want 0..n-1" % (where, entry, indices))
    return [slots[index] for index in indices]


def load_built(path):
    """Return the built charge lists and the entry elements that carry them."""
    root = ET.parse(path).getroot()
    outer = None
    for child in root:
        if child.tag == "Property" and child.get("name") == "Table":
            outer = child
            break
    if outer is None:
        raise SystemExit("%s: no Table section" % path)

    lists = {}
    elements = {}
    for entry_el in outer:
        if entry_el.tag != "Property" or entry_el.get("name") != "Table":
            continue
        entry = entry_el.get("_id")
        if not entry:
            continue
        heading = None
        for child in entry_el:
            if child.tag == "Property" and child.get("name") == "ChargeBy":
                heading = child
                break
        if heading is None:
            continue
        slots = {}
        for item in heading:
            if item.tag != "Property" or item.get("name") != "ChargeBy":
                raise SystemExit(
                    "%s: %s has an unexpected %r inside ChargeBy"
                    % (path, entry, item.get("name"))
                )
            index = item.get("_index")
            if index is None:
                raise SystemExit("%s: %s has a ChargeBy slot without _index" % (path, entry))
            slots[int(index)] = item.get("value")
        lists[entry] = ordered(slots, entry, path)
        elements[entry] = entry_el
    return lists, elements


def check_variant(build, mod_set, variant, expected_path, vanilla, failures):
    """Check one variant, appending any problems to failures."""
    script = os.path.join(build, "%s.lua" % variant)
    exml = os.path.join(
        build, "%s - %s" % (mod_set, variant), TABLE_REL.replace("/", os.sep)
    )

    if not os.path.isfile(exml):
        failures.append("%s: MISSING %s" % (variant, TABLE_REL))
        return
    if os.path.getmtime(exml) < os.path.getmtime(script):
        failures.append(
            "%s: STALE %s - older than the script that should have produced it"
            % (variant, TABLE_REL)
        )

    with open(exml, encoding="utf-8") as handle:
        text = handle.read()
    if "!#" in text:
        failures.append("%s: marker tags present in %s" % (variant, TABLE_REL))
    if "_remove=" in text or "_overwrite=" in text:
        failures.append("%s: AMUMSS marker attributes left in %s" % (variant, TABLE_REL))

    expected, bases = read_expected(expected_path)
    built, built_elements = load_built(exml)

    # Job 2: the patched lists, slot by slot.
    for entry, slots in expected.items():
        want = ordered(slots, entry, expected_path)
        if entry not in built:
            failures.append("%s: %s has no charge list" % (variant, entry))
            continue
        if built[entry] != want:
            failures.append(
                "%s: %s charge list is %r, want %r"
                % (variant, entry, built[entry], want)
            )

    # Job 3: the EXML is a list of line replacements, so it must carry the
    # patched technologies only.
    extra = sorted(set(built) - set(expected))
    if extra:
        failures.append(
            "%s: patched technologies the table does not name: %s"
            % (variant, ", ".join(extra))
        )

    # Job 4: the table still patches what the game actually ships. An
    # empty BASE means the game ships no slot there: the list is written,
    # not reordered, and any shipped slot is a surprise.
    for (entry, index), base in sorted(bases.items()):
        shipped = vanilla.get(entry, {}).get(index)
        if base == "":
            if shipped is not None:
                failures.append(
                    "%s: %s slot %d is written but the vanilla snapshot ships %r"
                    % (variant, entry, index, shipped)
                )
        elif shipped != base:
            failures.append(
                "%s: %s slot %d: BASE is %r but the vanilla snapshot has %r"
                % (variant, entry, index, base, shipped)
            )

    # Job 3, continued: each patched row must carry the charge list and
    # nothing else.
    for entry in expected:
        if entry not in built:
            continue
        names = [child.get("name") for child in built_elements[entry]]
        if names != ["ChargeBy"]:
            failures.append(
                "%s: %s patches %r, want only the ChargeBy list" % (variant, entry, names)
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", required=True)
    parser.add_argument("--mod-set", required=True)
    parser.add_argument("--variants", required=True)
    parser.add_argument("--vanilla", required=True)
    args = parser.parse_args()

    vanilla = read_vanilla(args.vanilla)

    failures = []
    variants = args.variants.split()
    for variant in variants:
        expected_path = os.path.join(args.build, "%s.expected.tsv" % variant)
        check_variant(args.build, args.mod_set, variant, expected_path, vanilla, failures)

    if failures:
        for failure in failures:
            print("BAD " + failure, file=sys.stderr)
        return 1
    print(
        "verify: OK (variants %s, all fresh this run, no marker attributes)"
        % ", ".join(variants)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
