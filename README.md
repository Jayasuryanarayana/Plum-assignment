#AI-Powered Medical Report Simplifier

This backend service provides a REST API to simplify medical lab reports. It accepts either raw text or scanned images of a report and returns a structured JSON object containing normalized test results and patient-friendly explanations.

This project is designed to be robust, scalable, and safe, incorporating image pre-processing for improved OCR accuracy, advanced validation guardrails, and a service-oriented architecture for maintainability.

Table of Contents
1.Architecture
2.Features
3.Setup and Installation
4.Running the Service
5.API Usage
     Endpoint: /simplify
     Example 1: Text Input
     Example 2: Image Input
Project Enhancements

Architecture:-
This project follows a service-oriented architecture to ensure a clean separation of concerns, making the codebase modular, testable, and easy to maintain.
1)app.py: The main entry point. It contains only the Flask API routing and request/response handling logic. It acts as a controller that orchestrates the flow of data between the services.

2)services/ Directory: A dedicated module for all business logic.
2-a)ocr_service.py: Handles all aspects of Optical Character Recognition (OCR). This includes a crucial image pre-processing step (using OpenCV) to clean and enhance images before sending them to Tesseract, maximizing accuracy.
2-b)normalization_service.py: Responsible for parsing raw text, identifying medical tests using fuzzy string matching (rapidfuzz), and normalizing them into a structured format. It includes physiological sanity checks to discard impossible values that may result from OCR errors.
2-c)summary_service.py: Generates the final patient-friendly summary and explanations. It includes a critical hallucination guardrail to ensure explanations are only generated for tests that were actually present in the input.

Features
Dual Input: Accepts both raw text and image files.
Robust OCR: Utilizes image pre-processing (grayscale, binarization) to improve the accuracy of text extraction from scans.
Fuzzy Matching: Accurately identifies medical tests even with common spelling mistakes or OCR errors.
Advanced Guardrails: Implements safety checks to prevent physiologically impossible values and hallucinated results.
Consistent API Schema: Provides predictable and reliable JSON responses for both success and error states.

Setup and Installation
Prerequisites
1)Python 3.8+
2)Tesseract OCR Engine

Step-by-Step Guide
1.Clone the Repository:
git clone https://github.com/Jayasuryanarayana/Plum-assignment
cd Plum-assignment

2.Create and Activate a Virtual Environment:

# This isolates the project's dependencies.# Create the environment
python -m venv venv

# Activate the environment (use the command for your OS)
# Windows (Git Bash)
source venv/Scripts/activate
# macOS/Linux
source venv/bin/activate

3.Install Dependencies:
The enhanced version requires OpenCV.
{pip install -r requirements.txt}

4.(Windows Only) Configure Tesseract Path:If Tesseract was not added to your system's PATH during installation, you must specify its location.Open app.py.Uncomment the configuration lines at the top and provide the correct path to tesseract.exe.# from services.ocr_service import set_tesseract_path
# set_tesseract_path(r'C:\Program Files\Tesseract-OCR\tesseract.exe')

Running the Service
With your virtual environment activated, start the Flask development server:
{python app.py}
The API is now running and accessible at http://127.0.0.1:5000.

API Usage
The service provides a single endpoint for all operations.
Endpoint: /simplify
Method: POST
Content-Type: multipart/form-data
Parameters:text (string, optional): The raw text from a medical report.
image (file, optional): An image file (e.g., PNG, JPG) of a scanned report.
Note: You must provide either text or image, but not both.

Example 1: Text Input
This example sends raw text to the endpoint using curl.
curl -X POST \
  -F "text=CBC: Hemglobin 10.2 g/dL (Low), WBC 11200 /uL (Hgh)" \
  [http://127.0.0.1:5000/simplify](http://127.0.0.1:5000/simplify)
Success Response (200 OK):{
  "explanations": [
    "Low hemoglobin might be related to a condition called anemia...",
    "High white blood cells can be a sign that your body is fighting an infection."
  ],
  "status": "ok",
  "summary": "Your results show low hemoglobin and high white blood cell count.",
  "tests": [
    {
      "name": "Hemoglobin",
      "ref_range": { "high": 15.0, "low": 12.0 },
      "status": "low",
      "unit": "g/dL",
      "value": 10.2
    },
    {
      "name": "WBC",
      "ref_range": { "high": 11000, "low": 4000 },
      "status": "high",
      "unit": "/uL",
      "value": 11200
    }
  ]
}
Example 2: Image InputThis example uploads an image file named report.png using curl.curl -X POST \
  -F "image=@/path/to/your/report.png" \
  [http://127.0.0.1:5000/simplify](http://127.0.0.1:5000/simplify)
  
Success Response (200 OK):The response will be in the same JSON format as the text input example, based on the text extracted from the image.
Error Response (400 Bad Request):If no valid tests are found, the response will follow a consistent error schema:{
  "status": "error",
  "message": "No valid test result lines found in the input."
}
