import re
import threading

MODEL_NAME = "all-MiniLM-L6-v2"
MAX_CHARS = 20_000          # input cap, protects CPU
MAX_CHUNKS = 40

# Raw cosine similarity between related texts sits around 0.15 to 0.65.
# Scale that range to 0-100. Tune these two numbers after testing (see notes).
SIM_LOW, SIM_HIGH = 0.15, 0.65

# ---------- Skills list: name → aliases (lowercase) ----------
SKILLS = {
    # languages
    "Python": ["python"], "Java": ["java"], "JavaScript": ["javascript", "js", "ecmascript"],
    "TypeScript": ["typescript"], "C++": ["c++"], "C#": ["c#"], "Go": ["golang"],
    "PHP": ["php"], "Ruby": ["ruby"], "Kotlin": ["kotlin"],
    "SQL": ["sql", "t-sql", "pl/sql"], "HTML": ["html", "html5"], "CSS": ["css", "css3"],
    # frameworks
    "Django": ["django"], "Django REST Framework": ["django rest framework", "drf"],
    "Flask": ["flask"], "FastAPI": ["fastapi"], "Spring Boot": ["spring boot", "springboot", "spring framework"],
    "Node.js": ["node.js", "nodejs"], "Express.js": ["express.js", "expressjs"],
    "React": ["react", "reactjs", "react.js"], "Angular": ["angular", "angularjs"],
    "Vue.js": ["vue", "vue.js", "vuejs"], "Next.js": ["next.js", "nextjs"],
    ".NET": [".net", "dotnet", "asp.net"], "Laravel": ["laravel"],
    # APIs and architecture
    "REST APIs": ["rest api", "rest apis", "restful", "restful api", "restful apis"],
    "GraphQL": ["graphql"], "Microservices": ["microservice", "microservices"],
    "Celery": ["celery"], "RabbitMQ": ["rabbitmq"], "Kafka": ["kafka"], "JWT": ["jwt"],
    # databases
    "MySQL": ["mysql"], "PostgreSQL": ["postgresql", "postgres"], "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"], "SQLite": ["sqlite"], "Oracle": ["oracle"],
    "SQL Server": ["sql server", "mssql"], "Elasticsearch": ["elasticsearch"],
    # cloud and devops
    "AWS": ["aws", "amazon web services"], "Azure": ["azure"], "GCP": ["gcp", "google cloud"],
    "Docker": ["docker"], "Kubernetes": ["kubernetes", "k8s"],
    "CI/CD": ["ci/cd", "cicd", "ci cd", "continuous integration"],
    "Git": ["git", "github", "gitlab", "bitbucket"], "Jenkins": ["jenkins"],
    "Linux": ["linux"], "Terraform": ["terraform"], "Nginx": ["nginx"],
    # data and ML
    "Pandas": ["pandas"], "NumPy": ["numpy"], "scikit-learn": ["scikit-learn", "sklearn"],
    "TensorFlow": ["tensorflow"], "PyTorch": ["pytorch"], "Machine Learning": ["machine learning"],
    "NLP": ["nlp", "natural language processing"], "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"], "Excel": ["ms excel", "microsoft excel", "advanced excel"],
    # engineering basics
    "OOP": ["oop", "oops", "object-oriented", "object oriented"],
    "Data Structures": ["data structures", "dsa"], "Algorithms": ["algorithms"],
    "System Design": ["system design"],
    "Unit Testing": ["unit testing", "unit tests", "pytest", "unittest", "junit"],
    "Agile": ["agile", "scrum"], "Selenium": ["selenium"],
}

# "java" must not match inside "javascript", and "sql" must not match inside "mysql".
_BEFORE = r"(?<![A-Za-z0-9+#.])"
_AFTER = r"(?![A-Za-z0-9+#])"


def _build_patterns():
    patterns = {}
    for name, aliases in SKILLS.items():
        parts = "|".join(re.escape(a) for a in sorted(aliases, key=len, reverse=True))
        patterns[name] = re.compile(f"{_BEFORE}(?:{parts}){_AFTER}", re.IGNORECASE)
    return patterns


PATTERNS = _build_patterns()


def find_skills(text):
    """Skill names found in the text, in list order."""
    return [name for name, pattern in PATTERNS.items() if pattern.search(text)]


# ---------- Embedding model: loaded once, on first use ----------
_model = None
_lock = threading.Lock()


def get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                # Heavy import (PyTorch). Doing it here keeps Django startup fast.
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer(MODEL_NAME)
    return _model


def chunk_text(text, target_words=80):
    """The model reads only ~256 word pieces, so split long text into chunks."""
    pieces = [p.strip() for p in re.split(r"\n+|(?<=[.!?])\s+", text) if p.strip()]
    chunks, current, count = [], [], 0
    for piece in pieces:
        current.append(piece)
        count += len(piece.split())
        if count >= target_words:
            chunks.append(" ".join(current))
            current, count = [], 0
    if current:
        chunks.append(" ".join(current))
    return chunks[:MAX_CHUNKS]


def _to_percent(similarity):
    return max(0.0, min(1.0, (similarity - SIM_LOW) / (SIM_HIGH - SIM_LOW))) * 100


def _label(score):
    if score >= 75:
        return "Strong match"
    if score >= 55:
        return "Good match"
    if score >= 35:
        return "Partial match"
    return "Weak match"


def compute_match(jd_text, resume_text):
    jd_text = jd_text[:MAX_CHARS]
    resume_text = resume_text[:MAX_CHARS]

    # 1. Keyword check: free, no AI
    jd_skills = find_skills(jd_text)
    resume_skills = set(find_skills(resume_text))
    matched = [s for s in jd_skills if s in resume_skills]
    missing = [s for s in jd_skills if s not in resume_skills]
    skill_score = round(len(matched) * 100 / len(jd_skills), 1) if jd_skills else None

    # 2. Meaning check: embeddings
    jd_chunks = chunk_text(jd_text)
    resume_chunks = chunk_text(resume_text)
    raw = 0.0
    if jd_chunks and resume_chunks:
        from sentence_transformers import util
        model = get_model()
        jd_emb = model.encode(jd_chunks, convert_to_tensor=True,
                              normalize_embeddings=True, show_progress_bar=False)
        resume_emb = model.encode(resume_chunks, convert_to_tensor=True,
                                  normalize_embeddings=True, show_progress_bar=False)
        sims = util.cos_sim(jd_emb, resume_emb)          # rows = JD chunks, cols = resume chunks
        raw = float(sims.max(dim=1).values.mean())       # best resume chunk per JD chunk, averaged
    semantic_score = round(_to_percent(raw), 1)

    # 3. Blend. If the JD names no known skills, use meaning only.
    if skill_score is None:
        score = semantic_score
    else:
        score = round(0.6 * semantic_score + 0.4 * skill_score, 1)

    return {
        "score": score,
        "label": _label(score),
        "semantic_score": semantic_score,
        "skill_score": skill_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "raw_similarity": round(raw, 3),     # for tuning only
    }