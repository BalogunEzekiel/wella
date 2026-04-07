def get_recommendation(symptoms):
    symptoms = symptoms.lower()

    if "fever" in symptoms:
        return "Suspected malaria. Start ACT. Give paracetamol."

    if "cough" in symptoms:
        return "Check for pneumonia. Monitor breathing."

    return "Provide symptomatic treatment and monitor."