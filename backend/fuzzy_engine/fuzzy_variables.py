"""
=========================================================
Eye Expert System
Fuzzy Variables

Contains:
- Input Variables
- Output Variables
- Membership Functions

Compatible with:
- fuzzy_rules.py
- diagnosis_engine.py
=========================================================
"""


import numpy as np

import skfuzzy as fuzz

from skfuzzy import control as ctrl




# =========================================================
#               INPUT VARIABLES
# =========================================================


# -------------------------
# Age
# -------------------------

age = ctrl.Antecedent(
    np.arange(0,101,1),
    'age'
)



# -------------------------
# Symptoms (0 - 10)
# -------------------------


pain = ctrl.Antecedent(
    np.arange(0,11,1),
    'pain'
)


redness = ctrl.Antecedent(
    np.arange(0,11,1),
    'redness'
)


vision_blur = ctrl.Antecedent(
    np.arange(0,11,1),
    'vision_blur'
)


dryness = ctrl.Antecedent(
    np.arange(0,11,1),
    'dryness'
)


itching = ctrl.Antecedent(
    np.arange(0,11,1),
    'itching'
)


tearing = ctrl.Antecedent(
    np.arange(0,11,1),
    'tearing'
)


discharge = ctrl.Antecedent(
    np.arange(0,11,1),
    'discharge'
)


photophobia = ctrl.Antecedent(
    np.arange(0,11,1),
    'photophobia'
)


halos = ctrl.Antecedent(
    np.arange(0,11,1),
    'halos'
)


headache = ctrl.Antecedent(
    np.arange(0,11,1),
    'headache'
)


nausea = ctrl.Antecedent(
    np.arange(0,11,1),
    'nausea'
)


floaters = ctrl.Antecedent(
    np.arange(0,11,1),
    'floaters'
)


vision_loss = ctrl.Antecedent(
    np.arange(0,11,1),
    'vision_loss'
)


peripheral_loss = ctrl.Antecedent(
    np.arange(0,11,1),
    'peripheral_loss'
)


burning = ctrl.Antecedent(
    np.arange(0,11,1),
    'burning'
)


foreign_body = ctrl.Antecedent(
    np.arange(0,11,1),
    'foreign_body'
)


eye_fatigue = ctrl.Antecedent(
    np.arange(0,11,1),
    'eye_fatigue'
)



# -------------------------
# Screen Time
# -------------------------


screen_time = ctrl.Antecedent(
    np.arange(0,13,1),
    'screen_time'
)





# =========================================================
# Binary Variables (0-1)
# Improved resolution
# =========================================================



contact_lens = ctrl.Antecedent(
    np.arange(0,1.01,0.01),
    'contact_lens'
)


diabetes = ctrl.Antecedent(
    np.arange(0,1.01,0.01),
    'diabetes'
)


hypertension = ctrl.Antecedent(
    np.arange(0,1.01,0.01),
    'hypertension'
)


family_glaucoma = ctrl.Antecedent(
    np.arange(0,1.01,0.01),
    'family_glaucoma'
)


previous_surgery = ctrl.Antecedent(
    np.arange(0,1.01,0.01),
    'previous_surgery'
)


eye_trauma = ctrl.Antecedent(
    np.arange(0,1.01,0.01),
    'eye_trauma'
)


smoking = ctrl.Antecedent(
    np.arange(0,1.01,0.01),
    'smoking'
)



# New variable for uveitis rules

autoimmune_condition = ctrl.Antecedent(
    np.arange(0,1.01,0.01),
    'autoimmune_condition'
)
# =========================================================
#               OUTPUT VARIABLES
# =========================================================


glaucoma = ctrl.Consequent(
    np.arange(0,101,1),
    'glaucoma'
)


cataract = ctrl.Consequent(
    np.arange(0,101,1),
    'cataract'
)


dry_eye = ctrl.Consequent(
    np.arange(0,101,1),
    'dry_eye'
)


conjunctivitis = ctrl.Consequent(
    np.arange(0,101,1),
    'conjunctivitis'
)


keratitis = ctrl.Consequent(
    np.arange(0,101,1),
    'keratitis'
)


uveitis = ctrl.Consequent(
    np.arange(0,101,1),
    'uveitis'
)


retinopathy = ctrl.Consequent(
    np.arange(0,101,1),
    'retinopathy'
)


computer_vision = ctrl.Consequent(
    np.arange(0,101,1),
    'computer_vision'
)





# =========================================================
#               AGE MEMBERSHIP FUNCTIONS
# =========================================================


age['child'] = fuzz.trapmf(
    age.universe,
    [0,0,10,18]
)


age['young'] = fuzz.trimf(
    age.universe,
    [15,25,40]
)


age['middle'] = fuzz.trimf(
    age.universe,
    [35,50,65]
)


age['old'] = fuzz.trapmf(
    age.universe,
    [60,70,100,100]
)






# =========================================================
#               GENERAL SYMPTOM SCALE
#               Range: 0 - 10
# =========================================================


def create_scale(variable):


    variable['none'] = fuzz.trapmf(
        variable.universe,
        [0,0,1,2]
    )


    variable['mild'] = fuzz.trimf(
        variable.universe,
        [1,3,5]
    )


    variable['moderate'] = fuzz.trimf(
        variable.universe,
        [4,6,8]
    )


    variable['severe'] = fuzz.trapmf(
        variable.universe,
        [7,8.5,10,10]
    )






# Apply symptom scale


symptom_variables = [

    pain,

    redness,

    vision_blur,

    dryness,

    itching,

    tearing,

    discharge,

    photophobia,

    halos,

    headache,

    nausea,

    floaters,

    vision_loss,

    peripheral_loss,

    burning,

    foreign_body,

    eye_fatigue

]


for variable in symptom_variables:

    create_scale(variable)






# =========================================================
#               SCREEN TIME MEMBERSHIP
#               Range: 0 - 12 hours
# =========================================================


screen_time['none'] = fuzz.trapmf(
    screen_time.universe,
    [0,0,1,2]
)


screen_time['low'] = fuzz.trapmf(
    screen_time.universe,
    [0,0,2,4]
)


screen_time['medium'] = fuzz.trimf(
    screen_time.universe,
    [3,6,8]
)


screen_time['high'] = fuzz.trapmf(
    screen_time.universe,
    [7,9,12,12]
)







# =========================================================
#               BINARY MEMBERSHIP
# =========================================================


def create_binary(variable):


    variable['no'] = fuzz.trapmf(
        variable.universe,
        [0,0,0.25,0.5]
    )


    variable['yes'] = fuzz.trapmf(
        variable.universe,
        [0.5,0.75,1,1]
    )





binary_variables = [

    contact_lens,

    diabetes,

    hypertension,

    family_glaucoma,

    previous_surgery,

    eye_trauma,

    smoking,

    autoimmune_condition

]


for variable in binary_variables:

    create_binary(variable)
# =========================================================
#               OUTPUT MEMBERSHIP FUNCTIONS
# =========================================================


def create_output(variable):


    variable['very_low'] = fuzz.trapmf(
        variable.universe,
        [0,0,10,20]
    )


    variable['low'] = fuzz.trimf(
        variable.universe,
        [15,30,45]
    )


    variable['moderate'] = fuzz.trimf(
        variable.universe,
        [40,55,70]
    )


    variable['high'] = fuzz.trimf(
        variable.universe,
        [65,80,90]
    )


    variable['very_high'] = fuzz.trapmf(
        variable.universe,
        [85,95,100,100]
    )





# Apply output membership functions


output_variables = [

    glaucoma,

    cataract,

    dry_eye,

    conjunctivitis,

    keratitis,

    uveitis,

    retinopathy,

    computer_vision

]


for variable in output_variables:

    create_output(variable)






# =========================================================
#               INPUT EXPORT
# =========================================================


INPUTS = {


    "age": age,


    "pain": pain,


    "redness": redness,


    "vision_blur": vision_blur,


    "dryness": dryness,


    "itching": itching,


    "tearing": tearing,


    "discharge": discharge,


    "photophobia": photophobia,


    "halos": halos,


    "headache": headache,


    "nausea": nausea,


    "floaters": floaters,


    "vision_loss": vision_loss,


    "peripheral_loss": peripheral_loss,


    "burning": burning,


    "foreign_body": foreign_body,


    "eye_fatigue": eye_fatigue,


    "screen_time": screen_time,


    "contact_lens": contact_lens,


    "diabetes": diabetes,


    "hypertension": hypertension,


    "family_glaucoma": family_glaucoma,


    "previous_surgery": previous_surgery,


    "eye_trauma": eye_trauma,


    "smoking": smoking,


    "autoimmune_condition": autoimmune_condition

}






# =========================================================
#               OUTPUT EXPORT
# =========================================================


OUTPUTS = {


    "glaucoma": glaucoma,


    "cataract": cataract,


    "dry_eye": dry_eye,


    "conjunctivitis": conjunctivitis,


    "keratitis": keratitis,


    "uveitis": uveitis,


    "retinopathy": retinopathy,


    "computer_vision": computer_vision

}






# =========================================================
#               COMPATIBILITY VARIABLES
#               For old modules
# =========================================================


eye_redness = redness


eye_pain = pain


blurred_vision = vision_blur


light_sensitivity = photophobia


age_factor = age






# =========================================================
#               RISK OUTPUT VARIABLE
# =========================================================


risk_level = ctrl.Consequent(

    np.arange(0,101,1),

    'risk_level'

)





risk_level['safe'] = fuzz.trimf(

    risk_level.universe,

    [0,0,35]

)



risk_level['warning'] = fuzz.trimf(

    risk_level.universe,

    [25,50,75]

)



risk_level['danger'] = fuzz.trimf(

    risk_level.universe,

    [65,100,100]

)






# =========================================================
#               FILE END
# =========================================================


