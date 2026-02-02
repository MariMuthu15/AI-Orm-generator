import asyncio
import re
import os
from services.ai_service import AIService


def generate_filters_with_ai(user_query: str) -> str:
    model = AIService(model_name=os.getenv("AI_MODEL"))

    """
       Generates a Django ORM query string from a natural language query using an AI model.

       :param user_query: The user's natural language query.
       :return: A single-line Django ORM query as a string.
    """
    prompt = f"""
    You are a Django ORM query generator. Convert the given natural language query into a valid **single-line** Django ORM call.

MODEL STRUCTURE:
CandidateProfile.objects.filter(
    user__first_name__icontains=…,
    dob__exact=… | dob__gt=… | dob__gte=… | dob__lt=… | dob__lte=…,
    gender='male' | 'female' | 'other' | 'transgender',  # exact only
    user__email__icontains=…,
    user__phone__icontains=…,
    permanent_address_district__icontains=…,
    college__name__icontains=…,
    college__district__icontains=…,
    college__affiliated_university__icontains=…,
    college__category__icontains=…,
    college__branch__icontains=…,
    college__type__icontains=…,
    year_of_passout__icontains=…,
    medium__icontains=…,
    mode_of_study__icontains=…,
    stream__icontains=…,
    certifications__name__icontains=…
    placement_status= True | False
)

RULES:
1. Return only: `CandidateProfile.objects.filter(...)` or with `.all()[:N]` or `.count()`.
2. Output must be a **single line**, with **no markdown**, **no extra text**, and **no quotes** around the call.
3. Use `icontains` for all text fields; use **exact match** for gender.
4. For `dob`, support filters: `exact`, `gt`, `gte`, `lt`, `lte`.
5. Convert number words to digits (e.g., "five" → 5).
6. If a specific number of students is mentioned (e.g., "top 5"), use `.all()[:N]`.
7. If the query asks for a count (e.g., "how many students"), return `.count()`.
8. If any **skill**, **course**, **certifications**, or **subject** is mentioned (e.g., "Python", "Deep Learning"), match only using:
   → `certifications__name__icontains='X'`
9. For location mentions (e.g., "students in Chennai"), match using:
   → `permanent_address_district__icontains='Chennai'`
10. **STRICT Q() usage rules:**
    - Always place **all Q(...) conditions first** inside `.filter(...)`, before any normal kwargs.
    - Combine OR conditions for repeated fields using Q objects.
    - Example: If multiple values for same field (e.g., multiple districts), use:
      `Q(permanent_address_district__icontains='A') | Q(permanent_address_district__icontains='B')`
    - Combine multiple Q expressions properly using `|` or `&`.
    - Do NOT repeat the same keyword argument in `.filter(...)`.

SPECIAL CASES:
- Engineering Candidates:  
  → `college__type__icontains='engineering'`
- Polytechnic Candidates:  
  → `college__type__icontains='polytechnic'`
- ITI Candidates:  
  → `college__type__icontains='iti'`
- Arts and Science or Arts & Science:  
  → `college__type__icontains='arts'`
- Gender:
  - Male → `gender='male'`
  - Female → `gender='female'`
  - Other → `gender='other'`
  - Transgender → `gender='transgender'`
  
PLACEMENT STATUS RULE:
- By default, **always include `placement_status=False`** in the filter.
- If the query refers to "experienced", "working", "already placed", "got a job", "employed", etc., 
  then instead use `placement_status=True`.
  
CERTIFICATION RULE (IMPORTANT)
When matching skills, courses, subjects, or certifications:
- ALWAYS use:
    certifications__name__icontains='X', certifications__is_uploaded_by_nm=True
- Never match certifications where is_uploaded_by_nm=False
- Candidate should be INCLUDED if ANY certification with is_uploaded_by_nm=True matches
- Non-NM certifications must never be used in filtering.

Examples of correct use:
    certifications__name__icontains='python', certifications__is_uploaded_by_nm=True
    Q(certifications__name__icontains='gen ai', certifications__is_uploaded_by_nm=True)


EXAMPLES:
- "Find male candidates from 2025 passout batch taking Deep Learning"  
  → CandidateProfile.objects.filter(certifications__name__icontains='Deep Learning', certifications__is_uploaded_by_nm=True, gender='male', year_of_passout__icontains='2025', placement_status=False)

- "Candidates from Chennai with Python skill"  
  → CandidateProfile.objects.filter(certifications__name__icontains='Python', certifications__is_uploaded_by_nm=True, permanent_address_district__icontains='Chennai', placement_status=False)

- "Female engineering candidates in Coimbatore"  
  → CandidateProfile.objects.filter(gender='female', college__type__icontains='engineering', permanent_address_district__icontains='Coimbatore', placement_status=False)

- "Female candidates from Chennai or Chengalpattu with IoT and PEB Design skills"  
  → CandidateProfile.objects.filter(Q(permanent_address_district__icontains='Chennai') | Q(permanent_address_district__icontains='Chengalpattu'),Q(certifications__name__icontains='IoT',  certifications__is_uploaded_by_nm=True) | Q(certifications__name__icontains='PEB Design',  certifications__is_uploaded_by_nm=True),gender='female', placement_status=False)
  
- "Female engineering candidates in Coimbatore who are currently working"
  → CandidateProfile.objects.filter(gender='female', college__type__icontains='engineering', permanent_address_district__icontains='Coimbatore', placement_status=True)
  
- "எனக்கு சென்னையிலிருந்து பெண்கள் தேவை"
  → CandidateProfile.objects.filter(Q(permanent_address_district__icontains='Chennai'), gender='female', placement_status=False)

- "எனக்கு சென்னை மற்றும் செங்கல்பட்டில் இருந்து ஐடிஐ மாணவர்கள் வேண்டும்"
  → CandidateProfile.objects.filter(Q(permanent_address_district__icontains='Chennai') | Q(permanent_address_district__icontains='Chengalpattu'), college__type__icontains='iti', placement_status=False)

- "எனக்கு சென்னை மற்றும் செங்கல்பட்டில் இருந்து பாலிடெக்னிக் விண்ணப்பதாரர் தேவை"    
  → CandidateProfile.objects.filter(Q(permanent_address_district__icontains='Chennai') | Q(permanent_address_district__icontains='Chengalpattu'), college__type__icontains='polytechnic', gender='female', placement_status=False)

- "எனக்கு ஈரோட்டில் இருந்து இன்ஜினியரிங் விண்ணப்பதாரர் தேவை"
  → CandidateProfile.objects.filter(gender='female', college__type__icontains='engineering', permanent_address_district__icontains='Erode', placement_status=False)

- I need Candidate who have certifications from industry 4.0
  → CandidateProfile.objects.filter(Q(certifications__name__icontains='industry 4.0',  certifications__is_uploaded_by_nm=True) | Q(certifications__name__icontains='iot',  certifications__is_uploaded_by_nm=True) | Q(certifications__name__icontains='machine learning',  certifications__is_uploaded_by_nm=True))
 
 - I need male candidates in Coimbatore region who has studied industry 4.0 and passed out in 2024 and 2025 candidates
  → CandidateProfile.objects.filter(Q(certifications__name__icontains='industry 4.0',  certifications__is_uploaded_by_nm=True) | Q(certifications__name__icontains='iot',  certifications__is_uploaded_by_nm=True) | Q(certifications__name__icontains='machine learning',  certifications__is_uploaded_by_nm=True),Q(year_of_passout__icontains='2024') | Q(year_of_passout__icontains='2025'),   gender='male',permanent_address_district__icontains='Coimbatore',placement_status=False)
  
- I need freshers from chennai who have done generative ai skills
  → CandidateProfile.objects.filter(certifications__name__icontains='generative ai', certifications__is_uploaded_by_nm=True, permanent_address_district__icontains='chennai', placement_status=False)
  
- I need experienced candidates who has skill on generative ai
  → CandidateProfile.objects.filter(certifications__name__icontains='generative ai', certifications__is_uploaded_by_nm=True, placement_status=True)
  
- I need Female working professionals with python and gen ai skills from chennai and karur
  → CandidateProfile.objects.filter(Q(permanent_address_district__icontains='chennai') | Q(permanent_address_district__icontains='karur'),  Q(certifications__name__icontains='python',  certifications__is_uploaded_by_nm=True) |  Q(certifications__name__icontains='generative ai',  certifications__is_uploaded_by_nm=True), gender='female',placement_status=True)
  
- I Need experienced candidates with iot skills
  → CandidateProfile.objects.filter(certifications__name__icontains='iot', certifications__is_uploaded_by_nm=True, placement_status=True)
QUERY:
"{user_query}"

"""

    async def run_chat():
        raw = await model.chat(messages=[{"role": "user", "content": prompt}])
        return re.sub(
            r"^```(?:python)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE
        ).strip()

    return asyncio.run(run_chat())
