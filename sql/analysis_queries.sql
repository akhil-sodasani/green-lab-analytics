-- analysis_queries.sql
-- All core metrics are computed in SQL (SQLite). Python is only used for
-- ETL and plotting. Queries are labelled Q1..Q4 and mirrored in src/02_analysis.py.

---------------------------------------------------------------------------
-- Q1 · Faraday constant from copper electrolysis
--      F = Q * M / (z * dm),  Q = I * t,  z = 2,  M(Cu) = 63.55 g/mol
--      Computed twice: from cathode mass gain and anode mass loss.
---------------------------------------------------------------------------
WITH params AS (
    SELECT current_a * time_min * 60.0                 AS charge_c,
           electrode1_after_g - electrode1_before_g    AS dm_cathode_g,
           electrode2_before_g - electrode2_after_g    AS dm_anode_g
    FROM faraday_experiment
)
SELECT ROUND(charge_c, 1)                                        AS charge_C,
       ROUND(dm_cathode_g, 3)                                    AS dm_cathode_g,
       ROUND(dm_anode_g, 3)                                      AS dm_anode_g,
       ROUND(charge_c * 63.55 / (2 * dm_cathode_g), 0)           AS F_cathode,
       ROUND(charge_c * 63.55 / (2 * dm_anode_g), 0)             AS F_anode,
       ROUND(100 * (charge_c * 63.55 / (2 * dm_cathode_g) - 96485) / 96485, 1)
                                                                 AS err_cathode_pct,
       ROUND(100 * (charge_c * 63.55 / (2 * dm_anode_g) - 96485) / 96485, 1)
                                                                 AS err_anode_pct
FROM params;

---------------------------------------------------------------------------
-- Q2 · Battery KPI table: SOC, remaining capacity, energy density
--      Recomputes energy density = capacity_current * OCV / weight
--      (the source spreadsheet contained a broken formula for LiPo).
---------------------------------------------------------------------------
SELECT battery,
       ROUND(100 * soc, 1)                                       AS soc_pct,
       capacity_max_mah,
       ROUND(capacity_current_mah, 0)                            AS capacity_now_mah,
       ROUND(capacity_current_mah * ocv_measured_v / weight_g, 1)
                                                                 AS energy_density_mwh_per_g,
       RANK() OVER (ORDER BY capacity_current_mah * ocv_measured_v / weight_g DESC)
                                                                 AS density_rank
FROM battery_soc
ORDER BY density_rank;

---------------------------------------------------------------------------
-- Q3 · Internal resistance via ordinary-least-squares fit, in pure SQL
--      Model: U = U0 - Ri * I   ->   Ri = -slope
--      Current is in mA, so slope [V/mA] * 1000 = Ri [ohm].
--      Fit region: measurement artifacts excluded (Li-Ion rebound point at
--      1 ohm, Lead-acid points saturated at the 200 mA instrument limit).
---------------------------------------------------------------------------
WITH fit_region AS (
    SELECT battery, current_ma AS x, voltage_v AS y
    FROM ui_curve
    WHERE NOT (battery = 'Li-Ion'    AND load_resistance_ohm = 1)   -- rebound artifact
      AND NOT (battery = 'Lead-acid' AND current_ma >= 200)         -- current clipping
),
stats AS (
    SELECT battery,
           COUNT(*)   AS n,
           AVG(x)     AS mean_x,
           AVG(y)     AS mean_y,
           AVG(x * y) AS mean_xy,
           AVG(x * x) AS mean_xx
    FROM fit_region
    GROUP BY battery
)
SELECT battery,
       n                                                          AS points_used,
       ROUND(-1000.0 * (mean_xy - mean_x * mean_y)
                     / (mean_xx - mean_x * mean_x), 2)             AS internal_resistance_ohm,
       ROUND(mean_y + (mean_xy - mean_x * mean_y)
                    / (mean_xx - mean_x * mean_x) * (0 - mean_x), 3)
                                                                  AS u0_intercept_v
FROM stats
ORDER BY internal_resistance_ohm;

---------------------------------------------------------------------------
-- Q4 · NiMH round-trip energy efficiency (5 min discharge / 5 min charge
--      at 230 mA), trapezoidal integration with window functions:
--      W = I * sum( (U_i + U_{i-1})/2 * dt ),  eta = W_dis / W_chg
---------------------------------------------------------------------------
WITH steps AS (
    SELECT phase, time_s, voltage_v, current_ma,
           LAG(voltage_v) OVER (PARTITION BY phase ORDER BY time_s) AS v_prev,
           time_s - LAG(time_s) OVER (PARTITION BY phase ORDER BY time_s) AS dt
    FROM cycle_test
),
energy AS (
    SELECT phase,
           -- [V]*[s] * [mA]/1000 = [V]*[A]*[s] = joules
           SUM((voltage_v + v_prev) / 2.0 * dt) * MAX(current_ma) / 1000.0
               AS energy_j
    FROM steps
    WHERE v_prev IS NOT NULL
    GROUP BY phase
)
SELECT ROUND(MAX(CASE WHEN phase = 'discharge' THEN energy_j END), 2)
           AS w_discharge_j,
       ROUND(MAX(CASE WHEN phase = 'charge' THEN energy_j END), 2)
           AS w_charge_j,
       ROUND(100.0 * MAX(CASE WHEN phase = 'discharge' THEN energy_j END)
                   / MAX(CASE WHEN phase = 'charge' THEN energy_j END), 1)
           AS voltage_efficiency_pct
FROM energy;
