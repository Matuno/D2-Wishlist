import json
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from d2_wishlist.dim_loadouts import (
    DIM_LONG_BASE,
    DimManifestLookup,
    build_dim_loadout_url,
    build_loadout_for_doc,
    parse_build_doc,
    rewrite_build_doc_dim_link,
)


class DimLoadoutUrlTests(unittest.TestCase):
    def test_build_dim_loadout_url_round_trips_loadout_json(self):
        loadout = {
            "id": "monument-hunter-arc",
            "name": "Hunter Arc - Shinobu Arcworks",
            "classType": 1,
            "equipped": [
                {"hash": 2328211300, "socketOverrides": {"2": 3769507632}},
                {"hash": 1786557270},
            ],
            "unequipped": [{"hash": 3325463374}],
            "parameters": {
                "exoticArmorHash": 1786557270,
                "artifactUnlocks": {
                    "seasonNumber": 29,
                    "unlockedItemHashes": [2596646298],
                },
            },
        }

        url = build_dim_loadout_url(loadout)

        self.assertTrue(url.startswith(DIM_LONG_BASE))
        encoded = parse_qs(urlparse(url).query)["loadout"][0]
        self.assertEqual(json.loads(encoded), loadout)


class DimManifestLookupTests(unittest.TestCase):
    def test_subclass_lookup_requires_exact_class_type(self):
        item_defs = {
            "100": {
                "displayProperties": {"name": "Gunslinger"},
                "itemType": 16,
                "classType": 1,
            },
            "999": {
                "displayProperties": {"name": "Gunslinger"},
                "itemType": 16,
                "classType": 3,
            },
        }
        lookup = DimManifestLookup(item_defs, {})

        item = lookup.subclass_item("Gunslinger", class_type=1)

        self.assertEqual(item.hash, 100)

    def test_socket_overrides_map_plugs_to_available_subclass_sockets(self):
        item_defs = {
            "100": {
                "displayProperties": {"name": "Arcstrider"},
                "itemType": 16,
                "classType": 1,
                "sockets": {
                    "socketEntries": [
                        {"reusablePlugSetHash": 1},
                        {"reusablePlugSetHash": 2},
                        {"reusablePlugSetHash": 3},
                    ]
                },
            },
            "200": {"displayProperties": {"name": "Gathering Storm"}, "itemType": 19},
            "201": {"displayProperties": {"name": "Tempest Strike"}, "itemType": 19},
            "202": {"displayProperties": {"name": "Ascension"}, "itemType": 19},
        }
        plug_sets = {
            "1": {"reusablePlugItems": [{"plugItemHash": 200}]},
            "2": {"reusablePlugItems": [{"plugItemHash": 201}, {"plugItemHash": 202}]},
            "3": {"reusablePlugItems": [{"plugItemHash": 201}, {"plugItemHash": 202}]},
        }
        lookup = DimManifestLookup(item_defs, plug_sets)

        item = lookup.subclass_item("Arcstrider", class_type=1)
        overrides = lookup.socket_overrides(item.hash, ["Gathering Storm", "Tempest Strike", "Ascension"])

        self.assertEqual(overrides, {"0": 200, "1": 201, "2": 202})


class BuildDocParsingTests(unittest.TestCase):
    def test_build_loadout_for_doc_includes_subclass_exotic_weapon_and_artifact(self):
        markdown = """# Hunter Arc - Shinobu Arcworks

DIM: Manual checklist fallback.

## Subclass Setup

- Super: Gathering Storm
- Class ability: Gambler's Dodge
- Melee: Disorienting Blow
- Grenade: Skip Grenade
- Aspects: Ascension, Tempest Strike
- Fragments: Spark of Resistance, Spark of Shock

## Weapons

- Required exotic weapon: Thunderlord is recommended for this fixture.

## Exotic Armor

Shinobu's Vow is the center of the build.

## Relic Configuration

Artifact: Tablet of Ruin.

- Flashover
- Horde Shuttle
- Unraveling Orbs
- Photonic Flare
- Dielectric
- Defibrillating Blast
- To Shreds
"""
        item_defs = {
            "100": {
                "displayProperties": {"name": "Arcstrider"},
                "itemType": 16,
                "classType": 1,
                "sockets": {"socketEntries": [{"reusablePlugSetHash": 1}]},
            },
            "200": {"displayProperties": {"name": "Gathering Storm"}, "itemType": 19},
            "201": {"displayProperties": {"name": "Gambler's Dodge"}, "itemType": 19},
            "202": {"displayProperties": {"name": "Disorienting Blow"}, "itemType": 19},
            "203": {"displayProperties": {"name": "Skip Grenade"}, "itemType": 19},
            "204": {"displayProperties": {"name": "Ascension"}, "itemType": 19},
            "205": {"displayProperties": {"name": "Tempest Strike"}, "itemType": 19},
            "206": {"displayProperties": {"name": "Spark of Resistance"}, "itemType": 19},
            "207": {"displayProperties": {"name": "Spark of Shock"}, "itemType": 19},
            "300": {
                "displayProperties": {"name": "Shinobu's Vow"},
                "itemType": 2,
                "classType": 1,
            },
            "400": {
                "displayProperties": {"name": "Thunderlord"},
                "itemType": 3,
                "classType": 3,
            },
            "500": {"displayProperties": {"name": "Flashover"}, "itemType": 19},
            "501": {"displayProperties": {"name": "Horde Shuttle"}, "itemType": 19},
            "502": {"displayProperties": {"name": "Unraveling Orbs"}, "itemType": 19},
            "503": {"displayProperties": {"name": "Photonic Flare"}, "itemType": 19},
            "504": {"displayProperties": {"name": "Dielectric"}, "itemType": 19},
            "505": {"displayProperties": {"name": "Defibrillating Blast"}, "itemType": 19},
            "506": {"displayProperties": {"name": "To Shreds"}, "itemType": 19},
        }
        plug_sets = {
            "1": {
                "reusablePlugItems": [
                    {"plugItemHash": 200},
                    {"plugItemHash": 201},
                    {"plugItemHash": 202},
                    {"plugItemHash": 203},
                    {"plugItemHash": 204},
                    {"plugItemHash": 205},
                    {"plugItemHash": 206},
                    {"plugItemHash": 207},
                ]
            }
        }
        item_defs["100"]["sockets"]["socketEntries"] = [{"reusablePlugSetHash": 1} for _ in range(8)]
        lookup = DimManifestLookup(item_defs, plug_sets)
        doc = parse_build_doc(Path("hunter/arc.md"), markdown)

        result = build_loadout_for_doc(doc, lookup, season_number=29)

        self.assertEqual(result.unresolved, [])
        self.assertEqual(result.loadout["classType"], 1)
        self.assertEqual(result.loadout["parameters"]["exoticArmorHash"], 300)
        self.assertEqual(result.loadout["equipped"][0]["hash"], 100)
        self.assertEqual(
            result.loadout["equipped"][0]["socketOverrides"],
            {"0": 200, "1": 201, "2": 202, "3": 203, "4": 204, "5": 205, "6": 206, "7": 207},
        )
        self.assertIn({"hash": 400}, result.loadout["unequipped"])
        self.assertEqual(
            result.loadout["parameters"]["artifactUnlocks"],
            {"seasonNumber": 29, "unlockedItemHashes": [500, 501, 502, 503, 504, 505, 506]},
        )

    def test_rewrite_build_doc_dim_link_preserves_public_dim_reference(self):
        original = "# Titan Void - No Backup Shotgun Void\n\nDIM: [Void](https://dim.gg/3amqc4y/Void)\n"
        long_url = "https://app.destinyitemmanager.com/loadouts?loadout=%7B%7D"

        rewritten = rewrite_build_doc_dim_link(original, long_url)

        self.assertIn("DIM: [Long-form import][dim-long] / [source public DIM](https://dim.gg/3amqc4y/Void)", rewritten)
        self.assertIn(f"[dim-long]: {long_url}", rewritten)

    def test_rewrite_build_doc_dim_link_is_idempotent(self):
        original = "# Hunter Arc - Shinobu Arcworks\n\nDIM: Manual checklist fallback.\n"
        long_url = "https://app.destinyitemmanager.com/loadouts?loadout=%7B%7D"

        once = rewrite_build_doc_dim_link(original, long_url)
        twice = rewrite_build_doc_dim_link(once, long_url)

        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
