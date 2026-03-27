"""
Jenan BIZ — Main FastAPI Application
─────────────────────────────────────
Entry point:  uvicorn app.main:app --reload

Features:
  ✓ CORS for Vue.js frontend
  ✓ Lifespan: create tables + seed demo data
  ✓ API router mounts (/api/...)
  ✓ Health check
  ✓ Structured logging
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.database import create_tables, async_session
from app.utils import setup_logger

# Import API routers
from app.api.auth import router as auth_router
from app.api.cases import router as cases_router
from app.api.users import router as users_router
from app.api.analysis import router as analysis_router
from app.api.entity_rules import router as entity_rules_router
from app.api.notifications import router as notifications_router
from app.api.contacts import router as contacts_router
from app.api.campaigns import router as campaigns_router

settings = get_settings()


# ─── Lifespan ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown events."""
    setup_logger()
    logger.info("Jenan BIZ Backend starting...")

    # Create tables (dev only — use Alembic in production)
    await create_tables()
    logger.info("Database tables ready")

    # Always clean up demo accounts first
    await _remove_demo_accounts()

    # Seed owner account + always sync entity rules
    if settings.SEED_DEMO_DATA:
        await _seed_demo_data()
    await _sync_entity_rules()

    yield

    logger.info("Jenan BIZ Backend shutting down")


async def _remove_demo_accounts():
    """Always delete legacy demo accounts and all their data on every startup."""
    from sqlalchemy import select, delete, update
    from app.models.user import User
    from app.models.case import Case
    from app.models.audit import AuditLog

    DEMO_PHONES = ["0500000001", "0500000002", "0500000003", "0500000004"]
    async with async_session() as db:
        for phone in DEMO_PHONES:
            user = (await db.execute(
                select(User).where(User.phone == phone)
            )).scalar_one_or_none()
            if not user:
                continue

            uid = user.id

            # 1) Delete cases owned by this partner (CASCADE removes stage_history,
            #    assignments, internal_notes, stage_approvals automatically)
            await db.execute(delete(Case).where(Case.partner_id == uid))

            # 2) Nullify assignments to this user in remaining cases
            await db.execute(
                update(Case).where(Case.assigned_to == uid).values(assigned_to=None)
            )

            # 3) Delete audit log entries (no ondelete on user_id FK)
            await db.execute(delete(AuditLog).where(AuditLog.user_id == uid))

            # 4) Delete the user (notifications cascade-delete via ondelete="CASCADE")
            await db.execute(delete(User).where(User.id == uid))

            logger.info(f"Removed demo account: {phone}")

        await db.commit()


async def _seed_demo_data():
    """Ensure the owner account exists (idempotent)."""
    from sqlalchemy import select
    from app.models.user import User, UserRole
    from app.core import hash_password

    async with async_session() as db:
        owner_exists = (await db.execute(
            select(User).where(User.phone == settings.OWNER_PHONE)
        )).scalar_one_or_none()

        if owner_exists:
            logger.info("Owner account already exists, skipping seed")
            return

        logger.info("Seeding owner account...")
        owner = User(
            name=settings.OWNER_NAME,
            phone=settings.OWNER_PHONE,
            password_hash=hash_password(settings.OWNER_PASSWORD),
            role=UserRole.owner,
        )
        db.add(owner)
        await db.commit()
        logger.info(f"Seeded owner account: {settings.OWNER_PHONE}")


async def _sync_entity_rules():
    """
    Always-run upsert of all entity rules per the canonical spec.
    Priority order: 1.الراجحي  2.إمكان  3.صندوق التنمية  4.أملاك  5.سهل
    """
    from sqlalchemy import select
    from app.models.entity_rule import EntityRule

    # ── Document lists ────────────────────────────────────────────────────

    rajhi_base_docs = [
        "صورة السجل التجاري",
        "صورة الهوية/الإقامة",
        "عقد التأسيس (إن كانت شركة)",
        "شهادة البلدية",
        "شهادة التوطين",
        "العنوان الوطني للمنشأة والملاك",
        "شهادة الآيبان بالباركود",
        "صور النشاط (داخل وخارج)",
        "موقع المنشأة Google Map",
        "كشف حساب Excel حسب مدة العمر المطلوبة",
    ]

    sdf_base_docs = [
        "صورة السجل التجاري",
        "صورة الهوية",
        "عقد التأسيس (إن كانت شركة)",
        "شهادة البلدية",
        "شهادة الزكاة والدخل",
        "شهادة القيمة المضافة",
        "شهادة التأمينات الاجتماعية",
        "العنوان الوطني",
        "شهادة الآيبان",
        "كشف حساب Excel حسب المدة المطلوبة",
        "الإقرارات الضريبية (6 ربع سنوي أو 15 شهري)",
        "القوائم المالية (داخلية للمؤسسة / معتمدة للشركة)",
    ]

    amlak_sahl_docs = [
        "صورة السجل التجاري",
        "صورة الهوية/الإقامة",
        "عقد التأسيس (إن كانت شركة)",
        "الترخيص الاستثماري (إن كانت شركة استثمارية)",
        "شهادة البلدية",
        "شهادة الزكاة والدخل",
        "شهادة القيمة المضافة",
        "شهادة التأمينات الاجتماعية",
        "العنوان الوطني للمنشأة والملاك",
        "شهادة الآيبان بالباركود",
        "القوائم المالية المعتمدة (إلزامي)",
        "الإقرارات الضريبية (6 ربع سنوي أو 15 شهري)",
        "كشف حساب Excel لآخر 12 شهر",
        "العقود (إن وجدت)",
    ]

    # ── Canonical rule definitions ────────────────────────────────────────
    # Each dict maps directly to EntityRule fields.
    desired: list[dict] = [

        # ══════════════════════════════════════════════════════════════════
        # 1. مصرف الراجحي — priority 1
        # ══════════════════════════════════════════════════════════════════
        dict(
            entity_name="مصرف الراجحي",
            entity_code="RAJHI",
            product_code="RAJHI_POS",
            product_name="نقاط بيع",
            facility_types=["pos"],
            priority=1,
            min_age_months=24,
            requires_pos=False,
            requires_invoices=False,
            max_partners=None,
            accepts_foreign=True,
            blocked_activities=["الذهب"],
            allowed_entity_types=None,
            min_pos_rajhi=800_000.0,
            min_pos_other=2_000_000.0,
            min_total_deposits=None,
            min_total_revenue=None,
            min_profit_ratio=None,
            requires_stability_check=False,
            tax_returns_count=None,
            tax_returns_frequency=None,
            financial_statement_rule=None,
            offer_code_prefix="RAJ",
            required_docs=rajhi_base_docs,
            description="الراجحي نقاط بيع — عمر ≥24، POS ≥800K (راجحي) أو 2M (خارجي)، النشاط: كل ما عدا الذهب",
        ),
        dict(
            entity_name="مصرف الراجحي",
            entity_code="RAJHI",
            product_code="RAJHI_CASH",
            product_name="كاش",
            facility_types=["cash"],
            priority=1,
            min_age_months=36,
            requires_pos=False,
            requires_invoices=False,
            max_partners=None,
            accepts_foreign=True,
            blocked_activities=["الذهب"],
            allowed_entity_types=None,
            min_pos_rajhi=None,
            min_pos_other=None,
            min_total_deposits=5_000_000.0,
            min_total_revenue=None,
            min_profit_ratio=None,
            requires_stability_check=False,
            tax_returns_count=3,
            tax_returns_frequency="yearly",
            financial_statement_rule=None,
            offer_code_prefix="RAJ",
            required_docs=rajhi_base_docs + ["إقرارات ضريبية لآخر 3 سنوات"],
            description="الراجحي كاش — عمر ≥36، إيداعات ≥5M، إقرارات ضريبية لآخر 3 سنوات",
        ),
        dict(
            entity_name="مصرف الراجحي",
            entity_code="RAJHI",
            product_code="RAJHI_FLEET",
            product_name="أسطول",
            facility_types=["fleet"],
            priority=1,
            min_age_months=24,
            requires_pos=False,
            requires_invoices=False,
            max_partners=None,
            accepts_foreign=True,
            blocked_activities=["الذهب"],
            allowed_entity_types=None,
            min_pos_rajhi=None,
            min_pos_other=None,
            min_total_deposits=None,
            min_total_revenue=None,
            min_profit_ratio=None,
            requires_stability_check=False,
            tax_returns_count=None,
            tax_returns_frequency=None,
            financial_statement_rule=None,
            offer_code_prefix="RAJ",
            required_docs=rajhi_base_docs,
            description="الراجحي أسطول — عمر ≥24، تقييم عبر كشف الحساب والمستندات، لا يشترط إقرارات",
        ),

        # ══════════════════════════════════════════════════════════════════
        # 2. إمكان — priority 2
        # ══════════════════════════════════════════════════════════════════
        dict(
            entity_name="إمكان",
            entity_code="EMKAN",
            product_code="EMKAN",
            product_name="نقاط بيع",
            facility_types=["pos"],
            priority=2,
            min_age_months=6,
            requires_pos=True,
            requires_invoices=False,
            max_partners=1,
            accepts_foreign=False,
            blocked_activities=None,
            # مؤسسة أو شركة شخص واحد فقط
            allowed_entity_types=["مؤسسة", "مؤسسة فردية", "شركة شخص واحد", "شركة ذات مسؤولية محدودة"],
            min_pos_rajhi=800_000.0,
            min_pos_other=2_000_000.0,
            min_total_deposits=None,
            min_total_revenue=None,
            min_profit_ratio=None,
            requires_stability_check=False,
            tax_returns_count=None,
            tax_returns_frequency=None,
            financial_statement_rule=None,
            offer_code_prefix="EMK",
            required_docs=[
                "صورة السجل التجاري",
                "صورة الهوية",
                "شهادة البلدية",
                "شهادة التوطين",
                "العنوان الوطني للمنشأة والمالك",
                "صور النشاط (داخل وخارج)",
                "شهادة الآيبان بالباركود",
                "كشف حساب Excel حسب مدة العمر المطلوبة",
                "كشف آخر 3 أشهر مختوم: أول 5 صفحات + آخر 5 صفحات",
            ],
            description="إمكان — عمر ≥6، مؤسسة/شخص واحد، سعودي فقط، يتطلب POS ≥800K (راجحي) أو 2M (خارجي)",
        ),

        # ══════════════════════════════════════════════════════════════════
        # 3. صندوق التنمية — priority 3 — مساران
        # ══════════════════════════════════════════════════════════════════
        dict(
            entity_name="صندوق التنمية",
            entity_code="SDF",
            product_code="SDF_POS",
            product_name="نقاط بيع",
            facility_types=["pos"],
            priority=3,
            min_age_months=18,
            requires_pos=True,
            requires_invoices=False,
            max_partners=None,
            accepts_foreign=True,
            blocked_activities=None,
            allowed_entity_types=None,
            min_pos_rajhi=None,
            min_pos_other=None,
            min_total_deposits=None,
            min_total_revenue=6_000_000.0,
            min_profit_ratio=None,
            requires_stability_check=True,
            tax_returns_count=6,
            tax_returns_frequency="quarterly",
            financial_statement_rule="conditional",
            offer_code_prefix="SDF",
            required_docs=sdf_base_docs + [
                "مستند داعم لنقاط البيع (إن توفر حسب البنك/مزود الدفع)",
            ],
            description="صندوق التنمية — مسار POS — عمر ≥18، إيرادات ≥6M، استقرار إيرادات، إقرارات (6 ربع سنوي أو 15 شهري)",
        ),
        dict(
            entity_name="صندوق التنمية",
            entity_code="SDF",
            product_code="SDF_INVOICES",
            product_name="فواتير",
            facility_types=["cash", "fleet"],
            priority=3,
            min_age_months=18,
            requires_pos=False,
            requires_invoices=False,   # path selected by facility_type, not user question
            max_partners=None,
            accepts_foreign=True,
            blocked_activities=None,
            allowed_entity_types=None,
            min_pos_rajhi=None,
            min_pos_other=None,
            min_total_deposits=None,
            min_total_revenue=6_000_000.0,
            min_profit_ratio=None,
            requires_stability_check=True,
            tax_returns_count=6,
            tax_returns_frequency="quarterly",
            financial_statement_rule="conditional",
            offer_code_prefix="SDF",
            required_docs=sdf_base_docs + [
                "ملف/ملفات فواتير المبيعات (Excel/PDF)",
            ],
            description="صندوق التنمية — مسار فواتير — عمر ≥18، إيرادات ≥6M، استقرار إيرادات، فواتير مبيعات",
        ),

        # ══════════════════════════════════════════════════════════════════
        # 4. أملاك — priority 4
        # ══════════════════════════════════════════════════════════════════
        dict(
            entity_name="أملاك",
            entity_code="AMLAK",
            product_code="AMLAK",
            product_name="تمويل أملاك",
            facility_types=["pos", "cash", "fleet"],
            priority=4,
            min_age_months=24,
            requires_pos=False,
            requires_invoices=False,
            max_partners=None,
            accepts_foreign=True,
            blocked_activities=None,
            allowed_entity_types=None,
            min_pos_rajhi=None,
            min_pos_other=None,
            min_total_deposits=None,
            min_total_revenue=7_000_000.0,
            min_profit_ratio=0.08,
            requires_stability_check=False,
            tax_returns_count=6,
            tax_returns_frequency="quarterly",
            financial_statement_rule="certified",
            offer_code_prefix="AML",
            required_docs=amlak_sahl_docs,
            description="أملاك — عمر ≥24، إيرادات ≥7M، صافي ربح ≥8%، قوائم معتمدة إلزامية",
        ),

        # ══════════════════════════════════════════════════════════════════
        # 5. سهل — priority 5 (نفس شروط أملاك)
        # ══════════════════════════════════════════════════════════════════
        dict(
            entity_name="سهل",
            entity_code="SAHL",
            product_code="SAHL",
            product_name="تمويل سهل",
            facility_types=["pos", "cash", "fleet"],
            priority=5,
            min_age_months=24,
            requires_pos=False,
            requires_invoices=False,
            max_partners=None,
            accepts_foreign=True,
            blocked_activities=None,
            allowed_entity_types=None,
            min_pos_rajhi=None,
            min_pos_other=None,
            min_total_deposits=None,
            min_total_revenue=7_000_000.0,
            min_profit_ratio=0.08,
            requires_stability_check=False,
            tax_returns_count=6,
            tax_returns_frequency="quarterly",
            financial_statement_rule="certified",
            offer_code_prefix="SHL",
            required_docs=amlak_sahl_docs,
            description="سهل — نفس شروط أملاك تمامًا (عمر ≥24، إيرادات ≥7M، صافي ربح ≥8%، قوائم معتمدة إلزامية)",
        ),
    ]

    # ── Upsert logic ─────────────────────────────────────────────────────
    async with async_session() as db:
        existing_result = await db.execute(select(EntityRule))
        existing_map: dict[str, EntityRule] = {
            r.product_code: r for r in existing_result.scalars().all()
        }

        created = skipped = 0
        for rule_data in desired:
            code = rule_data["product_code"]
            if code in existing_map:
                # Already exists — never overwrite manual edits from the UI
                skipped += 1
            else:
                db.add(EntityRule(**rule_data))
                created += 1

        await db.commit()
        logger.info(f"Entity rules synced: {created} created, {skipped} skipped (preserved)")




# ─── App ───────────────────────────────────────────────

app = FastAPI(
    title="Jenan BIZ API",
    description="منصة جنان بز لإدارة طلبات التسهيلات المالية",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS — read from ALLOWED_ORIGINS env variable, always include GitHub Pages
_origins_raw = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
_origins = list(set(_origins_raw + [
    "https://r1eox.github.io",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
]))
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(entity_rules_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")
app.include_router(contacts_router, prefix="/api")
app.include_router(campaigns_router, prefix="/api")


# ─── Health check ──────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "Jenan BIZ API",
        "version": "1.0.0",
    }
