# Recharge Priority
# Builds the FOMOD installer with the AMUMSS Linux port.
#
# What it does: the game spends the first recharge fuel it can find in a
# technology's ChargeBy list. The suit option rewrites that order so Ion
# Batteries and Life Support Gel come first, and the raw substances stay
# behind them as fallbacks. The Terrain Manipulator ships no list at all,
# only a substance category, so the terrain option writes one: Silicate
# Powder first, the three ferrites behind it. No game binaries live in
# this repo: every list slot is rendered into the scripts from
# src/patches.tsv.
#
# Usage:
#   make release      clean + rebuild + verify + pack dist/ zip (default)
#   make verify       sanity-check the built outputs and the installer
#   make clean        remove build/ and dist/
#   make assets       regenerate the Nexus page header
#
# Override the AMUMSS install location if needed:
#   make AMUMSS_HOME=/path/to/AMUMSS release
#
# Game-update playbook (see README.md):
#   1. fetch latest MBINCompiler into AMUMSS_HOME
#   2. re-derive the bases in src/patches.tsv (see README.md)
#   3. bump VERSION below (the mod version, published on Nexus)
#   4. make release, import + deploy + test in game

AMUMSS_HOME ?= $(HOME)/AMUMSS
AMUMSS_LINUX ?= $(HOME)/Git/AMUMSS/linux

# The mod version, published as the version of the Nexus release. An
# unreleased build stays at 0.0.0; the first public release bumps this in the
# same commit that publishes it. The version is deliberately not part of the
# mod name: the artifact is named after the mod alone (see FOMOD_ZIP), because
# a mod manager names the installed mod after the archive file name and shows
# the version in a column of its own.
VERSION      := 0.1.0

MOD_SET      := Recharge Priority

SRC_TEMPLATE := src/recharge.lua.in
SRC_TABLE    := src/patches.tsv
SRC_VANILLA  := src/vanilla-chargeby.tsv

BUILD := build
DIST  := dist
STAMP := $(BUILD)/.built

# Installer variants. Each variant label names the rendered script, the
# CreatedMODS folder, the fomod source folder and the in-game pak suffix,
# so it must match ModuleConfig.xml exactly. Separate toggles are not
# offered: both options ship the same EXML path, so two folders would
# overwrite each other and the last one would win regardless of the pick.
VARIANT := full suit-only terrain-only

# The scopes each variant renders: the tags in src/patches.tsv whose rows
# carry this variant's lists.
SCOPES_full         := suit terrain
SCOPES_suit-only    := suit
SCOPES_terrain-only := terrain

DESC_full         := Ion Batteries and Life Support Gel first for every suit recharge, Silicate Powder first for the Terrain Manipulator
DESC_suit-only    := Ion Batteries and Life Support Gel first in every suit recharge list
DESC_terrain-only := Silicate Powder first for the Terrain Manipulator

RENDERED := $(addprefix $(BUILD)/,$(addsuffix .lua,$(VARIANT)))
EXPECTED := $(addprefix $(BUILD)/,$(addsuffix .expected.tsv,$(VARIANT)))

# clean runs before build runs before verify, so release must not be parallel.
.NOTPARALLEL:

.PHONY: all release build verify assets clean

all: release

# The artifact is named after the mod and nothing else, for the same reason
# the mod name carries no version: the file name is what a mod manager shows
# as the mod name.
FOMOD_ZIP := $(DIST)/$(MOD_SET).zip

release: clean build verify
	@rm -rf "$(BUILD)/fomodz" && mkdir -p "$(BUILD)/fomodz/fomod" $(addprefix "$(BUILD)/fomodz/",$(VARIANT))
	@set -e; for v in $(VARIANT); do cp -a "$(BUILD)/$(MOD_SET) - $$v/." "$(BUILD)/fomodz/$$v/"; done
	@cp src/ModuleConfig.xml "$(BUILD)/fomodz/fomod/"
	@mkdir -p "$(DIST)" && rm -f "$(FOMOD_ZIP)" && cd "$(BUILD)/fomodz" && zip -qr "$(shell pwd)/$(FOMOD_ZIP)" fomod $(VARIANT)
	@python3 src/verify_installer.py --config src/ModuleConfig.xml --archive "$(FOMOD_ZIP)" --mod-set "$(MOD_SET)" --variants "$(VARIANT)"
	@echo "packed: $(FOMOD_ZIP) (version $(VERSION))"

# Render one variant: the script and the expected values that verify checks
# the built EXML against. The guard turns a typo in VARIANT into a loud
# failure rather than a script with no patches.
$(BUILD)/%.lua $(BUILD)/%.expected.tsv: $(SRC_TEMPLATE) $(SRC_TABLE) src/render_mod.py
	@mkdir -p "$(BUILD)"
	@test -n "$(SCOPES_$*)" -a -n "$(DESC_$*)" || { echo "ERROR: unknown variant '$*' - add SCOPES_$* and DESC_$* to the Makefile" >&2; exit 1; }
	@python3 src/render_mod.py --variant "$*" --desc "$(DESC_$*)" --scopes "$(SCOPES_$*)" --table "$(SRC_TABLE)" \
		--template "$(SRC_TEMPLATE)" \
		--out-script "$(BUILD)/$*.lua" --out-expected "$(BUILD)/$*.expected.tsv"

# One pipeline run builds every variant as an individual mod.
build: $(RENDERED)
	@test -d "$(AMUMSS_HOME)/MODBUILDER" || (echo "ERROR: no AMUMSS install at $(AMUMSS_HOME) (set AMUMSS_HOME=...)" >&2; exit 1; )
	@test -x "$(AMUMSS_HOME)/MODBUILDER/MBINCompiler-linux" || (echo "ERROR: run $(AMUMSS_LINUX)/scripts/fetch_mbincompiler.sh with AMUMSS_HOME=$(AMUMSS_HOME) first" >&2; exit 1; )
	@mkdir -p "$(BUILD)"
	@set -e; \
	if [ -d "$(AMUMSS_HOME)/ModScript" ]; then mv "$(AMUMSS_HOME)/ModScript" "$(AMUMSS_HOME)/ModScript.makebak"; trap 'rm -rf "$(AMUMSS_HOME)/ModScript"; mv "$(AMUMSS_HOME)/ModScript.makebak" "$(AMUMSS_HOME)/ModScript"' EXIT; fi; \
	mkdir -p "$(AMUMSS_HOME)/ModScript"; \
	cp $(RENDERED) "$(AMUMSS_HOME)/ModScript/"; \
	for v in $(VARIANT); do rm -rf "$(AMUMSS_HOME)/CreatedMODS/$(MOD_SET) - $$v"; done; \
	AMUMSS_HOME="$(AMUMSS_HOME)" "$(AMUMSS_LINUX)/buildmod.sh" --run-pipeline; \
	rm -rf "$(AMUMSS_HOME)/ModScript"; \
	if [ -d "$(AMUMSS_HOME)/ModScript.makebak" ]; then mv "$(AMUMSS_HOME)/ModScript.makebak" "$(AMUMSS_HOME)/ModScript"; fi; \
	trap - EXIT
	@set -e; for v in $(VARIANT); do \
		rm -rf "$(BUILD)/$(MOD_SET) - $$v"; \
		mkdir -p "$(BUILD)/$(MOD_SET) - $$v"; \
		cp -a "$(AMUMSS_HOME)/CreatedMODS/$(MOD_SET) - $$v"/* "$(BUILD)/$(MOD_SET) - $$v/"; \
		cp "$(BUILD)/$$v.lua" "$(BUILD)/$(MOD_SET) - $$v/$$v.lua"; \
		rm -f "$(BUILD)/$(MOD_SET) - $$v/AMUMSS_v"*.txt; \
	done
	@touch "$(STAMP)"
	@echo "built: $(foreach v,$(VARIANT),$(BUILD)/$(MOD_SET) - $(v) )"

# verify_build.py checks each built EXML against its rendered table.
# verify_installer.py checks that ModuleConfig.xml offers exactly the shipped
# variants, one folder per plugin, and that every offered folder was built.
# It also rejects conditional file installs: Amethyst applies every pattern in
# one regardless of the flags, which would install every variant at once.
verify: build
	@for n in "$$(sed -n 's:.*<moduleName>\(.*\)</moduleName>.*:\1:p' src/ModuleConfig.xml)" "$(MOD_SET)"; do \
		if printf '%s' "$$n" | grep -qE '[vV]?[0-9]+(\.[0-9]+)+'; then \
			echo "ERROR: the mod name must not carry a version: '$$n'" >&2; exit 1; \
		fi; \
	done
	@python3 src/verify_build.py --build "$(BUILD)" --mod-set "$(MOD_SET)" --variants "$(VARIANT)" --vanilla "$(SRC_VANILLA)"
	@python3 src/verify_installer.py --config src/ModuleConfig.xml --build "$(BUILD)" --mod-set "$(MOD_SET)" --variants "$(VARIANT)" --diag ""

# Nexus page header from the source screenshot in assets/src/. The header
# is a build artifact and is not tracked; the screenshots and the
# typeface are. There is no generated gallery still: the before/after
# comparison stills in src/ upload to Nexus directly.
assets: assets/src/header-recharge-priority.jpg assets/generate.py
	python3 assets/generate.py

clean:
	rm -rf "$(BUILD)" "$(DIST)"
