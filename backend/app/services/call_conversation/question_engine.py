from __future__ import annotations

from dataclasses import dataclass

LANGUAGE_ALIASES = {
    "en": "english",
    "english": "english",
    "hi": "hindi",
    "hindi": "hindi",
    "gu": "gujarati",
    "gujarati": "gujarati",
}

LANGUAGE_SELECTION_GREETING = "\n\n".join(
    [
        "Hello, I am from RG Opti Matrix Solutions.\nWhich language would you prefer for communication?",
        "नमस्ते, मैं RG Opti Matrix Solutions से बोल रहा हूँ।\nआप किस भाषा में बात करना पसंद करेंगे?",
        "નમસ્તે, હું RG Opti Matrix Solutions માંથી બોલું છું.\nતમે કઈ ભાષામાં વાતચીત કરવા માંગો છો?",
    ]
)

SERVICE_OPTIONS = [
    "Website Development",
    "Mobile App Development",
    "Custom Software",
    "ERP",
    "CRM",
    "AI Calling Agent",
    "AI Chatbot",
    "Digital Marketing",
    "SEO",
    "Other",
]


@dataclass(frozen=True)
class Question:
    key: str
    text: str
    phase: str


PROFILE_QUESTIONS = [
    Question("full_name", "May I know your full name?", "profile"),
    Question("company_name", "What is your company name?", "profile"),
    Question("email", "What is your email address?", "profile"),
    Question("city", "Which city are you based in?", "profile"),
    Question("state", "Which state are you based in?", "profile"),
    Question("country", "Which country are you based in?", "profile"),
    Question("business_category", "What is your business category?", "profile"),
    Question("years_in_business", "How many years have you been in business?", "profile"),
    Question("website", "Do you currently have a website?", "profile"),
    Question("budget", "What budget range have you planned?", "profile"),
    Question("timeline", "What timeline are you targeting?", "profile"),
    Question(
        "preferred_contact_method",
        "What is your preferred contact method?",
        "profile",
    ),
]

SERVICE_SELECTION_QUESTION = Question(
    "service_type",
    "Which service are you looking for?\n" + "\n".join(f"- {option}" for option in SERVICE_OPTIONS),
    "service_selection",
)

SERVICE_QUESTIONS: dict[str, list[Question]] = {
    "website_development": [
        Question("website_type", "What type of website do you need?", "service"),
        Question("website_pages", "Which pages or sections should it include?", "service"),
        Question("website_features", "What features do you need on the website?", "service"),
        Question("website_content_ready", "Is your content, logo, and branding ready?", "service"),
        Question("website_reference", "Do you have reference websites you like?", "service"),
    ],
    "mobile_app_development": [
        Question("app_platforms", "Do you need Android, iOS, or both?", "service"),
        Question("app_user_roles", "Who will use the app and what roles are needed?", "service"),
        Question("app_core_features", "What are the core app features?", "service"),
        Question("app_backend", "Do you need an admin panel or backend system?", "service"),
        Question("app_integrations", "Which payment, map, OTP, or third-party integrations are needed?", "service"),
    ],
    "custom_software": [
        Question("software_problem", "What business problem should the software solve?", "service"),
        Question("software_users", "Which teams or users will use it?", "service"),
        Question("software_workflows", "Which workflows should be automated?", "service"),
        Question("software_reports", "What reports or dashboards are required?", "service"),
        Question("software_integrations", "Which existing tools should it integrate with?", "service"),
    ],
    "erp": [
        Question("erp_modules", "Which ERP modules do you need?", "service"),
        Question("erp_departments", "Which departments will use the ERP?", "service"),
        Question("erp_existing_system", "Are you replacing or integrating with an existing system?", "service"),
        Question("erp_reporting", "What reports and approvals are required?", "service"),
        Question("erp_users", "How many users will use the ERP?", "service"),
    ],
    "crm": [
        Question("crm_sales_process", "What is your current sales or lead process?", "service"),
        Question("crm_pipeline", "What pipeline stages do you need?", "service"),
        Question("crm_automation", "Which follow-ups or automations are required?", "service"),
        Question("crm_integrations", "Which channels should connect to the CRM?", "service"),
        Question("crm_users", "How many team members will use the CRM?", "service"),
    ],
    "ai_calling_agent": [
        Question("ai_calling_use_case", "What should the AI calling agent handle?", "service"),
        Question("ai_calling_volume", "How many calls per day do you expect?", "service"),
        Question("ai_calling_languages", "Which languages should the agent support?", "service"),
        Question("ai_calling_integrations", "Which CRM, calendar, or phone systems should connect?", "service"),
        Question("ai_calling_handoff", "When should the AI hand over to a human?", "service"),
    ],
    "ai_chatbot": [
        Question("chatbot_channels", "Where should the chatbot run?", "service"),
        Question("chatbot_use_case", "What should the chatbot answer or automate?", "service"),
        Question("chatbot_knowledge", "What knowledge base or documents should it use?", "service"),
        Question("chatbot_languages", "Which languages should it support?", "service"),
        Question("chatbot_handoff", "How should it hand over to your team?", "service"),
    ],
    "digital_marketing": [
        Question("marketing_goals", "What are your marketing goals?", "service"),
        Question("marketing_channels", "Which channels do you want to use?", "service"),
        Question("marketing_audience", "Who is your target audience?", "service"),
        Question("marketing_location", "Which locations should campaigns target?", "service"),
        Question("marketing_assets", "Do you already have creatives, landing pages, or ad accounts?", "service"),
    ],
    "seo": [
        Question("seo_website", "Which website should we optimize?", "service"),
        Question("seo_keywords", "Which keywords or services should you rank for?", "service"),
        Question("seo_locations", "Which target locations matter for SEO?", "service"),
        Question("seo_competitors", "Who are your main competitors?", "service"),
        Question("seo_current_status", "Have you done SEO before?", "service"),
    ],
    "other": [
        Question("other_requirement", "Please describe the service or solution you need.", "service"),
        Question("other_goal", "What outcome are you expecting?", "service"),
        Question("other_users", "Who will use or benefit from it?", "service"),
    ],
}

SERVICE_ALIASES = {
    "website": "website_development",
    "website development": "website_development",
    "mobile app": "mobile_app_development",
    "mobile app development": "mobile_app_development",
    "app": "mobile_app_development",
    "custom software": "custom_software",
    "software": "custom_software",
    "erp": "erp",
    "crm": "crm",
    "ai calling agent": "ai_calling_agent",
    "calling agent": "ai_calling_agent",
    "ai agent": "ai_calling_agent",
    "ai chatbot": "ai_chatbot",
    "chatbot": "ai_chatbot",
    "digital marketing": "digital_marketing",
    "marketing": "digital_marketing",
    "seo": "seo",
    "other": "other",
}


def normalize_language(language: str) -> str:
    return LANGUAGE_ALIASES.get(language.strip().lower(), "english")


def normalize_service_type(service: str) -> str:
    cleaned = service.strip().lower().replace("-", " ").replace("_", " ")
    if cleaned in SERVICE_ALIASES:
        return SERVICE_ALIASES[cleaned]
    for alias, key in SERVICE_ALIASES.items():
        if alias in cleaned:
            return key
    return "other"


def service_label(service_key: str | None) -> str | None:
    if not service_key:
        return None
    for option in SERVICE_OPTIONS:
        if normalize_service_type(option) == service_key:
            return option
    return service_key.replace("_", " ").title()


def questions_for_service(service_key: str | None) -> list[Question]:
    return SERVICE_QUESTIONS.get(service_key or "other", SERVICE_QUESTIONS["other"])


def base_questions() -> list[Question]:
    return [*PROFILE_QUESTIONS, SERVICE_SELECTION_QUESTION]


def questions_for(service_key: str | None = None) -> list[Question]:
    questions = base_questions()
    if service_key:
        questions.extend(questions_for_service(service_key))
    return questions


def question_at(index: int, service_key: str | None = None) -> Question | None:
    questions = questions_for(service_key)
    if 0 <= index < len(questions):
        return questions[index]
    return None
