"""
Step 1: Clean the Prodigy JSONL NER dataset.

Handles:
- Garbled text detection and removal (OCR artifacts with single-char tokens)
- Intra-record duplicate content removal
- Span re-alignment after text surgery
- Span validation
- Records with too few usable spans are dropped
"""

import json
import re
import copy
import sys
from pathlib import Path
from collections import Counter


def find_garbled_zones(tokens, min_run=8):
    """
    Detect zones of garbled text: runs of >=min_run consecutive
    single-character tokens (typical of bad PDF extraction).
    Returns list of (text_start, text_end) byte ranges.
    """
    zones = []
    run_start = None
    run_count = 0

    for i, tok in enumerate(tokens):
        if len(tok["text"].strip()) <= 1:
            if run_start is None:
                run_start = i
            run_count += 1
        else:
            if run_count >= min_run:
                start_char = tokens[run_start]["start"]
                end_char = tokens[i - 1]["start"] + len(tokens[i - 1]["text"])
                # extend to surrounding whitespace
                zones.append((start_char, end_char))
            run_start = None
            run_count = 0

    # handle trailing run
    if run_count >= min_run:
        start_char = tokens[run_start]["start"]
        last = tokens[-1]
        end_char = last["start"] + len(last["text"])
        zones.append((start_char, end_char))

    return merge_zones(zones)


def merge_zones(zones, gap=20):
    """Merge zones that are close together."""
    if not zones:
        return []
    zones = sorted(zones)
    merged = [zones[0]]
    for s, e in zones[1:]:
        if s - merged[-1][1] <= gap:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def detect_duplicate_content(text, threshold=0.6):
    """
    Detect if a record contains the same CV text repeated.
    Returns the cutoff index if duplicate found, else None.
    """
    if len(text) < 200:
        return None

    # Look for the pattern: first significant word sequence repeated
    words = text.split()
    if len(words) < 40:
        return None

    # Take the first 15 words as a fingerprint
    fingerprint = " ".join(words[:15])
    # Search for it again after the first 30% of text
    search_start = len(text) // 4
    second_occurrence = text.find(fingerprint, search_start)

    if second_occurrence > 0:
        # Verify it's a real duplicate (not just a repeated phrase)
        chunk1 = text[:second_occurrence].strip()
        chunk2 = text[second_occurrence:second_occurrence + len(chunk1)].strip()
        # Simple similarity: shared words ratio
        words1 = set(chunk1.lower().split())
        words2 = set(chunk2.lower().split())
        if words1 and words2:
            overlap = len(words1 & words2) / max(len(words1), len(words2))
            if overlap > threshold:
                return second_occurrence
    return None


def remove_zones_from_text(text, zones):
    """
    Remove garbled zones from text and build an offset mapping.
    Returns (new_text, offset_map) where offset_map maps old char positions to new ones.
    """
    if not zones:
        return text, lambda x: x

    # Build list of ranges to keep
    keep_ranges = []
    prev_end = 0
    for zs, ze in sorted(zones):
        if prev_end < zs:
            keep_ranges.append((prev_end, zs))
        prev_end = ze
    if prev_end < len(text):
        keep_ranges.append((prev_end, len(text)))

    # Build new text and offset mapping
    new_text_parts = []
    old_to_new = {}
    new_pos = 0

    for ks, ke in keep_ranges:
        segment = text[ks:ke]
        new_text_parts.append(segment)
        for old_idx in range(ks, ke):
            old_to_new[old_idx] = new_pos + (old_idx - ks)
        new_pos += len(segment)

    new_text = "".join(new_text_parts)

    def map_offset(old_pos):
        return old_to_new.get(old_pos)

    return new_text, map_offset


def remap_spans(spans, offset_map, new_text_len):
    """
    Remap span offsets using the offset map.
    Drops spans that can't be mapped (fell in removed zones).
    """
    remapped = []
    for span in spans:
        new_start = offset_map(span["start"])
        # end is exclusive, so map end-1 then add 1
        new_end = offset_map(span["end"] - 1)

        if new_start is not None and new_end is not None:
            new_end += 1
            if 0 <= new_start < new_end <= new_text_len:
                new_span = copy.deepcopy(span)
                new_span["start"] = new_start
                new_span["end"] = new_end
                # Remove token-level keys (will be re-tokenized by spaCy)
                new_span.pop("token_start", None)
                new_span.pop("token_end", None)
                remapped.append(new_span)
    return remapped


def clean_text_whitespace(text):
    """Normalize excessive whitespace while preserving span alignment."""
    # We do NOT modify the text here to preserve span offsets
    # Whitespace normalization happens after span remapping
    return text


def clean_record(record):
    """
    Clean a single Prodigy NER record.
    Returns cleaned record or None if too degraded.
    """
    text = record["text"]
    spans = record.get("spans", [])
    tokens = record.get("tokens", [])

    if not spans:
        return None

    original_span_count = len(spans)

    # Step 1: Find garbled zones
    garbled_zones = find_garbled_zones(tokens) if tokens else []

    # Step 2: Detect duplicate content
    dup_cutoff = detect_duplicate_content(text)
    if dup_cutoff:
        # Add everything after cutoff as a zone to remove
        garbled_zones.append((dup_cutoff, len(text)))
        garbled_zones = merge_zones(garbled_zones, gap=0)

    # Step 3: Remove zones and remap
    if garbled_zones:
        new_text, offset_map = remove_zones_from_text(text, garbled_zones)
        new_spans = remap_spans(spans, offset_map, len(new_text))
    else:
        new_text = text
        new_spans = spans

    # Step 4: Validate spans against actual text
    validated_spans = []
    for span in new_spans:
        extracted = new_text[span["start"]:span["end"]]
        if extracted.strip():  # non-empty after extraction
            validated_spans.append(span)

    # Step 5: Drop record if too many spans were lost
    if len(validated_spans) < 3:
        return None

    # Build clean record (minimal keys needed for conversion)
    clean = {
        "text": new_text,
        "spans": validated_spans,
        "answer": record.get("answer", "accept"),
    }
    if "_task_hash" in record:
        clean["_task_hash"] = record["_task_hash"]

    return clean


def oversample_rare_entities(records, max_multiplier=3):
    """
    Mildly duplicate records containing rare entity types.
    max_multiplier: at most N copies of each rare-label record.
    Only oversample labels with < median span count.
    """
    label_counts = Counter()
    records_by_label = {}
    for i, rec in enumerate(records):
        labels_in_rec = set()
        for span in rec.get("spans", []):
            label = span["label"]
            label_counts[label] += 1
            labels_in_rec.add(label)
        for label in labels_in_rec:
            records_by_label.setdefault(label, []).append(i)

    if not label_counts:
        return records

    counts = sorted(label_counts.values())
    median_count = counts[len(counts) // 2]

    rare_labels = {label for label, count in label_counts.items() if count < median_count}

    if not rare_labels:
        return records

    extra = []
    added_indices = set()
    for label in rare_labels:
        indices = records_by_label.get(label, [])
        # How many times to duplicate: proportional to how rare it is
        ratio = min(median_count / max(label_counts[label], 1), max_multiplier)
        copies = max(int(ratio) - 1, 1)  # at least 1 extra copy
        for idx in indices:
            if idx not in added_indices:
                for _ in range(copies):
                    extra.append(copy.deepcopy(records[idx]))
                added_indices.add(idx)

    print(f"  Oversampling: added {len(extra)} records for rare labels: {rare_labels}")
    return records + extra


def main():
    # Paths
    project_root = Path(__file__).parent.parent
    raw_path = project_root.parent / "CV_Ners.jsonl"
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "cleaned.jsonl"

    if not raw_path.exists():
        print(f"ERROR: Source file not found: {raw_path}")
        sys.exit(1)

    # Load records
    records = []
    with open(raw_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    print(f"Loaded {len(records)} records")

    # Stats before cleaning
    label_before = Counter()
    for r in records:
        for s in r.get("spans", []):
            label_before[s["label"]] += 1
    print(f"Spans before cleaning: {sum(label_before.values())}")
    for label, count in label_before.most_common():
        print(f"  {label}: {count}")

    # Clean each record
    cleaned = []
    dropped = 0
    for rec in records:
        result = clean_record(rec)
        if result:
            cleaned.append(result)
        else:
            dropped += 1

    print(f"\nAfter cleaning: {len(cleaned)} records ({dropped} dropped)")

    # Stats after cleaning
    label_after = Counter()
    for r in cleaned:
        for s in r.get("spans", []):
            label_after[s["label"]] += 1
    print(f"Spans after cleaning: {sum(label_after.values())}")
    for label, count in label_after.most_common():
        print(f"  {label}: {count}")

    # Oversample rare entities
    print("\nBalancing class distribution...")
    balanced = oversample_rare_entities(cleaned)
    print(f"Records after balancing: {len(balanced)}")

    label_final = Counter()
    for r in balanced:
        for s in r.get("spans", []):
            label_final[s["label"]] += 1
    print("Final label distribution:")
    for label, count in label_final.most_common():
        print(f"  {label}: {count}")

    # Save
    with open(output_path, "w", encoding="utf-8") as f:
        for rec in balanced:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"\nSaved cleaned data to {output_path}")


if __name__ == "__main__":
    main()
