# Electrochemical Storage Lab — Results Summary

## Q1 · Faraday constant from copper electrolysis

|   charge_C |   dm_cathode_g |   dm_anode_g |   F_cathode |   F_anode |   err_cathode_pct |   err_anode_pct |
|-----------:|---------------:|-------------:|------------:|----------:|------------------:|----------------:|
|       1350 |           0.38 |         0.46 |      112885 |     93253 |                17 |            -3.4 |

## Q2 · Battery KPIs: SOC, capacity, energy density

| battery   |   soc_pct |   capacity_max_mah |   capacity_now_mah |   energy_density_mwh_per_g |   density_rank |
|:----------|----------:|-------------------:|-------------------:|---------------------------:|---------------:|
| LiPo      |      80   |                980 |                784 |                       79.6 |              1 |
| NiMH      |      88.6 |                600 |                531 |                       53.6 |              2 |
| NiZn      |      22   |                550 |                121 |                       15.5 |              3 |
| Lead-acid |      48   |               2500 |               1200 |                       12.4 |              4 |

## Q3 · Internal resistance (OLS fit in SQL)

| battery   |   points_used |   internal_resistance_ohm |   u0_intercept_v |
|:----------|--------------:|--------------------------:|-----------------:|
| Lead-acid |            10 |                      0.17 |            2.062 |
| NiMH      |            12 |                      0.18 |            1.308 |
| Li-Ion    |            11 |                      0.22 |            3.963 |

## Q4 · NiMH round-trip energy efficiency

|   w_discharge_j |   w_charge_j |   voltage_efficiency_pct |
|----------------:|-------------:|-------------------------:|
|           86.42 |        91.18 |                     94.8 |
