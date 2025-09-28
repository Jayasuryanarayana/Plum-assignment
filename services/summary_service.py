from .normalization_service import KNOWN_TESTS

def generate_summary(normalized_tests):
    """
    Generates a patient-friendly summary from normalized test results.
    Includes a hallucination guardrail.
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
    
    for test in abnormal_tests:
        summary_parts.append(f"{test['status']} {test['name'].lower()}")
        
        # Template-based explanations
        if test['name'] == 'Hemoglobin' and test['status'] == 'low':
            explanations.append("Low hemoglobin might be related to a condition called anemia, where your body has fewer red blood cells than normal. This can cause feelings of tiredness or weakness.")
        elif (test['name'] == 'WBC' or test['name'] == 'White Blood Cell Count') and test['status'] == 'high':
             explanations.append("High white blood cells can be a sign that your body is fighting an infection.")
        # Add more explanation templates here in a real application

    summary = "Your results show " + " and ".join(summary_parts) + "."
    
    # Guardrail: Check for hallucinated tests in the final output
    original_abnormal_names = {t['name'].lower() for t in abnormal_tests}
    explanation_text = " ".join(explanations).lower()
    
    for known_test in KNOWN_TESTS:
        if known_test.lower() in explanation_text and known_test.lower() not in original_abnormal_names:
            # If an explanation mentions a test that wasn't abnormal, it's a potential hallucination.
            return {
                "status": "unprocessed", 
                "reason": f"Potential hallucination detected: explanation mentions '{known_test}' which was not an abnormal result."
            }
            
    return {
        "summary": summary, 
        "explanations": explanations, 
        "status": "ok"
    }
