"""
Jenan BIZ - AI Service (OpenAI Integration)
Cost-efficient: uses the cheapest suitable model per task.

Tasks:
  1. analyze_cr_document()  - PDF -> pypdf text -> gpt-4o-mini (text, fast+cheap)
                              Image -> gpt-4o vision
  2. generate_bs_summary()  - gpt-4o-mini, Arabic narrative summary
"""

from __future__ import annotations

import base64
import json
from typing import Any

from loguru import logger


def _get_client():
    """Return a configured AsyncOpenAI client."""
    from openai import AsyncOpenAI
    from app.config import get_settings
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


CR_SYSTEM_PROMPT = """You are a financial analyst specializing in Saudi commercial registrations.
Extract the following fields from the CR document text/image:
- company_name: Name of the company/establishment in Arabic
- registration_number: CR number (10 digits)
- issue_date: Issue date in YYYY-MM-DD format
- entity_type: One of the following Arabic strings exactly:
    "mua-ssasa fardiya" = use "mua-ssasa fardiya" style? NO - use Arabic:
    Choose from: مؤسسة فردية | شركة ذات مسؤولية محدودة | شركة مساهمة | شركة تضامنية | فرع شركة أجنبية
- activity: Main business activity description in Arabic

Reply with JSON only, no extra text. Example:
{
  "company_name": "مؤسسة النجاح للتجارة",
  "registration_number": "1234567890",
  "issue_date": "2020-03-15",
  "entity_type": "مؤسسة فردية",
  "activity": "تجارة التجزئة"
}
If you cannot read a field, use empty string "".
"""


def _extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF using pypdf (max 4 pages, 3000 chars)."""
    try:
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(file_bytes))
        texts = []
        for i, page in enumerate(reader.pages):
            if i >= 4:
                break
            t = page.extract_text() or ""
            texts.append(t)
        full = "\n".join(texts)
        return full[:3000]
    except Exception as e:
        logger.warning(f"PDF text extraction failed: {e}")
        return ""


async def analyze_cr_document(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """
    AI OCR for CR documents.
    PDF files   -> text extraction via pypdf -> gpt-4o-mini (cheap)
    Image files -> base64 data url           -> gpt-4o vision
    Returns dict: company_name, registration_number, issue_date, entity_type, activity
    """
    from app.config import get_settings
    settings = get_settings()

    if not settings.OPENAI_ENABLED or not settings.OPENAI_API_KEY:
        logger.warning("OpenAI disabled -- skipping CR analysis")
        return {}

    raw = ""
    try:
        fname_lower = filename.lower()
        is_pdf = fname_lower.endswith(".pdf")
        client = _get_client()

        if is_pdf:
            pdf_text = _extract_pdf_text(file_bytes)
            if pdf_text.strip():
                logger.info(f"PDF text extracted: {len(pdf_text)} chars -- sending to gpt-4o-mini")
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=400,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": CR_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Extract CR data from this text:\n\n{pdf_text}"},
                    ],
                )
                raw = (response.choices[0].message.content or "").strip()
                raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                data = json.loads(raw)
                logger.info(f"CR PDF analysis OK: {data.get('company_name', '?')}")
                return data
            else:
                logger.warning("PDF text extraction empty -- cannot process this file")
                return {}

        # Image path: base64 -> gpt-4o vision
        if fname_lower.endswith(".png"):
            media_type = "image/png"
        elif fname_lower.endswith(".webp"):
            media_type = "image/webp"
        else:
            media_type = "image/jpeg"

        b64 = base64.b64encode(file_bytes).decode()
        data_url = f"data:{media_type};base64,{b64}"

        response = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=400,
            temperature=0,
            messages=[
                {"role": "system", "content": CR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract CR data from this image:"},
                        {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                    ],
                },
            ],
        )
        raw = (response.choices[0].message.content or "").strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        logger.info(f"CR Image analysis OK: {data.get('company_name', '?')}")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"CR AI JSON parse error: {e} -- raw: {raw[:200]}")
        return {}
    except Exception as e:
        logger.error(f"CR AI analysis failed: {e}")
        return {}


BS_SYSTEM_PROMPT = """You are a financial consultant for the Jenan BIZ platform.
Based on the bank statement analysis results provided, write a professional Arabic summary (4-6 lines):
- Start with a sentence about the company's overall financial status
- Mention key numbers (monthly revenue, profit ratio, POS if present)
- Note any risk factors or strengths
- End with a brief recommendation (eligible / needs review / not eligible)
Reply in Arabic only, professional direct style, no headings or bullet points."""


async def summarize_supplementary_docs(doc_names: list[str], company_name: str = "") -> str:
    """
    AI-generated Arabic summary of the supplementary documents uploaded.
    Uses gpt-4o-mini.
    """
    from app.config import get_settings
    settings = get_settings()
    if not settings.OPENAI_ENABLED or not settings.OPENAI_API_KEY:
        return ""
    try:
        client = _get_client()
        docs_list = "\n".join(f"- {n}" for n in doc_names)
        prompt = (
            f"المنشأة: {company_name or 'غير محدد'}\n"
            f"المستندات المرفوعة:\n{docs_list}\n\n"
            "اكتب ملخصاً احترافياً بالعربية (3–4 سطور) يصف ما تم رفعه من مستندات ومدى اكتمالها والخطوة التالية. "
            "لا تذكر أسماء الملفات التقنية."
        )
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            temperature=0.3,
            messages=[
                {"role": "system", "content": "أنت محلل مالي متخصص في ملفات التمويل."},
                {"role": "user", "content": prompt},
            ],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning(f"summarize_supplementary_docs failed: {e}")
        return ""


async def generate_bs_summary(analysis_data: dict[str, Any]) -> str:
    """
    Use gpt-4o-mini to generate a human-readable Arabic summary
    from the structured bank statement analysis result dict.
    """
    from app.config import get_settings
    settings = get_settings()

    if not settings.OPENAI_ENABLED or not settings.OPENAI_API_KEY:
        logger.warning("OpenAI disabled -- skipping BS summary")
        return ""

    try:
        flags_text = ""
        for f in analysis_data.get("risk_flags", [])[:5]:
            flags_text += f"\n  - [{f.get('level', '?')}] {f.get('title_ar', '')}: {f.get('detail_ar', '')}"

        user_msg = (
            f"Analysis results:\n"
            f"- Total revenue: {analysis_data.get('total_credits', 0):,.0f} SAR"
            f" over {analysis_data.get('months_covered', 0)} months\n"
            f"- Avg monthly revenue: {analysis_data.get('avg_monthly_credit', 0):,.0f} SAR\n"
            f"- POS: {analysis_data.get('pos_total', 0):,.0f} SAR"
            f" ({analysis_data.get('pos_percentage', 0):.1f}%)\n"
            f"- Net profit ratio: {analysis_data.get('profit_ratio', 0) * 100:.1f}%\n"
            f"- Returned cheques: {analysis_data.get('returned_cheques_count', 0)}\n"
            f"- Confidence score: {analysis_data.get('confidence_score', 0) * 100:.0f}%\n"
            f"- Eligible: {'Yes' if analysis_data.get('is_eligible') else 'No'}\n"
            f"- Matched entity: {analysis_data.get('matched_entity') or 'None'}\n"
            f"- Risk flags:{flags_text if flags_text else ' None'}\n"
            f"- Rejection reasons: {', '.join(analysis_data.get('rejection_reasons', [])) or 'None'}"
        )

        client = _get_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=350,
            temperature=0.3,
            messages=[
                {"role": "system", "content": BS_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )

        summary = (response.choices[0].message.content or "").strip()
        logger.info("BS AI summary generated successfully")
        return summary

    except Exception as e:
        logger.error(f"BS AI summary failed: {e}")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# 3. PDF Bank Statement AI Analyzer — gpt-4o-mini
#    Extracts structured financial data from a scanned/text-based PDF statement.
#    Returns a dict compatible with AnalysisResult fields so the rule engine
#    can evaluate it exactly like an Excel-parsed result.
# ─────────────────────────────────────────────────────────────────────────────

BS_EXTRACTION_PROMPT = """You are a financial data extraction expert specializing in Saudi bank statements.

Extract the following financial data from the bank statement text provided.
Return ONLY valid JSON with these exact keys. Use 0 for missing values.

Required JSON structure:
{
  "total_credits": <sum of all deposits/credits in SAR>,
  "total_debits": <sum of all withdrawals/debits in SAR>,
  "pos_total": <sum of POS/point-of-sale transactions in SAR (look for: POS, نقاط البيع, مدى, MADA, Visa, Mastercard merchant payments)>,
  "returned_cheques_count": <number of returned/bounced cheques>,
  "months_covered": <number of months in the statement>,
  "avg_monthly_credit": <average monthly credits (total_credits / months_covered)>,
  "max_monthly_drop_pct": <max revenue drop between consecutive months as decimal e.g. 0.25 = 25%>,
  "profit_ratio": <(total_credits - total_debits) / total_credits as decimal, 0 if no credits>,
  "date_range_start": "<earliest transaction date in YYYY-MM-DD>",
  "date_range_end": "<latest transaction date in YYYY-MM-DD>",
  "monthly": [
    {"year": <int>, "month": <int>, "total_credit": <float>, "total_debit": <float>, "pos_credit": <float>, "returned_cheques": <int>}
  ],
  "confidence": <0.0-1.0, how confident you are in the extraction quality>
}

Important rules:
- Include ALL months found in the statement in "monthly" array
- For POS: only count merchant POS sales inflows (not ATM withdrawals)
- Internal bank transfers between own accounts should be noted but ideally excluded from revenue
- All amounts in SAR
- If a value cannot be determined reliably, use 0"""


async def analyze_bs_pdf(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """
    Use GPT-4o-mini to extract structured financial data from a PDF bank statement.
    
    Returns a dict with AnalysisResult-compatible fields:
      total_credits, total_debits, pos_total, returned_cheques_count,
      months_covered, avg_monthly_credit, max_monthly_drop_pct,
      profit_ratio, monthly (list), confidence_score
    
    Returns empty dict on failure.
    """
    from app.config import get_settings
    settings = get_settings()

    if not settings.OPENAI_ENABLED or not settings.OPENAI_API_KEY:
        logger.warning("OpenAI disabled -- skipping BS PDF analysis")
        return {}

    # Extract text from PDF
    pdf_text = _extract_pdf_text(file_bytes)
    if not pdf_text.strip():
        logger.warning(f"PDF text extraction returned empty for BS file: {filename}")
        return {}

    logger.info(f"BS PDF text extracted: {len(pdf_text)} chars from {filename}")

    raw = ""
    try:
        client = _get_client()

        # If text is very long, try to fit within token budget (~12k chars)
        text_snippet = pdf_text[:12000]

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1500,
            temperature=0,
            messages=[
                {"role": "system", "content": BS_EXTRACTION_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Extract financial data from this Saudi bank statement:\n\n"
                        f"```\n{text_snippet}\n```"
                    ),
                },
            ],
        )

        raw = (response.choices[0].message.content or "").strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)

        # Normalize and return in AnalysisResult-compatible format
        total_credits = float(data.get("total_credits") or 0)
        total_debits = float(data.get("total_debits") or 0)
        months = int(data.get("months_covered") or 1)
        pos_total = float(data.get("pos_total") or 0)

        result = {
            "total_credits": total_credits,
            "total_debits": total_debits,
            "net_revenue": total_credits - total_debits,
            "avg_monthly_credit": float(data.get("avg_monthly_credit") or (total_credits / months if months else 0)),
            "avg_monthly_debit": total_debits / months if months else 0,
            "pos_total": pos_total,
            "pos_percentage": (pos_total / total_credits * 100) if total_credits > 0 else 0.0,
            "returned_cheques_count": int(data.get("returned_cheques_count") or 0),
            "bounced_percentage": 0.0,
            "months_covered": months,
            "date_range_start": str(data.get("date_range_start") or ""),
            "date_range_end": str(data.get("date_range_end") or ""),
            "total_transactions": 0,
            "max_monthly_drop_pct": float(data.get("max_monthly_drop_pct") or 0),
            "profit_ratio": float(data.get("profit_ratio") or (
                (total_credits - total_debits) / total_credits if total_credits > 0 else 0
            )),
            "salary_transfers_total": 0.0,
            "loan_payments_total": 0.0,
            "confidence_score": float(data.get("confidence") or 0.7),
            "issues": [],
            "risk_flags": [],
            "monthly": [
                {
                    "year": int(m.get("year", 0)),
                    "month": int(m.get("month", 0)),
                    "total_credit": float(m.get("total_credit", 0)),
                    "total_debit": float(m.get("total_debit", 0)),
                    "pos_credit": float(m.get("pos_credit", 0)),
                    "returned_cheques": int(m.get("returned_cheques", 0)),
                }
                for m in (data.get("monthly") or [])
            ],
            "pdf_source": True,
        }

        logger.info(
            f"BS PDF AI analysis OK: credits={total_credits:,.0f}, "
            f"months={months}, POS={pos_total:,.0f}, confidence={result['confidence_score']:.0%}"
        )
        return result

    except json.JSONDecodeError as e:
        logger.error(f"BS PDF AI JSON parse error: {e} -- raw: {raw[:300]}")
        return {}
    except Exception as e:
        logger.error(f"BS PDF AI analysis failed: {e}")
        return {}
