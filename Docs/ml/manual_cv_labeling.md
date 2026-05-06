# Manual CV Quality Labeling

Use this workflow to replace weak/synthetic labels with real reviewed CV labels.

1. Copy the template:

```text
DocumentAI/CVQualityScoring/data/manual_labeling_template.csv
```

2. Fill one row per PDF:

```text
file_path,label,reviewer,review_date,notes
Data/samples/cv/Test CV/CV_Riahi_Chaima.pdf,Pro,Yassine,2026-05-05,Complete professional CV
```

3. Generate manual JSONL:

```bash
python DocumentAI/CVQualityScoring/training/merge_manual_labels.py --input DocumentAI/CVQualityScoring/data/manual_labeling_template.csv
```

4. Train on manual labels:

```bash
python DocumentAI/CVQualityScoring/training/train_quality_model.py --dataset DocumentAI/CVQualityScoring/data/cv_quality_manual.jsonl
```

Recommended minimum before final claims:

```text
20 Pro CVs
20 Non Pro CVs
weak_label=false
synthetic=false
```
