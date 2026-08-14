"""
=========================================================
Eye Expert System
Fuzzy Rules
Compatible with fuzzy_variables.py
=========================================================
"""

from skfuzzy import control as ctrl

from .fuzzy_variables import *

# =========================================================
#                GLAUCOMA RULES
# =========================================================

glaucoma_rules = [

# 1
ctrl.Rule(
    halos['severe'] &
    pain['severe'] &
    nausea['moderate'],
    glaucoma['very_high']
),

# 2
ctrl.Rule(
    halos['severe'] &
    headache['severe'],
    glaucoma['very_high']
),

# 3
ctrl.Rule(
    halos['moderate'] &
    age['old'] &
    family_glaucoma['yes'],
    glaucoma['high']
),

# 4
ctrl.Rule(
    vision_loss['moderate'] &
    peripheral_loss['moderate'] &
    age['old'],
    glaucoma['high']
),

# 5
ctrl.Rule(
    hypertension['yes'] &
    age['old'],
    glaucoma['high']
),

# 6
ctrl.Rule(
    family_glaucoma['yes'] &
    age['middle'],
    glaucoma['moderate']
),

# 7
ctrl.Rule(
    family_glaucoma['yes'] &
    halos['moderate'],
    glaucoma['high']
),

# 8
ctrl.Rule(
    family_glaucoma['yes'] &
    vision_blur['moderate'],
    glaucoma['moderate']
),

# 9
ctrl.Rule(
    pain['severe'] &
    headache['moderate'] &
    halos['moderate'],
    glaucoma['high']
),

# 10
ctrl.Rule(
    vision_blur['severe'] &
    halos['severe'],
    glaucoma['very_high']
),

# 11
ctrl.Rule(
    peripheral_loss['severe'],
    glaucoma['very_high']
),

# 12
ctrl.Rule(
    peripheral_loss['moderate'] &
    age['old'],
    glaucoma['high']
),

# 13
ctrl.Rule(
    vision_loss['severe'],
    glaucoma['very_high']
),

# 14
ctrl.Rule(
    age['old'] &
    hypertension['yes'] &
    family_glaucoma['yes'],
    glaucoma['very_high']
),

# 15
ctrl.Rule(
    age['old'] &
    vision_blur['moderate'],
    glaucoma['moderate']
),

# 16
ctrl.Rule(
    age['old'] &
    halos['moderate'],
    glaucoma['moderate']
),

# 17
ctrl.Rule(
    pain['moderate'] &
    halos['moderate'] &
    headache['moderate'],
    glaucoma['moderate']
),

# 18
ctrl.Rule(
    pain['severe'] &
    nausea['severe'],
    glaucoma['very_high']
),

# 19
ctrl.Rule(
    redness['moderate'] &
    pain['moderate'] &
    halos['moderate'],
    glaucoma['moderate']
),

# 20
ctrl.Rule(
    age['old'] &
    vision_loss['moderate'] &
    family_glaucoma['yes'],
    glaucoma['high']
),

# 21
ctrl.Rule(
    age['old'] &
    peripheral_loss['moderate'] &
    hypertension['yes'],
    glaucoma['high']
),

# 22
ctrl.Rule(
    age['old'] &
    headache['moderate'] &
    halos['moderate'],
    glaucoma['high']
),

# 23
ctrl.Rule(
    vision_blur['moderate'] &
    headache['moderate'],
    glaucoma['moderate']
),

# 24
ctrl.Rule(
    halos['moderate'] &
    nausea['moderate'],
    glaucoma['moderate']
),

# 25
ctrl.Rule(
    family_glaucoma['yes'] &
    hypertension['yes'],
    glaucoma['high']
)

]
# =========================================================
#                CATARACT RULES
# =========================================================

cataract_rules = [

# 1
ctrl.Rule(
    age['old'] &
    vision_blur['severe'],
    cataract['very_high']
),

# 2
ctrl.Rule(
    age['old'] &
    vision_blur['moderate'],
    cataract['high']
),

# 3
ctrl.Rule(
    age['middle'] &
    vision_blur['moderate'],
    cataract['moderate']
),

# 4
ctrl.Rule(
    age['old'] &
    halos['moderate'],
    cataract['high']
),

# 5
ctrl.Rule(
    age['old'] &
    halos['severe'],
    cataract['very_high']
),

# 6
ctrl.Rule(
    diabetes['yes'] &
    age['old'],
    cataract['high']
),

# 7
ctrl.Rule(
    diabetes['yes'] &
    vision_blur['moderate'],
    cataract['moderate']
),

# 8
ctrl.Rule(
    smoking['yes'] &
    age['old'],
    cataract['moderate']
),

# 9
ctrl.Rule(
    smoking['yes'] &
    vision_blur['moderate'],
    cataract['moderate']
),

# 10
ctrl.Rule(
    age['old'] &
    photophobia['moderate'],
    cataract['moderate']
),

# 11
ctrl.Rule(
    age['old'] &
    photophobia['severe'],
    cataract['high']
),

# 12
ctrl.Rule(
    age['old'] &
    vision_loss['moderate'],
    cataract['high']
),

# 13
ctrl.Rule(
    vision_blur['severe'] &
    halos['moderate'],
    cataract['high']
),

# 14
ctrl.Rule(
    vision_blur['severe'] &
    halos['severe'],
    cataract['very_high']
),

# 15
ctrl.Rule(
    age['old'] &
    diabetes['yes'] &
    vision_blur['severe'],
    cataract['very_high']
),

# 16
ctrl.Rule(
    age['old'] &
    smoking['yes'] &
    vision_blur['moderate'],
    cataract['high']
),

# 17
ctrl.Rule(
    age['middle'] &
    diabetes['yes'] &
    vision_blur['moderate'],
    cataract['high']
),

# 18
ctrl.Rule(
    age['old'] &
    floaters['none'] &
    pain['none'],
    cataract['moderate']
),

# 19
ctrl.Rule(
    age['old'] &
    redness['none'] &
    vision_blur['moderate'],
    cataract['high']
),

# 20
ctrl.Rule(
    age['old'] &
    vision_blur['moderate'] &
    halos['moderate'],
    cataract['very_high']
),

# 21
ctrl.Rule(
    diabetes['yes'] &
    smoking['yes'],
    cataract['moderate']
),

# 22
ctrl.Rule(
    vision_blur['moderate'] &
    photophobia['moderate'],
    cataract['moderate']
),

# 23
ctrl.Rule(
    vision_blur['severe'] &
    photophobia['moderate'],
    cataract['high']
),

# 24
ctrl.Rule(
    age['old'] &
    previous_surgery['yes'],
    cataract['moderate']
),

# 25
ctrl.Rule(
    age['old'] &
    diabetes['yes'] &
    smoking['yes'],
    cataract['very_high']
)

]
# =========================================================
#                DRY EYE RULES
# =========================================================

dry_eye_rules = [

# 1
ctrl.Rule(
    dryness['severe'] &
    burning['severe'],
    dry_eye['very_high']
),

# 2
ctrl.Rule(
    dryness['severe'] &
    foreign_body['severe'],
    dry_eye['very_high']
),

# 3
ctrl.Rule(
    dryness['moderate'] &
    burning['moderate'],
    dry_eye['high']
),

# 4
ctrl.Rule(
    dryness['moderate'] &
    eye_fatigue['moderate'],
    dry_eye['high']
),

# 5
ctrl.Rule(
    screen_time['high'] &
    dryness['moderate'],
    dry_eye['high']
),

# 6
ctrl.Rule(
    screen_time['high'] &
    eye_fatigue['severe'],
    dry_eye['very_high']
),

# 7
ctrl.Rule(
    screen_time['high'] &
    burning['moderate'],
    dry_eye['high']
),

# 8
ctrl.Rule(
    screen_time['high'] &
    foreign_body['moderate'],
    dry_eye['high']
),

# 9
ctrl.Rule(
    contact_lens['yes'] &
    dryness['moderate'],
    dry_eye['high']
),

# 10
ctrl.Rule(
    contact_lens['yes'] &
    burning['moderate'],
    dry_eye['high']
),

# 11
ctrl.Rule(
    contact_lens['yes'] &
    foreign_body['moderate'],
    dry_eye['high']
),

# 12
ctrl.Rule(
    contact_lens['yes'] &
    screen_time['high'],
    dry_eye['very_high']
),

# 13
ctrl.Rule(
    age['old'] &
    dryness['moderate'],
    dry_eye['moderate']
),

# 14
ctrl.Rule(
    age['old'] &
    burning['moderate'],
    dry_eye['moderate']
),

# 15
ctrl.Rule(
    smoking['yes'] &
    dryness['moderate'],
    dry_eye['moderate']
),

# 16
ctrl.Rule(
    smoking['yes'] &
    burning['moderate'],
    dry_eye['moderate']
),

# 17
ctrl.Rule(
    dryness['severe'] &
    photophobia['moderate'],
    dry_eye['high']
),

# 18
ctrl.Rule(
    dryness['moderate'] &
    tearing['moderate'],
    dry_eye['moderate']
),

# 19
ctrl.Rule(
    eye_fatigue['severe'] &
    vision_blur['moderate'],
    dry_eye['high']
),

# 20
ctrl.Rule(
    screen_time['medium'] &
    eye_fatigue['moderate'],
    dry_eye['moderate']
),

# 21
ctrl.Rule(
    dryness['moderate'] &
    itching['moderate'],
    dry_eye['moderate']
),

# 22
ctrl.Rule(
    burning['severe'] &
    foreign_body['moderate'],
    dry_eye['high']
),

# 23
ctrl.Rule(
    screen_time['high'] &
    dryness['severe'] &
    burning['moderate'],
    dry_eye['very_high']
),

# 24
ctrl.Rule(
    contact_lens['yes'] &
    dryness['severe'] &
    foreign_body['moderate'],
    dry_eye['very_high']
),

# 25
ctrl.Rule(
    dryness['severe'] &
    eye_fatigue['severe'] &
    vision_blur['moderate'],
    dry_eye['very_high']
)

]
# =========================================================
#                CONJUNCTIVITIS RULES
# =========================================================

conjunctivitis_rules = [

# 1
ctrl.Rule(
    redness['severe'] &
    discharge['severe'],
    conjunctivitis['very_high']
),

# 2
ctrl.Rule(
    redness['moderate'] &
    itching['severe'],
    conjunctivitis['high']
),

# 3
ctrl.Rule(
    redness['severe'] &
    tearing['moderate'],
    conjunctivitis['high']
),

# 4
ctrl.Rule(
    discharge['moderate'] &
    itching['moderate'],
    conjunctivitis['high']
),

# 5
ctrl.Rule(
    discharge['severe'],
    conjunctivitis['very_high']
),

# 6
ctrl.Rule(
    redness['moderate'] &
    discharge['moderate'],
    conjunctivitis['high']
),

# 7
ctrl.Rule(
    itching['severe'] &
    redness['moderate'],
    conjunctivitis['high']
),

# 8
ctrl.Rule(
    tearing['severe'] &
    redness['moderate'],
    conjunctivitis['moderate']
),

# 9
ctrl.Rule(
    foreign_body['moderate'] &
    redness['moderate'],
    conjunctivitis['moderate']
),

# 10
ctrl.Rule(
    photophobia['moderate'] &
    redness['severe'],
    conjunctivitis['high']
),

# 11
ctrl.Rule(
    discharge['severe'] &
    redness['severe'],
    conjunctivitis['very_high']
),

# 12
ctrl.Rule(
    itching['moderate'] &
    tearing['moderate'],
    conjunctivitis['moderate']
),

# 13
ctrl.Rule(
    contact_lens['yes'] &
    redness['moderate'],
    conjunctivitis['high']
),

# 14
ctrl.Rule(
    contact_lens['yes'] &
    discharge['moderate'],
    conjunctivitis['high']
),

# 15
ctrl.Rule(
    foreign_body['severe'] &
    redness['severe'],
    conjunctivitis['high']
),

# 16
ctrl.Rule(
    redness['moderate'] &
    burning['moderate'],
    conjunctivitis['moderate']
),

# 17
ctrl.Rule(
    tearing['severe'] &
    discharge['moderate'],
    conjunctivitis['high']
),

# 18
ctrl.Rule(
    itching['severe'] &
    discharge['moderate'],
    conjunctivitis['high']
),

# 19
ctrl.Rule(
    redness['severe'] &
    photophobia['moderate'] &
    discharge['moderate'],
    conjunctivitis['very_high']
),

# 20
ctrl.Rule(
    contact_lens['yes'] &
    redness['severe'] &
    discharge['severe'],
    conjunctivitis['very_high']
)

]
# =========================================================
#                KERATITIS RULES
# =========================================================

keratitis_rules = [

# 1
ctrl.Rule(
    pain['severe'] &
    redness['severe'],
    keratitis['very_high']
),

# 2
ctrl.Rule(
    pain['severe'] &
    photophobia['severe'],
    keratitis['very_high']
),

# 3
ctrl.Rule(
    redness['severe'] &
    photophobia['moderate'],
    keratitis['high']
),

# 4
ctrl.Rule(
    foreign_body['severe'] &
    pain['moderate'],
    keratitis['high']
),

# 5
ctrl.Rule(
    contact_lens['yes'] &
    pain['moderate'],
    keratitis['high']
),

# 6
ctrl.Rule(
    contact_lens['yes'] &
    redness['severe'],
    keratitis['very_high']
),

# 7
ctrl.Rule(
    contact_lens['yes'] &
    photophobia['severe'],
    keratitis['very_high']
),

# 8
ctrl.Rule(
    vision_blur['moderate'] &
    pain['moderate'],
    keratitis['high']
),

# 9
ctrl.Rule(
    vision_blur['severe'] &
    pain['severe'],
    keratitis['very_high']
),

# 10
ctrl.Rule(
    tearing['severe'] &
    pain['moderate'],
    keratitis['high']
),

# 11
ctrl.Rule(
    foreign_body['moderate'] &
    redness['moderate'],
    keratitis['moderate']
),

# 12
ctrl.Rule(
    burning['severe'] &
    redness['severe'],
    keratitis['high']
),

# 13
ctrl.Rule(
    photophobia['severe'] &
    vision_blur['moderate'],
    keratitis['high']
),

# 14
ctrl.Rule(
    eye_trauma['yes'] &
    pain['severe'],
    keratitis['very_high']
),

# 15
ctrl.Rule(
    eye_trauma['yes'] &
    redness['severe'],
    keratitis['high']
),

# 16
ctrl.Rule(
    eye_trauma['yes'] &
    photophobia['moderate'],
    keratitis['high']
),

# 17
ctrl.Rule(
    pain['moderate'] &
    redness['moderate'] &
    tearing['moderate'],
    keratitis['moderate']
),

# 18
ctrl.Rule(
    pain['severe'] &
    vision_loss['moderate'],
    keratitis['very_high']
),

# 19
ctrl.Rule(
    contact_lens['yes'] &
    foreign_body['severe'] &
    pain['severe'],
    keratitis['very_high']
),

# 20
ctrl.Rule(
    pain['severe'] &
    photophobia['severe'] &
    vision_blur['severe'],
    keratitis['very_high']
)

]
# =========================================================
#                UVEITIS RULES
# =========================================================

uveitis_rules = [

# 1
ctrl.Rule(
    pain['severe'] &
    photophobia['severe'],
    uveitis['very_high']
),

# 2
ctrl.Rule(
    redness['severe'] &
    pain['moderate'],
    uveitis['high']
),

# 3
ctrl.Rule(
    photophobia['severe'] &
    redness['moderate'],
    uveitis['high']
),

# 4
ctrl.Rule(
    vision_blur['moderate'] &
    pain['moderate'],
    uveitis['high']
),

# 5
ctrl.Rule(
    vision_blur['severe'] &
    photophobia['severe'],
    uveitis['very_high']
),

# 6
ctrl.Rule(
    floaters['moderate'] &
    vision_blur['moderate'],
    uveitis['high']
),

# 7
ctrl.Rule(
    floaters['severe'],
    uveitis['very_high']
),

# 8
ctrl.Rule(
    redness['severe'] &
    floaters['moderate'],
    uveitis['high']
),

# 9
ctrl.Rule(
    pain['moderate'] &
    photophobia['moderate'],
    uveitis['moderate']
),

# 10
ctrl.Rule(
    eye_trauma['yes'] &
    pain['severe'],
    uveitis['high']
),

# 11
ctrl.Rule(
    eye_trauma['yes'] &
    redness['severe'],
    uveitis['high']
),

# 12
ctrl.Rule(
    diabetes['yes'] &
    redness['moderate'],
    uveitis['high']
),

# 13
ctrl.Rule(
    vision_loss['moderate'] &
    pain['moderate'],
    uveitis['high']
),

# 14
ctrl.Rule(
    vision_loss['severe'],
    uveitis['very_high']
),

# 15
ctrl.Rule(
    photophobia['moderate'] &
    redness['moderate'],
    uveitis['moderate']
),

# 16
ctrl.Rule(
    floaters['moderate'] &
    photophobia['moderate'],
    uveitis['high']
),

# 17
ctrl.Rule(
    age['middle'] &
    pain['moderate'] &
    redness['moderate'],
    uveitis['moderate']
),

# 18
ctrl.Rule(
    age['old'] &
    vision_loss['moderate'],
    uveitis['high']
),

# 19
ctrl.Rule(
    pain['severe'] &
    vision_loss['moderate'] &
    photophobia['severe'],
    uveitis['very_high']
),

# 20
ctrl.Rule(
    redness['severe'] &
    floaters['severe'] &
    vision_blur['severe'],
    uveitis['very_high']
)

]
# =========================================================
#          DIABETIC RETINOPATHY RULES
# =========================================================

retinopathy_rules = [

# 1
ctrl.Rule(
    diabetes['yes'] &
    vision_blur['moderate'],
    retinopathy['high']
),

# 2
ctrl.Rule(
    diabetes['yes'] &
    vision_loss['moderate'],
    retinopathy['high']
),

# 3
ctrl.Rule(
    diabetes['yes'] &
    floaters['moderate'],
    retinopathy['high']
),

# 4
ctrl.Rule(
    diabetes['yes'] &
    floaters['severe'],
    retinopathy['very_high']
),

# 5
ctrl.Rule(
    diabetes['yes'] &
    vision_loss['severe'],
    retinopathy['very_high']
),

# 6
ctrl.Rule(
    diabetes['yes'] &
    age['old'],
    retinopathy['moderate']
),

# 7
ctrl.Rule(
    diabetes['yes'] &
    hypertension['yes'],
    retinopathy['high']
),

# 8
ctrl.Rule(
    diabetes['yes'] &
    hypertension['yes'] &
    vision_blur['severe'],
    retinopathy['very_high']
),

# 9
ctrl.Rule(
    diabetes['yes'] &
    peripheral_loss['moderate'],
    retinopathy['high']
),

# 10
ctrl.Rule(
    diabetes['yes'] &
    peripheral_loss['severe'],
    retinopathy['very_high']
),

# 11
ctrl.Rule(
    age['old'] &
    diabetes['yes'] &
    vision_blur['moderate'],
    retinopathy['high']
),

# 12
ctrl.Rule(
    diabetes['yes'] &
    headache['moderate'],
    retinopathy['moderate']
),

# 13
ctrl.Rule(
    diabetes['yes'] &
    floaters['moderate'] &
    vision_blur['moderate'],
    retinopathy['high']
),

# 14
ctrl.Rule(
    diabetes['yes'] &
    floaters['severe'] &
    vision_loss['moderate'],
    retinopathy['very_high']
),

# 15
ctrl.Rule(
    diabetes['yes'] &
    peripheral_loss['moderate'] &
    age['old'],
    retinopathy['high']
)

]
# =========================================================
#          COMPUTER VISION SYNDROME RULES
# =========================================================

computer_vision_rules = [

# 1
ctrl.Rule(
    screen_time['high'] &
    eye_fatigue['severe'],
    computer_vision['very_high']
),

# 2
ctrl.Rule(
    screen_time['high'] &
    dryness['moderate'],
    computer_vision['high']
),

# 3
ctrl.Rule(
    screen_time['high'] &
    vision_blur['moderate'],
    computer_vision['high']
),

# 4
ctrl.Rule(
    eye_fatigue['severe'] &
    headache['moderate'],
    computer_vision['high']
),

# 5
ctrl.Rule(
    eye_fatigue['severe'] &
    burning['moderate'],
    computer_vision['high']
),

# 6
ctrl.Rule(
    eye_fatigue['moderate'] &
    screen_time['medium'],
    computer_vision['moderate']
),

# 7
ctrl.Rule(
    screen_time['high'] &
    headache['severe'],
    computer_vision['very_high']
),

# 8
ctrl.Rule(
    screen_time['high'] &
    tearing['moderate'],
    computer_vision['moderate']
),

# 9
ctrl.Rule(
    screen_time['high'] &
    photophobia['moderate'],
    computer_vision['high']
),

# 10
ctrl.Rule(
    eye_fatigue['moderate'] &
    dryness['moderate'],
    computer_vision['moderate']
),

# 11
ctrl.Rule(
    screen_time['high'] &
    dryness['severe'] &
    burning['severe'],
    computer_vision['very_high']
),

# 12
ctrl.Rule(
    screen_time['medium'] &
    vision_blur['moderate'],
    computer_vision['moderate']
),

# 13
ctrl.Rule(
    screen_time['high'] &
    foreign_body['moderate'],
    computer_vision['high']
),

# 14
ctrl.Rule(
    eye_fatigue['severe'] &
    vision_blur['severe'],
    computer_vision['very_high']
),

# 15
ctrl.Rule(
    screen_time['high'] &
    contact_lens['yes'],
    computer_vision['high']
),

# 16
ctrl.Rule(
    screen_time['high'] &
    age['young'] &
    eye_fatigue['moderate'],
    computer_vision['moderate']
),

# 17
ctrl.Rule(
    screen_time['high'] &
    age['middle'] &
    dryness['moderate'],
    computer_vision['high']
),

# 18
ctrl.Rule(
    screen_time['high'] &
    headache['moderate'] &
    eye_fatigue['moderate'],
    computer_vision['high']
),

# 19
ctrl.Rule(
    eye_fatigue['severe'] &
    burning['severe'] &
    dryness['severe'],
    computer_vision['very_high']
),

# 20
ctrl.Rule(
    screen_time['high'] &
    vision_blur['moderate'] &
    dryness['moderate'],
    computer_vision['very_high']
)

]
# =========================================================
#              RULE EXPORT FUNCTIONS
# =========================================================


def get_glaucoma_rules():

    return glaucoma_rules



def get_cataract_rules():

    return cataract_rules



def get_dry_eye_rules():

    return dry_eye_rules



def get_conjunctivitis_rules():

    return conjunctivitis_rules



def get_keratitis_rules():

    return keratitis_rules



def get_uveitis_rules():

    return uveitis_rules



def get_retinopathy_rules():

    return retinopathy_rules



def get_computer_vision_rules():

    return computer_vision_rules



# =========================================================
#              ALL RULES
# =========================================================


ALL_RULES = {

    "glaucoma":
        glaucoma_rules,

    "cataract":
        cataract_rules,

    "dry_eye":
        dry_eye_rules,

    "conjunctivitis":
        conjunctivitis_rules,

    "keratitis":
        keratitis_rules,

    "uveitis":
        uveitis_rules,

    "retinopathy":
        retinopathy_rules,

    "computer_vision":
        computer_vision_rules
}