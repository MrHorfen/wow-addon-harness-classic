import unittest

from harness.loader import load_addon
from harness.wow_mock import WowRuntime
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1] / "addon" / "AHProbe"


class LegacyClientTest(unittest.TestCase):
    def setUp(self):
        self.runtime = WowRuntime("legacy")
        self.files = load_addon(self.runtime, ADDON)
        self.runtime.fire("ADDON_LOADED", "AHProbe")
        self.ns = self.runtime.L.globals().AHProbeNS

    def test_toc_loads_every_lua_file_in_order(self):
        self.assertEqual(
            self.files,
            ["Core/Init.lua", "Core/Env.lua", "Core/Probe.lua", "UI/Main.lua"],
        )

    def test_detects_legacy_client(self):
        self.assertFalse(self.ns.Env.IsModern())
        self.assertEqual(self.ns.Env.Flavor(), "legacy")
        self.assertIsNotNone(self.runtime.L.globals().AuctionFrame)
        self.assertIsNone(self.runtime.L.globals().AuctionHouseFrame)

    def test_scan_uses_legacy_query_and_reads_the_second_return(self):
        self.assertTrue(self.ns.Probe.Scan())
        queries = self.runtime.queries()
        self.assertEqual(len(queries), 1)
        self.assertEqual(queries[0]["name"], "")

        self.runtime.fire("AUCTION_ITEM_LIST_UPDATE")
        self.assertEqual(self.ns.Probe.count, 3)

    def test_modern_event_is_not_registered_on_legacy(self):
        fired = self.runtime.fire("AUCTION_HOUSE_BROWSE_RESULTS_UPDATED")
        self.assertEqual(fired, 0)

    def test_ui_updates_after_results(self):
        self.runtime.fire("PLAYER_LOGIN")
        self.ns.Probe.Scan()
        self.runtime.fire("AUCTION_ITEM_LIST_UPDATE")
        frame = self.runtime.L.globals().AHProbeFrame
        self.assertEqual(frame["countLabel"]["_text"], "Auctions: 3")

    def test_chinese_locale(self):
        runtime = WowRuntime("legacy", locale="zhCN")
        load_addon(runtime, ADDON)
        runtime.fire("ADDON_LOADED", "AHProbe")
        runtime.fire("PLAYER_LOGIN")
        frame = runtime.L.globals().AHProbeFrame
        self.assertEqual(frame["countLabel"]["_text"], "拍卖行条目: 0")

    def test_bag_info_normalizes_multiple_returns(self):
        info = self.ns.Env.BagItemInfo(0, 1)
        self.assertEqual(info["itemID"], 103)
        self.assertEqual(info["stackCount"], 5)

        seen = []
        visited = self.ns.Env.ForEachBagSlot(lambda *args: seen.append(args))
        self.assertEqual(visited, 1)
        self.assertEqual(seen[0][0:2], (0, 1))

    def test_item_helpers_use_verified_indexes(self):
        self.assertEqual(self.ns.Env.ItemMaxStack(103), 20)
        self.assertEqual(self.ns.Env.ItemClassID(101), 2)
        self.assertEqual(self.ns.Env.ItemEquipLoc(101), "INVTYPE_WEAPON")


if __name__ == "__main__":
    unittest.main()
