-- analysis_pv_queries.sql
-- Photovoltaics lab: module IV curves (Sinus IV tracer, module area 1.28 m2).
-- KPIs are recomputed FROM THE RAW SWEEPS in SQL and validated against the
-- instrument's own summary values.
--
-- Three raw-data traps, all caught by validating against the instrument:
--   (1) current is logged in LOAD convention (negative) - first pass gave
--       negative Isc and 10 W Pmax vs the instrument's 72 W
--   (2) the sweep extends into REVERSE BIAS (V down to -2.2 V) where current
--       exceeds Isc - naive 'V < 1' filtering gave Isc = 5.94 A at every
--       irradiance
--   (3) sampling near V = 0 is sparse (one sweep jumps -1.4 V to +2.5 V), so
--       Isc is LINEARLY INTERPOLATED across V = 0 from the two bracketing
--       samples using window-style edge extraction.

---------------------------------------------------------------------------
-- Q14 · Module KPIs from raw IV data, validated against the instrument.
--       eta_actual uses the REAL measured irradiance. The instrument's ETA
--       always divides by the 1000 W/m2 STC reference, which misstates
--       efficiency whenever G differs from STC.
---------------------------------------------------------------------------
WITH edge AS (
    SELECT dataset,
           MAX(CASE WHEN voltage_v <= 0 THEN voltage_v END) AS v0,
           MIN(CASE WHEN voltage_v > 0 THEN voltage_v END)  AS v1
    FROM pv_iv_raw GROUP BY dataset
),
isc AS (
    SELECT e.dataset,
           -( (SELECT r.current_a FROM pv_iv_raw r
               WHERE r.dataset = e.dataset AND r.voltage_v = e.v0)
              + (0 - e.v0) *
              ( (SELECT r.current_a FROM pv_iv_raw r
                 WHERE r.dataset = e.dataset AND r.voltage_v = e.v1)
                - (SELECT r.current_a FROM pv_iv_raw r
                   WHERE r.dataset = e.dataset AND r.voltage_v = e.v0) )
              / (e.v1 - e.v0) ) AS isc_a
    FROM edge e
),
kpi AS (
    SELECT r.dataset,
           MAX(-r.voltage_v * r.current_a) AS pmax_w,
           MAX(r.voltage_v)                AS voc_v
    FROM pv_iv_raw r GROUP BY r.dataset
)
SELECT m.label,
       m.irradiance_wm2                                    AS g_wm2,
       m.module_temp_c                                     AS t_c,
       ROUND(i.isc_a, 2)                                   AS isc_a,
       ROUND(m.inst_isc_a, 2)                              AS inst_isc_a,
       ROUND(k.voc_v, 1)                                   AS voc_v,
       ROUND(k.pmax_w, 1)                                  AS pmax_w,
       ROUND(m.inst_pmpp_w, 1)                             AS inst_pmax_w,
       ROUND(100.0 * k.pmax_w / (i.isc_a * k.voc_v), 1)    AS ff_pct,
       ROUND(100.0 * k.pmax_w /
             (m.area_cm2 / 10000.0 * m.irradiance_wm2), 2) AS eta_actual_pct,
       ROUND(m.inst_eta_pct, 2)                            AS inst_eta_pct
FROM kpi k JOIN isc i USING (dataset) JOIN pv_measurement m USING (dataset)
ORDER BY m.condition, m.irradiance_wm2;

---------------------------------------------------------------------------
-- Q15 · Irradiance dependence (OLS in SQL over the 5-point series at ~24 C):
--       Isc scales linearly with G (Voc only logarithmically). The near-zero
--       intercept confirms proportionality - the photocurrent law.
---------------------------------------------------------------------------
WITH edge AS (
    SELECT dataset,
           MAX(CASE WHEN voltage_v <= 0 THEN voltage_v END) AS v0,
           MIN(CASE WHEN voltage_v > 0 THEN voltage_v END)  AS v1
    FROM pv_iv_raw GROUP BY dataset
),
series AS (
    SELECT m.irradiance_wm2 AS g,
           -( (SELECT r.current_a FROM pv_iv_raw r
               WHERE r.dataset = e.dataset AND r.voltage_v = e.v0)
              + (0 - e.v0) *
              ( (SELECT r.current_a FROM pv_iv_raw r
                 WHERE r.dataset = e.dataset AND r.voltage_v = e.v1)
                - (SELECT r.current_a FROM pv_iv_raw r
                   WHERE r.dataset = e.dataset AND r.voltage_v = e.v0) )
              / (e.v1 - e.v0) ) AS isc,
           (SELECT MAX(-r.voltage_v * r.current_a) FROM pv_iv_raw r
            WHERE r.dataset = e.dataset) AS pmax
    FROM edge e JOIN pv_measurement m USING (dataset)
    WHERE m.condition = 'irradiance_series'
),
stats AS (SELECT AVG(g) AS gbar, AVG(isc) AS ibar, AVG(pmax) AS pbar,
                 COUNT(*) AS n FROM series)
SELECT n                                                    AS points,
       ROUND(1000.0 * SUM((g - gbar) * (isc - ibar))
             / SUM((g - gbar) * (g - gbar)), 3)             AS isc_slope_ma_per_wm2,
       ROUND(ibar - SUM((g - gbar) * (isc - ibar))
             / SUM((g - gbar) * (g - gbar)) * gbar, 3)      AS isc_intercept_a,
       ROUND(SUM((g - gbar) * (pmax - pbar))
             / SUM((g - gbar) * (g - gbar)), 4)             AS pmax_slope_w_per_wm2
FROM series, stats;

---------------------------------------------------------------------------
-- Q16 · Shading impact at ~1055 W/m2: power loss vs the unshaded reference.
--       One shaded cell in a series string collapses module power far beyond
--       its area share - the classic PV mismatch effect (bypass-diode case).
---------------------------------------------------------------------------
WITH kpi AS (
    SELECT m.label, m.condition,
           MAX(-r.voltage_v * r.current_a) AS pmax_w
    FROM pv_iv_raw r JOIN pv_measurement m USING (dataset)
    WHERE m.condition IN ('shading_ref', 'shading')
    GROUP BY m.dataset
),
ref AS (SELECT pmax_w FROM kpi WHERE condition = 'shading_ref')
SELECT k.label,
       ROUND(k.pmax_w, 1)                              AS pmax_w,
       ROUND(100.0 * (1.0 - k.pmax_w / ref.pmax_w), 1) AS power_loss_pct
FROM kpi k, ref
ORDER BY k.pmax_w DESC;
