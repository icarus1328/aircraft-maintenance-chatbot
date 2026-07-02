CREATE TABLE IF NOT EXISTS appendix_a_fastener_torque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_section TEXT,
    document_version TEXT,
    thread_size TEXT,
    dry_torque_in_lbf TEXT,
    dry_torque_nm TEXT,
    lubed_torque_in_lbf TEXT,
    lubed_torque_nm TEXT
);

CREATE TABLE IF NOT EXISTS appendix_a_hydraulic_torque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_section TEXT,
    document_version TEXT,
    tube_od TEXT,
    aluminum_in_lbf TEXT,
    steel_in_lbf TEXT,
    aluminum_nm TEXT,
    steel_nm TEXT
);

CREATE TABLE IF NOT EXISTS appendix_a_engine_torque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_section TEXT,
    document_version TEXT,
    application TEXT,
    bolt_size TEXT,
    torque_in_lbf TEXT,
    torque_nm TEXT,
    pattern TEXT
);

CREATE TABLE IF NOT EXISTS appendix_a_pump_torque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_section TEXT,
    document_version TEXT,
    connection TEXT,
    tube_size TEXT,
    torque_in_lbf TEXT,
    torque_nm TEXT
);

CREATE TABLE IF NOT EXISTS appendix_a_gear_fasteners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_section TEXT,
    document_version TEXT,
    application TEXT,
    specification TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS appendix_a_electrical_torque (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_section TEXT,
    document_version TEXT,
    terminal_type TEXT,
    torque_in_lbf TEXT,
    torque_nm TEXT
);

CREATE TABLE IF NOT EXISTS hazmat_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_section TEXT,
    document_version TEXT,
    material TEXT,
    typical_use TEXT,
    principal_hazards TEXT,
    required_ppe TEXT
);

CREATE TABLE IF NOT EXISTS ppe_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_section TEXT,
    document_version TEXT,
    body_region TEXT,
    typical_ppe TEXT,
    selection_criteria TEXT
);

CREATE TABLE IF NOT EXISTS engine_hazard_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_section TEXT,
    document_version TEXT,
    engine_power_setting TEXT,
    forward_intake_hazard_zone TEXT,
    aft_exhaust_hazard_zone TEXT,
    side_clearance TEXT
);

CREATE TABLE IF NOT EXISTS maintenance_check_intervals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_section TEXT,
    document_version TEXT,
    check_type TEXT,
    typical_interval TEXT,
    approximate_duration TEXT,
    scope_summary TEXT
);
