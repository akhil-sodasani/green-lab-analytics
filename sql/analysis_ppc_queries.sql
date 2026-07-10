-- analysis_ppc_queries.sql
-- Production Planning & Control business game: 4 rounds, 8 batches,
-- 7 workstations. Batch-level data measured for Rounds 1 & 3.
-- Rounds 2 & 4 come from the report (raw files were Round-1 copies / proposal).

---------------------------------------------------------------------------
-- Q11 · Round-over-round improvement (LAG window function)
---------------------------------------------------------------------------
SELECT round, label, horizon_min, utilization_pct, source,
       ROUND(100.0 * (LAG(horizon_min) OVER (ORDER BY round) - horizon_min)
             / LAG(horizon_min) OVER (ORDER BY round), 1) AS horizon_reduction_pct,
       ROUND(100.0 * (1.0 - horizon_min /
             FIRST_VALUE(horizon_min) OVER (ORDER BY round)), 1)
                                                          AS vs_baseline_pct
FROM ppc_round_summary
ORDER BY round;

---------------------------------------------------------------------------
-- Q12 · Batch KPIs per round: cycle, waiting, and waiting share of cycle.
--       Round 1 shows queue build-up: waiting share grows monotonically as
--       WIP accumulates in front of the bottlenecks.
---------------------------------------------------------------------------
SELECT round,
       COUNT(*)                                        AS batches,
       ROUND(AVG(cycle_min), 1)                        AS avg_cycle_min,
       ROUND(MIN(cycle_min), 1)                        AS best_batch_min,
       ROUND(MAX(cycle_min), 1)                        AS worst_batch_min,
       ROUND(AVG(waiting_min), 1)                      AS avg_waiting_min,
       ROUND(100.0 * SUM(waiting_min) / SUM(cycle_min), 1)
                                                       AS waiting_share_pct,
       MAX(source)                                     AS source
FROM ppc_batch
GROUP BY round
ORDER BY round;

---------------------------------------------------------------------------
-- Q13 · Workstation bottleneck analysis: operation time, idle time, and
--       share of total load per round. RANK() flags the bottleneck.
--       Round 1 A3/Storage rows are NULL - broken #VALUE! formulas in the
--       source workbook, preserved as missing rather than silently zeroed.
---------------------------------------------------------------------------
SELECT round, workstation,
       operation_min,
       idle_min,
       ROUND(100.0 * operation_min /
             SUM(operation_min) OVER (PARTITION BY round), 1) AS load_share_pct,
       RANK() OVER (PARTITION BY round
                    ORDER BY operation_min DESC)              AS bottleneck_rank
FROM ppc_workstation
WHERE operation_min IS NOT NULL
ORDER BY round, bottleneck_rank;
