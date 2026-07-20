from __future__ import annotations

import re
from dataclasses import dataclass


ROLE_FAMILIES: tuple[str, ...] = (
    "Data & Analytics",
    "Software Engineering",
    "AI & Machine Learning",
    "Cloud & Platform",
    "Database",
    "IT & Security",
    "Technology Consulting",
    "Other Technology",
)


@dataclass(frozen=True)
class RoleDefinition:
    role_name: str
    role_family: str
    patterns: tuple[str, ...]


@dataclass(frozen=True)
class RoleClassification:
    role_name: str
    role_family: str


@dataclass(frozen=True)
class TechnologySkill:
    skill: str
    category: str
    patterns: tuple[str, ...]
    role_families: tuple[str, ...]
    target_roles: tuple[str, ...]
    market_signal: tuple[int, int, int, str]


ROLE_DEFINITIONS: tuple[RoleDefinition, ...] = (
    RoleDefinition("AI/ML Consultant", "Technology Consulting", (r"\b(ai|ml|machine learning|artificial intelligence)(?:\s+\w+){0,2}\s+consultant\b",)),
    RoleDefinition("Data Consultant", "Technology Consulting", (r"\b(data|analytics|business intelligence|bi)(?:\s+\w+){0,2}\s+consultant\b",)),
    RoleDefinition("Cloud Consultant", "Technology Consulting", (r"\b(cloud|devops|platform)(?:\s+\w+){0,2}\s+consultant\b",)),
    RoleDefinition("Technology Consultant", "Technology Consulting", (r"\b(it|technology|technical|software|digital|solutions?) consultant\b",)),
    RoleDefinition("MLOps Engineer", "AI & Machine Learning", (r"\bmlops\b", r"\bmachine learning platform engineer\b")),
    RoleDefinition("Machine Learning Engineer", "AI & Machine Learning", (r"\bmachine learning engineer\b", r"\bml engineer\b")),
    RoleDefinition("AI Engineer", "AI & Machine Learning", (r"\b(ai|artificial intelligence|generative ai|genai|llm) engineer\b",)),
    RoleDefinition("NLP Engineer", "AI & Machine Learning", (r"\b(nlp|natural language processing) engineer\b",)),
    RoleDefinition("Computer Vision Engineer", "AI & Machine Learning", (r"\b(computer vision|vision) engineer\b",)),
    RoleDefinition("Applied Scientist", "AI & Machine Learning", (r"\b(applied|research) scientist\b",)),
    RoleDefinition("Data Scientist", "AI & Machine Learning", (r"\bdata scientist\b",)),
    RoleDefinition("Analytics Engineer", "Data & Analytics", (r"\banalytics engineer\b", r"\bbi engineer\b")),
    RoleDefinition("Data Engineer", "Data & Analytics", (r"\b(data|etl|warehouse|big data) engineer\b", r"\bdata platform engineer\b")),
    RoleDefinition("BI Developer", "Data & Analytics", (r"\b(bi|business intelligence) developer\b",)),
    RoleDefinition("BI Analyst", "Data & Analytics", (r"\b(bi|business intelligence) analyst\b",)),
    RoleDefinition("Data Analyst", "Data & Analytics", (r"\b(data|product|reporting|analytics)(?:\s+\w+){0,2}\s+analyst\b", r"\b(marketing analytics|data visualization|bi analytics|data governance) (manager|lead|specialist)\b")),
    RoleDefinition("Data Architect", "Data & Analytics", (r"\b(data|analytics) architect\b",)),
    RoleDefinition("Database Reliability Engineer", "Database", (r"\bdatabase reliability engineer\b", r"\bdre\b")),
    RoleDefinition("Database Administrator", "Database", (r"\bdatabase administrator\b", r"\bdba\b")),
    RoleDefinition("Database Engineer", "Database", (r"\bdatabase (engineer|developer)\b", r"\bsql developer\b")),
    RoleDefinition("Site Reliability Engineer", "Cloud & Platform", (r"\bsite reliability engineer\b", r"\bsre\b")),
    RoleDefinition("DevOps Engineer", "Cloud & Platform", (r"\bdevops\b", r"\bdevsecops\b")),
    RoleDefinition("Cloud Engineer", "Cloud & Platform", (r"\bcloud (engineer|developer)\b",)),
    RoleDefinition("Cloud Architect", "Cloud & Platform", (r"\bcloud architect\b",)),
    RoleDefinition("Platform Engineer", "Cloud & Platform", (r"\bplatform engineer\b", r"\binfrastructure engineer\b")),
    RoleDefinition("Systems Engineer", "Cloud & Platform", (r"\bsystems? engineer\b",)),
    RoleDefinition("Security Engineer", "IT & Security", (r"\b(cybersecurity|cyber security|security) engineer\b",)),
    RoleDefinition("Security Analyst", "IT & Security", (r"\b(cybersecurity|cyber security|security|soc) analyst\b",)),
    RoleDefinition("Network Engineer", "IT & Security", (r"\bnetwork (engineer|administrator)\b",)),
    RoleDefinition("Systems Administrator", "IT & Security", (r"\bsystems? administrator\b", r"\bsysadmin\b")),
    RoleDefinition("IT Support Engineer", "IT & Security", (r"\b(it|technical|application|desktop) support (engineer|specialist|analyst)\b", r"\bhelp desk\b")),
    RoleDefinition("QA Automation Engineer", "Software Engineering", (r"\b(qa|quality assurance|test automation|software test) (engineer|developer)\b", r"\bsdet\b")),
    RoleDefinition("Frontend Engineer", "Software Engineering", (r"\b(front[ -]?end|ui) (engineer|developer)\b",)),
    RoleDefinition("Backend Engineer", "Software Engineering", (r"\b(back[ -]?end|server[ -]?side) (engineer|developer)\b",)),
    RoleDefinition("Full Stack Engineer", "Software Engineering", (r"\bfull[ -]?stack (engineer|developer)\b",)),
    RoleDefinition("Mobile Engineer", "Software Engineering", (r"\b(mobile|android|ios) (engineer|developer)\b",)),
    RoleDefinition("Software Architect", "Software Engineering", (r"\b(software|solution) architect\b",)),
    RoleDefinition("Software Engineer", "Software Engineering", (r"\bsoftware (engineer|developer)\b", r"\bapplication developer\b", r"\bprogrammer\b")),
)


def _skill(
    name: str,
    category: str,
    patterns: tuple[str, ...],
    families: tuple[str, ...],
    roles: tuple[str, ...],
    signal: tuple[int, int, int, str],
) -> TechnologySkill:
    return TechnologySkill(name, category, patterns, families, roles, signal)


SOFTWARE = ("Software Engineering",)
PLATFORM = ("Cloud & Platform",)
AI_ML = ("AI & Machine Learning",)
DATABASE = ("Database",)
IT_SECURITY = ("IT & Security",)
CONSULTING = ("Technology Consulting",)


TECHNOLOGY_SKILLS: tuple[TechnologySkill, ...] = (
    _skill("Java", "Programming", (r"\bjava\b",), SOFTWARE + PLATFORM, ("Backend Engineer", "Software Engineer"), (55, 65, 65, "Stable")),
    _skill("JavaScript", "Programming", (r"\bjavascript\b", r"\becmascript\b"), SOFTWARE, ("Frontend Engineer", "Full Stack Engineer"), (60, 60, 75, "Stable")),
    _skill("TypeScript", "Programming", (r"\btypescript\b",), SOFTWARE, ("Frontend Engineer", "Full Stack Engineer"), (70, 65, 55, "Growing")),
    _skill("C#", "Programming", (r"\bcsharp\b",), SOFTWARE, (".NET Developer", "Backend Engineer"), (55, 65, 55, "Stable")),
    _skill("C++", "Programming", (r"\bcpp\b",), SOFTWARE + AI_ML, ("Systems Engineer", "Computer Vision Engineer"), (50, 70, 50, "Stable")),
    _skill("Go", "Programming", (r"\bgolang\b", r"\bgo language\b"), SOFTWARE + PLATFORM, ("Backend Engineer", "Platform Engineer"), (70, 70, 40, "Growing")),
    _skill("Rust", "Programming", (r"\brust\b",), SOFTWARE + PLATFORM, ("Systems Engineer", "Platform Engineer"), (65, 70, 35, "Growing")),
    _skill("PHP", "Programming", (r"\bphp\b",), SOFTWARE, ("Backend Engineer", "Full Stack Engineer"), (35, 45, 65, "Stable")),
    _skill("Ruby", "Programming", (r"\bruby\b", r"\bruby on rails\b"), SOFTWARE, ("Backend Engineer", "Full Stack Engineer"), (35, 50, 55, "Stable")),
    _skill("Kotlin", "Programming", (r"\bkotlin\b",), SOFTWARE, ("Android Developer", "Backend Engineer"), (55, 60, 40, "Growing")),
    _skill("Swift", "Programming", (r"\bswift\b", r"\bswiftui\b"), SOFTWARE, ("iOS Developer", "Mobile Engineer"), (50, 60, 40, "Stable")),
    _skill("HTML", "Web Engineering", (r"\bhtml5?\b",), SOFTWARE, ("Frontend Engineer", "Full Stack Engineer"), (35, 35, 85, "Basic requirement")),
    _skill("CSS", "Web Engineering", (r"\bcss3?\b", r"\btailwind css\b"), SOFTWARE, ("Frontend Engineer", "Full Stack Engineer"), (35, 35, 85, "Basic requirement")),
    _skill("React", "Web Engineering", (r"\breact(?:\.js|js)?\b",), SOFTWARE, ("Frontend Engineer", "Full Stack Engineer"), (65, 60, 65, "Growing")),
    _skill("Next.js", "Web Engineering", (r"\bnext\.js\b", r"\bnextjs\b"), SOFTWARE, ("Frontend Engineer", "Full Stack Engineer"), (70, 65, 45, "Growing")),
    _skill("Node.js", "Web Engineering", (r"\bnode\.js\b", r"\bnodejs\b"), SOFTWARE, ("Backend Engineer", "Full Stack Engineer"), (60, 60, 65, "Stable")),
    _skill("Spring Boot", "Web Engineering", (r"\bspring boot\b",), SOFTWARE, ("Backend Engineer", "Software Engineer"), (55, 65, 50, "Stable")),
    _skill(".NET", "Web Engineering", (r"\b\.net\b", r"\bdotnet\b"), SOFTWARE, (".NET Developer", "Backend Engineer"), (55, 65, 55, "Stable")),
    _skill("Django", "Web Engineering", (r"\bdjango\b",), SOFTWARE, ("Backend Engineer", "Full Stack Engineer"), (50, 55, 50, "Stable")),
    _skill("Flask", "Web Engineering", (r"\bflask\b",), SOFTWARE, ("Backend Engineer", "Python Developer"), (45, 50, 55, "Stable")),
    _skill("GraphQL", "Web Engineering", (r"\bgraphql\b",), SOFTWARE, ("Backend Engineer", "Full Stack Engineer"), (55, 60, 40, "Growing")),
    _skill("Microservices", "Software Architecture", (r"\bmicroservices?\b",), SOFTWARE + PLATFORM, ("Software Architect", "Backend Engineer"), (65, 70, 55, "Growing")),
    _skill("MongoDB", "Database", (r"\bmongodb\b",), DATABASE + SOFTWARE, ("Database Engineer", "Backend Engineer"), (50, 55, 55, "Stable")),
    _skill("Redis", "Database", (r"\bredis\b",), DATABASE + SOFTWARE, ("Database Engineer", "Backend Engineer"), (55, 60, 45, "Growing")),
    _skill("Oracle Database", "Database", (r"\boracle database\b", r"\boracle db\b"), DATABASE, ("Database Administrator", "Database Engineer"), (45, 65, 55, "Stable")),
    _skill("PL/SQL", "Database", (r"\bpl\s*sql\b",), DATABASE, ("Database Administrator", "SQL Developer"), (40, 55, 55, "Stable")),
    _skill("Cassandra", "Database", (r"\bcassandra\b",), DATABASE + ("Data & Analytics",), ("Database Engineer", "Data Engineer"), (45, 60, 40, "Stable")),
    _skill("Database Administration", "Database", (r"\bdatabase administration\b", r"\bdatabase performance tuning\b"), DATABASE, ("Database Administrator", "Database Reliability Engineer"), (55, 65, 45, "Stable")),
    _skill("Kubernetes", "Cloud & Platform", (r"\bkubernetes\b", r"\bk8s\b"), PLATFORM + AI_ML, ("Platform Engineer", "DevOps Engineer", "MLOps Engineer"), (75, 75, 50, "Growing")),
    _skill("Terraform", "Cloud & Platform", (r"\bterraform\b",), PLATFORM, ("Cloud Engineer", "DevOps Engineer"), (75, 70, 45, "Growing")),
    _skill("CI/CD", "Cloud & Platform", (r"\bci\s*cd\b", r"\bcontinuous integration\b", r"\bcontinuous delivery\b"), PLATFORM + SOFTWARE, ("DevOps Engineer", "Software Engineer"), (60, 60, 70, "Basic requirement")),
    _skill("Linux", "IT & Security", (r"\blinux\b",), PLATFORM + IT_SECURITY, ("Systems Administrator", "Platform Engineer"), (55, 55, 75, "Basic requirement")),
    _skill("Bash", "IT & Security", (r"\bbash\b", r"\bshell scripting\b"), PLATFORM + IT_SECURITY, ("Systems Administrator", "DevOps Engineer"), (45, 50, 65, "Basic requirement")),
    _skill("Jenkins", "Cloud & Platform", (r"\bjenkins\b",), PLATFORM, ("DevOps Engineer", "Platform Engineer"), (40, 50, 60, "Stable")),
    _skill("GitHub Actions", "Cloud & Platform", (r"\bgithub actions\b",), PLATFORM + SOFTWARE, ("DevOps Engineer", "Software Engineer"), (65, 55, 50, "Growing")),
    _skill("Helm", "Cloud & Platform", (r"\bhelm\b", r"\bhelm charts?\b"), PLATFORM, ("Platform Engineer", "DevOps Engineer"), (60, 60, 40, "Growing")),
    _skill("Ansible", "Cloud & Platform", (r"\bansible\b",), PLATFORM + IT_SECURITY, ("DevOps Engineer", "Systems Administrator"), (45, 55, 50, "Stable")),
    _skill("Kafka", "Distributed Systems", (r"\bkafka\b", r"\bapache kafka\b"), ("Data & Analytics",) + SOFTWARE + PLATFORM, ("Data Engineer", "Backend Engineer", "Platform Engineer"), (65, 70, 50, "Growing")),
    _skill("BigQuery", "Database", (r"\bbigquery\b",), ("Data & Analytics",) + DATABASE, ("Cloud Data Engineer", "Analytics Engineer"), (60, 65, 40, "Growing")),
    _skill("Redshift", "Database", (r"\bredshift\b", r"\bamazon redshift\b"), ("Data & Analytics",) + DATABASE, ("Cloud Data Engineer", "Database Engineer"), (50, 60, 45, "Stable")),
    _skill("MLOps", "Machine Learning", (r"\bmlops\b", r"\bml operations\b"), AI_ML + PLATFORM, ("MLOps Engineer", "ML Engineer"), (80, 80, 35, "Growing")),
    _skill("MLflow", "Machine Learning", (r"\bmlflow\b",), AI_ML, ("MLOps Engineer", "ML Engineer"), (65, 65, 35, "Growing")),
    _skill("Hugging Face", "Machine Learning", (r"\bhugging face\b", r"\bhuggingface\b"), AI_ML, ("AI Engineer", "NLP Engineer"), (75, 70, 35, "Growing")),
    _skill("Computer Vision", "Machine Learning", (r"\bcomputer vision\b", r"\bimage recognition\b"), AI_ML, ("Computer Vision Engineer", "ML Engineer"), (65, 75, 40, "Growing")),
    _skill("OpenCV", "Machine Learning", (r"\bopencv\b",), AI_ML, ("Computer Vision Engineer", "ML Engineer"), (50, 60, 45, "Stable")),
    _skill("RAG", "Machine Learning", (r"\bretrieval augmented generation\b", r"\brag\b"), AI_ML, ("AI Engineer", "LLM Engineer"), (85, 75, 25, "Growing")),
    _skill("Prompt Engineering", "Machine Learning", (r"\bprompt engineering\b", r"\bprompt design\b"), AI_ML + CONSULTING, ("AI Engineer", "AI/ML Consultant"), (70, 60, 45, "Growing")),
    _skill("LangChain", "Machine Learning", (r"\blangchain\b",), AI_ML, ("AI Engineer", "LLM Engineer"), (65, 60, 40, "Growing")),
    _skill("Cybersecurity", "IT & Security", (r"\bcybersecurity\b", r"\bcyber security\b", r"\binformation security\b"), IT_SECURITY, ("Security Analyst", "Security Engineer"), (70, 70, 55, "Growing")),
    _skill("IAM", "IT & Security", (r"\bidentity and access management\b", r"\biam\b"), IT_SECURITY + PLATFORM, ("Security Engineer", "IAM Engineer"), (65, 70, 40, "Growing")),
    _skill("SIEM", "IT & Security", (r"\bsiem\b", r"\bsecurity information and event management\b"), IT_SECURITY, ("Security Analyst", "SOC Analyst"), (60, 65, 40, "Growing")),
    _skill("Networking", "IT & Security", (r"\bcomputer networking\b", r"\bnetwork engineering\b"), IT_SECURITY + PLATFORM, ("Network Engineer", "Systems Administrator"), (45, 55, 65, "Stable")),
    _skill("TCP/IP", "IT & Security", (r"\btcp\s*ip\b",), IT_SECURITY, ("Network Engineer", "Systems Administrator"), (35, 45, 75, "Basic requirement")),
    _skill("Active Directory", "IT & Security", (r"\bactive directory\b", r"\bmicrosoft entra id\b"), IT_SECURITY, ("Systems Administrator", "IAM Engineer"), (45, 50, 60, "Stable")),
    _skill("Windows Server", "IT & Security", (r"\bwindows server\b",), IT_SECURITY, ("Systems Administrator", "IT Support Engineer"), (40, 50, 60, "Stable")),
    _skill("ServiceNow", "IT & Security", (r"\bservicenow\b",), IT_SECURITY + CONSULTING, ("IT Support Analyst", "ServiceNow Consultant"), (55, 60, 45, "Growing")),
    _skill("ITIL", "Technology Consulting", (r"\bitil\b", r"\bit service management\b"), CONSULTING + IT_SECURITY, ("Technology Consultant", "IT Service Manager"), (45, 50, 55, "Stable")),
    _skill("Selenium", "Software Testing", (r"\bselenium\b",), SOFTWARE, ("QA Automation Engineer", "SDET"), (45, 50, 55, "Stable")),
    _skill("Playwright", "Software Testing", (r"\bplaywright\b",), SOFTWARE, ("QA Automation Engineer", "Frontend Engineer"), (65, 55, 35, "Growing")),
    _skill("Test Automation", "Software Testing", (r"\btest automation\b", r"\bautomated testing\b"), SOFTWARE, ("QA Automation Engineer", "SDET"), (55, 55, 55, "Stable")),
    _skill("pytest", "Software Testing", (r"\bpytest\b",), SOFTWARE + ("Data & Analytics",) + AI_ML, ("Python Developer", "Data Engineer", "ML Engineer"), (45, 45, 55, "Stable")),
    _skill("Prometheus", "Observability", (r"\bprometheus\b",), PLATFORM, ("Site Reliability Engineer", "Platform Engineer"), (60, 65, 40, "Growing")),
    _skill("Grafana", "Observability", (r"\bgrafana\b",), PLATFORM + IT_SECURITY, ("Site Reliability Engineer", "Platform Engineer"), (60, 60, 45, "Growing")),
    _skill("Requirements Analysis", "Technology Consulting", (r"\brequirements analysis\b", r"\brequirements gathering\b"), CONSULTING, ("Technology Consultant", "Business Systems Analyst"), (45, 55, 60, "Stable")),
    _skill("Stakeholder Management", "Technology Consulting", (r"\bstakeholder management\b", r"\bstakeholder engagement\b"), CONSULTING, ("Technology Consultant", "Data Consultant"), (50, 60, 60, "Stable")),
    _skill("Solution Architecture", "Software Architecture", (r"\bsolution architecture\b", r"\bsolutions architect\b"), CONSULTING + PLATFORM + SOFTWARE, ("Solutions Architect", "Cloud Architect"), (65, 75, 40, "Growing")),
    _skill("Agile", "Delivery", (r"\bagile\b",), CONSULTING + SOFTWARE, ("Technology Consultant", "Software Engineer"), (35, 40, 80, "Basic requirement")),
    _skill("Scrum", "Delivery", (r"\bscrum\b",), CONSULTING + SOFTWARE, ("Scrum Master", "Technology Consultant"), (35, 40, 75, "Basic requirement")),
)


TECHNOLOGY_JOB_SEARCH_TERMS: tuple[str, ...] = (
    "data engineer",
    "software engineer",
    "machine learning engineer",
    "cloud devops engineer",
    "database administrator",
    "technology consultant",
    "cybersecurity engineer",
)


def classify_role(title: str) -> RoleClassification:
    normalized = _normalize_role_text(title)
    for definition in ROLE_DEFINITIONS:
        if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in definition.patterns):
            return RoleClassification(definition.role_name, definition.role_family)
    if any(term in normalized for term in ("developer", "engineer", "programmer")):
        return RoleClassification("Software Engineer", "Software Engineering")
    if any(term in normalized for term in ("it ", "technology", "technical", "systems", "application")):
        return RoleClassification("Other IT Role", "Other Technology")
    return RoleClassification("Other Technology Role", "Other Technology")


def role_family_for_role(role_name: str) -> str:
    return classify_role(role_name).role_family


def technology_skill(skill: str) -> TechnologySkill | None:
    return next((item for item in TECHNOLOGY_SKILLS if item.skill == skill), None)


def technology_skill_role_families(skill: str) -> tuple[str, ...]:
    definition = technology_skill(skill)
    return definition.role_families if definition else ()


def technology_skill_target_roles(skill: str) -> tuple[str, ...]:
    definition = technology_skill(skill)
    return definition.target_roles if definition else ()


def _normalize_role_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).replace("_", " ").replace("-", " ")).strip().lower()

