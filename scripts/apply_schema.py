import psycopg2
import os
import sys

DB_URL = os.environ.get('DATABASE_URL') or "postgresql://postgres:mybday28jul@db.yevnlrajklfkqjhcrdps.supabase.co:5432/postgres"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'supabase', 'schema.sql')

print('Using DB URL:', DB_URL[:60] + '...')
print('Reading schema from', SCHEMA_PATH)

try:
    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()
except Exception as e:
    print('❌ Could not read schema.sql:', e)
    sys.exit(2)

try:
    conn = psycopg2.connect(DB_URL)
    conn.set_session(autocommit=True)
    cur = conn.cursor()
    cur.execute(schema)
    print('✅ Schema executed (commit sent).')

    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
    tables = [r[0] for r in cur.fetchall()]
    print('\n📊 Public tables (count={}):'.format(len(tables)))
    for t in tables:
        print(' -', t)

    cur.close()
    conn.close()
except Exception as e:
    import traceback
    print('❌ Error applying schema:', e)
    traceback.print_exc()
    sys.exit(3)
