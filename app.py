import streamlit as st
from st_keyup import st_keyup
import streamlit.components.v1 as components
import json
from pathlib import Path



st.set_page_config(layout="wide")



st.markdown("""
<style>
div[role="dialog"] {
    width: min(900px, 95vw) !important;
    max-width: 95vw !important;
}

div[role="dialog"] > div {
    width: 100% !important;
    max-width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
mark {
    background-color: #fff3a3;
    padding: 0 2px;
    border-radius: 3px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
textarea {
    white-space: pre-wrap !important;
    overflow-x: hidden !important;
}
</style>
""", unsafe_allow_html=True)

h1, h2 = st.columns([8, 1])

def close_preview():
    st.session_state["kw_show_preview"] = False
    st.session_state["keywords_preview_id"] = None
def close_group_preview():
    st.session_state["kw_show_group_preview"] = False
    st.session_state["keywords_preview_group_index"] = None
def close_edit():
    st.session_state["kw_show_edit"] = False
    st.session_state["kw_edit_cid"] = None
def close_history():
    st.session_state["kw_show_history_dialog"] = False

def close_all_dialogs():
    close_preview()
    close_group_preview()
    close_edit()
    close_history()
    st.session_state["kw_show_save_dialog"] = False
    st.session_state["kw_show_create_dialog"] = False 

with h1:
    st.title("Boolean Builder")
with h2:
    if st.button("🕘", key="btn_open_history_top", use_container_width=True):
        close_all_dialogs()
        st.session_state["kw_show_history_dialog"] = True
        st.session_state["kw_skip_close_history_once"] = True
        st.rerun()
# Testdaten (so wie spaeter aus DB)
CATEGORIES = {
    "keywords": [
        {
            "id": 1,
            "name": "NN - AIF",
            "terms": ["AIF", "advanced interface framework", "advanced-interface-framework"],
        },
        {
            "id": 2,
            "name": "SAP - ABAP",
            "terms": ["ABAP", "SAPABAP", "Advanced Business Application Programming", "Abap-oo"],
        },
        {
            "id": 3,
            "name": "NN - CDO",
            "terms": ["CDO","Chief Digital Officer","Leiter Digitalisierung","Digitalisierungsleiter"],
        },
        {
            "id": 4,
            "name": "NN - Berater / Consultant - German",
            "terms": ["Berater","Beraterin","Consultant","Beratungs","Expertin","Experte","Betreuer","Betreuerin","Administrator","Administratorin","Admin","Spezialist",
                "Spezialistin","Analytiker","Analyst","Subject Matter Expert","Beratung","Administration","Konsultiert","Konsultieren","Engineer","Specialist","Eng",
                "Engineering","Enginer","Enginner","Modulberater","Modulberaterin","Modulbetreuer","Modulbetreuerin","Module Owner","Modulverantwortlicher","Modul Verantwortlicher",
                "Modulverantwortliche","Modul Verantwortliche","Product Owner"]
        },
    ]
}

DATA_FILE = Path("kw_categories_big.json")

HISTORY_FILE = Path("kw_history.json")

def load_kw_history() -> list[dict]:
    if HISTORY_FILE.exists():
        try:
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                # minimal clean
                cleaned = []
                for it in data:
                    if isinstance(it, dict) and "id" in it and "name" in it and "boolean" in it:
                        cleaned.append(it)
                return cleaned
        except:
            pass
    return []

def save_kw_history(items: list[dict]) -> None:
    HISTORY_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def load_kw_categories(default_map: dict) -> dict:
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # keys aus json sind strings -> wieder int
                cleaned = {}
                for k, v in data.items():
                    try:
                        cid = int(k)
                    except:
                        continue
                    if isinstance(v, dict) and "name" in v and "terms" in v:
                        cleaned[cid] = {"name": str(v["name"]), "terms": list(v["terms"])}
                # falls neue Defaults dazu kommen, beibehalten
                for cid, dv in default_map.items():
                    cleaned.setdefault(cid, {"name": dv["name"], "terms": list(dv["terms"])})
                return cleaned
        except:
            pass
    return default_map

def save_kw_categories(cat_map: dict) -> None:
    # int keys -> string keys fuer json
    dumpable = {str(cid): {"name": v["name"], "terms": list(v["terms"])} for cid, v in cat_map.items()}
    DATA_FILE.write_text(json.dumps(dumpable, ensure_ascii=False, indent=2), encoding="utf-8")

def normalize_search_text(text: str) -> str:
    text = (
        text.lower()
        .replace("/", " ")
        .replace("-", " ")
        .replace("_", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace(".", " ")
        .replace(",", " ")
    )
    return " ".join(text.split())

def build_search_index(categories):
    index = {}

    for cid, cat in categories.items():
        texts = [cat["name"]] + cat["terms"]

        for text in texts:
            normalized = normalize_search_text(str(text))

            # kompletter Text
            variants = [normalized]

            # einzelne Wörter zusätzlich
            variants.extend(normalized.split())

            for variant in variants:
                variant = variant.strip()
                if not variant:
                    continue

                for i in range(1, min(len(variant), 20) + 1):
                    prefix = variant[:i]

                    if prefix not in index:
                        index[prefix] = []

                    index[prefix].append(cid)

    return index

def build_search_records(categories):
    records = {}

    for cid, cat in categories.items():
        name = str(cat["name"])
        terms = [str(t) for t in cat.get("terms", [])]

        records[cid] = {
            "id": cid,
            "name": name,
            "terms": terms,
            "name_norm": normalize_search_text(name),
            "terms_norm": [normalize_search_text(t) for t in terms],
        }

    return records

# --- Base Daten (so als waere es spaeter DB) + temporaere Overrides ---
if "kw_base_categories" not in st.session_state:
    default_map = {
        c["id"]: {"name": c["name"], "terms": list(c["terms"])}
        for c in CATEGORIES["keywords"]
    }
    st.session_state["kw_base_categories"] = load_kw_categories(default_map)

if "kw_search_index" not in st.session_state:
    st.session_state["kw_search_index"] = build_search_index(st.session_state["kw_base_categories"])
if "kw_search_records" not in st.session_state:
    st.session_state["kw_search_records"] = build_search_records(st.session_state["kw_base_categories"])


search_index = st.session_state["kw_search_index"]

def get_candidate_ids(search_index, q: str, all_ids: list[int]) -> list[int]:
    tokens = [t for t in q.split() if t]

    if not tokens:
        return []

    token_sets = []
    for tok in tokens:
        ids = search_index.get(tok, [])
        if ids:
            token_sets.append(set(ids))

    # Wenn kein Token im Index gefunden wurde -> langsamer Fallback
    if not token_sets:
        return all_ids

    # Bei mehreren Tokens: Schnittmenge = deutlich kleinere Kandidatenliste
    candidate_set = token_sets[0]
    for s in token_sets[1:]:
        candidate_set = candidate_set.intersection(s)

    # Falls Schnittmenge leer, lieber Union statt kompletter Vollscan
    if not candidate_set:
        candidate_set = set()
        for s in token_sets:
            candidate_set.update(s)

    return list(candidate_set)

if "kw_overrides" not in st.session_state:
    st.session_state["kw_overrides"] = {}

def build_term_pool() -> list[str]:
    # Alle bereits gespeicherten Unterkategorien (Terms) einsammeln
    pool = set()
    for _, data in st.session_state["kw_base_categories"].items():
        for t in data.get("terms", []):
            tt = (t or "").strip()
            if tt:
                pool.add(tt)

    # OPTIONAL: wenn du temporaere Overrides auch als Vorschlaege willst, dann anlassen
    for _, ov in st.session_state.get("kw_overrides", {}).items():
        for t in ov.get("terms", []):
            tt = (t or "").strip()
            if tt:
                pool.add(tt)

    return sorted(pool, key=lambda x: x.lower())

def rank_term_suggestions(pool: list[str], query: str, exclude: list[str] | None = None) -> list[str]:
    q = (query or "").strip().lower()
    if not q:
        return []

    # nur exakte Begriffe ausschließen, nicht lowercase-gleich
    exclude_exact = set((t or "").strip() for t in (exclude or []))

    ranked = []
    seen = set()

    for term in pool:
        term_clean = (term or "").strip()
        if not term_clean:
            continue

        term_lower = term_clean.lower()

        # nur exakt gleiche Vorschläge doppelt verhindern
        if term_clean in seen:
            continue
        seen.add(term_clean)

        # nur exakt gleiche bereits vorhandene Begriffe ausschließen
        if term_clean in exclude_exact:
            continue

        if term_lower == q:
            score = 1
        elif term_lower.startswith(q):
            score = 2
        elif any(word.startswith(q) for word in term_lower.replace("/", " ").replace("-", " ").split()):
            score = 3
        elif q in term_lower:
            score = 4
        else:
            continue

        ranked.append((score, len(term_clean), term_clean.lower(), term_clean))

    ranked.sort(key=lambda x: (x[0], x[1], x[2]))
    return [x[3] for x in ranked[:10]]

from datetime import datetime

def make_history_snapshot(name: str) -> dict:
    # aktuelle Auswahl “einfrieren”
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Kategorien-Gruppen als Namen anzeigen (zur Historie)
    cat_groups = []
    for g in st.session_state.get("keywords_groups", []):
        names = [get_cat(cid)["name"] for cid in g]
        cat_groups.append({
        "cids": list(g),
        "names": names,
        "is_not": bool(g) and all(cid in st.session_state.get("kw_not_cids", set()) for cid in g),
        })

    # Unterkategorie-Gruppen
    term_groups = []
    for tg in st.session_state.get("kw_term_groups", []):
        term_groups.append(list(tg))

    snap = {
        "id": str(int(datetime.now().timestamp() * 1000)),  # simple unique id
        "name": (name or "").strip(),
        "created_at": now,
        "updated_at": now,
        "boolean": st.session_state.get("kw_out", ""),  # dein aktueller Output
        "state": {
            "keywords_groups": [list(g) for g in st.session_state.get("keywords_groups", [])],
            "kw_term_groups": [list(tg) for tg in st.session_state.get("kw_term_groups", [])],
            "kw_not_cids": sorted(list(st.session_state.get("kw_not_cids", set()))),
        },
        "summary": {
            "category_groups": cat_groups,
            "term_groups": term_groups,
        },
    }
    return snap

# Merker fuer Vorschau
if "keywords_preview_id" not in st.session_state:
    st.session_state["keywords_preview_id"] = None
if "keywords_selected" not in st.session_state:
    st.session_state["keywords_selected"] = []
if "kw_show_preview" not in st.session_state:
    st.session_state["kw_show_preview"] = False
if "keywords_groups" not in st.session_state:
    st.session_state["keywords_groups"] = []   # z.B. [[1],[2,3]]
if "kw_show_group_preview" not in st.session_state:
    st.session_state["kw_show_group_preview"] = False
if "keywords_preview_group_index" not in st.session_state:
    st.session_state["keywords_preview_group_index"] = None
if "kw_preview_tick" not in st.session_state:
    st.session_state["kw_preview_tick"] = 0
if "kw_preview_open_tick" not in st.session_state:
    st.session_state["kw_preview_open_tick"] = -1
if "kw_group_mode" not in st.session_state:
    st.session_state["kw_group_mode"] = False
if "kw_group_select" not in st.session_state:
    st.session_state["kw_group_select"] = set()
if "kw_group_filter" not in st.session_state:
    st.session_state["kw_group_filter"] = None  # None | "NOT" | "NORMAL"
if "kw_not_cids" not in st.session_state:
    st.session_state["kw_not_cids"] = set()  # Kategorie-IDs die NOT sind
if "kw_copy_now" not in st.session_state:
    st.session_state["kw_copy_now"] = False
if "kw_term_groups" not in st.session_state:
    st.session_state["kw_term_groups"] = []  # freie Unterkategorien als Gruppen, z.B. [["AI"], ["ML","LLM"]]
if "kw_search_mode" not in st.session_state:
    st.session_state["kw_search_mode"] = "Kategorie"  # oder "Unterkategorie"
if "kw_last_mode" not in st.session_state:
    st.session_state["kw_last_mode"] = st.session_state["kw_search_mode"]
if "kw_show_create_dialog" not in st.session_state:
    st.session_state["kw_show_create_dialog"] = False
if "kw_create_terms" not in st.session_state:
    st.session_state["kw_create_terms"] = []
if "kw_reset_create_dialog" not in st.session_state:
    st.session_state["kw_reset_create_dialog"] = False
if "kw_reset_create_term_input" not in st.session_state:
    st.session_state["kw_reset_create_term_input"] = False
if "kw_reset_edit_term_input" not in st.session_state:
    st.session_state["kw_reset_edit_term_input"] = False
if "kw_hits_cache" not in st.session_state:
    st.session_state["kw_hits_cache"] = []

if "kw_hits_cache_key" not in st.session_state:
    st.session_state["kw_hits_cache_key"] = None

if "kw_data_version" not in st.session_state:
    st.session_state["kw_data_version"] = 0

# Temporaere Aenderungen: cid -> {"name": ..., "terms": [...]}
if "kw_overrides" not in st.session_state:
    st.session_state["kw_overrides"] = {}

if "kw_last_query" not in st.session_state:
    st.session_state["kw_last_query"] = ""

if "kw_history" not in st.session_state:
    st.session_state["kw_history"] = load_kw_history()

if "kw_history_selected_id" not in st.session_state:
    st.session_state["kw_history_selected_id"] = None

if "kw_history_edit_mode" not in st.session_state:
    st.session_state["kw_history_edit_mode"] = False  # False = neuer Save, True = Update eines bestehenden

if "kw_show_save_dialog" not in st.session_state:
    st.session_state["kw_show_save_dialog"] = False

if "kw_show_history_dialog" not in st.session_state:
    st.session_state["kw_show_history_dialog"] = False

if "kw_history_selected_id" not in st.session_state:
    st.session_state["kw_history_selected_id"] = None

if "kw_results_limit" not in st.session_state:
    st.session_state["kw_results_limit"] = 11

if "kw_reset_save_dialog" not in st.session_state:
    st.session_state["kw_reset_save_dialog"] = False

if "kw_last_overlay_text" not in st.session_state:
    st.session_state["kw_last_overlay_text"] = None

if "kw_skip_close_history_once" not in st.session_state:
    st.session_state["kw_skip_close_history_once"] = False

import time

if "kw_copy_time" not in st.session_state:
    st.session_state["kw_copy_time"] = 0
def all_selected_category_ids():
    return [cid for g in st.session_state["keywords_groups"] for cid in g]

def get_cat(cid: int):
    base_all = st.session_state.get("kw_base_categories", {})
    if cid not in base_all:
        return None

    base = base_all[cid]
    ov = st.session_state.get("kw_overrides", {}).get(cid)

    if not ov:
        return {
            "id": cid,
            "name": base["name"],
            "terms": base["terms"]
        }

    return {
        "id": cid,
        "name": ov.get("name", base["name"]),
        "terms": ov.get("terms", base["terms"])
    }

if "kw_show_edit" not in st.session_state:
    st.session_state["kw_show_edit"] = False
if "kw_edit_cid" not in st.session_state:
    st.session_state["kw_edit_cid"] = None
if "kw_edit_mode" not in st.session_state:
    st.session_state["kw_edit_mode"] = "temp"

def remove_cids_from_groups(cids_to_remove):
    new_groups = []
    for g in st.session_state["keywords_groups"]:
        g2 = [cid for cid in g if cid not in cids_to_remove]
        if g2:
            new_groups.append(g2)
    st.session_state["keywords_groups"] = new_groups

# --- Edit Dialog State ---
if "kw_show_edit" not in st.session_state:
    st.session_state["kw_show_edit"] = False
if "kw_edit_cid" not in st.session_state:
    st.session_state["kw_edit_cid"] = None
if "kw_edit_mode" not in st.session_state:
    # "permanent" = dauerhaft speichern (Base)
    # "temp" = nur fuer aktuelle Auswahl/Session
    st.session_state["kw_edit_mode"] = "temp"
if "kw_clear_key" not in st.session_state:
    st.session_state["kw_clear_key"] = None

def open_edit(cid: int, mode: str):
    st.session_state["kw_edit_cid"] = cid
    st.session_state["kw_edit_mode"] = mode
    st.session_state["kw_show_edit"] = True

def get_match_score(cat_now, q: str):
    name = cat_now["name_norm"]
    terms = cat_now["terms_norm"]

    if name == q:
        return 1

    if name.startswith(q):
        return 2

    name_words = name.split()
    if any(w.startswith(q) for w in name_words):
        return 3

    if q in name:
        return 4

    if any(t == q for t in terms):
        return 5

    if any(t.startswith(q) for t in terms):
        return 6

    if any(q in t for t in terms):
        return 7

    token_score = token_match_score(cat_now, q)
    if token_score < 999:
        return token_score

    return 999

def token_match_score(cat_now, q: str):
    q_tokens = [t for t in q.split() if t]
    if not q_tokens:
        return 999

    name = cat_now["name_norm"]
    terms = cat_now["terms_norm"]

    if all(tok in name for tok in q_tokens):
        return 8

    if any(all(tok in term for tok in q_tokens) for term in terms):
        return 9

    return 999

import re

def highlight_query(text: str, query: str) -> str:
    if not query:
        return text

    pattern = re.escape(query)
    return re.sub(
        pattern,
        lambda m: f"<mark>{m.group(0)}</mark>",
        text,
        flags=re.IGNORECASE
    )


def build_boolean(groups_local):
            def fmt_term(t: str) -> str:
                if any(ch in t for ch in [" ", "-", ".", "/", "(", ")", "+", "&"]):
                    return f'"{t}"'
                return t

            def cat_terms(cid: int) -> list[str]:
                cat = get_cat(cid)
                return [fmt_term(t) for t in cat["terms"]]

            blocks = []

            # 0) Freie Unterkategorien (Session-only) als eigene Blöcke
            # 0) Unterkategorien (Session-only) als OR-Gruppen
            for tg in st.session_state.get("kw_term_groups", []):
                clean = []
                for term in tg:
                    tt = (term or "").strip()
                    if tt:
                        clean.append(fmt_term(tt))
                if clean:
                    blocks.append("(" + " OR ".join(clean) + ")")

            for g in groups_local:
                if not g:
                    continue

                # FLAT: alle Terms aller Kategorien in dieser Gruppe zusammenwerfen
                all_terms = []
                for cid in g:
                    all_terms.extend(cat_terms(cid))

                block = "(" + " OR ".join(all_terms) + ")"

                # NOT: wenn ALLE Kategorien in der Gruppe NOT sind
                if all(cid in st.session_state["kw_not_cids"] for cid in g):
                    block = "NOT " + block

                blocks.append(block)

            return " AND ".join(blocks)

left_col, middle_col, right_col = st.columns([1.25, 1.15, 1.1])

with left_col:
    st.header("Keywords")

# Modus Switch: Kategorie oder Unterkategorie
    mode_col, btn_col = st.columns([7,2])

    with mode_col:
        st.radio(
            "",
            ["Kategorie", "Unterkategorie"],
            horizontal=True,
            key="kw_search_mode",
            label_visibility="collapsed"
        )

    with btn_col:
        if st.button("＋ Kategorie", key="kw_create_cat_btn", use_container_width=True):
            close_all_dialogs()
            st.session_state["kw_show_create_dialog"] = True
            st.rerun()

    mode_now = st.session_state["kw_search_mode"]

    if mode_now != st.session_state["kw_last_mode"]:
        close_all_dialogs()
        st.session_state["kw_last_mode"] = mode_now
        st.rerun()

    # 1) Live-Eingabe ohne Enter
    placeholder = "Tippe z.B. NN oder SAP..." if st.session_state["kw_search_mode"] == "Kategorie" else "Tippe eine Unterkategorie z.B. AI..."
    query_widget = st_keyup(
        label="Suche Keywords",
        placeholder=placeholder,
        key="kw_query",
    )

    query_value = st.session_state.get("kw_query", query_widget or "")
    q_raw = (query_value or "").strip()
    q = normalize_search_text(q_raw)

    if q != st.session_state.get("kw_last_query", ""):
        st.session_state["kw_last_query"] = q
        st.session_state["kw_results_limit"] = 11

        close_preview()
        close_group_preview()
        close_edit()

        if st.session_state.get("kw_skip_close_history_once"):
            st.session_state["kw_skip_close_history_once"] = False
        else:
            close_history()

    # 2) Trefferliste wie Sourcebreaker (unter dem Feld)
    selected_ids = {
        cid
        for group in st.session_state["keywords_groups"]
        for cid in group
    }
    
    hits = []

    cache_key = (
        q,
        st.session_state["kw_search_mode"],
        st.session_state["kw_data_version"],
    )

    if len(q) >= 1:
        if st.session_state.get("kw_hits_cache_key") != cache_key:
            mode = st.session_state["kw_search_mode"]

            all_ids = list(st.session_state["kw_base_categories"].keys())
            candidate_ids = get_candidate_ids(search_index, q, all_ids)

            # Dubletten entfernen, Reihenfolge behalten
            seen = set()
            candidate_ids = [cid for cid in candidate_ids if not (cid in seen or seen.add(cid))]

            new_hits = []

            if mode == "Kategorie":
                ranked_hits = []

                for cid in candidate_ids:
                    cat_view = get_cat(cid)
                    cat_now = st.session_state["kw_search_records"][cid]
                    score = get_match_score(cat_now, q)

                    if score < 999:
                        ranked_hits.append({
                            "type": "cat",
                            "id": cid,
                            "name": cat_view["name"],
                            "score": score
                        })

                ranked_hits.sort(key=lambda x: (x["score"], x["name"].lower()))
                new_hits = ranked_hits

            else:
                new_hits.append({"type": "free_term", "term": (q_raw or "").strip()})

                ranked_hits = []

                for cid in candidate_ids:
                    cat_view = get_cat(cid)
                    cat_now = st.session_state["kw_search_records"][cid]
                    terms_norm = cat_now["terms_norm"]

                    score = 999
                    if any(t == q for t in terms_norm):
                        score = 1
                    elif any(t.startswith(q) for t in terms_norm):
                        score = 2
                    elif any(q in t for t in terms_norm):
                        score = 3

                    if score < 999:
                        ranked_hits.append({
                            "type": "cat_term_match",
                            "id": cid,
                            "name": cat_view["name"],
                            "score": score
                        })

                ranked_hits.sort(key=lambda x: (x["score"], x["name"].lower()))
                new_hits.extend(ranked_hits)

            st.session_state["kw_hits_cache"] = new_hits
            st.session_state["kw_hits_cache_key"] = cache_key

        # cache verwenden und nur aktuell ausgewählte Kategorien ausblenden
        selected_ids = {
            cid
            for group in st.session_state["keywords_groups"]
            for cid in group
        }

        hits = [
            item for item in st.session_state["kw_hits_cache"]
            if not (
                item.get("type") in ("cat", "cat_term_match")
                and item.get("id") in selected_ids
            )
        ]

    if len(q) >= 1:
        st.caption(f"Zeige {min(len(hits), st.session_state['kw_results_limit'])} von {len(hits)} Treffern")

    # 3) Liste rendern (Name links, + und Auge rechts)
    with st.container(height=260):
        if len(q) >= 1 and not hits:
            st.caption("Keine Treffer.")
        elif len(q) == 0:
            st.caption("Tippe, um Kategorien zu sehen.")
        else:
            for item in hits[:st.session_state["kw_results_limit"]]:
                t = item.get("type")

                # --- 1) Free Term Option (nur im Unterkategorie Modus) ---
                if t == "free_term":
                    term = (item.get("term") or "").strip()
                    row1, row2 = st.columns([9, 1])

                    with row1:
                        st.write(f'Unterkategorie: "{term}" direkt hinzufuegen')

                    with row2:
                        # schon vorhanden, wenn term in irgendeiner term-gruppe steckt
                        already = any(term in g for g in st.session_state["kw_term_groups"])
                        disabled = (term == "") or already

                        if st.button("＋", key=f"kw_add_free_term_{term}", disabled=disabled):
                            close_preview()
                            close_group_preview()
                            close_edit()
                            close_history()

                            st.session_state["kw_term_groups"].append([term])

                    continue

                # --- 2) Kategorien Treffer (normal oder term-match) ---
                name = item["name"]
                cid = item["id"]

                row1, row2, row3 = st.columns([8, 1, 1])

                with row1:
                    prefix = ""

                    if item.get("score") == 1:
                        prefix = "⭐ "
                    elif item.get("score") == 2:
                        prefix = "⬆️ "
                    elif item.get("score") == 3:
                        prefix = "🔤 "
                    elif item.get("score") == 4:
                        prefix = "📝 "
                    elif item.get("score") >= 5:
                        prefix = "🔎 "

                    label = f"{prefix}{name}"

                    if t == "cat_term_match":
                        label += "  (Unterkategorie)"

                    st.write(label)

                with row2:
                    if st.button("＋", key=f"kw_add_{cid}"):
                        close_all_dialogs()

                        already = any(cid in g for g in st.session_state["keywords_groups"])
                        if not already:
                            st.session_state["keywords_groups"] = [
                                *st.session_state["keywords_groups"],
                                [cid]
                            ]
                            st.rerun()


                with row3:
                    if st.button("👁", key=f"kw_eye_{cid}"):
                        close_all_dialogs()
                        st.session_state["keywords_preview_id"] = cid
                        st.session_state["kw_show_preview"] = True
                        st.rerun()

    if len(hits) > st.session_state["kw_results_limit"]:
        if st.button("Mehr anzeigen", key="kw_load_more"):
            st.session_state["kw_results_limit"] += 11
    
    st.caption(f"Zeige {min(len(hits), st.session_state['kw_results_limit'])} von {len(hits)} Treffern")

    # 4) Preview als "Popover" per Dialog (stabil)

    pv_id = st.session_state.get("keywords_preview_id")

    if st.session_state["kw_show_preview"] and pv_id is not None:
        cat = get_cat(pv_id)

        if cat is None:
            close_preview()
            st.rerun()

        @st.dialog("Preview")
        def show_preview():
            pv_id = st.session_state["keywords_preview_id"]
            cat = get_cat(pv_id)

            if cat is None:
                st.warning("Diese Kategorie ist nicht mehr verfügbar.")
                if st.button("Schließen", key="dlg_close_invalid"):
                    close_preview()
                    st.rerun()
                return

            st.subheader(cat["name"])
            st.caption("Unterkategorien")
            st.write("  ".join([f"`{t}`" for t in cat["terms"]]))
            st.divider()

            already_selected = any(
                pv_id in group for group in st.session_state["keywords_groups"]
            )

            c1, c2, c3 = st.columns([2, 1, 1])

            with c1:
                if already_selected:
                    st.button("Schon ausgewählt", disabled=True)
                else:
                    if st.button("Kategorie hinzufügen", key="dlg_add"):
                        close_preview()
                        st.session_state["keywords_groups"] = [
                            *st.session_state["keywords_groups"],
                            [pv_id]
                        ]
                        st.rerun()

            with c2:
                if st.button("Schließen", key="dlg_close"):
                    close_preview()
                    st.rerun()

            with c3:
                if st.button("✏️", key="dlg_edit"):
                    close_preview()
                    open_edit(pv_id, mode="permanent")
                    st.rerun()

        show_preview()

    

with middle_col:
    def render_middle():
        st.subheader("Ausgewählte Kategorien (Gruppen)")

        topA, topB = st.columns([1, 4])
        with topA:
            if not st.session_state["kw_group_mode"]:
                if st.button("Gruppieren", key="kw_group_btn"):
                    close_preview()
                    close_group_preview()
                    st.session_state["kw_group_mode"] = True
                    st.session_state["kw_group_select"] = set()
            else:
                if st.button("Abbrechen", key="kw_group_cancel"):
                    st.session_state["kw_group_mode"] = False
                    st.session_state["kw_group_select"] = set()
                    st.session_state["kw_group_filter"] = None

        groups = st.session_state["keywords_groups"]

        boolean_string = build_boolean(groups)

        # --- Gruppier-Modus: Checkboxen anzeigen ---
        if st.session_state["kw_group_mode"]:
            st.info("Wähle mindestens 2 Gruppen aus und drücke dann Gruppieren ✅")

            # ---- gemeinsame Liste: Term-Gruppen + Kategorien-Gruppen ----
            items = []

            

            # Kategorien-Gruppen danach
            def is_group_not(g):
                return len(g) > 0 and all(cid in st.session_state["kw_not_cids"] for cid in g)

            for gi, g in enumerate(groups):
                names = []
                for cid in g:
                    cat = get_cat(cid)
                    if cat:
                        names.append(cat["name"])

                is_not = is_group_not(g)

                label = "  OR  ".join(names)
                if is_not:
                    label = "NOT " + label

                items.append({
                    "key": f"cat:{gi}",
                    "kind": "cat",
                    "index": gi,
                    "label": label,
                    "not": is_not,
                })

            # Filter:
            # None | "TERM" | "CAT_NOT" | "CAT_NORMAL"

            current_selected_keys = set()

            for it in items:
                widget_key = f"kw_grpchk_{it['key']}"
                if st.session_state.get(widget_key, False):
                    current_selected_keys.add(it["key"])

            # Fallback: falls Widgets noch nicht existieren
            if not current_selected_keys:
                current_selected_keys = set(st.session_state.get("kw_group_select", set()))

            derived_flt = None
            if current_selected_keys:
                first_key = next(iter(current_selected_keys), None)
                first_item = next((x for x in items if x["key"] == first_key), None)

                if first_item is not None:
                    if first_item["kind"] == "term":
                        derived_flt = "TERM"
                    else:
                        derived_flt = "CAT_NOT" if first_item["not"] else "CAT_NORMAL"

            flt = derived_flt

            new_group_select = set()

            for it in items:
                incompatible = False

                if flt == "TERM":
                    incompatible = (it["kind"] != "term")
                elif flt == "CAT_NOT":
                    incompatible = (it["kind"] != "cat") or (it["not"] is not True)
                elif flt == "CAT_NORMAL":
                    incompatible = (it["kind"] != "cat") or (it["not"] is not False)

                disabled = (flt is not None and incompatible)
                widget_key = f"kw_grpchk_{it['key']}"

                val = st.checkbox(
                    it["label"],
                    key=widget_key,
                    disabled=disabled
                )

                if val and not disabled:
                    new_group_select.add(it["key"])

            st.session_state["kw_group_select"] = new_group_select
            st.session_state["kw_group_filter"] = flt

            if len(new_group_select) == 0 and st.session_state.get("kw_group_filter") is not None:
                st.session_state["kw_group_filter"] = None

            # Wenn nichts gewählt -> Filter zurücksetzen
            if len(st.session_state["kw_group_select"]) == 0 and st.session_state.get("kw_group_filter") is not None:
                st.session_state["kw_group_filter"] = None
                st.rerun()

            # Ausgewählte Keys (z.B. "cat:0", "term:1")
            chosen = sorted(list(st.session_state.get("kw_group_select", set())))

            cat_sel = []
            term_sel = []

            for k in chosen:
                if isinstance(k, str) and k.startswith("cat:"):
                    try:
                        cat_sel.append(int(k.split(":")[1]))
                    except:
                        pass
                elif isinstance(k, str) and k.startswith("term:"):
                    try:
                        term_sel.append(int(k.split(":")[1]))
                    except:
                        pass

            # Mixed Kind verhindern (Term + Kategorie)
            mixed_kind = bool(cat_sel and term_sel)
            if mixed_kind:
                st.error("Unterkategorien und Kategorien können nicht zusammen gruppiert werden.")

            # Hinweis: NOT vs Normal wird schon durch kw_group_filter verhindert (CAT_NOT / CAT_NORMAL),
            # deshalb brauchst du hier KEIN extra mixed-not-check mehr.
            # AUFLÖSEN möglich:
            # - genau 1 Kategorie-Gruppe gewählt und diese Gruppe hat >1 Kategorie
            # - ODER genau 1 Term-Gruppe gewählt und diese Gruppe hat >1 Term
            can_ungroup_cat = (
                (not mixed_kind)
                and len(cat_sel) == 1
                and 0 <= cat_sel[0] < len(groups)
                and len(groups[cat_sel[0]]) > 1
            )

            can_ungroup_term = (
                (not mixed_kind)
                and len(term_sel) == 1
                and 0 <= term_sel[0] < len(st.session_state.get("kw_term_groups", []))
                and len(st.session_state["kw_term_groups"][term_sel[0]]) > 1
            )

            can_ungroup = can_ungroup_cat or can_ungroup_term

            if can_ungroup:
                if st.button("Auflösen ✅", key="kw_group_apply_ungroup"):
                    close_preview()
                    close_group_preview()

                    # --- Kategorie-Gruppe auflösen ---
                    if can_ungroup_cat:
                        gi = cat_sel[0]
                        to_split = groups[gi]  # z.B. [1,3]

                        new_groups = []
                        for idx, g in enumerate(groups):
                            if idx == gi:
                                for cid in to_split:
                                    new_groups.append([cid])
                            else:
                                new_groups.append(g)

                        st.session_state["keywords_groups"] = new_groups

                    # --- Term-Gruppe auflösen ---
                    elif can_ungroup_term:
                        ti = term_sel[0]
                        to_split = st.session_state["kw_term_groups"][ti]  # z.B. ["AI","ML"]

                        new_tgroups = []
                        for idx, tg in enumerate(st.session_state["kw_term_groups"]):
                            if idx == ti:
                                for term in to_split:
                                    new_tgroups.append([term])
                            else:
                                new_tgroups.append(tg)

                        st.session_state["kw_term_groups"] = new_tgroups

                    st.session_state["kw_group_mode"] = False
                    st.session_state["kw_group_select"] = set()
                    st.session_state["kw_group_filter"] = None
                    st.rerun()

            else:
                # 2) GRUPPIEREN: mind. 2 Gruppen auswählen
                disabled = mixed_kind or (len(cat_sel) + len(term_sel) < 2)
                if st.button("Gruppieren ✅", key="kw_group_apply_group", disabled=disabled):
                    close_preview()
                    close_group_preview()

                    # ---- Kategorien gruppieren ----
                    if cat_sel:
                        merged = []
                        new_groups = []

                        for gi, g in enumerate(groups):
                            if gi in cat_sel:
                                merged.extend(g)
                            else:
                                new_groups.append(g)

                        new_groups.append(merged)
                        st.session_state["keywords_groups"] = new_groups

                    # ---- Unterkategorien gruppieren ----
                    elif term_sel:
                        merged = []
                        new_groups = []

                        for gi, g in enumerate(st.session_state["kw_term_groups"]):
                            if gi in term_sel:
                                merged.extend(g)
                            else:
                                new_groups.append(g)

                        new_groups.append(merged)
                        st.session_state["kw_term_groups"] = new_groups

                    st.session_state["kw_group_mode"] = False
                    st.session_state["kw_group_select"] = set()
                    st.session_state["kw_group_filter"] = None
                    st.rerun()

        else:
            
            # --- Unterkategorien anzeigen (Session-only, als Gruppen) ---
            if st.session_state.get("kw_term_groups"):
                st.caption("Unterkategorien (direkt hinzugefuegt)")
                for gi, tg in enumerate(list(st.session_state["kw_term_groups"])):
                    cL, cR = st.columns([9, 1])
                    with cL:
                        st.write('Unterkategorie: "' + '"  OR  "'.join(tg) + '"')
                    with cR:
                        if st.button("X", key=f"kw_term_group_rm_{gi}"):
                            st.session_state["kw_term_groups"].pop(gi)
                # Linie nur anzeigen wenn auch Kategorien existieren
                if groups:
                    st.divider()

            # --- Normale Ansicht: Gruppen anzeigen ---
            if (not groups) and (not st.session_state.get("kw_term_groups")):
                st.caption("Noch nichts ausgewählt.")
            else:
                for i, group in enumerate(groups):
                    left, notcol, eye, right = st.columns([6, 1, 1, 1])

                    with left:
                        names = []
                        for cid in group:
                            cat = get_cat(cid)
                            names.append(cat["name"])

                        label = "  OR  ".join(names)

                        # prüfen ob NOT aktiv (auch für gemergte Gruppen)
                        if all(cid in st.session_state["kw_not_cids"] for cid in group):
                            st.markdown(
                                f'<span style="color:red;font-weight:bold;">NOT</span> {label}',
                                unsafe_allow_html=True
                            )
                        else:
                            st.write(label)
                    
                    with notcol:
                        cid = group[0] if len(group) == 1 else None

                        if cid is not None:
                            active = cid in st.session_state["kw_not_cids"]

                            icon = "🔴" if active else "⭕"

                            if st.button(icon, key=f"kw_not_{cid}"):
                                if active:
                                    st.session_state["kw_not_cids"].discard(cid)
                                else:
                                    st.session_state["kw_not_cids"].add(cid)

                                st.rerun()

                    group_key = "_".join(str(cid) for cid in group)

                    with eye:
                        if st.button("👁", key=f"kw_group_eye_{group_key}"):
                            close_preview()
                            close_group_preview()
                            st.session_state["keywords_preview_group_index"] = i
                            st.session_state["kw_show_group_preview"] = True
                            st.rerun()

                    with right:
                        if st.button("X", key=f"kw_group_remove_{group_key}"):
                            close_preview()
                            close_group_preview()

                            new_groups = []
                            for idx, g in enumerate(st.session_state["keywords_groups"]):
                                if idx != i:
                                    new_groups.append(g)
                                else:
                                    for cid in g:
                                        st.session_state["kw_not_cids"].discard(cid)

                            st.session_state["keywords_groups"] = new_groups
                            st.rerun()


                


        if st.session_state["kw_show_group_preview"] and st.session_state["keywords_preview_group_index"] is not None:
            @st.dialog("Preview (Gruppe)")
            def show_group_preview():
                i = st.session_state["keywords_preview_group_index"]

                groups_now = st.session_state["keywords_groups"]
                if i is None or i < 0 or i >= len(groups_now):
                    close_group_preview()
                    st.rerun()

                group = groups_now[i]

                st.subheader(f"Gruppe {i+1}")
                for cid in group:
                    cat = get_cat(cid)
                    st.write(cat["name"])
                    st.caption("Unterkategorien")
                    st.write("  ".join([f"`{t}`" for t in cat["terms"]]))
                    st.divider()

                    # Kopierungen (gemergte Gruppen) NICHT editierbar machen:
                    # Nur Einzelkategorie-Gruppen dürfen editiert werden.
                    if len(group) > 1:
                        st.info("Diese Gruppe ist eine Kopierung und kann nicht editiert werden.")
                        if st.button("Schließen", key="dlg_group_close"):
                            close_group_preview()
                            st.rerun()
                        return

                    # --- ab hier: nur 1 Kategorie in der Gruppe -> editierbar ---
                    edit_cid = group[0]

                    c1, c2 = st.columns([1, 1])

                    with c1:
                        if st.button("Schließen", key="dlg_group_close"):
                            close_group_preview()
                            st.rerun()

                    with c2:
                        # TEMP Edit: nur fuer diese Session (kw_overrides)
                        if st.button("✏️", key=f"dlg_group_edit_{i}"):
                            close_group_preview()
                            open_edit(edit_cid, mode="temp")
                            st.rerun()

            show_group_preview()
    render_middle()

with right_col:
    st.subheader("Boolean Output")

    boolean_string = build_boolean(st.session_state["keywords_groups"])

    # WICHTIG: Textarea-Value per Session-State updaten, sonst bleibt es leer
    st.session_state["kw_out"] = boolean_string

    st.text_area(
        "Output",
        boolean_string,
        height=120
    )

    cA, cB = st.columns([2, 1])

    with cA:
        if st.button("Boolean speichern", key="btn_save_under_output", disabled=not bool(st.session_state.get("kw_out"))):
            st.session_state["kw_show_save_dialog"] = True
            st.rerun()


        # Click-to-copy Overlay fuer normalen Boolean Output
        if boolean_string and st.session_state.get("kw_last_overlay_text") != boolean_string:
            payload = json.dumps(boolean_string)

            components.html(
                f"""
                <script>
                const text = {payload};

                function attachMainCopy() {{
                    const ta = parent.document.querySelector('textarea[aria-label="Output"]');
                    if (!ta) return false;

                    const box = ta.closest('[data-testid="stTextArea"]');
                    if (!box) return false;

                    box.querySelectorAll('.sb-main-overlay').forEach(el => el.remove());
                    box.style.position = 'relative';

                    const ov = parent.document.createElement('div');
                    ov.className = 'sb-main-overlay';
                    ov.style.position = 'absolute';
                    ov.style.left = '0';
                    ov.style.top = '0';
                    ov.style.right = '0';
                    ov.style.bottom = '0';
                    ov.style.cursor = 'pointer';
                    ov.style.background = 'transparent';
                    ov.style.zIndex = '9999';

                    const toast = parent.document.createElement('div');
                    toast.innerText = 'Kopiert!';
                    toast.style.position = 'absolute';
                    toast.style.left = '50%';
                    toast.style.top = '50%';
                    toast.style.transform = 'translate(-50%, -50%)';
                    toast.style.padding = '6px 10px';
                    toast.style.borderRadius = '10px';
                    toast.style.background = 'rgba(0,0,0,0.65)';
                    toast.style.color = 'white';
                    toast.style.fontSize = '14px';
                    toast.style.opacity = '0';
                    toast.style.transition = 'opacity 180ms ease';
                    toast.style.pointerEvents = 'none';

                    ov.appendChild(toast);

                    ov.addEventListener('click', async function(event) {{
                        event.preventDefault();
                        event.stopPropagation();

                        try {{
                            await navigator.clipboard.writeText(text);
                        }} catch (e) {{
                            const tmp = parent.document.createElement('textarea');
                            tmp.value = text;
                            parent.document.body.appendChild(tmp);
                            tmp.select();
                            parent.document.execCommand('copy');
                            parent.document.body.removeChild(tmp);
                        }}

                        toast.style.opacity = '1';
                        setTimeout(() => {{
                            toast.style.opacity = '0';
                        }}, 800);
                    }});

                    box.appendChild(ov);
                    return true;
                }}

                let tries = 0;
                const t = setInterval(() => {{
                    tries++;
                    if (attachMainCopy() || tries > 30) clearInterval(t);
                }}, 120);
                </script>
                """,
                height=0,
            )

            st.session_state["kw_last_overlay_text"] = boolean_string

    if st.session_state.get("kw_reset_save_dialog"):
        st.session_state.pop("kw_save_name", None)
        st.session_state["kw_reset_save_dialog"] = False

    # --- Dialog: Boolean speichern ---
    if st.session_state.get("kw_show_save_dialog"):
        @st.dialog("Boolean speichern")
        def dlg_save_boolean():
            st.caption("Gib einen Namen ein und speichere den aktuellen Boolean.")

            with st.form("save_form", clear_on_submit=False):
                nm = st.text_input("Name", key="kw_save_name")
                submitted = st.form_submit_button("Speichern")

            if submitted:
                name = (nm or "").strip()
                if not name:
                    st.error("Bitte Name eingeben.")
                    return
                if not st.session_state.get("kw_out"):
                    st.error("Kein Boolean vorhanden.")
                    return

                snap = make_history_snapshot(name)
                st.session_state["kw_history"].insert(0, snap)
                save_kw_history(st.session_state["kw_history"])

                st.session_state["kw_show_save_dialog"] = False
                st.session_state["kw_reset_save_dialog"] = True
                st.rerun()

            if st.button("Abbrechen", key="kw_save_cancel"):
                st.session_state["kw_show_save_dialog"] = False
                st.session_state["kw_reset_save_dialog"] = True
                st.rerun()
        dlg_save_boolean()
    
    # --- Dialog: Suchhistorie ---
    if st.session_state.get("kw_show_history_dialog"):
        @st.dialog("Suchhistorie")
        def dlg_history():
            items = st.session_state.get("kw_history", [])

            if not items:
                st.caption("Noch keine gespeicherten Booleans.")
                if st.button("Schließen", key="hist_close_empty"):
                    st.session_state["kw_show_history_dialog"] = False
                    st.rerun()
                return

            # Neueste zuerst
            def _dt(it):
                try:
                    return datetime.strptime(it.get("created_at", ""), "%Y-%m-%d %H:%M:%S")
                except:
                    return datetime.min

            items_sorted = sorted(items, key=_dt, reverse=True)

            left, right = st.columns([1.2, 2.8])

            with left:
                st.caption("Einträge")
                ids = [it["id"] for it in items_sorted]

                if st.session_state.get("kw_history_selected_id") not in ids:
                    st.session_state["kw_history_selected_id"] = ids[0]

                picked = st.radio(
                    " ",
                    options=ids,
                    index=ids.index(st.session_state["kw_history_selected_id"]),
                    format_func=lambda x: next(i for i in items_sorted if i["id"] == x).get("name", "(ohne Name)"),
                    key="hist_pick"
                )
                st.session_state["kw_history_selected_id"] = picked

            chosen = next(i for i in items_sorted if i["id"] == st.session_state["kw_history_selected_id"])

            with right:
                st.subheader(chosen.get("name", "(ohne Name)"))
                st.write(f'Erstellt: {chosen.get("created_at", "")}')
                if chosen.get("updated_at") and chosen.get("updated_at") != chosen.get("created_at"):
                    st.write(f'Aktualisiert: {chosen.get("updated_at", "")}')

                st.divider()
                st.caption("Auswahl (gespeichert)")

                summ = chosen.get("summary", {})

                has_any = False

                for tg in summ.get("term_groups", []):
                    has_any = True
                    st.markdown(
                        f"<div style='padding:6px 10px; border:1px solid #e6e6e6; border-radius:10px; margin-bottom:8px;'>"
                        f"<b>Unterkategorie:</b> {' OR '.join([f'\"{t}\"' for t in tg])}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                for g in summ.get("category_groups", []):
                    has_any = True
                    prefix = "NOT " if g.get("is_not") else ""
                    st.markdown(
                        f"<div style='padding:6px 10px; border:1px solid #e6e6e6; border-radius:10px; margin-bottom:8px;'>"
                        f"{prefix}{' OR '.join(g.get('names', []))}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                if not has_any:
                    st.caption("Keine gespeicherte Auswahl vorhanden.")

                st.divider()
                st.caption("Boolean")
                st.code(chosen.get("boolean", ""), language=None)

                st.divider()
                st.caption("Aktionen")

                a2, a3, a4 = st.columns([1.3, 1, 1])

                
                with a2:
                    if st.button("In Builder laden", key="hist_load", use_container_width=True):
                        state = chosen.get("state", {})
                        st.session_state["keywords_groups"] = [list(g) for g in state.get("keywords_groups", [])]
                        st.session_state["kw_term_groups"] = [list(tg) for tg in state.get("kw_term_groups", [])]
                        st.session_state["kw_not_cids"] = set(state.get("kw_not_cids", []))
                        st.session_state["kw_group_mode"] = False
                        st.session_state["kw_group_select"] = set()
                        st.session_state["kw_group_filter"] = None
                        st.session_state["kw_show_history_dialog"] = False
                        st.rerun()

                with a3:
                    if st.button("Update", key="hist_update", use_container_width=True):
                        if not st.session_state.get("kw_out"):
                            st.error("Kein aktueller Boolean zum Updaten.")
                        else:
                            updated = make_history_snapshot(chosen.get("name", ""))
                            updated["id"] = chosen["id"]
                            updated["created_at"] = chosen.get("created_at")
                            updated["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            orig = st.session_state["kw_history"]
                            for idx, it in enumerate(orig):
                                if it.get("id") == chosen["id"]:
                                    orig[idx] = updated
                                    break
                            save_kw_history(orig)
                            st.success("Aktualisiert.")
                            st.rerun()

                with a4:
                    if st.button("Löschen", key="hist_delete", use_container_width=True):
                        st.session_state["kw_history"] = [
                            it for it in st.session_state["kw_history"]
                            if it.get("id") != chosen["id"]
                        ]
                        save_kw_history(st.session_state["kw_history"])
                        st.session_state["kw_history_selected_id"] = None
                        st.rerun()

            close_col_left, close_col_right = st.columns([5, 1])

            with close_col_right:
                if st.button("Schließen", key="hist_close", use_container_width=True):
                    st.session_state["kw_show_history_dialog"] = False
                    st.rerun()

            copy_js_slot = st.empty()


        dlg_history()

        

    if st.session_state.get("kw_reset_create_dialog"):
        st.session_state.pop("kw_create_name", None)
        st.session_state.pop("kw_create_new_term", None)
        st.session_state["kw_create_terms"] = []
        st.session_state["kw_reset_create_dialog"] = False

    # --- Create Dialog ---
    if st.session_state.get("kw_show_create_dialog"):
        @st.dialog("Kategorie erstellen")
        def create_dialog():
            st.caption("Lege eine neue Kategorie mit Unterkategorien an.")

            new_name = st.text_input("Kategoriename", key="kw_create_name")

            st.divider()
            st.caption("Unterkategorien")

            current_terms = sorted(st.session_state.get("kw_create_terms", []), key=str.lower)

            with st.container(height=170):
                if not current_terms:
                    st.caption("Noch keine Unterkategorien hinzugefügt.")
                else:
                    for i, term in enumerate(current_terms):
                        c1, c2 = st.columns([8, 1])
                        with c1:
                            st.write(term)
                        with c2:
                            if st.button("X", key=f"kw_create_term_del_{i}"):
                                st.session_state["kw_create_terms"].pop(i)
                                st.rerun()

            if st.session_state.get("kw_reset_create_term_input"):
                st.session_state.pop("kw_create_new_term", None)
                st.session_state["kw_reset_create_term_input"] = False

            new_term = st_keyup(
                label="Neue Unterkategorie",
                placeholder="Tippe z.B. Consultant ...",
                key="kw_create_new_term"
            )

            qq = (new_term or "").strip().lower()
            pool = build_term_pool()

            suggestions = rank_term_suggestions(
                pool=pool,
                query=qq,
                exclude=st.session_state["kw_create_terms"]
            )

            with st.container(height=140):
                if qq and suggestions:
                    for s in suggestions:
                        c1, c2 = st.columns([8, 2])
                        with c1:
                            st.write(s)
                        with c2:
                            if st.button("＋", key=f"kw_create_take_{s}"):
                                existing_exact = [t.strip() for t in st.session_state["kw_create_terms"]]
                                if s.strip() not in existing_exact:
                                    st.session_state["kw_create_terms"].append(s)
                                st.session_state["kw_reset_create_term_input"] = True
                                st.rerun()
                elif qq:
                    st.caption("Keine Vorschläge gefunden.")

            cA, cB, cC = st.columns(3)

            with cA:
                if st.button("Unterkategorie hinzufügen", key="kw_create_add_term"):
                    nt = (new_term or "").strip()

                    existing_exact = [t.strip() for t in st.session_state["kw_create_terms"]]

                    if nt:
                        if nt not in existing_exact:
                            st.session_state["kw_create_terms"].append(nt)
                            st.session_state["kw_reset_create_term_input"] = True
                            st.rerun()
                        else:
                            st.error("Diese Unterkategorie existiert bereits.")

            with cB:
                if st.button("Speichern", key="kw_create_save"):

                    name = (st.session_state.get("kw_create_name") or "").strip()
                    terms = list(st.session_state.get("kw_create_terms", []))

                    if not name:
                        st.error("Bitte einen Kategorienamen eingeben.")
                        st.stop()

                    if not terms:
                        st.error("Bitte mindestens eine Unterkategorie hinzufügen.")
                        st.stop()

                    base = st.session_state["kw_base_categories"]

                    new_id = max(base.keys(), default=0) + 1

                    base[new_id] = {
                        "name": name,
                        "terms": terms
                    }

                    save_kw_categories(base)

                    st.session_state["kw_search_index"] = build_search_index(base)
                    st.session_state["kw_search_records"] = build_search_records(base)
                    st.session_state["kw_data_version"] += 1

                    st.session_state["kw_show_create_dialog"] = False
                    st.session_state["kw_reset_create_dialog"] = True
                    st.rerun()

            with cC:
                if st.button("Abbrechen", key="kw_create_cancel"):
                    st.session_state["kw_show_create_dialog"] = False
                    st.session_state["kw_reset_create_dialog"] = True
                    st.rerun()
        create_dialog()

    # --- Edit Dialog ---
    if st.session_state.get("kw_show_edit") and st.session_state.get("kw_edit_cid") is not None:
        @st.dialog("Kategorie bearbeiten")
        def edit_dialog():
            cid = st.session_state["kw_edit_cid"]
            mode = st.session_state["kw_edit_mode"]  # "permanent" oder "temp"
            cat = get_cat(cid)

            # Name
            new_name = st.text_input("Name", value=cat["name"], key=f"kw_edit_name_{cid}")

            st.divider()
            st.caption("Unterkategorien (Terms)")

            # Terms laden (Zwischenspeicher im Dialog)
            tmp_key = f"kw_edit_terms_{cid}"
            if tmp_key not in st.session_state:
                st.session_state[tmp_key] = list(cat["terms"])
            terms = list(st.session_state[tmp_key])

            # Liste + Entfernen
            remove_idx = None

            with st.container(height=170):
                for i, t in enumerate(terms):
                    c1, c2 = st.columns([8, 1])
                    with c1:
                        st.write(t)
                    with c2:
                        if st.button("X", key=f"kw_term_del_{cid}_{i}"):
                            remove_idx = i

            if remove_idx is not None:
                terms.pop(remove_idx)
                st.session_state[tmp_key] = terms
                st.rerun()

            st.divider()

            # Hinzufuegen + Vorschlaege (wie bei Oberkategorien)
            new_term_key = f"kw_new_term_in_{cid}"

            if st.session_state.get("kw_reset_edit_term_input"):
                st.session_state.pop(new_term_key, None)
                st.session_state["kw_reset_edit_term_input"] = False

            typed = st_keyup(
                label="Neue Unterkategorie",
                placeholder="Tippe z.B. AI ...",
                key=new_term_key
            )

            qq = (typed or "").strip().lower()

            # Vorschlags-Pool aus allen gespeicherten Terms
            pool = build_term_pool()

            suggestions = rank_term_suggestions(
                pool=pool,
                query=qq,
                exclude=terms
            )

            # --- Callbacks (wichtig: Session State nur hier anfassen) ---
            def _take_suggestion(val: str):
                current_terms = list(st.session_state.get(tmp_key, []))
                v = (val or "").strip()

                existing_exact = [(t or "").strip() for t in current_terms]

                if v and v not in existing_exact:
                    current_terms.append(v)
                    st.session_state[tmp_key] = current_terms

                st.session_state["kw_reset_edit_term_input"] = True

            def _add_typed_term():
                nt = (typed or "").strip()
                current_terms = list(st.session_state.get(tmp_key, []))

                existing_exact = [t.strip() for t in current_terms]

                if nt and nt not in existing_exact:
                    current_terms.append(nt)
                    st.session_state[tmp_key] = current_terms

                st.session_state["kw_reset_edit_term_input"] = True

            # --- Vorschlagsliste anzeigen ---
            with st.container(height=160):
                if not qq:
                    st.caption("Tippe, um Vorschläge zu sehen.")
                elif qq and not suggestions:
                    st.caption("Keine Vorschläge gefunden.")
                else:
                    for s in suggestions:
                        r1, r2 = st.columns([8, 2])
                        with r1:
                            st.write(s)
                        with r2:
                            st.button(
                                "＋",
                                key=f"kw_take_term_{cid}_{s}",
                                on_click=_take_suggestion,
                                args=(s,)
                            )

            st.button(
                "Unterkategorie hinzufügen",
                key=f"kw_add_term_btn_{cid}",
                on_click=_add_typed_term
            )

            cA, cB, cC = st.columns(3)

            with cA:
                if st.button("Speichern", key=f"kw_edit_save_{cid}"):
                    saved = {"name": new_name.strip(), "terms": list(terms)}

                    if mode == "permanent":
                        st.session_state["kw_base_categories"][cid] = saved
                        st.session_state["kw_overrides"].pop(cid, None)
                        save_kw_categories(st.session_state["kw_base_categories"])

                        st.session_state["kw_search_index"] = build_search_index(
                            st.session_state["kw_base_categories"]
                        )
                        st.session_state["kw_search_records"] = build_search_records(
                            st.session_state["kw_base_categories"]
                        )
                        st.session_state["kw_data_version"] += 1

                    else:
                        st.session_state["kw_overrides"][cid] = saved

                    st.session_state["kw_show_edit"] = False
                    st.session_state["kw_edit_cid"] = None
                    st.session_state.pop(tmp_key, None)
                    st.rerun()

            with cB:
                if st.button("Abbrechen", key=f"kw_edit_cancel_{cid}"):
                    st.session_state["kw_show_edit"] = False
                    st.session_state["kw_edit_cid"] = None
                    st.session_state.pop(tmp_key, None)
                    st.rerun()

            with cC:
                if st.button("Löschen", key=f"kw_edit_delete_{cid}"):
                    # nur dauerhaft gespeicherte Kategorien löschen
                    if cid in st.session_state["kw_base_categories"]:
                        st.session_state["kw_base_categories"].pop(cid, None)

                    # eventuelle temp overrides auch entfernen
                    st.session_state["kw_overrides"].pop(cid, None)

                    # aus aktuellen Gruppen entfernen
                    remove_cids_from_groups({cid})

                    # NOT-Status entfernen
                    st.session_state["kw_not_cids"].discard(cid)

                    # speichern + Suchindex neu bauen
                    save_kw_categories(st.session_state["kw_base_categories"])
                    st.session_state["kw_search_index"] = build_search_index(
                        st.session_state["kw_base_categories"]
                    )
                    st.session_state["kw_search_records"] = build_search_records(
                        st.session_state["kw_base_categories"]
                    )
                    st.session_state["kw_data_version"] += 1

                    # Dialog sauber schließen
                    st.session_state["kw_show_edit"] = False
                    st.session_state["kw_edit_cid"] = None
                    st.session_state.pop(tmp_key, None)

                    st.rerun()

        edit_dialog()
            
  
