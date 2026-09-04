import tempfile
import unittest
from pathlib import Path

from ptz_controller.presets import PresetStore


class PresetStoreTests(unittest.TestCase):
    def test_saves_and_loads_sorted_preset_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PresetStore(Path(directory) / "presets.json")
            store.save([{"number": 5, "name": "Audience"}, {"number": 1, "name": "Pulpit"}])
            self.assertEqual(store.load(), [{"number": 1, "name": "Pulpit"}, {"number": 5, "name": "Audience"}])
