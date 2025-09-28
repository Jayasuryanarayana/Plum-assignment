import os
import re
import io
import json
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
from rapidfuzz import process, fuzz

app = Flask(__name__)

# --- Database for Test Normalization ---
KNOWN_TESTS = {
    "Hemoglobin": {"unit": "g/dL", "ref_range": {"low": 12.0, "high": 15.0}},
    "WBC": {"unit": "/uL", "ref_range": {"low": 4000, "high": 11000}},
    "White Blood Cell Count": {"unit": "/uL", "ref_range": {"low": 4000, "high": 11000}},
    "Platelets": {"unit": "10^3/uL", "ref_range": {"low": 150, "high": 450}},
    "Glucose": {"unit": "mg/dL", "ref_range": {"low": 70, "high": 100}},
}

# --- OCR and Text Extraction ---
def extract_text_from_image(image_file):
    """
    Performs OCR on an image file to extract text using Tesseract.
    """
    try:
        image = Image.open(io.BytesIO(image_file.read()))
        text = pytesseract.image_to_string(image)
        # Assume a high confidence for any successful OCR operation
        return text, 0.95
    except Exception as e:
        print(f"OCR Error: {e}")
        return None, 0.0

def extract_raw_tests_from_text(text):
    lines = text.strip().split('\n')
    test_lines = [line.strip() for line in lines if re.search(r'\d', line)]
    confidence = min(1.0, len(test_lines) / 5.0) 
    return {"tests_raw": test_lines, "confidence": confidence}


# --- Test Normalization ---
def normalize_tests(raw_tests):
    normalized = []
    total_confidence = 0
    
    for raw_test in raw_tests:
        try:
            test_name_match = process.extractOne(raw_test, KNOWN_TESTS.keys(), scorer=fuzz.WRatio)
            if not test_name_match or test_name_match[1] < 70:
                continue

            name = test_name_match[0]
            total_confidence += test_name_match[1] / 100.0
            value_match = re.search(r'(\d[\d,]*\.?\d*)', raw_test)
            if not value_match:
                continue
            
            value = float(value_match.group(1).replace(',', ''))
            ref_range = KNOWN_TESTS[name]['ref_range']
            status = "normal"
            if value < ref_range['low']:
                status = "low"
            elif value > ref_range['high']:
                status = "high"

            normalized.append({
                "name": name,
                "value": value,
                "unit": KNOWN_TESTS[name]['unit'],
                "status": status,
                "ref_range": ref_range
            })

        except Exception as e:
            print(f"Error normalizing test: '{raw_test}'. Error: {e}")
            continue

    avg_confidence = (total_confidence / len(raw_tests)) if raw_tests else 0
    return {"tests": normalized, "normalization_confidence": round(avg_confidence, 2)}


# --- Patient-Friendly Summary Generation ---
def generate_summary(normalized_tests):
    """
    Generates a patient-friendly summary from normalized test results.
    This is a simplified, rule-based implementation. In a real system,
    this would be a call to a powerful, fine-tuned Large Language Model (LLM).
    """
    abnormal_tests = [t for t in normalized_tests if t['status'] != 'normal']
    if not abnormal_tests:
        return {
            "summary": "All test results appear to be within the normal range.",
            "explanations": [],
            "status": "ok"
        }
    
    summary_parts = []
    explanations = []

    # explanations for abnormal results
    for test in abnormal_tests:
        summary_parts.append(f"{test['status']} {test['name'].lower()}")
        if test['name'] == 'Hemoglobin' and test['status'] == 'low':
            explanations.append("Low hemoglobin might be related to a condition called anemia, where your body has fewer red blood cells than normal. This can cause feelings of tiredness or weakness.")
        elif (test['name'] == 'WBC' or test['name'] == 'White Blood Cell Count') and test['status'] == 'high':
             explanations.append("High white blood cells can be a sign that your body is fighting an infection.")
    
    summary = "Your results show " + " and ".join(summary_parts) + "."
    
    # Guardrail 
    original_abnormal_names = {t['name'].lower() for t in abnormal_tests}
    explanation_text = " ".join(explanations).lower()
    for known_test in KNOWN_TESTS:
        if known_test.lower() in explanation_text and known_test.lower() not in original_abnormal_names:
            return {"status": "unprocessed", "reason": f"potential hallucinated test '{known_test}' in explanation"}

    return {"summary": summary, "explanations": explanations, "status": "ok"}


# ---  API Endpoint ---
@app.route('/simplify', methods=['POST'])
def simplify_report():
    """
    Main API endpoint to process medical reports from text or images.
    """
    if 'image' in request.files:
        image_file = request.files['image']
        text, _ = extract_text_from_image(image_file)
        if not text:
            return jsonify({"error": "Could not extract text from image."}), 400
    elif 'text' in request.form:
        text = request.form['text']
    else:
        return jsonify({"error": "Request must contain either 'text' or 'image' data."}), 400

    raw_results = extract_raw_tests_from_text(text)
    if not raw_results['tests_raw']:
        return jsonify({"error": "No valid test results found in the input text."}), 400

    normalization_result = normalize_tests(raw_results['tests_raw'])
    if not normalization_result['tests']:
         return jsonify({"status":"unprocessed","reason":"Could not normalize any tests from the input"}), 400

    summary_result = generate_summary(normalization_result['tests'])
    if summary_result['status'] != 'ok':
        return jsonify(summary_result), 400

    final_output = {
        "tests": normalization_result['tests'],
        "summary": summary_result['summary'],
        "explanations": summary_result['explanations'],
        "status": "ok"
    }
    
    return jsonify(final_output)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

