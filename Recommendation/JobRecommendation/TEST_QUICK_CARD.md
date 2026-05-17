# 🧪 TEST BERT - Quick Reference Card

## ⚡ FASTEST TEST (5 min)
```bash
cd Recommendation/JobRecommendation/src
python test_bert_integration.py
```
**Result**: ✅ 4/4 tests pass

---

## 📊 DETAILED TEST (15 min)
```bash
cd Recommendation/JobRecommendation/src
python bert_comparison.py
```
**Result**: ✅ Shows BERT vs TF-IDF metrics

---

## 🌐 FULL APP TEST (30 min)
```powershell
.\start_talent_bridge.ps1
# Then open: http://localhost:5173
# Upload CV → See recommendations
```
**Result**: ✅ BERT scoring in action

---

## 📋 Test Results Checklist

### Unit Tests (test_bert_integration.py)
```
✅ Model Loading
✅ Basic Scoring  
✅ Score Range (0-100)
✅ Empty Inputs
→ 4/4 PASS
```

### Comparison (bert_comparison.py)
```
✅ Performance measured
✅ Quality analyzed
✅ Statistics computed
✅ CSV exported
```

### Full App
```
✅ Startup works
✅ CV uploads
✅ Jobs scored
✅ Results display
```

---

## 🎯 What You'll See

### Console Output (Unit Tests)
```
Loading Sentence Transformer model: sentence-transformers/all-MiniLM-L6-v2
Model loaded successfully: sentence-transformers/all-MiniLM-L6-v2

✓ Model Loading
✓ Basic Scoring
✓ Score Range
✓ Empty Input Handling

✅ All tests passed!
```

### CSV Output (Comparison)
```
Job Title,Category,BERT Score,TF-IDF Score,Difference
Senior ML Engineer,Data Scientist,92.50,82.00,10.50
Data Analyst,Business Analyst,42.30,38.00,4.30
Python Developer,Software Engineer,68.20,62.50,5.70
```

### App Display
```
Recommended Jobs for You:
1. Senior ML Engineer - Match: 78/100 ⭐⭐⭐⭐⭐
2. Data Scientist - Match: 72/100 ⭐⭐⭐⭐
3. ML Engineer - Match: 68/100 ⭐⭐⭐⭐
```

---

## 🚨 If Tests Fail

| Error | Fix |
|-------|-----|
| `ImportError: sentence_transformers` | `pip install sentence-transformers` |
| Model hangs | Wait (first run takes 2-5 min) |
| App won't start | `.\start_talent_bridge.ps1 -SkipSql` |
| BERT not loading | Check logs, ensure no errors |

---

## ✅ How to Know It's Working

| Sign | Status |
|------|--------|
| All 4 unit tests pass | ✅ Good |
| BERT scores > TF-IDF | ✅ Good |
| Model loads in console | ✅ Good |
| CV uploads work | ✅ Good |
| Recommendations appear | ✅ Good |

---

## 📊 Expected Performance

| Test | Time | Status |
|------|------|--------|
| Unit tests | ~10 sec | ✅ Fast |
| Comparison | ~60 sec | ✅ OK |
| App startup | ~2 min | ✅ First run |
| App startup | ~30 sec | ✅ Cached |
| Job scoring | ~100ms | ✅ Fast |

---

## 🎯 Testing Plan

```
1. RUN UNIT TESTS (5 min)
   ↓
   ✅ All pass? Continue
   ❌ Failed? Check logs
   
2. RUN COMPARISON (10 min)
   ↓
   ✅ CSV generated? Continue
   ❌ Failed? Install sentence-transformers
   
3. START APP (20 min)
   ↓
   ✅ Model loads? Continue
   ❌ Error? Skip SQL setup
   
4. UPLOAD CV (5 min)
   ↓
   ✅ Works? Done! 🎉
   ❌ Failed? Check browser console
```

---

## 📁 Test Files

**Location**: `Recommendation/JobRecommendation/src/`

- `test_bert_integration.py` → Run unit tests
- `bert_comparison.py` → See improvements
- `semantic_similarity.py` → Core BERT code

---

## 🔗 URLs (When App is Running)

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 👤 Demo Credentials

```
Email: candidate@talentbridge.local
Password: candidate123
```

---

## 🎉 Success = All Tests Pass + App Works

```
✅ Unit tests: 4/4
✅ Comparison: Metrics shown
✅ App starts: No errors
✅ CV uploads: Works
✅ Recommendations: Display
✅ BERT loads: In logs

→ BERT IS WORKING! 🚀
```

---

## 📞 Quick Help

**Tests won't run?**
```bash
pip install sentence-transformers
```

**App won't start?**
```powershell
.\start_talent_bridge.ps1 -SkipSql
```

**Need details?**
See: `HOW_TO_TEST.md` or `TESTING_GUIDE.md`

---

**START HERE**: `python test_bert_integration.py` ⭐
