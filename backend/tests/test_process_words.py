import json
import tempfile
import unittest
from pathlib import Path
from scripts.process_words import (
    load_words_dictionary,
    group_words_by_length,
    save_words_by_length,
    process_words,
)


class TestProcessWords(unittest.TestCase):
    def test_group_words_by_length(self):
        words = ["cat", "dog", "apple", "banana", "a", "it", "Jean-Pierre"]
        
        # Test default grouping
        grouped = group_words_by_length(words, sort_words=True, only_alpha=False, lowercase=True)
        self.assertIn(1, grouped)
        self.assertEqual(grouped[1], ["a"])
        self.assertIn(2, grouped)
        self.assertEqual(grouped[2], ["it"])
        self.assertIn(3, grouped)
        self.assertEqual(grouped[3], ["cat", "dog"])
        self.assertIn(5, grouped)
        self.assertEqual(grouped[5], ["apple"])
        self.assertIn(6, grouped)
        self.assertEqual(grouped[6], ["banana"])
        self.assertIn(11, grouped)
        self.assertEqual(grouped[11], ["jean-pierre"])

    def test_group_words_with_filters(self):
        words = ["cat", "dog", "apple", "banana", "a", "it", "jean-pierre"]
        
        # Filter only alpha
        grouped_alpha = group_words_by_length(words, only_alpha=True)
        self.assertNotIn(11, grouped_alpha)

        # Filter by min and max length
        grouped_len = group_words_by_length(words, min_length=3, max_length=5)
        self.assertEqual(set(grouped_len.keys()), {3, 5})

    def test_save_words_by_length(self):
        grouped = {
            3: ["cat", "dog"],
            5: ["apple", "crane"],
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            summary = save_words_by_length(grouped, tmp_path, output_format="both", generate_manifest=True)
            
            self.assertEqual(summary["total_words"], 4)
            self.assertEqual(summary["total_unique_lengths"], 2)
            
            # Check files created
            self.assertTrue((tmp_path / "words_3.json").exists())
            self.assertTrue((tmp_path / "words_3.txt").exists())
            self.assertTrue((tmp_path / "words_5.json").exists())
            self.assertTrue((tmp_path / "words_5.txt").exists())
            self.assertTrue((tmp_path / "manifest.json").exists())

            # Check content of JSON
            with open(tmp_path / "words_5.json", "r") as f:
                words_5 = json.load(f)
                self.assertEqual(words_5, ["apple", "crane"])

            # Check content of TXT
            with open(tmp_path / "words_3.txt", "r") as f:
                lines = f.read().splitlines()
                self.assertEqual(lines, ["cat", "dog"])

    def test_full_pipeline(self):
        sample_dict = {"apple": 1, "banana": 1, "cat": 1, "dog": 1}
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            input_file = tmp_path / "sample_dict.json"
            output_dir = tmp_path / "output"

            with open(input_file, "w") as f:
                json.dump(sample_dict, f)

            summary = process_words(input_file, output_dir, output_format="json")
            self.assertEqual(summary["total_words"], 4)
            self.assertTrue((output_dir / "words_3.json").exists())
            self.assertTrue((output_dir / "words_5.json").exists())
            self.assertTrue((output_dir / "words_6.json").exists())


if __name__ == "__main__":
    unittest.main()
