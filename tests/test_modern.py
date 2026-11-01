import unittest

from harness.loader import load_addon
from harness.wow_mock import WowRuntime
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1] / "addon" / "AHProbe"


class ModernClientTest(unittest.TestCase):
    def setUp(self):
        self.runtime = WowRuntime("modern")
        load_addon(self.runtime, ADDON)
        self.runtime.fire("ADDON_LOADED", "AHProbe")
        self.ns = self.runtime.L.globals().AHProbeNS

    def test_detects_modern_client(self):
        self.assertTrue(self.ns.Env.IsModern())
        self.assertEqual(self.ns.Env.Flavor(), "modern")
        self.assertIsNotNone(self.runtime.L.globals().AuctionHouseFrame)
        self.assertIsNone(self.runtime.L.globals().AuctionFrame)

    def test_scan_uses_modern_browse_query(self):
        self.assertTrue(self.ns.Probe.Scan())
        self.assertEqual(len(self.runtime.queries()), 1)

    def test_legacy_api_is_absent(self):
        self.assertFalse(self.ns.Env.Has("QueryAuctionItems"))
        self.assertIsNone(self.runtime.L.globals().QueryAuctionItems)
        self.assertIsNone(self.runtime.L.globals().GetNumAuctionItems)

    def test_browse_results_are_a_table(self):
        self.ns.Probe.Scan()
        self.runtime.fire("AUCTION_HOUSE_BROWSE_RESULTS_UPDATED")
        self.assertEqual(self.ns.Probe.count, 3)

    def test_legacy_event_is_not_registered_on_modern(self):
        fired = self.runtime.fire("AUCTION_ITEM_LIST_UPDATE")
        self.assertEqual(fired, 0)

    def test_ui_updates_after_results(self):
        self.runtime.fire("PLAYER_LOGIN")
        self.ns.Probe.Scan()
        self.runtime.fire("AUCTION_HOUSE_BROWSE_RESULTS_UPDATED")
        frame = self.runtime.L.globals().AHProbeFrame
        self.assertEqual(frame["countLabel"]["_text"], "Auctions: 3")

    def test_bag_info_normalizes_info_table(self):
        info = self.ns.Env.BagItemInfo(0, 1)
        self.assertEqual(info["itemID"], 203)
        self.assertEqual(info["stackCount"], 5)

        seen = []
        visited = self.ns.Env.ForEachBagSlot(lambda *args: seen.append(args))
        self.assertEqual(visited, 1)
        self.assertEqual(seen[0][0:2], (0, 1))

    def test_item_helpers_use_verified_indexes(self):
        self.assertEqual(self.ns.Env.ItemMaxStack(203), 20)
        self.assertEqual(self.ns.Env.ItemClassID(201), 2)
        self.assertEqual(self.ns.Env.ItemEquipLoc(201), "INVTYPE_WEAPON")


if __name__ == "__main__":
    unittest.main()
