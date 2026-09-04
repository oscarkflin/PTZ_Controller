import unittest

from ptz_controller.visca import ViscaClient


class ViscaPacketTests(unittest.TestCase):
    def setUp(self):
        self.client = ViscaClient("127.0.0.1", enabled=False)

    def tearDown(self):
        self.client.close()

    def test_pan_right_packet(self):
        packet = self.client.pan_tilt(1, 0, 6, 6)
        self.assertEqual(packet, bytes.fromhex("01 00 00 09 00 00 00 00 81 01 06 01 06 06 02 03 FF"))

    def test_zoom_wide_packet(self):
        packet = self.client.zoom(-1, 4)
        self.assertEqual(packet, bytes.fromhex("01 00 00 06 00 00 00 00 81 01 04 07 34 FF"))

    def test_preset_packet(self):
        packet = self.client.recall_preset(3)
        self.assertEqual(packet, bytes.fromhex("01 00 00 07 00 00 00 00 81 01 04 3F 02 03 FF"))

    def test_store_preset_packet(self):
        packet = self.client.store_preset(3)
        self.assertEqual(packet, bytes.fromhex("01 00 00 07 00 00 00 00 81 01 04 3F 01 03 FF"))


if __name__ == "__main__":
    unittest.main()
