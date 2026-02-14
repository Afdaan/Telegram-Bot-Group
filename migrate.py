import asyncio
import os
import sys
import re
from urllib.parse import quote
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

# Build DB URL from separate env vars
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "telegram_bot")

if not DB_USER or not DB_NAME:
    print("❌ Missing DB credentials in .env")
    sys.exit(1)

# URL-encode the password to handle special characters
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
        
        # Test connection first
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Connection successful.")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    migrations = [
        "migrations/002_blacklist.sql",
        "migrations/003_report_setting.sql",
        "migrations/004_rss_feeds.sql",
        "migrations/005_userinfo.sql",
        "migrations/006_warn_upgrade.sql"
    ]

    async with engine.begin() as conn:
        for migration_file in migrations:
            print(f"\n📄 Checking {migration_file}...")
            if not os.path.exists(migration_file):
                print(f"   ⚠️ File not found: {migration_file}, skipping.")
                continue

            with open(migration_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Split by semicolon but ignore empty lines
                sql_commands = [cmd.strip() for cmd in content.split(";") if cmd.strip()]
            
            print(f"   🚀 Running {len(sql_commands)} commands...")
            for i, cmd in enumerate(sql_commands, 1):
                try:
                    # Check if this is an ALTER TABLE ADD COLUMN command
                    if "ALTER TABLE" in cmd.upper() and "ADD COLUMN" in cmd.upper():
                        # Extract table and column names
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
                    # Check for "Duplicate column" or "Table exists" errors
                    err_str = str(e).lower()
                    if "1060" in err_str or "duplicate column" in err_str:
                        print(f"      Cmd {i}: Create/Alter skipped (already exists).")
                    elif "1050" in err_str or "already exists" in err_str:
                         print(f"      Cmd {i}: Table skipped (already exists).")
                    else:
                        print(f"      ⚠️ Warning on Cmd {i}: {e}")
            print(f"   ✅ {migration_file} processed.")

    await engine.dispose()
    print("\n🎉 All migrations finished successfully!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_migrations())
