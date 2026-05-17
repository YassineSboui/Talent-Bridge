# 🧪 Quick Test Guide - Test BERT in 3 Steps

## ⚡ Quick Path: 5 Minutes

### Step 1: Run Unit Tests
```bash
cd Recommendation/JobRecommendation/src
python test_bert_integration.py
```

✅ **Expected**: 
```
✓ Model Loading
✓ Basic Scoring
✓ Score Range
✓ Empty Input Handling
Total: 4/4 tests passed
✅ All tests passed!
```

---

## 🔄 Medium Path: 15 Minutes

### Step 1: Unit Tests (5 min)
```bash
cd Recommendation/JobRecommendation/src
python test_bert_integration.py
```

### Step 2: Comparison Analysis (10 min)
```bash
python bert_comparison.py
```

✅ **Expected**:
- Console output showing BERT vs TF-IDF scores
- CSV file generated: `comparison_results/bert_vs_tfidf_comparison.csv`
- Performance metrics printed

---

## 🚀 Full Path: Start the App (30 Minutes)

### Step 1: From Repository Root
```powershell
.\start_talent_bridge.ps1
```

⏳ **Wait for startup** (~2 minutes on first run for BERT model load)

✅ **Expected Output**:
```
Loading Sentence Transformer model: sentence-transformers/all-MiniLM-L6-v2
Model loaded successfully
Frontend running at: http://localhost:5173
Backend running at: http://localhost:8000
```

### Step 2: Open the App

**Frontend**: http://localhost:5173

**Backend Docs**: http://localhost:8000/docs

### Step 3: Test It

1. **Login** with demo credentials:
   - Email: `candidate@talentbridge.local`
   - Password: `candidate123`

2. **Upload a CV** (or use `Backend/TalentBridgeAPI/test_cv.pdf`)

3. **View Recommendations** → BERT is now scoring them! 🎉

4. **Check Console Logs** → Should see BERT model loading message

---

## 🔍 What Each Test Does

### test_bert_integration.py ✓
Tests BERT functionality directly:
- Can model load?
- Do scores work?
- Are scores in valid range?
- Handle edge cases?

### bert_comparison.py 📊
Compares BERT vs TF-IDF:
- Performance (speed)
- Accuracy (quality)
- Statistical analysis
- CSV export

### Full App Test 🌐
End-to-end test:
- Upload real CV
- Extract skills
- Score jobs semantically
- Rank recommendations
- Display results

---

## ✅ Quick Checklist

- [ ] Unit tests pass (4/4)
- [ ] Comparison runs successfully
- [ ] App starts without errors
- [ ] Model loads (check logs)
- [ ] CV upload works
- [ ] Recommendations display

---

## 🐛 If Something Goes Wrong

### Can't import sentence_transformers?
```bash
pip install sentence-transformers
```

### Model download hangs?
- Normal for first run (~80MB)
- Wait or check internet connection

### App won't start?
```powershell
# Try skipping SQL
.\start_talent_bridge.ps1 -SkipSql

# Or with SQL Express
.\start_talent_bridge.ps1 -SqlServer ".\SQLEXPRESS"
```

### BERT not being used?
Check logs for:
```
Loading Sentence Transformer model: sentence-transformers/all-MiniLM-L6-v2
Model loaded successfully
```

---

## 📊 Expected Results

### Test Output
```
✓ BERT model loads successfully
✓ Semantic scores are computed
✓ Scores range from 0-100
✓ Edge cases handled
```

### Performance
- Unit tests: ~10 seconds
- Comparison: ~30-60 seconds
- First API call: ~2 seconds (model loads)
- Subsequent calls: ~100ms

### Quality
- Related jobs score higher than unrelated
- Synonyms recognized (ML ≈ Machine Learning)
- Semantic similarities captured
- Scores make sense

---

## 🎯 Which Test Should I Run?

| Goal | Test | Time |
|------|------|------|
| Quick verify BERT works | test_bert_integration.py | 10 sec |
| See quality improvement | bert_comparison.py | 60 sec |
| Test full app | Start app + upload CV | 30 min |
| Production verify | All of the above | 35 min |

---

**START HERE**: `python test_bert_integration.py` ✨

Let me know if you need help with any step! 🚀
