-- schema.sql — normalized tables for the electrochemical storage lab data

DROP TABLE IF EXISTS faraday_experiment;
DROP TABLE IF EXISTS battery_soc;
DROP TABLE IF EXISTS ui_curve;
DROP TABLE IF EXISTS cycle_test;

CREATE TABLE faraday_experiment (
    electrode1_before_g REAL,   -- cathode (gains copper mass)
    electrode2_before_g REAL,   -- anode   (loses copper mass)
    electrode1_after_g  REAL,
    electrode2_after_g  REAL,
    current_a           REAL,
    time_min            REAL
);

CREATE TABLE battery_soc (
    battery                 TEXT PRIMARY KEY,
    v_max                   REAL,  -- nominal full-charge voltage [V]
    ocv_measured_v          REAL,  -- measured open-circuit voltage [V]
    mean_working_voltage_v  REAL,  -- may be NULL in source
    weight_g                REAL,
    soc                     REAL,  -- state of charge, 0..1
    capacity_max_mah        REAL,
    capacity_current_mah    REAL
);

CREATE TABLE ui_curve (
    battery             TEXT NOT NULL,
    load_resistance_ohm REAL NOT NULL,
    voltage_v           REAL,
    current_ma          REAL,
    PRIMARY KEY (battery, load_resistance_ohm)
);

CREATE TABLE cycle_test (
    phase      TEXT NOT NULL CHECK (phase IN ('discharge', 'charge')),
    time_s     REAL NOT NULL,
    voltage_v  REAL,
    current_ma REAL,
    PRIMARY KEY (phase, time_s)
);
