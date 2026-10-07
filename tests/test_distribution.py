"""Check shipped operator contracts stay aligned with their source versions."""
import unittest
from pathlib import Path


class DistributionTests(unittest.TestCase):
    def test_packaged_prompts_match_operator_sources(self):
        root = Path(__file__).resolve().parents[1]
        source = root / 'prompts'
        packaged = root / 'asdlc' / 'prompts'
        self.assertEqual({p.name for p in source.glob('*.md')},
                         {p.name for p in packaged.glob('*.md')})
        for path in source.glob('*.md'):
            with self.subTest(prompt=path.name):
                self.assertEqual(path.read_bytes(), (packaged / path.name).read_bytes())
