from io import BytesIO
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from d2_wishlist.generator import (
    ManifestResolver,
    Plug,
    SheetRow,
    WishlistRow,
    parse_workbook_bytes,
    write_outputs,
)


class WorkbookParserTests(unittest.TestCase):
    def test_parse_workbook_bytes_reads_current_weapon_header_shape(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Autos"
        sheet.append(["WEAPON", "INFO", "PERKS", "ANALYSIS"])
        sheet.append(
            [
                "Icon",
                "Name",
                "Season",
                "Energy",
                "Frame",
                "Ammo",
                "Up",
                "Barrel",
                "Mag",
                "Perk 1",
                "Perk 2",
                "Origin Trait",
                "Notes",
                "Rank",
                "Tier",
            ]
        )
        sheet.append(
            [
                "",
                "No Hesitation",
                24,
                "Solar",
                "Support",
                54,
                "Yes",
                "Full Bore",
                "Accurized Rounds",
                "Physic\nBurning Ambition",
                "Chaos Reshaped\nAttrition Orbs",
                "Nail, Meet Hammer",
                "on-demand survivability",
                1,
                "S",
            ]
        )
        handle = BytesIO()
        workbook.save(handle)

        rows = parse_workbook_bytes(handle.getvalue())

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].sheet, "Autos")
        self.assertEqual(rows[0].perk1, ["Physic", "Burning Ambition"])
        self.assertEqual(rows[0].perk2, ["Chaos Reshaped", "Attrition Orbs"])
        self.assertEqual(rows[0].origins, ["Nail, Meet Hammer"])

    def test_parse_workbook_bytes_skips_rows_without_main_perks(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Autos"
        sheet.append(["WEAPON", "INFO", "PERKS", "ANALYSIS"])
        sheet.append(
            [
                "Icon",
                "Name",
                "Season",
                "Energy",
                "Frame",
                "Ammo",
                "Up",
                "Barrel",
                "Mag",
                "Perk 1",
                "Perk 2",
                "Origin Trait",
                "Notes",
                "Rank",
                "Tier",
            ]
        )
        sheet.append(["", "Reckless Oracle", 29, "Void", "Rapid", 54, "Yes", "Fluted Barrel", "Flared Magwell", "", "", "", "", 4, "S"])
        handle = BytesIO()
        workbook.save(handle)

        rows = parse_workbook_bytes(handle.getvalue())

        self.assertEqual(rows, [])


class ManifestResolverTests(unittest.TestCase):
    def test_resolver_uses_weapon_socket_options_not_global_name_only(self):
        item_defs = {
            "1801007332": {
                "displayProperties": {"name": "No Hesitation"},
                "itemType": 3,
                "sockets": {
                    "socketEntries": [
                        {"randomizedPlugSetHash": 1},
                        {"randomizedPlugSetHash": 2},
                        {"randomizedPlugSetHash": 3},
                        {"randomizedPlugSetHash": 4},
                        {"singleInitialItemHash": 1988485648},
                    ]
                },
            },
            "999": {
                "displayProperties": {"name": "No Hesitation"},
                "itemType": 3,
                "sockets": {"socketEntries": []},
            },
            "202670084": {"displayProperties": {"name": "Full Bore"}},
            "3142289711": {"displayProperties": {"name": "Accurized Rounds"}},
            "2980589453": {"displayProperties": {"name": "Physic"}},
            "2890807135": {"displayProperties": {"name": "Burning Ambition"}},
            "3640170453": {"displayProperties": {"name": "Chaos Reshaped"}},
            "243981275": {"displayProperties": {"name": "Attrition Orbs"}},
            "1988485648": {"displayProperties": {"name": "Dealer's Choice"}},
        }
        plug_sets = {
            "1": {"reusablePlugItems": [{"plugItemHash": 202670084}]},
            "2": {"reusablePlugItems": [{"plugItemHash": 3142289711}]},
            "3": {
                "reusablePlugItems": [
                    {"plugItemHash": 2980589453},
                    {"plugItemHash": 2890807135},
                ]
            },
            "4": {
                "reusablePlugItems": [
                    {"plugItemHash": 3640170453},
                    {"plugItemHash": 243981275},
                ]
            },
        }
        sheet_row = SheetRow(
            sheet="Autos",
            row_number=3,
            name="No Hesitation",
            season="24",
            tier="S",
            rank=1.0,
            notes="",
            barrels=["Full Bore"],
            mags=["Accurized Rounds"],
            perk1=["Physic", "Burning Ambition"],
            perk2=["Chaos Reshaped", "Attrition Orbs"],
            origins=["Dealer's Choice"],
        )

        row, issues = ManifestResolver(item_defs, plug_sets).resolve(sheet_row)

        self.assertEqual(issues, [])
        self.assertIsNotNone(row)
        self.assertEqual(row.item_hash, 1801007332)
        self.assertEqual([plug.hash for plug in row.perk1], [2980589453, 2890807135])

    def test_resolver_warns_and_chooses_latest_release_for_equal_socket_coverage(self):
        item_defs = {
            "1": {
                "displayProperties": {"name": "Claws of the Wolf"},
                "itemType": 3,
                "traitIds": ["item.weapon.pulse_rifle", "releases.v800.season"],
                "sockets": {"socketEntries": [{"randomizedPlugSetHash": 1}]},
            },
            "2": {
                "displayProperties": {"name": "Claws of the Wolf"},
                "itemType": 3,
                "traitIds": ["item.weapon.pulse_rifle", "releases.v970.core"],
                "sockets": {"socketEntries": [{"randomizedPlugSetHash": 1}]},
            },
            "2980589453": {"displayProperties": {"name": "Repulsor Brace"}},
        }
        plug_sets = {"1": {"reusablePlugItems": [{"plugItemHash": 2980589453}]}}
        sheet_row = SheetRow(
            sheet="Pulses",
            row_number=3,
            name="Claws of the Wolf",
            season="29",
            tier="S",
            rank=1.0,
            notes="",
            barrels=[],
            mags=[],
            perk1=["Repulsor Brace"],
            perk2=[],
            origins=[],
        )

        row, issues = ManifestResolver(item_defs, plug_sets).resolve(sheet_row)

        self.assertEqual(row.item_hash, 2)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, "warning")

    def test_resolver_warns_and_drops_unavailable_quality_plugs(self):
        item_defs = {
            "1": {
                "displayProperties": {"name": "Reckless Endangerment"},
                "itemType": 3,
                "sockets": {"socketEntries": [{"randomizedPlugSetHash": 1}]},
            },
            "791862061": {"displayProperties": {"name": "Assault Mag"}},
            "1631667848": {"displayProperties": {"name": "Grave Robber"}},
        }
        plug_sets = {
            "1": {
                "reusablePlugItems": [
                    {"plugItemHash": 791862061},
                    {"plugItemHash": 1631667848},
                ]
            }
        }
        sheet_row = SheetRow(
            sheet="Shotguns",
            row_number=51,
            name="Reckless Endangerment",
            season="29",
            tier="C",
            rank=1.0,
            notes="",
            barrels=["Fluted Barrel"],
            mags=["Assault Mag"],
            perk1=["Grave Robber"],
            perk2=[],
            origins=[],
        )

        row, issues = ManifestResolver(item_defs, plug_sets).resolve(sheet_row)

        self.assertEqual([plug.name for plug in row.barrels], [])
        self.assertEqual([plug.name for plug in row.mags], ["Assault Mag"])
        self.assertEqual([issue.severity for issue in issues], ["warning"])

    def test_resolver_warns_and_ignores_configured_unavailable_main_plug(self):
        item_defs = {
            "1": {
                "displayProperties": {"name": "Lotus-Eater"},
                "itemType": 3,
                "sockets": {"socketEntries": [{"randomizedPlugSetHash": 1}]},
            },
            "10": {"displayProperties": {"name": "Repulsor Brace"}},
            "11": {"displayProperties": {"name": "Shoot to Loot"}},
        }
        plug_sets = {"1": {"reusablePlugItems": [{"plugItemHash": 10}]}}
        sheet_row = SheetRow(
            sheet="Rocket Sidearms",
            row_number=3,
            name="Lotus-Eater",
            season="29",
            tier="S",
            rank=1.0,
            notes="",
            barrels=[],
            mags=[],
            perk1=["Repulsor Brace", "Shoot to Loot"],
            perk2=[],
            origins=[],
        )
        overrides = {"ignored_plugs": {"Lotus-Eater": {"Perk 1": ["Shoot to Loot"]}}}

        row, issues = ManifestResolver(item_defs, plug_sets, overrides=overrides).resolve(sheet_row)

        self.assertEqual([plug.name for plug in row.perk1], ["Repulsor Brace"])
        self.assertEqual([issue.severity for issue in issues], ["warning"])
        self.assertEqual(issues[0].value, "Shoot to Loot")


class OutputWriterTests(unittest.TestCase):
    def test_write_outputs_creates_84_files_and_configurator_artifacts(self):
        row = WishlistRow(
            sheet="Autos",
            name="No Hesitation",
            item_hash=1801007332,
            tier="S",
            rank=1.0,
            notes="on-demand survivability",
            barrels=[Plug("Full Bore", 202670084)],
            mags=[Plug("Accurized Rounds", 3142289711)],
            perk1=[Plug("Physic", 2980589453), Plug("Burning Ambition", 2890807135)],
            perk2=[Plug("Chaos Reshaped", 3640170453), Plug("Attrition Orbs", 243981275)],
            origins=[Plug("Dealer's Choice", 1988485648)],
        )
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "dist"

            write_outputs([row], out_dir=out_dir, raw_base_url="https://example.test/raw")

            wishlist_files = list(out_dir.glob("AegisWishlist_MR*_PPC*_BMC*.txt"))
            self.assertEqual(len(wishlist_files), 84)
            self.assertTrue((out_dir / "index.html").exists())
            self.assertTrue((out_dir / "index.json").exists())
            self.assertTrue((out_dir / "audit.csv").exists())


if __name__ == "__main__":
    unittest.main()
