"""Inspect what's stored in LanceDB after pipeline run."""
import sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")
from store.db import VestioStore

store = VestioStore("../data/vestio.lance")

# Posts
posts = store.get_posts(limit=10)
print(f"=== POSTS ({len(posts)} total) ===")
for p in posts:
    print(f"  [{p['platform']}] @{p['author_name']}: {p['caption'][:60]}...")
    print(f"    likes={p['likes']} comments={p['comments_count']} media={p['media_type']}")
    print()

# Items
items = store.search_items([0.0] * 512, limit=50)
print(f"=== ITEMS ({len(items)} total) ===")
for item in items:
    emb_preview = item['image_embedding'][:3]
    print(f"  [{item['category']}/{item['subtype']}] colors={item['colors']} pattern={item['pattern']}")
    print(f"    material={item['material']} style={item['style_tags']} brand={item['brand']}")
    print(f"    confidence={item['confidence']:.2f} season={item['season']} occasion={item['occasion']}")
    print()
