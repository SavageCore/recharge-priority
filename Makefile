# Recharge Priority
# Builds the loose-folder mod with the AMUMSS Linux port.
#
# What it does: the game spends the first recharge fuel it can find in a
# technology's ChargeBy list. This rewrites that order so Ion Batteries and
# Life Support Gel come first, and the raw substances stay behind them as
# fallbacks. No game binaries live in this repo: the 16 list slots are
# rendered into the script from src/patches.tsv.
#
# Usage:
#   make release      clean rebuild + verify + pack dist/ zip (default)
#   make verify       sanity-check the built output
#   make clean        remove build/ and dist/
#   make assets       regenerate the Nexus page header
#
# Override the AMUMSS install location if needed:
#   make AMUMSS_HOME=/path/to/AMUMSS release
#
# Game-update playbook (see README.md):
#   1. fetch latest MBINCompiler into AMUMSS_HOME
#   2. re-derive src/patches.tsv and src/vanilla-chargeby.tsv (see README.md)
#   3. bump VERSION below (the mod version, published on Nexus)
#   4. make release, import + deploy + test in game

AMUMSS_HOME ?= $(HOME)/AMUMSS
AMUMSS_LINUX ?= $(HOME)/Git/AMUMSS/linux

# The mod version, published as the version of the Nexus release. An
# unreleased build stays at 0.0.0; the first public release bumps this in the
# same commit that publishes it.
VERSION      := 0.1.0

MOD_SET      := Recharge Priority

SRC_TEMPLATE := src/recharge.lua.in
SRC_TABLE    := src/patches.tsv
SRC_VANILLA  := src/vanilla-chargeby.tsv

BUILD := build
DIST  := dist
STAMP := $(BUILD)/.built

RENDERED := $(BUILD)/recharge.lua
EXPECTED := $(BUILD)/recharge.expected.tsv

.NOTPARALLEL:

.PHONY: all release render build verify clean rootzip assets

all: release

# Single canonical artifact: the mod folder zipped as-is (Amethyst default
# import, or drop the folder into GAMEDATA/MODS). A
# single-configuration mod ships a plain zip and nothing else.
ROOTZIP := $(DIST)/$(MOD_SET).zip

release: clean render build verify rootzip
	@echo "release: $(ROOTZIP) (version $(VERSION))"

# The slots in src/patches.tsv drive the rendered script, so a slot can
# never ship without its check.
render: $(SRC_TEMPLATE) $(SRC_TABLE) src/render_mod.py
	@mkdir -p "$(BUILD)"
	@python3 src/render_mod.py --table "$(SRC_TABLE)" --template "$(SRC_TEMPLATE)" \
		--out-script "$(RENDERED)" --out-expected "$(EXPECTED)"

build: render
	@test -d "$(AMUMSS_HOME)/MODBUILDER" || (echo "ERROR: no AMUMSS install at $(AMUMSS_HOME)" >&2; exit 1)
	@test -x "$(AMUMSS_HOME)/MODBUILDER/MBINCompiler-linux" || (echo "ERROR: MBINCompiler-linux missing" >&2; exit 1)
	@if [ -d "$(AMUMSS_HOME)/ModScript" ]; then mv "$(AMUMSS_HOME)/ModScript" "$(AMUMSS_HOME)/ModScript.makebak"; trap 'rm -rf "$(AMUMSS_HOME)/ModScript"; mv "$(AMUMSS_HOME)/ModScript.makebak" "$(AMUMSS_HOME)/ModScript";' EXIT; fi
	@mkdir -p "$(AMUMSS_HOME)/ModScript"
	@cp "$(RENDERED)" "$(AMUMSS_HOME)/ModScript/recharge.lua"
	@rm -rf "$(AMUMSS_HOME)/CreatedMODS/$(MOD_SET)"
	@AMUMSS_HOME="$(AMUMSS_HOME)" "$(AMUMSS_LINUX)/buildmod.sh" --run-pipeline
	@rm -rf "$(AMUMSS_HOME)/ModScript"
	@if [ -d "$(AMUMSS_HOME)/ModScript.makebak" ]; then mv "$(AMUMSS_HOME)/ModScript.makebak" "$(AMUMSS_HOME)/ModScript"; fi
	@trap - EXIT
	@rm -rf "$(BUILD)/$(MOD_SET)" && mkdir -p "$(BUILD)/$(MOD_SET)"
	@cp -a "$(AMUMSS_HOME)/CreatedMODS/$(MOD_SET)/." "$(BUILD)/$(MOD_SET)/"
	@cp "$(RENDERED)" "$(BUILD)/$(MOD_SET)/recharge.lua"
	@touch "$(STAMP)"
	@echo "built: $(BUILD)/$(MOD_SET)"

verify: build
	@set -e; \
	if [ ! -d "$(BUILD)/$(MOD_SET)" ]; then echo "MISSING build output" >&2; exit 1; fi
	@python3 src/verify_build.py --build "$(BUILD)" --mod-set "$(MOD_SET)" \
		--expected "$(EXPECTED)" --vanilla "$(SRC_VANILLA)" --script "$(RENDERED)"

# Single install archive: the bare mod folder maps to GAMEDATA/MODS/.
rootzip: verify
	@rm -rf "$(BUILD)/rootzip" && mkdir -p "$(BUILD)/rootzip"
	@cp -a "$(BUILD)/$(MOD_SET)" "$(BUILD)/rootzip/"
	@rm -f "$(BUILD)/rootzip/$(MOD_SET)/AMUMSS_v"*.txt
	@mkdir -p "$(DIST)" && rm -f "$(ROOTZIP)" && cd "$(BUILD)/rootzip" && zip -qr "$(shell pwd)/$(ROOTZIP)" "$(MOD_SET)"
	@echo "packed: $(ROOTZIP) (version $(VERSION))"
	@unzip -l "$(ROOTZIP)" | tail -4

# Nexus page header from the source screenshot in assets/src/. The header
# is a build artifact and is not tracked; the screenshots and the
# typeface are. There is no generated gallery still: the before/after
# comparison stills in src/ upload to Nexus directly.
assets: assets/src/header-recharge-priority.jpg assets/generate.py
	python3 assets/generate.py

clean:
	rm -rf "$(BUILD)" "$(DIST)"
