"""
=========================================================
Eye Expert System

Recommendations Engine

Purpose:
- Generate medical guidance
- Based on fuzzy diagnosis results
- Based on risk level

Compatible with:
- diagnosis_engine.py
- risk_engine.py
=========================================================
"""




# =========================================================
#               Disease Recommendations Database
# =========================================================


DISEASE_RECOMMENDATIONS = {


# ---------------------------------------------------------
# Glaucoma
# ---------------------------------------------------------


"glaucoma": {


    "title":

        "Glaucoma - الماء الأزرق",



    "description":

        "مرض يؤثر على العصب البصري وغالباً يرتبط بارتفاع ضغط العين.",



    "recommendations":

    [

        "إجراء فحص ضغط العين بشكل دوري.",

        "مراجعة طبيب العيون لفحص العصب البصري.",

        "الالتزام بأي قطرات علاجية موصوفة.",

        "تجنب إهمال تغيرات الرؤية الجانبية."

    ],



    "warning":

        "ارتفاع احتمال الزرق يحتاج متابعة طبية منتظمة لمنع فقدان الرؤية."

},






# ---------------------------------------------------------
# Cataract
# ---------------------------------------------------------


"cataract": {


    "title":

        "Cataract - الماء الأبيض",



    "description":

        "تعتم في عدسة العين يؤدي إلى انخفاض تدريجي في وضوح الرؤية.",



    "recommendations":

    [

        "فحص حدة النظر بشكل دوري.",

        "استخدام إضاءة مناسبة أثناء القراءة.",

        "حماية العين من الأشعة فوق البنفسجية.",

        "مراجعة الطبيب عند تأثير ضعف النظر على النشاط اليومي."

    ],



    "warning":

        "تطور عتامة العدسة قد يحتاج إلى تقييم جراحي."

},






# ---------------------------------------------------------
# Dry Eye
# ---------------------------------------------------------


"dry_eye": {


    "title":

        "Dry Eye Syndrome - جفاف العين",



    "description":

        "نقص كمية أو جودة الدموع مما يسبب جفاف وتهيج سطح العين.",



    "recommendations":

    [

        "استخدام قطرات مرطبة عند الحاجة.",

        "تقليل وقت استخدام الشاشات.",

        "أخذ فترات راحة أثناء العمل أمام الحاسوب.",

        "تجنب الهواء المباشر من المكيف."

    ],



    "warning":

        "الجفاف المزمن قد يسبب التهاب سطح العين."

}

# ---------------------------------------------------------
# Conjunctivitis
# التهاب الملتحمة
# ---------------------------------------------------------


,"conjunctivitis": {


    "title":

        "Conjunctivitis - التهاب الملتحمة",



    "description":

        "التهاب في الغشاء الذي يغطي الجزء الأمامي من العين وقد يكون بسبب عدوى أو حساسية.",



    "recommendations":

    [

        "تجنب لمس العين باليدين.",

        "غسل اليدين باستمرار.",

        "عدم مشاركة المناشف أو أدوات العين.",

        "مراجعة الطبيب عند وجود إفرازات شديدة أو ألم."

    ],



    "warning":

        "قد يكون التهاب الملتحمة معدياً في بعض الحالات."

},






# ---------------------------------------------------------
# Keratitis
# التهاب القرنية
# ---------------------------------------------------------


"keratitis": {


    "title":

        "Keratitis - التهاب القرنية",



    "description":

        "التهاب يصيب القرنية وقد يؤثر على وضوح الرؤية.",



    "recommendations":

    [

        "تجنب استخدام العدسات اللاصقة عند وجود ألم أو احمرار.",

        "عدم استخدام قطرات دون استشارة الطبيب.",

        "إجراء فحص سريع عند حدوث ألم شديد.",

        "الحفاظ على نظافة أدوات العدسات."

    ],



    "warning":

        "التهاب القرنية قد يؤثر على الرؤية ويحتاج تقييماً طبياً."

},






# ---------------------------------------------------------
# Uveitis
# التهاب العنبية
# ---------------------------------------------------------


"uveitis": {


    "title":

        "Uveitis - التهاب العنبية",



    "description":

        "التهاب في الطبقة الوسطى من العين وقد يرتبط بأمراض مناعية.",



    "recommendations":

    [

        "مراجعة طبيب العيون عند وجود حساسية شديدة للضوء.",

        "متابعة أي أمراض مناعية موجودة.",

        "الالتزام بالعلاج الموصوف.",

        "عدم تأخير الفحص عند انخفاض الرؤية."

    ],



    "warning":

        "التهاب العنبية يحتاج متابعة لأن إهماله قد يسبب مضاعفات."

},






# ---------------------------------------------------------
# Retinopathy
# اعتلال الشبكية السكري
# ---------------------------------------------------------


"retinopathy": {


    "title":

        "Diabetic Retinopathy - اعتلال الشبكية السكري",



    "description":

        "تغيرات تصيب أوعية الشبكية وقد ترتبط بمرض السكري.",



    "recommendations":

    [

        "السيطرة على مستوى السكر في الدم.",

        "إجراء فحص قاع العين بشكل دوري.",

        "متابعة ضغط الدم.",

        "اتباع نمط حياة صحي."

    ],



    "warning":

        "اعتلال الشبكية قد يؤدي إلى ضعف الرؤية إذا لم تتم متابعته."

},






# ---------------------------------------------------------
# Computer Vision Syndrome
# إجهاد العين الرقمي
# ---------------------------------------------------------


"computer_vision": {


    "title":

        "Computer Vision Syndrome - إجهاد العين الرقمي",



    "description":

        "إجهاد العين الناتج عن الاستخدام الطويل للشاشات الرقمية.",



    "recommendations":

    [

        "تطبيق قاعدة 20-20-20 أثناء استخدام الشاشة.",

        "زيادة عدد فترات الراحة.",

        "ضبط إضاءة الشاشة.",

        "الحفاظ على مسافة مناسبة من الشاشة."

    ],



    "warning":

        "الاستخدام الطويل للشاشات قد يزيد أعراض الجفاف والإرهاق."

}
}
# =========================================================
#               Recommendation Engine
# =========================================================


def get_disease_recommendation(disease):

    """
    Get static recommendation
    for one disease.
    """



    return DISEASE_RECOMMENDATIONS.get(

        disease,

        {

            "title":

                "Unknown Disease",


            "description":

                "No information available.",


            "recommendations":

                [

                    "Consult an eye specialist."

                ],


            "warning":

                "Medical evaluation is recommended."

        }

    )







# =========================================================
#               Select Important Diseases
# =========================================================


def select_high_risk_diseases(results):

    """
    Select diseases with
    significant probability.

    Input:

    {
        glaucoma:80,
        dry_eye:30
    }


    Output:

    [
        glaucoma
    ]

    """



    selected = []



    for disease, probability in results.items():


        if probability >= 40:


            selected.append(

                {

                    "disease": disease,

                    "probability": probability

                }

            )



    # Sort by probability


    selected.sort(

        key=lambda x:x["probability"],

        reverse=True

    )



    return selected







# =========================================================
#               Generate Recommendations
# =========================================================


def generate_recommendations(

        diagnosis_results,

        risk_level=None

):

    """
    Generate complete recommendations.

    Parameters:

        diagnosis_results:
            output from diagnosis_engine


        risk_level:
            output from risk_engine


    Returns:

        list of recommendations

    """



    recommendations = []



    high_risk = select_high_risk_diseases(

        diagnosis_results

    )




    # Add general risk warning


    if risk_level == "Danger":


        recommendations.append(

            {

            "type":

                "warning",


            "message":

                "High risk detected. Immediate ophthalmology consultation is recommended."

            }

        )



    elif risk_level == "Warning":


        recommendations.append(

            {

            "type":

                "warning",


            "message":

                "Moderate risk detected. Regular eye examination is recommended."

            }

        )






    # Disease recommendations


    for item in high_risk:


        disease = item["disease"]


        probability = item["probability"]




        data = get_disease_recommendation(

            disease

        )



        recommendations.append(

            {


            "disease":

                data["title"],



            "probability":

                probability,



            "description":

                data["description"],



            "actions":

                data["recommendations"],



            "warning":

                data["warning"]


            }

        )



    return recommendations







# =========================================================
#               Complete Patient Advice
# =========================================================


def get_patient_advice(

        diagnosis_results,

        risk_report

):

    """
    Final recommendation report.

    Used by UI.

    """



    return {


        "risk_level":

            risk_report.get(

                "risk_level",

                "Unknown"

            ),



        "risk_score":

            risk_report.get(

                "risk_score",

                0

            ),



        "recommendations":

            generate_recommendations(

                diagnosis_results,

                risk_report.get(

                    "risk_level"

                )

            )

    }







# =========================================================
#               TEST
# =========================================================


if __name__ == "__main__":


    test_results = {


        "glaucoma":82,


        "cataract":45,


        "dry_eye":60,


        "computer_vision":30

    }




    test_risk = {


        "risk_level":

            "Danger",


        "risk_score":

            75

    }




    report = get_patient_advice(

        test_results,

        test_risk

    )



    print(report)