import re
from rapidfuzz import process, fuzz

# --- Mock Databases ---
# In a real-world scenario, these would be in a comprehensive, external database.
KNOWN_TESTS = {
    "Hemoglobin": {"unit": "g/dL", "ref_range": {"low": 12.0, "high": 15.0}},
    "WBC": {"unit": "/uL", "ref_range": {"low": 4000, "high": 11000}},
    "White Blood Cell Count": {"unit": "/uL", "ref_range": {"low": 4000, "high": 11000}},
    "Platelets": {"unit": "10^3/uL", "ref_range": {"low": 150, "high": 450}},
    "Glucose": {"unit": "mg/dL", "ref_range": {"low": 70, "high": 100}},
}

# Advanced Guardrail: Physiological limits to catch major OCR errors
PHYSIOLOGICAL_LIMITS = {
    "Hemoglobin": {"min": 1.0, "max": 25.0},
    "WBC": {"min": 100, "max": 100000},
    "White Blood Cell Count": {"min": 100, "max": 100000},
    "Platelets": {"min": 10, "max": 1000},
    "Glucose": {"min": 20, "max": 1500},
}


def extract_raw_tests_from_text(text):
    """Extracts individual test lines from raw text using simple heuristics."""
    lines = text.strip().split('\n')
    # A line is considered a potential test if it contains at least one digit
    test_lines = [line.strip() for line in lines if re.search(r'\d', line)]
    return test_lines

def normalize_tests(raw_tests):
    """
    Normalizes raw test strings into a structured JSON format.
    Includes advanced validation guardrails.
    """
    normalized = []
    
    for raw_test in raw_tests:
        try:
            # 1. Fuzzy match the test name
            test_name_match = process.extractOne(raw_test, KNOWN_TESTS.keys(), scorer=fuzz.WRatio)
            if not test_name_match or test_name_match[1] < 70:
                continue # Confidence too low, skip this line
            
            name = test_name_match[0]

            # 2. Extract the numeric value
            value_match = re.search(r'(\d[\d,]*\.?\d*)', raw_test)
            if not value_match:
                continue
            
            value = float(value_match.group(1).replace(',', ''))

            # 3. Guardrail: Physiological Sanity Check
            limits = PHYSIOLOGICAL_LIMITS.get(name)
            if limits and not (limits['min'] <= value <= limits['max']):
                print(f"Value {value} for {name} is outside physiological limits. Skipping.")
                continue # Value is impossible, likely an OCR error

            # 4. Determine status based on reference range
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
            
    return {"tests": normalized}
