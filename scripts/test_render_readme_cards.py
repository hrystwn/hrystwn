"""Guards the things that actually broke while building the cards.

    python -m unittest discover -s scripts -p "test_*.py"
"""
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import unittest
import xml.dom.minidom

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_readme_cards.py"


def load():
    spec = importlib.util.spec_from_file_location("cards", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Rendered(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = (ROOT / "cards" / "hero.svg").stat().st_mtime_ns
        subprocess.run(
            [sys.executable, str(SCRIPT)],
            check=True, capture_output=True, env={**os.environ, "STATIC": "1"},
        )
        cls.data = json.loads((ROOT / "data" / "contributions.json").read_text(encoding="utf-8"))
        cls.dir = ROOT / "cards-preview"

    def test_static_never_touches_the_live_cards(self):
        self.assertEqual((ROOT / "cards" / "hero.svg").stat().st_mtime_ns, self.before)

    def test_every_card_is_valid_xml(self):
        files = sorted(self.dir.glob("*.svg"))
        self.assertEqual(len(files), 8)
        for path in files:
            xml.dom.minidom.parse(str(path))  # raises on broken markup

    def test_no_python_leaked_into_the_markup(self):
        for path in self.dir.glob("*.svg"):
            markup = path.read_text(encoding="utf-8").split("</style>", 1)[-1]
            for smell in (">None<", ">nan<", ">True<", ">False<"):
                if smell in markup:
                    self.fail(f"{path.name} contains {smell!r}")

    def test_graph_has_one_square_per_day(self):
        body = (self.dir / "graph.svg").read_text(encoding="utf-8")
        self.assertEqual(body.count('class="pop"'), len(self.data["days"]))

    def test_activity_states_the_real_total(self):
        body = (self.dir / "activity.svg").read_text(encoding="utf-8")
        self.assertIn(f'>{self.data["total"]}<', body)

    def test_graph_states_the_window(self):
        body = (self.dir / "graph.svg").read_text(encoding="utf-8")
        self.assertIn(" in 12 months<", body)
        self.assertNotIn(" this year<", body)

    def test_portrait_rows_keep_all_columns_at_one_width(self):
        # Viewers pick their own mono font, so the art only holds its shape if every
        # row keeps its spaces and is pinned to one textLength.
        body = (self.dir / "hero.svg").read_text(encoding="utf-8")
        rows = (ROOT / "data" / "portrait.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(body.count('xml:space="preserve"'), len(rows))
        self.assertEqual(len(set(re.findall(r'textLength="([\d.]+)"', body))), 1)


class Readme(unittest.TestCase):
    """README.md is hand-edited, so it cannot read data/site.json. Anything that
    drifts with the app's release state belongs on the cards, not in the alt text."""

    def test_alt_text_carries_no_release_claim(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for claim in ("Android", "App Store", "TestFlight"):
            self.assertNotIn(claim, readme)

    def test_every_image_has_alt_text(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for tag in re.findall(r"<img\b[^>]*>", readme):
            self.assertRegex(tag, r'alt="[^"]+"')


class Copy(unittest.TestCase):
    """The sentences that must follow data/site.json instead of memory."""

    @classmethod
    def setUpClass(cls):
        cls.m = load()
        cls.portrait = (ROOT / "data" / "portrait.txt").read_text(encoding="utf-8").splitlines()

    def test_hero_follows_the_app_store_flag(self):
        self.assertIn("live on the App Store", self.m.hero("x", self.portrait, {"appStore": True}))
        self.assertIn("private beta", self.m.hero("x", self.portrait, {"appStore": False}))

    def test_tiles_follow_the_site_facts(self):
        self.assertIn("18 posts", self.m.tile(2, {"posts": 18}))
        self.assertIn("tenangmail.com/blog", self.m.tile(2, {}))
        self.assertIn("App Store", self.m.tile(0, {"appStore": True}))
        self.assertIn("TestFlight", self.m.tile(0, {}))


if __name__ == "__main__":
    unittest.main()
