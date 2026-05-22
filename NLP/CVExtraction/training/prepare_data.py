"""
Step 2: Convert cleaned JSONL to spaCy binary format (.spacy).

- Reads cleaned.jsonl
- Creates spaCy Doc objects with entity annotations
- Handles tokenization alignment (drops misaligned spans gracefully)
- Stratified train/dev split (85/15) preserving label distribution
- Saves as train.spacy and dev.spacy
"""

import json
import sys
import random
from pathlib import Path
from collections import Counter

import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans
from sklearn.model_selection import train_test_split


LABELS = [
    "Skills",
    "Companies_Worked_At",
    "College_Name",
    "Years_of_Experience",
    "Degree",
    "Languages",
    "Name",
    "Email_Address",
]


def jsonl_to_spacy_doc(nlp, text, spans):
    """
    Convert a single JSONL record to a spaCy Doc with entities.
    Uses character offsets for alignment.
    """
    doc = nlp.make_doc(text)

    ents = []
    for span_data in spans:
        start = span_data["start"]
        end = span_data["end"]
        label = span_data["label"]

        # Use char_span to align to token boundaries
        span = doc.char_span(start, end, label=label, alignment_mode="contract")
        if span is not None:
            ents.append(span)

    # filter_spans resolves any remaining overlaps (keeps longest)
    doc.ents = filter_spans(ents)
    return doc


def get_dominant_label(record):
    """Get the rarest label in a record (for stratified splitting)."""
    label_counts = Counter()
    for span in record.get("spans", []):
        label_counts[span["label"]] += 1

    if not label_counts:
        return "none"

    # Return the rarest label (helps stratification preserve rare classes in both splits)
    rarest = label_counts.most_common()[-1][0]
    return rarest


def main():
    """Convert cleaned NER records into spaCy train/dev DocBin files."""
    random.seed(42)

    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "processed" / "cleaned.jsonl"
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"ERROR: {input_path} not found. Run clean_data.py first.")
        sys.exit(1)

    # Load cleaned data
    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    print(f"Loaded {len(records)} cleaned records")

    # Create blank English model for tokenization
    nlp = spacy.blank("en")

    # Convert all records to docs
    docs = []
    skipped = 0
    total_ents = 0
    dropped_spans = 0

    for rec in records:
        original_span_count = len(rec.get("spans", []))
        doc = jsonl_to_spacy_doc(nlp, rec["text"], rec.get("spans", []))
        ent_count = len(doc.ents)

        if ent_count == 0:
            skipped += 1
            continue

        dropped_spans += original_span_count - ent_count
        total_ents += ent_count
        docs.append((doc, rec))

    print(f"Converted {len(docs)} docs ({skipped} skipped, 0 entities)")
    print(f"Total entities: {total_ents} (dropped {dropped_spans} misaligned spans)")

    # Entity distribution
    ent_dist = Counter()
    for doc, _ in docs:
        for ent in doc.ents:
            ent_dist[ent.label_] += 1
    print("Entity distribution in converted data:")
    for label, count in ent_dist.most_common():
        print(f"  {label}: {count}")

    # Stratified train/dev split
    strat_labels = [get_dominant_label(rec) for _, rec in docs]

    # Handle rare labels that appear only once (can't stratify with 1 sample)
    label_freq = Counter(strat_labels)
    for i, label in enumerate(strat_labels):
        if label_freq[label] < 2:
            strat_labels[i] = "other"

    indices = list(range(len(docs)))
    train_idx, dev_idx = train_test_split(
        indices, test_size=0.15, random_state=42, stratify=strat_labels
    )

    print(f"\nSplit: {len(train_idx)} train, {len(dev_idx)} dev")

    # Verify both splits have all labels
    for split_name, split_idx in [("train", train_idx), ("dev", dev_idx)]:
        labels_in_split = set()
        for i in split_idx:
            doc, _ = docs[i]
            for ent in doc.ents:
                labels_in_split.add(ent.label_)
        print(f"  {split_name} labels: {sorted(labels_in_split)}")

    # Save as .spacy binary
    for split_name, split_idx in [("train", train_idx), ("dev", dev_idx)]:
        doc_bin = DocBin()
        for i in split_idx:
            doc, _ = docs[i]
            doc_bin.add(doc)
        out_path = output_dir / f"{split_name}.spacy"
        doc_bin.to_disk(out_path)
        print(f"Saved {out_path} ({len(split_idx)} docs)")


if __name__ == "__main__":
    main()
