from typing import List, Dict, Any, Tuple
from processing.models import DocumentElement, ContentType

class TableParser:
    @staticmethod
    def parse_document_tables(elements: List[DocumentElement], doc_version: str) -> Dict[str, List[Tuple[Any, ...]]]:
        """
        Parses DocumentElements containing TABLE_LOOKUP and maps them to SQLite schemas.
        Returns a dictionary mapping table name to a list of row tuples for SQL insertion.
        Each row tuple begins with (source_section, document_version, ...).
        """
        parsed_data = {
            "appendix_a_fastener_torque": [],
            "appendix_a_hydraulic_torque": [],
            "appendix_a_engine_torque": [],
            "appendix_a_pump_torque": [],
            "appendix_a_gear_fasteners": [],
            "appendix_a_electrical_torque": [],
            "hazmat_materials": [],
            "ppe_requirements": [],
            "engine_hazard_zones": [],
            "maintenance_check_intervals": []
        }

        for el in elements:
            if el.content_type != ContentType.TABLE_LOOKUP or not el.table_data or len(el.table_data) < 2:
                continue

            headers = [h.lower().strip() for h in el.table_data[0]]
            rows = el.table_data[1:]

            # Resolve the source section to cite
            source_section = el.section or el.subsection or el.chapter or "Unknown"

            # Match table based on header signatures
            if any("thread size" in h for h in headers):
                # appendix_a_fastener_torque
                # Expected headers: Thread Size, Dry Torque (in-lbf), Dry Torque (N·m), Lubricated (in-lbf), Lubricated (N·m)
                for row in rows:
                    if len(row) >= 5:
                        parsed_data["appendix_a_fastener_torque"].append((
                            source_section, doc_version,
                            row[0], row[1], row[2], row[3], row[4]
                        ))
            elif any("tube od" in h for h in headers):
                # appendix_a_hydraulic_torque
                # Expected headers: Tube OD, Aluminum (in-lbf), Steel (in-lbf), Aluminum (N·m), Steel (N·m)
                for row in rows:
                    if len(row) >= 5:
                        parsed_data["appendix_a_hydraulic_torque"].append((
                            source_section, doc_version,
                            row[0], row[1], row[2], row[3], row[4]
                        ))
            elif any("bolt size" in h for h in headers) and any("pattern" in h for h in headers):
                # appendix_a_engine_torque
                # Expected headers: Application, Bolt Size, Torque (in-lbf), Torque (N·m), Pattern
                for row in rows:
                    if len(row) >= 5:
                        parsed_data["appendix_a_engine_torque"].append((
                            source_section, doc_version,
                            row[0], row[1], row[2], row[3], row[4]
                        ))
            elif any("connection" in h for h in headers) and any("tube size" in h for h in headers):
                # appendix_a_pump_torque
                # Expected: Connection, Tube Size, Torque (in-lbf), Torque (N·m)
                for row in rows:
                    if len(row) >= 4:
                        parsed_data["appendix_a_pump_torque"].append((
                            source_section, doc_version,
                            row[0], row[1], row[2], row[3]
                        ))
            elif any("specification" in h for h in headers) and any("notes" in h for h in headers):
                # appendix_a_gear_fasteners
                # Expected: Application, Specification, Notes
                for row in rows:
                    if len(row) >= 3:
                        parsed_data["appendix_a_gear_fasteners"].append((
                            source_section, doc_version,
                            row[0], row[1], row[2]
                        ))
            elif any("terminal type" in h for h in headers):
                # appendix_a_electrical_torque
                # Expected: Terminal Type, Torque (in-lbf), Torque (N·m)
                for row in rows:
                    if len(row) >= 3:
                        parsed_data["appendix_a_electrical_torque"].append((
                            source_section, doc_version,
                            row[0], row[1], row[2]
                        ))
            elif any("material" in h for h in headers) and any("hazard" in h for h in headers):
                # hazmat_materials
                # Expected: Material, Typical Use, Principal Hazards, Required PPE
                for row in rows:
                    if len(row) >= 4:
                        parsed_data["hazmat_materials"].append((
                            source_section, doc_version,
                            row[0], row[1], row[2], row[3]
                        ))
            elif any("body region" in h for h in headers):
                # ppe_requirements
                # Expected: Body Region, Typical PPE, Selection Criteria
                for row in rows:
                    if len(row) >= 3:
                        parsed_data["ppe_requirements"].append((
                            source_section, doc_version,
                            row[0], row[1], row[2]
                        ))
            elif any("engine power setting" in h for h in headers):
                # engine_hazard_zones
                # Expected: Engine Power Setting, Forward Intake Hazard Zone, Aft Exhaust Hazard Zone, Side Clearance
                for row in rows:
                    if len(row) >= 4:
                        parsed_data["engine_hazard_zones"].append((
                            source_section, doc_version,
                            row[0], row[1], row[2], row[3]
                        ))
            elif any("check" in h for h in headers) and any("interval" in h for h in headers):
                # maintenance_check_intervals
                # Expected: Check, Typical Interval, Approximate Duration, Scope Summary
                for row in rows:
                    if len(row) >= 4:
                        parsed_data["maintenance_check_intervals"].append((
                            source_section, doc_version,
                            row[0], row[1], row[2], row[3]
                        ))

        return parsed_data
