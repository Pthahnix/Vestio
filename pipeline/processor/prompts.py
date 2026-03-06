"""VLM prompts for fashion attribute extraction."""

FASHION_EXTRACTION_PROMPT = """\
Analyze this fashion image. For each visible clothing item or accessory worn by a person, extract:

1. category: one of [top, bottom, dress, outerwear, footwear, accessory]
2. subtype: specific garment name (e.g., t-shirt, blazer, jeans, sneakers, handbag)
3. colors: list of primary colors
4. pattern: one of [solid, striped, floral, plaid, geometric, abstract, animal_print, tie_dye, other]
5. material: if identifiable (cotton, denim, silk, leather, knit, polyester, wool, linen, other)
6. style_tags: list from [casual, formal, streetwear, bohemian, minimalist, sporty, vintage, preppy, punk, romantic, other]
7. brand: if a logo or branding is visible, otherwise null
8. season: if apparent (spring, summer, fall, winter), otherwise null
9. occasion: if apparent (everyday, work, party, date, sport, beach), otherwise null
10. confidence: your confidence in this extraction (0.0 to 1.0)
11. bbox: approximate bounding box as [x_min, y_min, x_max, y_max] normalized to 0-1

Return ONLY a JSON array of objects. If no clothing items are visible, return an empty array [].

Example output:
[
  {
    "category": "top",
    "subtype": "blazer",
    "colors": ["navy"],
    "pattern": "solid",
    "material": "wool",
    "style_tags": ["formal", "minimalist"],
    "brand": null,
    "season": "fall",
    "occasion": "work",
    "confidence": 0.92,
    "bbox": [0.15, 0.1, 0.85, 0.55]
  }
]
"""
