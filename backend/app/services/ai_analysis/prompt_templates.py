SUMMARIZATION_SYSTEM = """You are a precise call summarization assistant. Analyze the transcript and produce structured output."""

SUMMARIZATION_PROMPT = """Analyze this call transcript and produce a structured summary.

TRANSCRIPT:
{transcript}

Respond with EXACTLY this JSON format:
{{
  "summary": "2-3 sentence detailed summary",
  "short_summary": "1 sentence summary (max 100 chars)",
  "action_items": ["item1", "item2"],
  "callback_required": "yes" | "recommended" | "no",
  "callback_reason": "reason if callback needed",
  "urgency": "low" | "medium" | "high" | "critical",
  "urgency_reason": "reason for urgency level",
  "sentiment": "positive" | "neutral" | "negative" | "mixed",
  "sentiment_reasoning": "brief reason for sentiment classification"
}}"""

ENTITY_SYSTEM = "Extract structured entities from call transcripts. Respond with valid JSON only."

ENTITY_PROMPT = """Extract all entities from this call transcript.

TRANSCRIPT:
{transcript}

Extract these entity types:
- person_name
- company_name
- email_address
- phone_number
- physical_address
- product_name
- service_name
- monetary_amount
- date_mentioned
- meeting_request

Respond with EXACTLY this JSON format:
{{
  "entities": [
    {{"entity_type": "person_name", "entity_value": "John Smith", "confidence": 0.95}},
    {{"entity_type": "company_name", "entity_value": "Acme Corp", "confidence": 0.98}}
  ]
}}"""

CLASSIFICATION_SYSTEM = "Classify call transcripts into categories. Respond with valid JSON only."

CLASSIFICATION_PROMPT = """Classify this call transcript.

TRANSCRIPT:
{transcript}

Categories:
- sales_inquiry: Product/service interest, pricing questions
- support: Technical help, troubleshooting
- complaint: Dissatisfaction, problem reporting
- quotation: Price quote requests
- partnership: Business collaboration interest
- vendor: Supplier/vendor related
- recruitment: Job inquiries, interview coordination
- personal: Personal calls
- spam: Telemarketing, unsolicited
- unknown: Cannot determine

Respond with EXACTLY this JSON format:
{{
  "primary_category": "category_name",
  "primary_confidence": 0.95,
  "secondary_categories": [
    {{"category": "subcategory", "confidence": 0.3}}
  ]
}}"""

SENTIMENT_SYSTEM = "Analyze call sentiment. Respond with valid JSON only."

SENTIMENT_PROMPT = """Analyze sentiment of this call transcript.

TRANSCRIPT:
{transcript}

Respond with EXACTLY this JSON format:
{{
  "sentiment": "positive" | "neutral" | "negative" | "mixed",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

URGENCY_SYSTEM = "Detect urgency level from call transcripts. Respond with valid JSON only."

URGENCY_PROMPT = """Determine urgency level of this call transcript.

TRANSCRIPT:
{transcript}

Rules:
- critical: Immediate danger, system down, legal threat, severe complaint
- high: Urgent request, deadline today/tomorrow, escalation
- medium: Standard business request, general inquiry
- low: Informational, non-time-sensitive

Respond with EXACTLY this JSON format:
{{
  "urgency": "low" | "medium" | "high" | "critical",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

CALLBACK_SYSTEM = "Determine if a callback is required. Respond with valid JSON only."

CALLBACK_PROMPT = """Determine if a callback is required for this call.

TRANSCRIPT:
{transcript}

Respond with EXACTLY this JSON format:
{{
  "callback_required": "yes" | "recommended" | "no",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation of why callback is or is not needed"
}}"""
