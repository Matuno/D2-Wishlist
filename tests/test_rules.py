import re
import unittest
from pathlib import Path

from d2_wishlist.generator import (
    Plug,
    WishlistRow,
    build_index,
    generate_rolls_for_row,
    generate_wishlist_text,
    should_include_tier,
)


class StrictnessRuleTests(unittest.TestCase):
    def sample_row(self):
        return WishlistRow(
            sheet="Autos",
            name="No Hesitation",
            item_hash=1801007332,
            tier="S",
            rank=1.0,
            notes="on-demand survivability",
            barrels=[Plug("Full Bore", 202670084)],
            mags=[Plug("Accurized Rounds", 3142289711)],
            perk1=[
                Plug("Physic", 2980589453),
                Plug("Burning Ambition", 2890807135),
            ],
            perk2=[
                Plug("Chaos Reshaped", 3640170453),
                Plug("Attrition Orbs", 243981275),
                Plug("Incandescent", 4293542123),
            ],
            origins=[Plug("Dealer's Choice", 1988485648)],
        )

    def test_tier_filter_keeps_rows_at_or_above_minimum_rank(self):
        self.assertTrue(should_include_tier("S", "A"))
        self.assertTrue(should_include_tier("A", "A"))
        self.assertFalse(should_include_tier("B", "A"))

    def test_ppc3_generates_existing_style_main_perk_fallbacks(self):
        rolls = generate_rolls_for_row(self.sample_row(), ppc=3, bmc=0)

        self.assertEqual(len(rolls), 8)
        self.assertEqual(
            rolls[0],
            (
                202670084,
                3142289711,
                2980589453,
                2890807135,
                3640170453,
                243981275,
                4293542123,
                1988485648,
            ),
        )
        self.assertEqual(
            rolls[-1],
            (2980589453, 2890807135, 3640170453, 243981275, 4293542123),
        )

    def test_bmc1_requires_a_barrel_or_magazine(self):
        rolls = generate_rolls_for_row(self.sample_row(), ppc=3, bmc=1)

        self.assertEqual(len(rolls), 6)
        for roll in rolls:
            self.assertTrue({202670084, 3142289711} & set(roll))

    def test_bmc2_requires_a_barrel_and_magazine(self):
        rolls = generate_rolls_for_row(self.sample_row(), ppc=3, bmc=2)

        self.assertEqual(len(rolls), 2)
        for roll in rolls:
            self.assertIn(202670084, roll)
            self.assertIn(3142289711, roll)

    def test_ppc0_allows_broad_matching_but_not_origin_only(self):
        rolls = generate_rolls_for_row(self.sample_row(), ppc=0, bmc=0)

        self.assertEqual(len(rolls), 254)
        self.assertIn((202670084,), rolls)
        self.assertIn((3142289711,), rolls)
        self.assertIn((3640170453,), rolls)
        self.assertNotIn((1988485648,), rolls)

    def test_wishlist_text_uses_dim_expert_syntax(self):
        text = generate_wishlist_text([self.sample_row()], min_tier="S", ppc=3, bmc=2)

        lines = [line for line in text.splitlines() if line.startswith("dimwishlist:")]
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertRegex(line, r"^dimwishlist:item=1801007332&perks=\d+(,\d+)*$")


class ConfiguratorIndexTests(unittest.TestCase):
    def test_build_index_creates_full_file_matrix(self):
        index = build_index(Path("dist"), raw_base_url="https://example.test/wishlists")

        self.assertEqual(len(index["files"]), 84)
        sample = next(
            entry
            for entry in index["files"]
            if entry["minimumRank"] == "A" and entry["ppc"] == 2 and entry["bmc"] == 1
        )
        self.assertEqual(sample["fileName"], "AegisWishlist_MRA_PPC2_BMC1.txt")
        self.assertEqual(sample["localPath"], "dist/AegisWishlist_MRA_PPC2_BMC1.txt")
        self.assertEqual(
            sample["rawUrl"],
            "https://example.test/wishlists/AegisWishlist_MRA_PPC2_BMC1.txt",
        )

    def test_build_index_uses_github_raw_template_without_base_url(self):
        index = build_index(Path("dist"))

        sample = index["files"][0]
        self.assertEqual(
            sample["rawUrl"],
            "https://raw.githubusercontent.com/<user>/<repo>/main/dist/AegisWishlist_MRS_PPC0_BMC0.txt",
        )


if __name__ == "__main__":
    unittest.main()
