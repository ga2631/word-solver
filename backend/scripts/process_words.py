#!/usr/bin/env python3
"""
Script to process the English words dictionary JSON file.
- Reads raw dictionary from backend/app/static/words_dictionary.json
- Groups words based on character length (number of characters)
- Separates list of words by length into individual files (JSON / TXT)
- Generates a summary manifest with statistics
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_words_dictionary(file_path: Path) -> Dict[str, Any]:
    """Load the source JSON dictionary file."""
    logger.info(f"Loading dictionary from: {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found at: {file_path}")

    start_time = time.time()
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    elapsed = time.time() - start_time

    logger.info(f"Successfully loaded {len(data):,} words in {elapsed:.2f}s")
    return data


def group_words_by_length(
    words: Iterable[str],
    sort_words: bool = True,
    only_alpha: bool = False,
    lowercase: bool = True,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> Dict[int, List[str]]:
    """
    Group words by character length.

    Args:
        words: Iterable of word strings.
        sort_words: Whether to sort word list alphabetically for each length.
        only_alpha: Whether to filter out words containing non-alphabetic characters.
        lowercase: Whether to convert words to lowercase.
        min_length: Minimum word length to include.
        max_length: Maximum word length to include.

    Returns:
        Dict mapping word length (int) to list of words (list[str]).
    """
    logger.info("Grouping words by character length...")
    grouped: Dict[int, List[str]] = {}
    skipped_count = 0

    for raw_word in words:
        if not isinstance(raw_word, str):
            continue

        w = raw_word.strip()
        if lowercase:
            w = w.lower()

        if only_alpha and not w.isalpha():
            skipped_count += 1
            continue

        length = len(w)
        if length == 0:
            continue

        if min_length is not None and length < min_length:
            continue
        if max_length is not None and length > max_length:
            continue

        if length not in grouped:
            grouped[length] = []
        grouped[length].append(w)

    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count:,} non-alphabetic words due to --only-alpha flag.")

    if sort_words:
        for length in grouped:
            grouped[length].sort()

    return dict(sorted(grouped.items()))


def save_words_by_length(
    grouped_words: Dict[int, List[str]],
    output_dir: Path,
    output_format: str = "json",
    indent: int = 2,
    generate_manifest: bool = True,
) -> Dict[str, Any]:
    """
    Save grouped words into separate files by length in output_dir.

    Args:
        grouped_words: Dict mapping length -> list of words.
        output_dir: Target directory to save split files.
        output_format: 'json', 'txt', or 'both'.
        indent: JSON indentation.
        generate_manifest: Whether to output manifest.json summarizing all files.

    Returns:
        Dictionary summarizing created files and statistics.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving partitioned files into: {output_dir}")

    manifest_entries = {}
    total_words_written = 0

    for length, words in grouped_words.items():
        total_words_written += len(words)
        file_info: Dict[str, Any] = {
            "length": length,
            "word_count": len(words),
            "sample_words": words[:5],
            "files": [],
        }

        # Save JSON format
        if output_format in ("json", "both"):
            json_filename = f"words_{length}.json"
            json_path = output_dir / json_filename
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(words, f, indent=indent, ensure_ascii=False)
            file_size_kb = round(json_path.stat().st_size / 1024, 2)
            file_info["files"].append({
                "format": "json",
                "filename": json_filename,
                "size_kb": file_size_kb,
            })

        # Save TXT format (one word per line)
        if output_format in ("txt", "both"):
            txt_filename = f"words_{length}.txt"
            txt_path = output_dir / txt_filename
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(words) + "\n")
            file_size_kb = round(txt_path.stat().st_size / 1024, 2)
            file_info["files"].append({
                "format": "txt",
                "filename": txt_filename,
                "size_kb": file_size_kb,
            })

        manifest_entries[str(length)] = file_info

    summary = {
        "total_unique_lengths": len(grouped_words),
        "total_words": total_words_written,
        "lengths_available": sorted(grouped_words.keys()),
        "distribution": {str(k): len(v) for k, v in grouped_words.items()},
        "details": manifest_entries,
    }

    if generate_manifest:
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"Generated manifest: {manifest_path}")

    return summary


def process_words(
    input_file: Path,
    output_dir: Path,
    output_format: str = "json",
    only_alpha: bool = False,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    indent: int = 2,
    generate_manifest: bool = True,
) -> Dict[str, Any]:
    """Execute the full data processing pipeline."""
    start_time = time.time()

    data = load_words_dictionary(input_file)
    grouped = group_words_by_length(
        words=data.keys(),
        sort_words=True,
        only_alpha=only_alpha,
        lowercase=True,
        min_length=min_length,
        max_length=max_length,
    )

    summary = save_words_by_length(
        grouped_words=grouped,
        output_dir=output_dir,
        output_format=output_format,
        indent=indent,
        generate_manifest=generate_manifest,
    )

    total_time = time.time() - start_time
    logger.info("=" * 60)
    logger.info(f"Processing completed in {total_time:.2f}s")
    logger.info(f"Total Words Processed : {summary['total_words']:,}")
    logger.info(f"Word Length Buckets    : {summary['total_unique_lengths']} (from len {min(grouped.keys())} to {max(grouped.keys())})")
    logger.info(f"Output Directory       : {output_dir}")
    logger.info("=" * 60)

    return summary


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    default_base_dir = Path(__file__).resolve().parent.parent
    default_input = default_base_dir / "app" / "static" / "words_dictionary.json"
    default_output = default_base_dir / "app" / "static" / "words_by_length"

    parser = argparse.ArgumentParser(
        description="Process words_dictionary.json into partitioned word files grouped by word length."
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=default_input,
        help=f"Path to input dictionary JSON (default: {default_input})",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=default_output,
        help=f"Directory to save partitioned files (default: {default_output})",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "txt", "both"],
        default="json",
        help="Output format for separated files: 'json', 'txt', or 'both' (default: json)",
    )
    parser.add_argument(
        "--only-alpha",
        action="store_true",
        help="Filter out words containing non-alphabetic characters (e.g. hyphens)",
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=None,
        help="Filter: minimum word length to include",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=None,
        help="Filter: maximum word length to include",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level for output files (default: 2)",
    )
    parser.add_argument(
        "--no-manifest",
        action="store_true",
        help="Do not generate manifest.json in the output directory",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()
    try:
        process_words(
            input_file=args.input,
            output_dir=args.output_dir,
            output_format=args.format,
            only_alpha=args.only_alpha,
            min_length=args.min_length,
            max_length=args.max_length,
            indent=args.indent,
            generate_manifest=not args.no_manifest,
        )
    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
