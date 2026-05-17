# Testing BERT Implementation in TalentBridge App

## Quick Start: Test BERT in the Running App

### Option 1: Run Full Integration Tests (Recommended)

```bash
cd Recommendation/JobRecommendation/src
python test_bert_integration.py
```

**Expected Output**:
```
✓ Model Loading
✓ Basic Scoring
✓ Score Range
✓ Empty Input Handling
Total: 4/4 tests passed
✅ All tests passed! BERT semantic matching is working correctly.
```

---

### Option 2: Run BERT vs TF-IDF Comparison

```bash
cd Recommendation/JobRecommendation/src
python bert_comparison.py
```

**Output**:
- Performance metrics (latency comparison)
- Score comparisons for sample jobs
- Statistical analysis
- CSV export: `comparison_results/bert_vs_tfidf_comparison.csv`

---

### Option 3: Start the Full App and Test End-to-End

#### Step 1: Start the TalentBridge Application

From repository root:

```powershell
.\start_talent_bridge.ps1
```

Or with verification:

```powershell
.\start_talent_bridge.ps1 -RunChecks
```

Or skip SQL setup:

```powershell
.\start_talent_bridge.ps1 -SkipSql
```

**Expected Output**:
```
Loading Sentence Transformer model: sentence-transformers/all-MiniLM-L6-v2
Model loaded successfully: sentence-transformers/all-MiniLM-L6-v2
Frontend running at: http://localhost:5173
Backend running at: http://localhost:8000
```

#### Step 2: Access the App

**Frontend**: http://localhost:5173  
**Backend Docs**: http://localhost:8000/docs

**Demo Credentials**:
- Candidate: `candidate@talentbridge.local` / `candidate123`
- Recruiter: `recruiter@talentbridge.local` / `recruiter123`

#### Step 3: Test BERT in the App

1. **Login** as a candidate or recruiter
2. **Upload a CV** (or use test file: `Backend/TalentBridgeAPI/test_cv.pdf`)
3. **View Job Recommendations**
4. **Check logs** to verify BERT is being used:
   ```
   Loading Sentence Transformer model: sentence-transformers/all-MiniLM-L6-v2
   Model loaded successfully
   ```

---

## Detailed Testing Scenarios

### Scenario 1: Verify BERT Model Loads

**Step 1**: Start the backend
```bash
cd Backend/TalentBridgeAPI
python run_server.py
```

**Step 2**: Watch logs for BERT loading message
```
Loading Sentence Transformer model: sentence-transformers/all-MiniLM-L6-v2
Model loaded successfully: sentence-transformers/all-MiniLM-L6-v2
```

**Expected**: Message should appear once (lazy loading)

**Success**: ✅ BERT model loaded successfully

---

### Scenario 2: Test Semantic Scoring in API

**Step 1**: Ensure backend is running (http://localhost:8000)

**Step 2**: Test the matching endpoint directly

```bash
# Using curl (from any terminal)
curl -X POST "http://localhost:8000/api/match" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_text": "Python developer with machine learning experience",
    "jobs": [
      {
        "job_title": "ML Engineer",
        "category_name": "Data Scientist",
        "skills_csv": "Python,TensorFlow,Machine Learning"
      },
      {
        "job_title": "Accountant",
        "category_name": "Finance",
        "skills_csv": "Excel,Accounting"
      }
    ]
  }'
```

**Expected Output**:
```json
{
  "scores": [92.50, 15.30],
  "backend": "sentence-transformers"
}
```

**Success Indicators**:
- ✅ ML Engineer scores higher (~90+)
- ✅ Accountant scores lower (~15)
- ✅ Backend shows "sentence-transformers"

---

### Scenario 3: Test with Real CV

**Step 1**: Upload a CV through the web interface

**Step 2**: Check console logs for:
```
Loading Sentence Transformer model: sentence-transformers/all-MiniLM-L6-v2
```

**Step 3**: View job recommendations

**Step 4**: Compare with expected results:
- Related jobs should rank higher
- Semantic matches should be more accurate
- Scores should reflect semantic similarity

**Success**: Recommendations look smarter and more relevant

---

### Scenario 4: Test Fallback to TF-IDF

**Step 1**: Force BERT to fail by setting environment variable:

```powershell
$env:TALENTBRIDGE_EMBEDDING_BACKEND="tfidf"
.\start_talent_bridge.ps1
```

**Expected Output**:
```
Using TF-IDF backend (BERT unavailable)
```

**Step 2**: Upload a CV and check recommendations

**Expected**: App still works, but uses TF-IDF scoring instead

**Success**: Fallback mechanism works ✅

---

## What Each Test Checks

### test_bert_integration.py

| Test | Checks |
|------|--------|
| Model Loading | BERT model can be loaded successfully |
| Basic Scoring | Semantic scores are computed correctly |
| Score Range | Scores stay within 0-100 range |
| Empty Inputs | System handles edge cases gracefully |

### bert_comparison.py

| Check | Measures |
|-------|----------|
| Performance | Latency comparison (BERT vs TF-IDF) |
| Accuracy | Semantic score correlation |
| Quality | Statistical analysis of improvements |
| Export | CSV report generation |

### App End-to-End Test

| Component | Verifies |
|-----------|----------|
| CV Upload | File processing works |
| CV Extraction | NLP extracts skills/experience |
| Semantic Matching | BERT computes scores correctly |
| Job Ranking | Results ranked by match_score |
| Display | Frontend shows recommendations |

---

## Troubleshooting Testing Issues

### Issue: "ImportError: sentence_transformers"

**Cause**: Package not installed

**Solution**:
```bash
pip install sentence-transformers>=2.2.0
```

### Issue: Model download hangs

**Cause**: Large model (~80MB), slow internet

**Solution**:
- Wait (can take 2-5 minutes on first run)
- Check internet connection
- Use alternate smaller model:
  ```bash
  export TALENTBRIDGE_SENTENCE_MODEL=sentence-transformers/all-MiniLM-L6-v2
  ```

### Issue: "CUDA out of memory"

**Cause**: GPU memory insufficient (if using GPU)

**Solution**:
```bash
export CUDA_VISIBLE_DEVICES=""  # Force CPU
```

### Issue: Different scores than expected

**Cause**: BERT provides different (better) semantic understanding

**Solution**:
- This is expected and correct
- BERT gives more nuanced scores
- Verify with comparison tool: `python bert_comparison.py`

### Issue: App startup fails

**Cause**: Multiple possible reasons

**Solutions**:
```powershell
# Try skipping SQL
.\start_talent_bridge.ps1 -SkipSql

# Try with specific SQL server
.\start_talent_bridge.ps1 -SqlServer ".\SQLEXPRESS"

# Start SQL Server manually
Start-Service MSSQLSERVER
```

---

## Step-by-Step: Full End-to-End Test

### 1. Unit Test (5 minutes)
```bash
cd Recommendation/JobRecommendation/src
python test_bert_integration.py
# ✅ Verify all 4 tests pass
```

### 2. Comparison Test (10 minutes)
```bash
python bert_comparison.py
# ✅ Review metrics in console
# ✅ Check CSV output
```

### 3. App Integration Test (15 minutes)
```powershell
# From repo root
.\start_talent_bridge.ps1

# Wait for startup (~2 min for model load first time)
# Open http://localhost:5173
# Login with demo credentials
# Upload a test CV
# Check recommendations
# ✅ Verify they look reasonable
```

### 4. Verify Logs (5 minutes)
- Check console for BERT loading message
- Verify no error messages
- Confirm performance metrics

**Total Time**: ~35 minutes for complete validation

---

## Quick Verification Checklist

- [ ] Integration tests pass (4/4)
- [ ] Comparison script runs successfully
- [ ] BERT model loads on app startup
- [ ] No error messages in logs
- [ ] CV upload works
- [ ] Recommendations display correctly
- [ ] Scores are in 0-100 range
- [ ] Related jobs rank higher than unrelated
- [ ] App performs acceptably (~1 second per CV)

---

## Expected Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Model load (first run) | 2-5 sec | One-time, then cached |
| Model load (cached) | 0.05 sec | Subsequent runs |
| 1 CV + 100 jobs | 0.1-0.2 sec | Via API |
| Integration tests | 10-20 sec | All 4 tests |
| Comparison analysis | 30-60 sec | Full metrics |

---

## Success Indicators

✅ **All tests pass**
```
python test_bert_integration.py
Total: 4/4 tests passed ✓
```

✅ **Comparison shows improvement**
```
python bert_comparison.py
BERT avg: 75.5, TF-IDF avg: 68.3, +7.2 improvement ✓
```

✅ **App starts without errors**
```
Loading Sentence Transformer model: sentence-transformers/all-MiniLM-L6-v2
Model loaded successfully ✓
Frontend: http://localhost:5173 ✓
Backend: http://localhost:8000 ✓
```

✅ **Recommendations look smart**
- Related jobs rank high
- Irrelevant jobs rank low
- Scores reflect semantic closeness

---

## What to Look For

### Good Signs ✅
- BERT model loads on first request
- Semantic scores seem reasonable
- Related jobs rank higher than unrelated
- Performance is acceptable (~100ms)
- No errors in logs

### Warning Signs ⚠️
- Model never loads (check internet connection)
- Scores always 0 or 100 (check data)
- App crashes (check logs)
- Very slow performance (check memory)

---

## Testing Summary

| Test | Command | Time | Expected Result |
|------|---------|------|-----------------|
| Unit Tests | `python test_bert_integration.py` | 10 sec | 4/4 pass ✓ |
| Comparison | `python bert_comparison.py` | 60 sec | CSV generated ✓ |
| API Direct | curl to /api/match | 0.1 sec | Scores returned ✓ |
| App Full | Upload CV via UI | 1 sec | Recommendations shown ✓ |

---

**Start with**: `python test_bert_integration.py` (simplest)  
**Then try**: `python bert_comparison.py` (see improvement)  
**Finally**: Full app test (end-to-end validation)

Need help with any specific test? Let me know! 🚀
