"""
Integration test to verify BERT semantic similarity is working correctly.
This can be run to ensure the system is functioning as expected.

Usage:
    python test_bert_integration.py
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Recommendation.JobRecommendation.src.semantic_similarity import semantic_similarity_scores, _load_sentence_transformer


def test_model_loading():
    """Test that BERT model loads successfully."""
    print("Test 1: BERT Model Loading")
    print("-" * 50)

    model = _load_sentence_transformer()
    if model is None:
        print("WARNING: BERT model failed to load")
        print("   System will fall back to TF-IDF")
        print("   Install: pip install sentence-transformers")
        return False

    print(f"PASS: Model loaded: {type(model).__name__}")
    print(f"PASS: Model type: {model.get_sentence_embedding_dimension()}-dimensional embeddings")
    return True


def test_basic_scoring():
    """Test basic semantic similarity scoring."""
    print("\nTest 2: Basic Scoring")
    print("-" * 50)

    candidate_text = "Python developer with machine learning experience"

    jobs = [
        {
            "job_title": "ML Engineer",
            "category_name": "Data Scientist",
            "company_name": "Tech Corp",
            "country": "USA",
            "city": "San Francisco",
            "is_work_from_home": True,
            "skills_csv": "Python,TensorFlow,Machine Learning",
            "skill_categories_csv": "ML,Programming",
            "schedule_types_csv": "Full-time",
            "no_degree_mention": False,
            "has_salary_info": True,
        },
        {
            "job_title": "Accountant",
            "category_name": "Finance",
            "company_name": "Finance Inc",
            "country": "USA",
            "city": "New York",
            "is_work_from_home": False,
            "skills_csv": "Excel,Accounting,Tax",
            "skill_categories_csv": "Finance",
            "schedule_types_csv": "Full-time",
            "no_degree_mention": True,
            "has_salary_info": False,
        },
    ]

    scores = semantic_similarity_scores(candidate_text, jobs)

    if len(scores) != 2:
        print(f"FAIL: Expected 2 scores, got {len(scores)}")
        return False

    if scores[0] < scores[1]:
        print(f"FAIL: ML Engineer ({scores[0]}) should score higher than Accountant ({scores[1]})")
        return False

    print(f"PASS: ML Engineer score: {scores[0]:.2f}")
    print(f"PASS: Accountant score: {scores[1]:.2f}")
    print("PASS: Correct ranking: ML Engineer > Accountant")

    if 50 <= scores[0] <= 100:
        print("PASS: Score in valid range [0, 100]")
    else:
        print(f"FAIL: Score out of range: {scores[0]}")
        return False

    return True


def test_score_range():
    """Test that scores are in valid 0-100 range."""
    print("\nTest 3: Score Range Validation")
    print("-" * 50)

    candidate_text = "Senior software engineer with 10 years experience"

    jobs = [
        {
            "job_title": "Senior Backend Engineer",
            "category_name": "Software Engineer",
            "company_name": "Tech Co",
            "country": "USA",
            "city": "SF",
            "is_work_from_home": True,
            "skills_csv": "Python,Java,Backend,API",
            "skill_categories_csv": "Backend,Programming",
            "schedule_types_csv": "Full-time",
            "no_degree_mention": False,
            "has_salary_info": True,
        },
        {
            "job_title": "Junior Frontend Dev",
            "category_name": "Web Developer",
            "company_name": "Startup",
            "country": "Canada",
            "city": "Toronto",
            "is_work_from_home": False,
            "skills_csv": "JavaScript,React,CSS",
            "skill_categories_csv": "Frontend",
            "schedule_types_csv": "Full-time",
            "no_degree_mention": True,
            "has_salary_info": False,
        },
    ]

    scores = semantic_similarity_scores(candidate_text, jobs)

    for i, score in enumerate(scores):
        if not (0 <= score <= 100):
            print(f"FAIL: Score {i} out of range: {score}")
            return False
        print(f"PASS: Score {i} in valid range: {score:.2f}")

    return True


def test_empty_inputs():
    """Test handling of empty inputs."""
    print("\nTest 4: Empty Input Handling")
    print("-" * 50)

    # Empty jobs list
    scores = semantic_similarity_scores("test candidate", [])
    if len(scores) != 0:
        print(f"FAIL: Empty jobs should return empty scores, got {len(scores)}")
        return False
    print("PASS: Empty jobs handled correctly")

    # Empty candidate text
    scores = semantic_similarity_scores("", [{"job_title": "Test", "category_name": "Test",
                                              "company_name": "Test", "country": "USA",
                                              "city": "SF", "is_work_from_home": False,
                                              "skills_csv": "Python", "skill_categories_csv": "Tech",
                                              "schedule_types_csv": "Full-time",
                                              "no_degree_mention": False, "has_salary_info": False}])
    if not all(s == 0.0 for s in scores):
        print(f"FAIL: Empty candidate should return zeros, got {scores}")
        return False
    print("PASS: Empty candidate handled correctly")

    return True


def run_all_tests():
    """Run all integration tests."""
    print("=" * 50)
    print("BERT Semantic Similarity Integration Tests")
    print("=" * 50)

    tests = [
        ("Model Loading", test_model_loading),
        ("Basic Scoring", test_basic_scoring),
        ("Score Range", test_score_range),
        ("Empty Inputs", test_empty_inputs),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\nFAIL: Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll tests passed. BERT semantic matching is working correctly.")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
