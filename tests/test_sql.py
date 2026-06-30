import sys
import os
import sqlite3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import settings

def test_sqlite_counts():
    db_path = settings.DB_PATH
    print(f"Connecting to database at {db_path}...")
    
    tables = [
        "appendix_a_fastener_torque",
        "appendix_a_hydraulic_torque",
        "appendix_a_engine_torque",
        "appendix_a_pump_torque",
        "appendix_a_gear_fasteners",
        "appendix_a_electrical_torque",
        "hazmat_materials",
        "ppe_requirements",
        "engine_hazard_zones",
        "maintenance_check_intervals"
    ]
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            count = cursor.fetchone()[0]
            print(f"Table {t:30} Count: {count}")
            if count > 0:
                cursor.execute(f"SELECT * FROM {t} LIMIT 1")
                row = cursor.fetchone()
                print(f"  Sample row: {row}")

if __name__ == "__main__":
    test_sqlite_counts()
