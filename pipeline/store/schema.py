"""LanceDB table schemas for Vestio."""
import pyarrow as pa

POSTS_SCHEMA = pa.schema([
    pa.field("id", pa.utf8(), nullable=False),
    pa.field("platform", pa.utf8()),
    pa.field("source_url", pa.utf8()),
    pa.field("author_id", pa.utf8()),
    pa.field("author_name", pa.utf8()),
    pa.field("author_followers", pa.int64()),
    pa.field("published_at", pa.utf8()),
    pa.field("caption", pa.utf8()),
    pa.field("hashtags", pa.list_(pa.utf8())),
    pa.field("transcript", pa.utf8(), nullable=True),
    pa.field("likes", pa.int64()),
    pa.field("comments_count", pa.int64()),
    pa.field("shares", pa.int64()),
    pa.field("media_type", pa.utf8()),
    pa.field("collected_at", pa.utf8()),
    pa.field("raw_metadata", pa.utf8()),
])

ITEMS_SCHEMA = pa.schema([
    pa.field("id", pa.utf8(), nullable=False),
    pa.field("post_id", pa.utf8()),
    pa.field("image", pa.large_binary(),
             metadata={b"lance-encoding:blob": b"true"}),
    pa.field("image_embedding", pa.list_(pa.float32(), list_size=512)),
    pa.field("category", pa.utf8()),
    pa.field("subtype", pa.utf8()),
    pa.field("colors", pa.list_(pa.utf8())),
    pa.field("pattern", pa.utf8()),
    pa.field("material", pa.utf8()),
    pa.field("style_tags", pa.list_(pa.utf8())),
    pa.field("brand", pa.utf8(), nullable=True),
    pa.field("season", pa.utf8(), nullable=True),
    pa.field("occasion", pa.utf8(), nullable=True),
    pa.field("confidence", pa.float64()),
    pa.field("bbox", pa.list_(pa.float64())),
])
