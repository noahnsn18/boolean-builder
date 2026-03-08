import json
import re
from collections import OrderedDict

SOURCE_FILE = "categories_clean.json"
OUTPUT_FILE = "kw_categories_big.json"

PART_OF_RE = re.compile(r"^(.*?)\s*\(part of\s+(.*?)\)\s*$", re.IGNORECASE)


def norm_term(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def add_term(term_list: list[str], seen_lower: set[str], term: str) -> None:
    clean = norm_term(term)
    if not clean:
        return
    key = clean.lower()
    if key not in seen_lower:
        term_list.append(clean)
        seen_lower.add(key)


with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

groups: OrderedDict[str, dict] = OrderedDict()

for item in data:
    raw_title = (item.get("title") or "").strip()
    keywords = item.get("keywords") or []

    # Standard: Titel ist Kategoriename
    category_name = raw_title
    extra_term_from_title = None

    # Falls "X (part of Y)" -> Kategorie = Y, extra Term = X
    m = PART_OF_RE.match(raw_title)
    if m:
        extra_term_from_title = m.group(1).strip()
        category_name = m.group(2).strip()

    if not category_name:
        continue

    if category_name not in groups:
        groups[category_name] = {
            "name": category_name,
            "terms": [],
            "_seen": set(),
        }

    bucket = groups[category_name]

    # Bei "X (part of Y)" den linken Teil als Term ergänzen
    if extra_term_from_title:
        add_term(bucket["terms"], bucket["_seen"], extra_term_from_title)

    # Keywords ergänzen
    for kw in keywords:
        if isinstance(kw, dict):
            term = kw.get("title", "")
        else:
            term = str(kw)

        add_term(bucket["terms"], bucket["_seen"], term)

# Optional: Wenn eine Kategorie am Ende gar keine Terms hat,
# nimm den Kategorienamen selbst als Term dazu
for bucket in groups.values():
    if not bucket["terms"]:
        add_term(bucket["terms"], bucket["_seen"], bucket["name"])

# Ausgabeformat wie deine Demo-Datei
result = {}
for i, bucket in enumerate(groups.values(), start=1):
    result[str(i)] = {
        "name": bucket["name"],
        "terms": bucket["terms"],
    }

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Fertig:", len(result), "Kategorien erzeugt")