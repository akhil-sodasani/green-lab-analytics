# RE05 Hydrogen Technologies & Regulator Experiments — Results

## Q5 · Electrolyzer: gas production, Faradaic & energy efficiency

|   load_ohm |   i_mean_ma |   t_s |   v_meas_ml |   v_theoretical_ml |   production_ml_per_min |   faradaic_eff_pct |   energy_eff_pct |
|-----------:|------------:|------:|------------:|-------------------:|------------------------:|-------------------:|-----------------:|
|          5 |       197.6 |   270 |          15 |               13.3 |                    3.33 |              112.8 |            102.2 |
|          3 |       282.7 |   270 |          15 |               19   |                    3.33 |               78.8 |             69.6 |

## Q6 · Electrolyzer I-U: decomposition voltage & overpotential

|   points_used |   u_decomposition_v |   u_dec_per_cell_v |   overpotential_total_v |   r_electrolyte_ohm |
|--------------:|--------------------:|-------------------:|------------------------:|--------------------:|
|            12 |               3.054 |              1.527 |                   0.594 |                1.61 |

## Q7 · PEM fuel cell: maximum power point & ohmic fit

|   p_max_mw |   i_at_pmax_ma |   u_at_pmax_mv |   r_load_at_pmax_ohm |   u0_extrapolated_mv |   ri_ohm |   voltage_eff_at_pmax_pct |
|-----------:|---------------:|---------------:|---------------------:|---------------------:|---------:|--------------------------:|
|       57.7 |          113.2 |            510 |                    4 |                 1092 |     5.14 |                      46.7 |

## Q8 · SOFC: maximum power, fit & energy efficiency

|   p_max_mw |   r_load_at_pmax_ohm |   u0_extrapolated_mv |   ri_ohm |   e_electrical_j |   burner_dm_g |   e_chemical_j |   energy_eff_pct |
|-----------:|---------------------:|---------------------:|---------:|-----------------:|--------------:|---------------:|-----------------:|
|       31.1 |                    2 |                  595 |     2.74 |             4.67 |        0.9041 |          41317 |           0.0113 |

## Q9 · Capacitor discharge time constants (ln-linear OLS in SQL)

|   run |   points_used |   tau_s |   i0_extrapolated_a |
|------:|--------------:|--------:|--------------------:|
|     1 |            89 |   1.064 |               0.672 |
|     2 |           138 |   2.137 |               0.643 |
|     3 |            74 |   1.004 |               0.975 |

## Q10 · Regulator topologies: energy delivered to the capacitor

| topology               |   e_to_cap_j |   u_cap_reached_v |   rank |
|:-----------------------|-------------:|------------------:|-------:|
| MPP + Shunt            |        3.287 |              3.32 |      1 |
| Shunt Regulator + Load |        3.028 |              3.21 |      2 |
| Series Regulator       |        1.88  |              1.83 |      3 |
| Shunt Regulator        |        0.242 |              1.46 |      4 |
| PWM                    |        0.064 |              4.05 |      5 |
