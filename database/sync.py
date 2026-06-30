import os
import sqlite3
from typing import List
from config.settings import settings
from processing.extractor import Extractor
from database.table_parser import TableParser

class DatabaseSync:
    def __init__(self, db_path: str = settings.DB_PATH, schema_path: str = settings.SCHEMA_PATH):
        self.db_path = db_path
        self.schema_path = schema_path

    def init_db(self):
        """Initializes the database by executing schema.sql."""
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            with open(self.schema_path, 'r') as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
            conn.commit()

    def clear_db(self):
        """Truncates all tables in the database to prepare for sync."""
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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")
            conn.commit()

    def sync_document(self, docx_path: str, doc_version: str):
        """
        Parses the document, extracts lookup tables, initializes DB, clears old records,
        and inserts the fresh dataset.
        """
        print(f"Starting DB sync for {docx_path} (Version: {doc_version})")
        
        # 1. Initialize and clear DB
        self.init_db()
        self.clear_db()

        # 2. Extract Document Elements
        extractor = Extractor(docx_path)
        elements = extractor.extract()

        # 3. Parse Tables
        parsed_tables = TableParser.parse_document_tables(elements, doc_version)

        # 4. Insert data into SQLite
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # appendix_a_fastener_torque
            if parsed_tables["appendix_a_fastener_torque"]:
                cursor.executemany(
                    """INSERT INTO appendix_a_fastener_torque 
                       (source_section, document_version, thread_size, dry_torque_in_lbf, dry_torque_nm, lubed_torque_in_lbf, lubed_torque_nm)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    parsed_tables["appendix_a_fastener_torque"]
                )

            # appendix_a_hydraulic_torque
            if parsed_tables["appendix_a_hydraulic_torque"]:
                cursor.executemany(
                    """INSERT INTO appendix_a_hydraulic_torque 
                       (source_section, document_version, tube_od, aluminum_in_lbf, steel_in_lbf, aluminum_nm, steel_nm)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    parsed_tables["appendix_a_hydraulic_torque"]
                )

            # appendix_a_engine_torque
            if parsed_tables["appendix_a_engine_torque"]:
                cursor.executemany(
                    """INSERT INTO appendix_a_engine_torque 
                       (source_section, document_version, application, bolt_size, torque_in_lbf, torque_nm, pattern)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    parsed_tables["appendix_a_engine_torque"]
                )

            # appendix_a_pump_torque
            if parsed_tables["appendix_a_pump_torque"]:
                cursor.executemany(
                    """INSERT INTO appendix_a_pump_torque 
                       (source_section, document_version, connection, tube_size, torque_in_lbf, torque_nm)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    parsed_tables["appendix_a_pump_torque"]
                )

            # appendix_a_gear_fasteners
            if parsed_tables["appendix_a_gear_fasteners"]:
                cursor.executemany(
                    """INSERT INTO appendix_a_gear_fasteners 
                       (source_section, document_version, application, specification, notes)
                       VALUES (?, ?, ?, ?, ?)""",
                    parsed_tables["appendix_a_gear_fasteners"]
                )

            # appendix_a_electrical_torque
            if parsed_tables["appendix_a_electrical_torque"]:
                cursor.executemany(
                    """INSERT INTO appendix_a_electrical_torque 
                       (source_section, document_version, terminal_type, torque_in_lbf, torque_nm)
                       VALUES (?, ?, ?, ?, ?)""",
                    parsed_tables["appendix_a_electrical_torque"]
                )

            # hazmat_materials
            if parsed_tables["hazmat_materials"]:
                cursor.executemany(
                    """INSERT INTO hazmat_materials 
                       (source_section, document_version, material, typical_use, principal_hazards, required_ppe)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    parsed_tables["hazmat_materials"]
                )

            # ppe_requirements
            if parsed_tables["ppe_requirements"]:
                cursor.executemany(
                    """INSERT INTO ppe_requirements 
                       (source_section, document_version, body_region, typical_ppe, selection_criteria)
                       VALUES (?, ?, ?, ?, ?)""",
                    parsed_tables["ppe_requirements"]
                )

            # engine_hazard_zones
            if parsed_tables["engine_hazard_zones"]:
                cursor.executemany(
                    """INSERT INTO engine_hazard_zones 
                       (source_section, document_version, engine_power_setting, forward_intake_hazard_zone, aft_exhaust_hazard_zone, side_clearance)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    parsed_tables["engine_hazard_zones"]
                )

            # maintenance_check_intervals
            if parsed_tables["maintenance_check_intervals"]:
                cursor.executemany(
                    """INSERT INTO maintenance_check_intervals 
                       (source_section, document_version, check_type, typical_interval, approximate_duration, scope_summary)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    parsed_tables["maintenance_check_intervals"]
                )
                
            conn.commit()
            
        print("Database sync completed successfully.")

if __name__ == "__main__":
    # Test sync
    sync = DatabaseSync()
    sync.sync_document(
        docx_path=os.path.join(settings.VERSIONS_DIR, "Synthetic manual_Boeing_737-800_Maintenance_1.docx"),
        doc_version="v1"
    )
