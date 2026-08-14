"""
=========================================================
Eye Expert System

Diagnosis Engine

Features:
- 8 Independent Fuzzy Disease Engines
- Fresh Simulation For Every Patient
- scikit-fuzzy Control System

Compatible with:
- fuzzy_variables.py
- fuzzy_rules.py
=========================================================
"""


import skfuzzy.control as ctrl



# =========================================================
# Import Fuzzy Variables
# =========================================================


from .fuzzy_variables import (

    glaucoma,
    cataract,
    dry_eye,
    conjunctivitis,
    keratitis,
    uveitis,
    retinopathy,
    computer_vision

)




# =========================================================
# Import Rules
# =========================================================


from .fuzzy_rules import (

    get_glaucoma_rules,

    get_cataract_rules,

    get_dry_eye_rules,

    get_conjunctivitis_rules,

    get_keratitis_rules,

    get_uveitis_rules,

    get_retinopathy_rules,

    get_computer_vision_rules

)





# =========================================================
# Create Fuzzy Control Systems
# =========================================================


def create_engine(rules):

    """
    Create fuzzy control system.

    Returns:
        ControlSystem

    Simulation is created later
    for every patient.
    """


    system = ctrl.ControlSystem(

        rules

    )


    return system






# =========================================================
# Disease Fuzzy Systems
# =========================================================


glaucoma_engine = create_engine(

    get_glaucoma_rules()

)



cataract_engine = create_engine(

    get_cataract_rules()

)



dry_eye_engine = create_engine(

    get_dry_eye_rules()

)



conjunctivitis_engine = create_engine(

    get_conjunctivitis_rules()

)



keratitis_engine = create_engine(

    get_keratitis_rules()

)



uveitis_engine = create_engine(

    get_uveitis_rules()

)



retinopathy_engine = create_engine(

    get_retinopathy_rules()

)



computer_vision_engine = create_engine(

    get_computer_vision_rules()

)





# =========================================================
# Mapping Disease -> Engine + Output
# =========================================================


DISEASE_ENGINES = {


    "glaucoma":

    (

        glaucoma_engine,

        glaucoma

    ),



    "cataract":

    (

        cataract_engine,

        cataract

    ),



    "dry_eye":

    (

        dry_eye_engine,

        dry_eye

    ),



    "conjunctivitis":

    (

        conjunctivitis_engine,

        conjunctivitis

    ),



    "keratitis":

    (

        keratitis_engine,

        keratitis

    ),



    "uveitis":

    (

        uveitis_engine,

        uveitis

    ),



    "retinopathy":

    (

        retinopathy_engine,

        retinopathy

    ),



    "computer_vision":

    (

        computer_vision_engine,

        computer_vision

    )

}
# =========================================================
#               DATA PREPROCESSING
# =========================================================


def normalize_patient_data(patient_data):

    """
    Convert all patient inputs to float values.

    Example:
        "5"  -> 5.0
        None -> 0.0
    """


    normalized = {}



    for key, value in patient_data.items():


        try:

            normalized[key] = float(value)


        except:


            normalized[key] = 0.0



    return normalized






# =========================================================
#               RUN ONE FUZZY ENGINE
# =========================================================


def run_engine(system, patient_data, output_variable):

    """
    Run one independent fuzzy system.

    Parameters:
        system:
            ControlSystem of one disease

        patient_data:
            Patient symptoms dictionary

        output_variable:
            Disease output variable


    Returns:
        Disease probability %
    """



    try:


        # Create fresh simulation
        # for every patient


        simulation = ctrl.ControlSystemSimulation(

            system

        )



        # Insert patient values


        for key, value in patient_data.items():


            try:

                simulation.input[key] = value


            except:


                # Ignore unused variables

                pass





        # Execute fuzzy inference


        simulation.compute()




        # Get disease percentage


        result = simulation.output[

            output_variable.label

        ]



        return round(

            float(result),

            2

        )




    except Exception as e:


        print(

            "Fuzzy Engine Error:",

            e

        )


        return 0.0







# =========================================================
#               MAIN DIAGNOSIS FUNCTION
# =========================================================


def diagnose(patient_data):

    """
    Run all eight disease engines.


    Input:

    {
        age: 60,
        pain: 7,
        redness: 5,
        ...
    }


    Output:

    {
        glaucoma: 80.5,
        cataract: 55.2,
        dry_eye: 20.0,
        ...
    }

    """



    patient_data = normalize_patient_data(

        patient_data

    )



    results = {}




    for disease, data in DISEASE_ENGINES.items():



        system, output_variable = data





        probability = run_engine(

            system,

            patient_data,

            output_variable

        )



        results[disease] = probability




    return results






# =========================================================
#               SORT RESULTS
# =========================================================


def rank_diseases(results):

    """
    Sort diseases descending by probability.
    """


    ranked = sorted(

        results.items(),

        key=lambda item: item[1],

        reverse=True

    )


    return ranked 
# =========================================================
#               FINAL DIAGNOSIS
# =========================================================


def get_final_diagnosis(patient_data):

    """
    Generate complete diagnosis report.

    Returns:

    {
        primary_diagnosis:
        confidence:
        all_results:
        severity:
    }

    """



    results = diagnose(

        patient_data

    )



    ranked = rank_diseases(

        results

    )



    if not ranked:


        return {


            "primary_diagnosis":

                "No diagnosis",



            "confidence":

                0,



            "severity":

                "Unknown",



            "all_results":

                {}

        }





    main_disease = ranked[0]



    return {


        "primary_diagnosis":

            main_disease[0],



        "confidence":

            main_disease[1],



        "severity":

            classify_severity(

                main_disease[1]

            ),



        "all_results":

            dict(ranked)

    }







# =========================================================
#               SEVERITY CLASSIFICATION
# =========================================================


def classify_severity(probability):

    """
    Convert percentage into risk level.
    """



    if probability < 25:


        return "Very Low"



    elif probability < 50:


        return "Low"



    elif probability < 75:


        return "Moderate"



    elif probability < 90:


        return "High"



    else:


        return "Very High"







# =========================================================
#               DISPLAY NAMES
# =========================================================


DISEASE_NAMES = {


    "glaucoma":

    "Glaucoma - الماء الأزرق",



    "cataract":

    "Cataract - الماء الأبيض",



    "dry_eye":

    "Dry Eye Syndrome - جفاف العين",



    "conjunctivitis":

    "Conjunctivitis - التهاب الملتحمة",



    "keratitis":

    "Keratitis - التهاب القرنية",



    "uveitis":

    "Uveitis - التهاب العنبية",



    "retinopathy":

    "Diabetic Retinopathy - اعتلال الشبكية السكري",



    "computer_vision":

    "Computer Vision Syndrome - متلازمة إجهاد العين الرقمي"

}







# =========================================================
#               HUMAN READABLE RESULTS
# =========================================================


def get_readable_results(results):

    """
    Replace technical names
    with user friendly names.
    """


    readable = {}



    for disease, value in results.items():


        name = DISEASE_NAMES.get(

            disease,

            disease

        )



        readable[name] = value



    return readable







# =========================================================
#               QUICK TEST
# =========================================================


if __name__ == "__main__":


    test_patient = {


        "age": 65,

        "pain": 6,

        "redness": 5,

        "vision_blur": 7,

        "dryness": 3,

        "halos": 8,

        "headache": 5,

        "nausea": 2,

        "diabetes": 1,

        "family_glaucoma": 1,

        "screen_time": 6

    }



    result = get_final_diagnosis(

        test_patient

    )



    print("\nDiagnosis Result:")


    print(result)



    print("\nReadable Results:")


    print(

        get_readable_results(

            result["all_results"]

        )

    )