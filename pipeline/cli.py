"""Vestio pipeline CLI.

Usage:
    python -m cli process --input data/raw/instagram-*.json --db data/vestio.lance
    python -m cli search --db data/vestio.lance --image path/to/query.jpg --limit 5
    python -m cli search --db data/vestio.lance --text "red floral dress" --limit 5
"""
from __future__ import annotations

import argparse
import glob
import sys


def cmd_process(args):
    from processor.pipeline import process_raw_posts

    input_files = []
    for pattern in args.input:
        input_files.extend(glob.glob(pattern))

    if not input_files:
        print(f"No files matched: {args.input}")
        sys.exit(1)

    total_stats = {"posts_processed": 0, "items_extracted": 0, "errors": 0}

    for filepath in input_files:
        print(f"Processing {filepath}...")
        stats = process_raw_posts(filepath, args.db, vlm_model=args.model)
        for k in total_stats:
            total_stats[k] += stats[k]
        print(f"  Posts: {stats['posts_processed']}, Items: {stats['items_extracted']}, Errors: {stats['errors']}")

    print(f"\nTotal: {total_stats}")


def cmd_search(args):
    from store.db import VestioStore

    store = VestioStore(args.db)

    if args.image:
        from processor.embedder import FashionEmbedder
        embedder = FashionEmbedder()
        query_vec = embedder.embed_image_bytes(open(args.image, "rb").read())
    elif args.text:
        # Text-to-image search via CLIP text encoder
        from processor.embedder import FashionEmbedder
        import torch
        embedder = FashionEmbedder()
        inputs = embedder.processor(text=[args.text], return_tensors="pt", padding=True)
        inputs = {k: v.to(embedder.device) for k, v in inputs.items()}
        with torch.no_grad():
            output = embedder.model.get_text_features(**inputs)
            features = output.pooler_output if hasattr(output, "pooler_output") else output
            features = features / features.norm(dim=-1, keepdim=True)
        query_vec = features[0].cpu().tolist()
    else:
        print("Provide --image or --text for search")
        sys.exit(1)

    where = f"category = '{args.category}'" if args.category else None
    results = store.search_items(query_vec, limit=args.limit, where=where)

    print(f"Found {len(results)} results:")
    for i, item in enumerate(results):
        dist = item.get("_distance", "?")
        print(f"  {i+1}. [{item['category']}/{item['subtype']}] "
              f"colors={item['colors']} pattern={item['pattern']} "
              f"confidence={item['confidence']:.2f} distance={dist}")


def main():
    parser = argparse.ArgumentParser(description="Vestio Pipeline CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # process command
    p_proc = sub.add_parser("process", help="Process raw posts into LanceDB")
    p_proc.add_argument("--input", nargs="+", required=True, help="Glob pattern(s) for raw JSON files")
    p_proc.add_argument("--db", default="data/vestio.lance", help="LanceDB path")
    p_proc.add_argument("--model", default=None, help="VLM model ID (default: env VLM_MODEL or google/gemini-2.5-flash)")

    # search command
    p_search = sub.add_parser("search", help="Search similar items")
    p_search.add_argument("--db", default="data/vestio.lance", help="LanceDB path")
    p_search.add_argument("--image", help="Query image path")
    p_search.add_argument("--text", help="Text query (e.g. 'red floral dress')")
    p_search.add_argument("--category", help="Filter by category")
    p_search.add_argument("--limit", type=int, default=5, help="Max results")

    args = parser.parse_args()
    if args.command == "process":
        cmd_process(args)
    elif args.command == "search":
        cmd_search(args)


if __name__ == "__main__":
    main()
