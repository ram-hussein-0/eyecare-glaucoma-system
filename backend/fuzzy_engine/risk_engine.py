"""
=========================================================
Eye Expert System

Risk Engine

Purpose:
- Calculate overall eye disease risk
- Analyze multiple fuzzy diagnosis outputs
- Generate risk level

Compatible with:
- fuzzy_variables.py
- diagnosis_engine.py
=========================================================
"""



# =========================================================
# Imports
# =========================================================


from .diagnosis_engine import (

    diagnose,

    get_final_diagnosis

)





# =========================================================
# Risk Weights
# =========================================================


"""
Different diseases have different
medical importance.

Weights affect the final risk score.
"""


DISEASE_WEIGHTS = {


    "glaucoma":

        1.5,


    "retinopathy":

        1.5,


    "keratitis":

        1.3,


    "uveitis":

        1.3,


    "cataract":

        1.0,


    "conjunctivitis":

        0.8,


    "dry_eye":

        0.7,


    "computer_vision":

        0.6

}






# =========================================================
# Risk Thresholds
# =========================================================


RISK_LEVELS = {


    "safe":

        (0,30),



    "warning":

        (30,70),



    "danger":

        (70,100)

}
# =========================================================
#               Calculate Overall Risk Score
# =========================================================


def calculate_risk_score(diagnosis_results):

    """
    Calculate total risk percentage.

    Input:

    {
        glaucoma: 80,
        cataract: 40,
        dry_eye: 20
    }


    Output:

    risk score 0-100

    """



    total_score = 0


    total_weight = 0




    for disease, probability in diagnosis_results.items():


        if disease in DISEASE_WEIGHTS:


            weight = DISEASE_WEIGHTS[disease]



            total_score += (

                probability * weight

            )



            total_weight += weight




    if total_weight == 0:


        return 0




    risk_score = (

        total_score /

        total_weight

    )



    return round(

        min(risk_score,100),

        2

    )







# =========================================================
#               Risk Classification
# =========================================================


def classify_risk(risk_score):

    """
    Convert risk score into category.
    """



    if risk_score < 30:


        return "Safe"



    elif risk_score < 70:


        return "Warning"



    else:


        return "Danger"








# =========================================================
#               Detect Risk Causes
# =========================================================


def detect_risk_causes(diagnosis_results):

    """
    Find diseases contributing
    to high risk.

    """


    causes = []



    for disease, probability in diagnosis_results.items():



        if probability >= 50:


            causes.append(

                {

                "disease": disease,

                "probability": probability

                }

            )



    return causes






# =========================================================
#               Risk Analysis
# =========================================================


def analyze_risk(diagnosis_results):

    """
    Complete risk analysis.

    Returns:

    {
        score: 75,
        level: Danger,
        causes:[]
    }

    """



    score = calculate_risk_score(

        diagnosis_results

    )



    level = classify_risk(

        score

    )



    causes = detect_risk_causes(

        diagnosis_results

    )



    return {


        "risk_score":

            score,



        "risk_level":

            level,



        "causes":

            causes

    } 
# =========================================================
#               COMPLETE PATIENT RISK REPORT
# =========================================================


def get_risk_report(patient_data):

    """
    Full pipeline:

    Patient Data
          |
          ↓
    Diagnosis Engine
          |
          ↓
    Risk Analysis
          |
          ↓
    Final Report

    """



    # Get all disease probabilities

    diagnosis_results = diagnose(

        patient_data

    )



    # Analyze overall risk

    risk_analysis = analyze_risk(

        diagnosis_results

    )



    # Get main diagnosis

    final_diagnosis = get_final_diagnosis(

        patient_data

    )




    report = {


        "main_diagnosis":

            final_diagnosis[

                "primary_diagnosis"

            ],



        "confidence":

            final_diagnosis[

                "confidence"

            ],



        "disease_probabilities":

            diagnosis_results,



        "risk_score":

            risk_analysis[

                "risk_score"

            ],



        "risk_level":

            risk_analysis[

                "risk_level"

            ],



        "risk_causes":

            risk_analysis[

                "causes"

            ]

    }



    return report






# =========================================================
#               Human Readable Risk
# =========================================================


def explain_risk(report):

    """
    Convert report into readable text.
    """



    text = []



    text.append(

        f"Main diagnosis: {report['main_diagnosis']}"

    )



    text.append(

        f"Confidence: {report['confidence']}%"

    )



    text.append(

        f"Overall Risk: {report['risk_score']}%"

    )



    text.append(

        f"Risk Level: {report['risk_level']}"

    )




    if report["risk_causes"]:



        text.append(

            "Risk Factors:"

        )



        for item in report["risk_causes"]:


            text.append(

                f"- {item['disease']} : {item['probability']}%"

            )



    else:


        text.append(

            "No significant risk factors detected."

        )



    return "\n".join(text)








# =========================================================
#               TEST
# =========================================================


if __name__ == "__main__":



    sample_patient = {


        "age":65,


        "pain":7,


        "redness":5,


        "vision_blur":8,


        "dryness":3,


        "halos":8,


        "floaters":4,


        "diabetes":1,


        "hypertension":1,


        "family_glaucoma":1,


        "screen_time":6

    }





    result = get_risk_report(

        sample_patient

    )



    print(

        "\n========== RISK REPORT ==========\n"

    )


    print(

        explain_risk(

            result

        )

    )