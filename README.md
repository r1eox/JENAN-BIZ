# Jenan BIZ — جنان بز

## منصة إدارة طلبات التسهيلات المالية

### البنية التقنية

| الطبقة | التقنية |
|--------|---------|
| Frontend | Vue.js 3.5 + Vite + TypeScript + Tailwind CSS |
| Backend | Python 3.11+ + FastAPI + SQLAlchemy (async) |
| Database | PostgreSQL 16 |
| Queue | Redis 7 + arq worker |
| Auth | JWT (HS256) + bcrypt |

### التشغيل السريع

#### 1. PostgreSQL + Redis
```bash
docker compose up -d
```

#### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 3. Worker (Redis queue)
```bash
cd backend
arq app.worker.WorkerSettings
```

#### 4. Frontend
```bash
npm install
npm run dev
```

### حسابات تجريبية

| الدور | الجوال | كلمة المرور |
|-------|--------|-------------|
| شريك | 0500000001 | password123 |
| موظف | 0500000002 | password123 |
| مشرف | 0500000003 | password123 |
| مالك | 0500000004 | password123 |

### API Documentation
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### المراحل (9 + مرفوض)
1. `analyzing` — تحليل آلي
2. `completing_request` — استكمال الطلب  
3. `fee_contract_signed` — توقيع عقد الأتعاب
4. `completing_forms` — تعبئة النماذج
5. `submitted` — مُقدَّم ⚿
6. `approved` — معتمد ⚿
7. `signed` — موقّع ⚿
8. `facilities_transferred` — تم تحويل التسهيلات ⚿
9. `fees_received` — تم استلام الأتعاب ⚿

⚿ = مرحلة مقفلة تتطلب موافقة المشرف/المالك

### الأدوار (RBAC)
- **شريك** (partner): رفع المستندات، متابعة الطلب
- **موظف** (employee): إدارة الطلبات، تقديم المراحل
- **مشرف** (supervisor): موافقة المراحل المقفلة، الرفض، التعيين، KPIs
- **مالك** (owner): كل الصلاحيات + رؤية أسماء الجهات + إدارة القواعد
