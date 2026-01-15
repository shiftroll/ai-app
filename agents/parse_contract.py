"""
Crafta Contract Parser Agent

Parses PDF/DOCX contracts and extracts structured terms including:
- Rate cards
- Milestone payments
- Fixed fees
- Payment terms
- Penalty/discount clauses

Uses OCR (Tesseract) as fallback and LLM for clause extraction.
Outputs Contract JSON with confidence scores per clause.
"""

import json
import os
import re
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import logging

# Document processing
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# LLM
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExtractedClause:
    """Represents a single extracted clause"""
    clause_id: str
    type: str
    description: str
    extracted_text: str
    value: str
    unit: str
    confidence: float
    requires_cfo_approval: bool = False
    rev_rec_treatment: Optional[str] = None


@dataclass
class ParsedContract:
    """Represents a fully parsed contract"""
    contract_id: str
    source_filename: str
    uploaded_by: str
    upload_time: datetime
    parties: List[Dict[str, str]]
    currency: str
    terms: List[ExtractedClause]
    raw_text: str
    parse_version: str
    status: str
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    payment_terms_days: int = 30


class ContractParser:
    """
    Main contract parsing engine.

    Supports:
    - PDF text extraction
    - DOCX text extraction
    - OCR fallback for scanned documents
    - LLM-powered clause extraction
    - Regex-based extraction for simple patterns
    """

    PARSE_VERSION = "v0.1"

    # Regex patterns for common contract terms
    PATTERNS = {
        "rate_card": [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per|\/)\s*(hour|day|week|month)',
            r'rate\s+(?:of|is)\s+\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per|\/)\s*(hour|day)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|dollars?)\s*(?:per|\/)\s*(hour|day)',
        ],
        "milestone_payment": [
            r'(?:upon|on)\s+(?:completion|acceptance|delivery)\s+(?:of\s+)?(.+?)\s*[,:]?\s*(?:client\s+)?(?:pays?|payment\s+of)\s+\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'deliverable\s+(\w+)\s*[-:]?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'milestone\s+(\d+|[A-Z])\s*[-:]?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ],
        "fixed_fee": [
            r'(?:fixed|flat)\s+fee\s+(?:of\s+)?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'total\s+(?:contract\s+)?(?:value|amount)\s*(?:of|is|:)?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ],
        "payment_terms": [
            r'(?:payment|net)\s+(?:terms?\s+)?(?:of\s+)?(\d+)\s*(?:days?|calendar\s+days?)',
            r'due\s+(?:within\s+)?(\d+)\s*(?:days?|calendar\s+days?)',
            r'net\s*(\d+)',
        ],
        "penalty": [
            r'(?:late|penalty)\s+(?:fee|charge)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*%',
            r'interest\s+(?:rate\s+)?(?:of\s+)?(\d+(?:\.\d+)?)\s*%\s*(?:per\s+)?(month|annum|year)',
        ],
        "discount": [
            r'(?:early\s+payment\s+)?discount\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s+discount',
        ],
    }

    # LLM prompt for clause extraction
    LLM_EXTRACTION_PROMPT = """
You are a contract analysis expert. Extract billing-relevant clauses from the following contract text.

For each clause found, provide:
1. type: One of [rate_card, milestone_payment, fixed_fee, recurring_fee, payment_terms, penalty, discount, rev_rec, other]
2. description: Brief human-readable description
3. extracted_text: The exact text from the contract
4. value: The numeric value (just the number)
5. unit: The unit type (hour, day, fixed, percent, etc.)
6. confidence: Your confidence in the extraction (0.0 to 1.0)
7. requires_cfo_approval: true if this involves revenue recognition complexity (multi-element, % completion)
8. rev_rec_treatment: If applicable, note the revenue recognition treatment

Contract text:
---
{contract_text}
---

Respond with a JSON array of extracted clauses. If no relevant clauses are found, return an empty array.
Example format:
[
  {{
    "type": "rate_card",
    "description": "Consulting rate of $200/hour",
    "extracted_text": "The consultant rate shall be $200 per hour...",
    "value": "200",
    "unit": "hour",
    "confidence": 0.95,
    "requires_cfo_approval": false,
    "rev_rec_treatment": null
  }}
]
"""

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the parser with optional OpenAI API key"""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        if self.openai_api_key and OPENAI_AVAILABLE:
            self.openai_client = OpenAI(api_key=self.openai_api_key)

    def parse(
        self,
        file_path: str,
        uploaded_by: str,
        contract_id: Optional[str] = None,
        use_llm: bool = True,
    ) -> ParsedContract:
        """
        Parse a contract file and extract structured terms.

        Args:
            file_path: Path to PDF or DOCX file
            uploaded_by: User ID who uploaded
            contract_id: Optional contract ID (generated if not provided)
            use_llm: Whether to use LLM for extraction (falls back to regex)

        Returns:
            ParsedContract with extracted terms and confidence scores
        """
        logger.info(f"Parsing contract: {file_path}")

        # Generate contract ID if not provided
        if not contract_id:
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            hash_suffix = hashlib.md5(file_path.encode()).hexdigest()[:6]
            contract_id = f"ctr_{timestamp}_{hash_suffix}"

        # Extract raw text
        raw_text = self._extract_text(file_path)
        if not raw_text or len(raw_text.strip()) < 50:
            logger.warning("Insufficient text extracted, trying OCR")
            raw_text = self._extract_text_ocr(file_path)

        # Extract parties (basic extraction)
        parties = self._extract_parties(raw_text)

        # Detect currency
        currency = self._detect_currency(raw_text)

        # Extract clauses
        if use_llm and self.openai_client:
            clauses = self._extract_clauses_llm(raw_text)
        else:
            clauses = self._extract_clauses_regex(raw_text)

        # Extract dates and payment terms
        effective_date = self._extract_date(raw_text, "effective")
        expiration_date = self._extract_date(raw_text, "expiration")
        payment_terms = self._extract_payment_terms_days(raw_text)

        return ParsedContract(
            contract_id=contract_id,
            source_filename=os.path.basename(file_path),
            uploaded_by=uploaded_by,
            upload_time=datetime.utcnow(),
            parties=parties,
            currency=currency,
            terms=clauses,
            raw_text=raw_text,
            parse_version=self.PARSE_VERSION,
            status="parsed" if clauses else "needs_review",
            effective_date=effective_date,
            expiration_date=expiration_date,
            payment_terms_days=payment_terms,
        )

    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF or DOCX"""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return self._extract_text_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return self._extract_text_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _extract_text_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        if not PdfReader:
            raise ImportError("PyPDF2 not installed")

        text_parts = []
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")

        return "\n".join(text_parts)

    def _extract_text_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        if not Document:
            raise ImportError("python-docx not installed")

        try:
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            return ""

    def _extract_text_ocr(self, file_path: str) -> str:
        """Extract text using OCR (for scanned documents)"""
        if not OCR_AVAILABLE:
            logger.warning("OCR not available")
            return ""

        try:
            images = convert_from_path(file_path)
            text_parts = []
            for image in images:
                text = pytesseract.image_to_string(image)
                text_parts.append(text)
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return ""

    def _extract_clauses_llm(self, raw_text: str) -> List[ExtractedClause]:
        """Extract clauses using LLM"""
        if not self.openai_client:
            return self._extract_clauses_regex(raw_text)

        # Truncate text if too long
        max_chars = 15000
        text_for_llm = raw_text[:max_chars] if len(raw_text) > max_chars else raw_text

        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "gpt-4-turbo-preview"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a contract analysis expert. Extract billing clauses accurately."
                    },
                    {
                        "role": "user",
                        "content": self.LLM_EXTRACTION_PROMPT.format(contract_text=text_for_llm)
                    }
                ],
                temperature=0.1,
                max_tokens=4000,
            )

            content = response.choices[0].message.content
            # Parse JSON from response
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                clauses_data = json.loads(json_match.group())
                clauses = []
                for i, c in enumerate(clauses_data):
                    clauses.append(ExtractedClause(
                        clause_id=f"c{i+1}",
                        type=c.get("type", "other"),
                        description=c.get("description", ""),
                        extracted_text=c.get("extracted_text", ""),
                        value=str(c.get("value", "")),
                        unit=c.get("unit", ""),
                        confidence=float(c.get("confidence", 0.5)),
                        requires_cfo_approval=c.get("requires_cfo_approval", False),
                        rev_rec_treatment=c.get("rev_rec_treatment"),
                    ))
                return clauses

        except Exception as e:
            logger.error(f"LLM extraction error: {e}")

        # Fallback to regex
        return self._extract_clauses_regex(raw_text)

    def _extract_clauses_regex(self, raw_text: str) -> List[ExtractedClause]:
        """Extract clauses using regex patterns"""
        clauses = []
        clause_count = 0
        text_lower = raw_text.lower()

        for clause_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    clause_count += 1
                    groups = match.groups()

                    # Extract value and unit based on pattern
                    if clause_type in ["rate_card"]:
                        value = groups[0].replace(",", "") if groups else ""
                        unit = groups[1] if len(groups) > 1 else "unit"
                    elif clause_type in ["milestone_payment"]:
                        value = groups[-1].replace(",", "") if groups else ""
                        unit = "fixed"
                    elif clause_type in ["fixed_fee"]:
                        value = groups[0].replace(",", "") if groups else ""
                        unit = "fixed"
                    elif clause_type in ["payment_terms"]:
                        value = groups[0] if groups else "30"
                        unit = "days"
                    elif clause_type in ["penalty", "discount"]:
                        value = groups[0] if groups else ""
                        unit = "percent"
                    else:
                        value = groups[0] if groups else ""
                        unit = "unit"

                    # Get surrounding text for context
                    start = max(0, match.start() - 50)
                    end = min(len(raw_text), match.end() + 50)
                    extracted_text = raw_text[start:end].strip()

                    clauses.append(ExtractedClause(
                        clause_id=f"c{clause_count}",
                        type=clause_type,
                        description=f"Extracted {clause_type}: {value} {unit}",
                        extracted_text=extracted_text,
                        value=value,
                        unit=unit,
                        confidence=0.75,  # Regex matches have lower confidence
                    ))

        return clauses

    def _extract_parties(self, raw_text: str) -> List[Dict[str, str]]:
        """Extract contract parties"""
        parties = []

        # Common patterns for party identification
        vendor_patterns = [
            r'(?:vendor|provider|contractor|consultant)[:\s]+([A-Z][A-Za-z\s&,]+(?:LLC|Inc|Corp|Ltd)?)',
            r'(?:by and between|between)\s+([A-Z][A-Za-z\s&,]+(?:LLC|Inc|Corp|Ltd)?)',
        ]

        client_patterns = [
            r'(?:client|customer|company)[:\s]+([A-Z][A-Za-z\s&,]+(?:LLC|Inc|Corp|Ltd)?)',
            r'(?:and|with)\s+([A-Z][A-Za-z\s&,]+(?:LLC|Inc|Corp|Ltd)?)\s+(?:\(|,|\.)',
        ]

        for pattern in vendor_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()[:100]
                parties.append({
                    "role": "vendor",
                    "name": name,
                    "identifier": self._generate_identifier(name)
                })
                break

        for pattern in client_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()[:100]
                parties.append({
                    "role": "client",
                    "name": name,
                    "identifier": self._generate_identifier(name)
                })
                break

        return parties

    def _generate_identifier(self, name: str) -> str:
        """Generate a short identifier from a name"""
        # Take first letters of words + hash suffix
        words = re.findall(r'\b[A-Z][a-z]*', name)
        prefix = "".join(w[0] for w in words[:4]).upper()
        suffix = hashlib.md5(name.encode()).hexdigest()[:3].upper()
        return f"{prefix}-{suffix}"

    def _detect_currency(self, raw_text: str) -> str:
        """Detect contract currency"""
        currency_patterns = {
            "USD": [r'\$', r'USD', r'US\s*dollars?', r'United States Dollars?'],
            "EUR": [r'€', r'EUR', r'euros?'],
            "GBP": [r'£', r'GBP', r'pounds?\s*sterling'],
            "IDR": [r'Rp\.?', r'IDR', r'rupiah'],
        }

        counts = {curr: 0 for curr in currency_patterns}
        for currency, patterns in currency_patterns.items():
            for pattern in patterns:
                counts[currency] += len(re.findall(pattern, raw_text, re.IGNORECASE))

        # Return most common, default to USD
        if max(counts.values()) > 0:
            return max(counts, key=counts.get)
        return "USD"

    def _extract_date(self, raw_text: str, date_type: str) -> Optional[datetime]:
        """Extract effective or expiration date"""
        patterns = {
            "effective": [
                r'effective\s+(?:date|as\s+of)[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'commencing\s+(?:on\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            ],
            "expiration": [
                r'(?:expir|terminat)\w*\s+(?:date|on)[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'valid\s+(?:until|through)[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            ],
        }

        for pattern in patterns.get(date_type, []):
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                try:
                    from dateutil.parser import parse as parse_date
                    return parse_date(match.group(1))
                except Exception:
                    pass
        return None

    def _extract_payment_terms_days(self, raw_text: str) -> int:
        """Extract payment terms in days"""
        patterns = [
            r'(?:payment|net)\s+(?:terms?\s+)?(?:of\s+)?(\d+)\s*(?:days?|calendar)',
            r'net\s*(\d+)',
            r'due\s+(?:within\s+)?(\d+)\s*days?',
        ]

        for pattern in patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        return 30  # Default

    def to_dict(self, parsed: ParsedContract) -> Dict[str, Any]:
        """Convert ParsedContract to dictionary"""
        return {
            "contract_id": parsed.contract_id,
            "source_filename": parsed.source_filename,
            "uploaded_by": parsed.uploaded_by,
            "upload_time": parsed.upload_time.isoformat(),
            "parties": parsed.parties,
            "currency": parsed.currency,
            "terms": [
                {
                    "clause_id": c.clause_id,
                    "type": c.type,
                    "description": c.description,
                    "extracted_text": c.extracted_text,
                    "value": c.value,
                    "unit": c.unit,
                    "confidence": c.confidence,
                    "requires_cfo_approval": c.requires_cfo_approval,
                    "rev_rec_treatment": c.rev_rec_treatment,
                }
                for c in parsed.terms
            ],
            "raw_text": parsed.raw_text[:1000] + "..." if len(parsed.raw_text) > 1000 else parsed.raw_text,
            "parse_version": parsed.parse_version,
            "status": parsed.status,
            "effective_date": parsed.effective_date.isoformat() if parsed.effective_date else None,
            "expiration_date": parsed.expiration_date.isoformat() if parsed.expiration_date else None,
            "payment_terms_days": parsed.payment_terms_days,
        }


def parse_contract_file(
    file_path: str,
    uploaded_by: str,
    contract_id: Optional[str] = None,
    use_llm: bool = True,
    openai_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main entry point for contract parsing.

    Args:
        file_path: Path to contract file (PDF or DOCX)
        uploaded_by: User ID who uploaded
        contract_id: Optional contract ID
        use_llm: Whether to use LLM (default True)
        openai_api_key: Optional OpenAI API key

    Returns:
        Dictionary with parsed contract data
    """
    parser = ContractParser(openai_api_key=openai_api_key)
    parsed = parser.parse(file_path, uploaded_by, contract_id, use_llm)
    return parser.to_dict(parsed)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parse_contract.py <file_path> [user_id]")
        sys.exit(1)

    file_path = sys.argv[1]
    user_id = sys.argv[2] if len(sys.argv) > 2 else "u:test@example.com"

    result = parse_contract_file(file_path, user_id)
    print(json.dumps(result, indent=2))
