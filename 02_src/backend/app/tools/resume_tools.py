"""
Wasel — Resume Tools
parse_resume · extract_skills · score_resume
Uses heuristic parsing + Saudi job market skill taxonomy.
"""
import io, re, logging
from typing import Dict, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Saudi tech market skill taxonomy ─────────────────────────
SKILLS_TAXONOMY = {
    "programming":  ["python","javascript","typescript","java","c++","c#","go","rust","ruby","php","kotlin","swift","r","sql","scala"],
    "data_ai":      ["machine learning","deep learning","nlp","arabic nlp","computer vision","pytorch","tensorflow","keras","scikit-learn","pandas","numpy","spark","hadoop","airflow","dbt","mlflow","hugging face","langchain","rag","vector database","llm","generative ai","data science","data analysis","data engineering","feature engineering","kubeflow","mlops"],
    "cloud_devops": ["aws","azure","gcp","google cloud","docker","kubernetes","terraform","ansible","ci/cd","jenkins","github actions","helm","serverless","prometheus","grafana","linux","bash"],
    "databases":    ["postgresql","mysql","mongodb","redis","elasticsearch","cassandra","dynamodb","sqlite","supabase","pinecone","chroma","faiss","pgvector","snowflake","delta lake","kafka","oracle","sql server"],
    "web":          ["react","vue","angular","node.js","fastapi","django","flask","express","graphql","rest apis","html","css","tailwind","next.js","redux","webpack","jest","typescript","swagger"],
    "mobile":       ["swift","swiftui","xcode","uikit","core data","android sdk","kotlin","jetpack compose","mvvm","firebase","testflight"],
    "security":     ["siem","network security","penetration testing","iso 27001","osint","soc","zero trust","endpoint security","firewall","splunk","incident response","threat intelligence"],
    "project":      ["pmp","agile","scrum","jira","confluence","risk management","ms project","prince2","safe","kanban","stakeholder management","okrs"],
    "design":       ["figma","adobe xd","user research","prototyping","design systems","usability testing","information architecture"],
    "sap":          ["sap s/4hana","sap fico","sap sd","sap erp","abap","sap sd"],
    "blockchain":   ["solidity","ethereum","web3.js","hyperledger","smart contracts"],
    "networking":   ["ccna","cisco","bgp","mpls","switching","routing"],
    "embedded":     ["c","c++","rtos","embedded linux","iot","can bus","arm","firmware development"],
    "bi":           ["power bi","tableau","excel","google analytics","statistics"],
}
ALL_SKILLS = list({s for skills in SKILLS_TAXONOMY.values() for s in skills})


def parse_resume(file_bytes: bytes, filename: str) -> Dict:
    """Extract raw text and structure from a PDF or DOCX file."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        raw = _pdf_text(file_bytes)
    elif ext in (".docx", ".doc"):
        raw = _docx_text(file_bytes)
    else:
        raw = file_bytes.decode("utf-8", errors="ignore")

    if not raw.strip():
        return {"error": "Could not extract text from file", "raw_text": ""}

    profile = _parse_profile(raw)
    profile["raw_text"] = raw
    return profile


def _pdf_text(b: bytes) -> str:
    try:
        import fitz
        doc = fitz.open(stream=b, filetype="pdf")
        text = "\n".join(p.get_text() for p in doc)
        doc.close()
        return text
    except Exception as e:
        logger.error(f"PDF error: {e}")
        return ""


def _docx_text(b: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(b))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        logger.error(f"DOCX error: {e}")
        return ""


def _parse_profile(text: str) -> Dict:
    profile = {
        "name": "", "email": "", "phone": "", "location": "",
        "summary": "", "skills": [], "experience": [],
        "education": [], "certifications": [], "languages": [],
    }
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Email
    em = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text, re.I)
    if em: profile["email"] = em.group(0)

    # Phone
    ph = re.search(r"(\+?\d[\d\s\-().]{7,15}\d)", text)
    if ph: profile["phone"] = ph.group(0).strip()

    # Name — first non-email, non-digit line
    for l in lines[:5]:
        if not re.search(r"[@\d]", l) and len(l) > 2:
            profile["name"] = l; break

    profile["skills"] = extract_skills(text)

    # Simple section detection
    headers = {
        "experience":    ["experience","work history","employment","career"],
        "education":     ["education","academic","qualification","degree"],
        "certifications":["certification","certificate","license","credential"],
        "summary":       ["summary","profile","about","objective","overview"],
    }
    cur, buf = None, []
    for line in lines:
        ll = line.lower()
        matched = next((s for s, kws in headers.items() if any(k in ll for k in kws) and len(ll) < 40), None)
        if matched:
            if cur and buf: _assign(profile, cur, buf)
            cur, buf = matched, []
        elif cur:
            buf.append(line)
    if cur and buf: _assign(profile, cur, buf)
    return profile


def _assign(profile: Dict, section: str, lines: List[str]):
    text = " ".join(lines)
    if section == "summary":           profile["summary"] = text[:500]
    elif section == "experience":      profile["experience"] = [{"text": " ".join(lines[:10])}]
    elif section == "education":       profile["education"] = [{"text": " ".join(lines[:5])}]
    elif section == "certifications":  profile["certifications"] = [l for l in lines if len(l) > 3][:10]


def extract_skills(text: str) -> List[str]:
    """Extract skills from text using the Saudi market taxonomy."""
    tl = text.lower()
    found = []
    for skill in ALL_SKILLS:
        pat = (r"\b" + re.escape(skill) + r"\b") if len(skill) <= 4 else re.escape(skill)
        if re.search(pat, tl):
            found.append(skill)
    return list(dict.fromkeys(found))


def score_resume(profile: Dict) -> Tuple[float, Dict, List[str]]:
    """Score resume quality 0-100. Returns (score, breakdown, suggestions)."""
    bd, sugg = {}, []

    # Contact (15)
    c = sum([bool(profile.get("email"))*5, bool(profile.get("phone"))*5, bool(profile.get("name"))*5])
    bd["contact"] = c
    if c < 15: sugg.append("Add complete contact info: name, email, and phone.")

    # Summary (15)
    s = profile.get("summary","")
    if len(s) > 100:     bd["summary"] = 15
    elif len(s) > 30:    bd["summary"] = 8;  sugg.append("Expand your summary to 3-5 sentences.")
    else:                bd["summary"] = 0;  sugg.append("Add a professional summary highlighting your value.")

    # Skills (25)
    sk = len(profile.get("skills",[]))
    bd["skills"] = min(25, sk * 2.5)
    if sk < 5:   sugg.append("List more technical skills relevant to Saudi tech roles.")
    elif sk < 10: sugg.append("Add more tools and technologies you have used.")

    # Experience (30)
    ex = len(profile.get("experience",[]))
    bd["experience"] = min(30, ex * 10)
    if not ex:  sugg.append("Add work experience with company, role, dates, and key achievements.")
    else:       sugg.append("Quantify achievements (e.g. 'Reduced API latency by 40%').")

    # Education (10)
    edu = len(profile.get("education",[]))
    bd["education"] = min(10, edu * 10)
    if not edu: sugg.append("Add your educational background.")

    # Certifications (5)
    bd["certifications"] = min(5, len(profile.get("certifications",[])) * 2.5)

    return round(sum(bd.values()), 1), bd, sugg
