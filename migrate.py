import asyncio
import os
import sys
import re
from urllib.parse import quote
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "telegram_bot")

if not DB_USER or not DB_NAME:
    print("❌ Missing DB credentials in .env")
    sys.exit(1)


encoded_password = quote(DB_PASSWORD, safe='')
DB_URL = f"mysql+aiomysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        result = await conn.execute(
            text("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = :table AND COLUMN_NAME = :col AND TABLE_SCHEMA = :db
            """),
            {"table": table_name, "col": column_name, "db": DB_NAME}
        )
        return result.fetchone() is not None
    except:
        return False

async def run_migrations():
    print(f"🔌 Connecting to database {DB_HOST}:{DB_PORT}/{DB_NAME}...")
    try:
        engine = create_async_engine(DB_URL, echo=False)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Connection successful.")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return


    migration_dir = "migrations"
    if not os.path.exists(migration_dir):
        print(f"❌ Directory '{migration_dir}' not found.")
        return


    migration_files = [
        os.path.join(migration_dir, f) 
        for f in os.listdir(migration_dir) 
        if f.endswith(".sql")
    ]
    migration_files.sort()

    async with engine.begin() as conn:
        for migration_file in migration_files:
            print(f"\n📄 Processing {migration_file}...")
            
            with open(migration_file, "r", encoding="utf-8") as f:
                content = f.read()
                sql_commands = [cmd.strip() for cmd in content.split(";") if cmd.strip()]
            
            print(f"   🚀 Running {len(sql_commands)} commands...")
            for i, cmd in enumerate(sql_commands, 1):
                try:
                    if "ALTER TABLE" in cmd.upper() and "ADD COLUMN" in cmd.upper():
                        table_match = re.search(r"ALTER TABLE\s+`?(\w+)`?", cmd, re.IGNORECASE)
                        col_match = re.search(r"ADD COLUMN\s+`?(\w+)`?", cmd, re.IGNORECASE)
                        
                        if table_match and col_match:
                            table_name = table_match.group(1)
                            col_name = col_match.group(1)
                            
                            if await column_exists(conn, table_name, col_name):
                                print(f"      Cmd {i}: Column '{col_name}' already exists, skipping.")
                                continue
                    
                    await conn.execute(text(cmd))
                except Exception as e:
                    err_str = str(e).lower()
                    if "1060" in err_str or "duplicate column" in err_str:
                        print(f"      Cmd {i}: Skipped (column already exists).")
                    elif "1050" in err_str or "already exists" in err_str:
                         print(f"      Cmd {i}: Table skipped (already exists).")
                    else:
                        print(f"      ⚠️ Warning on Cmd {i}: {e}")
            print(f"   ✅ {migration_file} processed.")

    await engine.dispose()
    print("\n🎉 Automated migrations finished successfully!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_migrations())
