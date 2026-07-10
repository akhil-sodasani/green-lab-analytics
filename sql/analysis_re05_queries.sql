-- analysis_re05_queries.sql
-- Hydrogen-technologies lab (RE05) + capacitor/regulator experiments.
-- All metrics in SQL. Physical constants used inline:
--   F  = 96485 C/mol            Faraday constant
--   VM = 24.05 L/mol            molar gas volume at ~20 C, 1013 mbar
--   H0 = 12182.8 J/L            higher heating value of H2 (from lab manual)
--   Hu_butane = 45700 J/g       lower heating value of butane (burner fuel)

---------------------------------------------------------------------------
-- Q5 · Double-cell electrolyzer: gas production, Faradaic & energy efficiency
--      V_theoretical = 2 cells * VM * (I_mean * t) / (z F),  z = 2
--      eta_F = V_measured / V_theoretical
--      eta_E = H0 * V_measured / (U_cell * I_mean * t)
---------------------------------------------------------------------------
WITH per_load AS (
    SELECT load_ohm,
           AVG(current_ma) / 1000.0                    AS i_mean_a,
           MAX(time_s)                                 AS t_s,
           MAX(h2_volume_ml)                           AS v_meas_ml,
           MAX(CASE WHEN time_s = 30 THEN voltage_v END) AS u_cell_v
    FROM electrolyzer_run
    GROUP BY load_ohm
),
calc AS (
    SELECT load_ohm, i_mean_a, t_s, v_meas_ml, u_cell_v,
           2.0 * 24.05 * 1000.0 * i_mean_a * t_s / (2.0 * 96485.0) AS v_theo_ml
    FROM per_load
)
SELECT load_ohm,
       ROUND(i_mean_a * 1000, 1)                       AS i_mean_ma,
       t_s,
       v_meas_ml,
       ROUND(v_theo_ml, 1)                             AS v_theoretical_ml,
       ROUND(60.0 * v_meas_ml / t_s, 2)                AS production_ml_per_min,
       ROUND(100.0 * v_meas_ml / v_theo_ml, 1)         AS faradaic_eff_pct,
       ROUND(100.0 * 12182.8 * v_meas_ml / 1000.0
             / (u_cell_v * i_mean_a * t_s), 1)         AS energy_eff_pct
FROM calc
ORDER BY load_ohm DESC;

---------------------------------------------------------------------------
-- Q6 · Electrolyzer I-U curve: decomposition voltage & overpotential
--      OLS fit U = U_dec + R_el * I on the characteristic.
--      Excluded: the 100-ohm point (15.9 mA, 3.50 V) - inconsistent with the
--      otherwise monotone curve (3.06..3.39 V), recording error suspected.
--      Thermodynamic minimum for the double cell: 2 * 1.23 V = 2.46 V.
---------------------------------------------------------------------------
WITH pts AS (
    SELECT current_ma AS x, voltage_v AS y
    FROM electrolyzer_iu
    WHERE NOT (resistance_ohm = 100)
),
s AS (
    SELECT COUNT(*) n, AVG(x) mx, AVG(y) my, AVG(x*y) mxy, AVG(x*x) mxx FROM pts
)
SELECT n                                                    AS points_used,
       ROUND(my - (mxy-mx*my)/(mxx-mx*mx)*mx, 3)            AS u_decomposition_v,
       ROUND((my - (mxy-mx*my)/(mxx-mx*mx)*mx) / 2.0, 3)    AS u_dec_per_cell_v,
       ROUND(my - (mxy-mx*my)/(mxx-mx*mx)*mx - 2.46, 3)     AS overpotential_total_v,
       ROUND(1000.0 * (mxy-mx*my)/(mxx-mx*mx), 2)           AS r_electrolyte_ohm
FROM s;

---------------------------------------------------------------------------
-- Q7 · PEM single cell: maximum power point and ohmic-region fit
--      P = U*I (mV * mA = uW). Fit on setup 2 in the ohmic region
--      (69.3..113.2 mA), i.e. after the documented mid-measurement restart
--      ('new setup') and before the diffusion-limited knee (>= 134 mA, where
--      the voltage collapses and a linear extrapolation is no longer valid).
---------------------------------------------------------------------------
WITH power AS (
    SELECT current_ma, voltage_mv, resistance_ohm, setup,
           current_ma * voltage_mv / 1000.0 AS p_mw
    FROM pem_cell_iu
),
mpp AS (
    SELECT * FROM power ORDER BY p_mw DESC LIMIT 1
),
fit_pts AS (
    SELECT current_ma AS x, voltage_mv AS y FROM power
    WHERE setup = 2 AND current_ma BETWEEN 69 AND 114
),
s AS (
    SELECT COUNT(*) n, AVG(x) mx, AVG(y) my, AVG(x*y) mxy, AVG(x*x) mxx
    FROM fit_pts
)
SELECT ROUND(mpp.p_mw, 1)                                   AS p_max_mw,
       mpp.current_ma                                       AS i_at_pmax_ma,
       mpp.voltage_mv                                       AS u_at_pmax_mv,
       mpp.resistance_ohm                                   AS r_load_at_pmax_ohm,
       ROUND(s.my - (s.mxy-s.mx*s.my)/(s.mxx-s.mx*s.mx)*s.mx, 0)
                                                            AS u0_extrapolated_mv,
       ROUND(-(s.mxy-s.mx*s.my)/(s.mxx-s.mx*s.mx), 2)       AS ri_ohm,
       ROUND(100.0 * mpp.voltage_mv
             / (s.my - (s.mxy-s.mx*s.my)/(s.mxx-s.mx*s.mx)*s.mx), 1)
                                                            AS voltage_eff_at_pmax_pct
FROM mpp, s;

---------------------------------------------------------------------------
-- Q8 · SOFC: U-I fit, maximum power, and energy efficiency at 2-ohm load
--      Fit excludes the near-short point (R = 0). Electrical energy of the
--      2-ohm run by trapezoidal integration (mV*mA = uW). Chemical energy
--      from burner mass loss * butane LHV. The t=0 sample has no U/I reading
--      (missing values in the protocol), so integration starts at t=30 s.
---------------------------------------------------------------------------
WITH fit_pts AS (
    SELECT current_ma AS x, voltage_mv AS y FROM sofc_iu WHERE resistance_ohm > 0
),
s AS (
    SELECT COUNT(*) n, AVG(x) mx, AVG(y) my, AVG(x*y) mxy, AVG(x*x) mxx FROM fit_pts
),
mpp AS (
    SELECT voltage_mv, current_ma, resistance_ohm,
           voltage_mv * current_ma / 1000.0 AS p_mw
    FROM sofc_iu ORDER BY p_mw DESC LIMIT 1
),
steps AS (
    SELECT time_s, voltage_mv, current_ma,
           LAG(voltage_mv * current_ma) OVER (ORDER BY time_s) AS p_prev_uw,
           time_s - LAG(time_s) OVER (ORDER BY time_s)         AS dt
    FROM sofc_run WHERE voltage_mv IS NOT NULL
),
energy AS (
    SELECT SUM((voltage_mv * current_ma + p_prev_uw) / 2.0 * dt) / 1e6 AS e_el_j
    FROM steps WHERE p_prev_uw IS NOT NULL
),
fuel AS (
    SELECT (before_g - after_g) * 45700.0 AS e_chem_j, before_g - after_g AS dm_g
    FROM burner_mass WHERE label = 'sofc_burner'
)
SELECT ROUND(mpp.p_mw, 1)                                  AS p_max_mw,
       mpp.resistance_ohm                                  AS r_load_at_pmax_ohm,
       ROUND(s.my - (s.mxy-s.mx*s.my)/(s.mxx-s.mx*s.mx)*s.mx, 0)
                                                           AS u0_extrapolated_mv,
       ROUND(-(s.mxy-s.mx*s.my)/(s.mxx-s.mx*s.mx), 2)      AS ri_ohm,
       ROUND(energy.e_el_j, 2)                             AS e_electrical_j,
       ROUND(fuel.dm_g, 4)                                 AS burner_dm_g,
       ROUND(fuel.e_chem_j, 0)                             AS e_chemical_j,
       ROUND(100.0 * energy.e_el_j / fuel.e_chem_j, 4)     AS energy_eff_pct
FROM mpp, s, energy, fuel;

---------------------------------------------------------------------------
-- Q9 · Capacitor discharge time constant per run
--      Resistive decay: I(t) = I0 * exp(-t/tau)  ->  ln I linear in t.
--      OLS on ln(current) restricted to the resistive region: after the
--      1.021 A current-limit plateau and above the 50 mA noise floor.
---------------------------------------------------------------------------
WITH decay AS (
    SELECT run, time_s AS x, LN(current_a) AS y
    FROM cap_discharge
    WHERE current_a > 0.05 AND current_a < 1.0
),
s AS (
    SELECT run, COUNT(*) n, AVG(x) mx, AVG(y) my, AVG(x*y) mxy, AVG(x*x) mxx
    FROM decay GROUP BY run
)
SELECT run,
       n                                                   AS points_used,
       ROUND(-1.0 / ((mxy-mx*my)/(mxx-mx*mx)), 3)          AS tau_s,
       ROUND(EXP(my - (mxy-mx*my)/(mxx-mx*mx)*mx), 3)      AS i0_extrapolated_a
FROM s ORDER BY run;

---------------------------------------------------------------------------
-- Q10 · Regulator topology comparison: energy delivered to the capacitor
--       E = trapezoid( U_cap * I_cap ) over the first 25 s (common window
--       across all five recordings), plus the capacitor voltage reached.
---------------------------------------------------------------------------
WITH windowed AS (
    SELECT topology, time_s, u_cap_v * i_cap_a AS p_w,
           LAG(u_cap_v * i_cap_a) OVER (PARTITION BY topology ORDER BY time_s) AS p_prev,
           time_s - LAG(time_s) OVER (PARTITION BY topology ORDER BY time_s)   AS dt,
           u_cap_v
    FROM regulator_run
    WHERE time_s <= 25
)
SELECT topology,
       ROUND(SUM((p_w + p_prev) / 2.0 * dt), 3)            AS e_to_cap_j,
       ROUND(MAX(u_cap_v), 2)                              AS u_cap_reached_v,
       RANK() OVER (ORDER BY SUM((p_w + p_prev) / 2.0 * dt) DESC) AS rank
FROM windowed
WHERE p_prev IS NOT NULL
GROUP BY topology
ORDER BY rank;
