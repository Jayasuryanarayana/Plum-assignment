import os
from flask import Flask, request, jsonify
from services import ocr_service, normalization_service, summary_service

# --- Configuration ---
# If Tesseract is not in your system's PATH, you may need to set its location.
# For Windows, the path might look like this:
# from services.ocr_service import set_tesseract_path
# set_tesseract_path(r'C:\Program Files\Tesseract-OCR\tesseract.exe')

app = Flask(__name__)

@app.route('/simplify', methods=['POST'])
def simplify_report():
    """Main API endpoint to process medical reports from text or images."""
    try:
        if 'image' in request.files:
            image_file = request.files['image']
            if not image_file or image_file.filename == '':
                return jsonify({"status": "error", "message": "No image file provided."}), 400
            
            text = ocr_service.extract_text_from_image(image_file)
            if not text:
                return jsonify({"status": "error", "message": "Could not extract text from image. The image might be empty or unreadable."}), 400
        
        elif 'text' in request.form:
            text = request.form['text']
            if not text.strip():
                 return jsonify({"status": "error", "message": "Text input cannot be empty."}), 400
        else:
            return jsonify({"status": "error", "message": "Request must contain either 'text' or 'image' data."}), 400

        # AI Chain: Step 1 - Extract raw text lines
        raw_tests = normalization_service.extract_raw_tests_from_text(text)
        if not raw_tests:
            return jsonify({"status": "error", "message": "No valid test result lines found in the input."}), 400

        # AI Chain: Step 2 - Normalize raw text into structured data with validation
        normalized_result = normalization_service.normalize_tests(raw_tests)
        if not normalized_result['tests']:
            return jsonify({"status": "unprocessed", "reason": "Could not normalize any valid tests from the input."}), 400
        
        # AI Chain: Step 3 - Generate summary with hallucination guardrail
        summary_result = summary_service.generate_summary(normalized_result['tests'])
        if summary_result['status'] != 'ok':
            # This handles the hallucination guardrail failure
            return jsonify(summary_result), 400

        # Final successful output
        final_output = {
            "tests": normalized_result['tests'],
            "summary": summary_result['summary'],
            "explanations": summary_result['explanations'],
            "status": "ok"
        }
        return jsonify(final_output)

    except Exception as e:
        # Generic server error for unexpected issues
        print(f"An unexpected error occurred: {e}")
        return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)