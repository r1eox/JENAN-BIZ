import asyncio, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from app.database import async_session as AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text(
            'SELECT display_id, stage, entity_name, bs_file_name, cr_file_name, is_eligible, result_summary, partner_id FROM cases ORDER BY created_at DESC'
        ))
        rows = r.fetchall()
        print("=== CASES ===")
        for row in rows:
            print(f"{row[0]}|{row[1]}|entity={row[2]}|bs={bool(row[3])}|cr={bool(row[4])}|elig={row[5]}|summary={str(row[6])[:50] if row[6] else None}|partner={str(row[7])[:8]}")
        
        print("\n=== ENTITY RULES ===")
        r2 = await db.execute(text('SELECT name, is_active, conditions FROM entity_rules'))
        for row in r2.fetchall():
            cond = str(row[2])[:80] if row[2] else "none"
            print(f"{row[0]}|active={row[1]}|conditions={cond}")
        
        print("\n=== NOTIFICATIONS (last 10) ===")
        r3 = await db.execute(text('SELECT type, title, is_read, created_at FROM notifications ORDER BY created_at DESC LIMIT 10'))
        for row in r3.fetchall():
            print(f"{row[0]}|{row[1][:50]}|read={row[2]}|{row[3]}")
        
        print("\n=== STAGE HISTORY (last 10) ===")
        r4 = await db.execute(text('SELECT c.display_id, sh.from_stage, sh.to_stage, sh.created_at FROM stage_history sh JOIN cases c ON c.id=sh.case_id ORDER BY sh.created_at DESC LIMIT 10'))
        for row in r4.fetchall():
            print(f"{row[0]}|{row[1]}->{row[2]}|{row[3]}")

asyncio.run(main())
