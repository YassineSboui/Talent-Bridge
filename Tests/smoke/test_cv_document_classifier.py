from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import torch

from DocumentAI.CVDocumentClassification.src.model import CvDocumentCnn
from DocumentAI.CVDocumentClassification.src.preprocessing import document_to_array
from DocumentAI.CVQualityScoring.src.grades import grade_from_score


def test_cv_document_preprocessing_and_model_forward():
    sample_pdf = Path("Data/samples/cv/Test CV/YassineSboui_CV_French.pdf")
    array = document_to_array(sample_pdf, image_size=(96, 128))

    assert array.shape == (96, 128)
    assert array.dtype.name == "uint8"

    model = CvDocumentCnn()
    logits = model(torch.zeros(2, 1, 96, 128))

    assert logits.shape == (2,)
    assert grade_from_score(92) == "Excellent"
    assert grade_from_score(80) == "Good"
    assert grade_from_score(60) == "Average"
    assert grade_from_score(40) == "Weak"
    assert grade_from_score(20) == "Poor"
