# Production Planning & Control Business Game — Results

## Q11 · Round-over-round improvement (LAG window function)

|   round | label                                       |   horizon_min |   utilization_pct | source                                 |   horizon_reduction_pct |   vs_baseline_pct |
|--------:|:--------------------------------------------|--------------:|------------------:|:---------------------------------------|------------------------:|------------------:|
|       1 | Baseline (separate stations, central QC)    |           125 |                24 | measured                               |                   nan   |               0   |
|       2 | A2 + A3 combined (Blender)                  |            75 |                28 | report (raw file is a copy of Round 1) |                    40   |              40   |
|       3 | Decentralized quality control               |            68 |                30 | measured                               |                     9.3 |              45.6 |
|       4 | Lean optimized (std. work, pre-staging, 5S) |            58 |                36 | theoretical proposal (report)          |                    14.7 |              53.6 |

## Q12 · Batch KPIs per round: cycle, waiting, waiting share

|   round |   batches |   avg_cycle_min |   best_batch_min |   worst_batch_min |   avg_waiting_min |   waiting_share_pct | source                         |
|--------:|----------:|----------------:|-----------------:|------------------:|------------------:|--------------------:|:-------------------------------|
|       1 |         8 |            85.7 |             48.8 |             140.2 |              55.6 |                64.8 | measured (ROUND_1.xlsx)        |
|       3 |         8 |            52.8 |             38.3 |              64.2 |              25.8 |                48.9 | measured (akhil_round_4_.xlsx) |
|       4 |         8 |            45.4 |             34   |              54   |              12.6 |                27.8 | theoretical proposal (report)  |

## Q13 · Workstation bottleneck analysis (RANK per round)

|   round | workstation   |   operation_min |   idle_min |   load_share_pct |   bottleneck_rank |
|--------:|:--------------|----------------:|-----------:|-----------------:|------------------:|
|       1 | Rework        |         110.229 |     45.783 |             45.7 |                 1 |
|       1 | Quality Check |          45.873 |      7.8   |             19   |                 2 |
|       1 | A1            |          41.097 |     11.921 |             17   |                 3 |
|       1 | A2            |          35.942 |     14.83  |             14.9 |                 4 |
|       1 | Refining      |           8     |     32.166 |              3.3 |                 5 |
|       3 | A1            |          74.205 |     12.894 |             34.4 |                 1 |
|       3 | Rework        |          65.861 |     40.888 |             30.5 |                 2 |
|       3 | A2            |          23.702 |     77.064 |             11   |                 3 |
|       3 | Quality Check |          22.74  |     68.336 |             10.5 |                 4 |
|       3 | A3            |          21.449 |     79.318 |              9.9 |                 5 |
|       3 | Refining      |           8     |     81.633 |              3.7 |                 6 |
