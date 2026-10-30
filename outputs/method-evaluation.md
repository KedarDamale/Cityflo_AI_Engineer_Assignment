# Exploratory comparison

Input: current CSV, 5,292 records; its parsed, whitespace-stripped records match the original Git blob in order, though byte hashes differ. 5,250 included, 24 unparseable and 18 with negative elapsed time excluded. Offset is interpreted as stamped; unverified clock misconfiguration remains possible. REC-114 membership is unresolved because vehicle series contains only two digits. All numbers are provisional.

| Route | n | Median | 10% trimmed | Huber c=1.5 | Mean | >10 min | >30 min |
|---|---:|---:|---:|---:|---:|---:|---:|
| R-14 | 118 | 8 | 7.90 | 7.97 | 8.07 | 28 | 0 |
| R-33 | 104 | 5 | 5.42 | 5.36 | 5.36 | 8 | 0 |
| R-26 | 103 | 4 | 4.52 | 4.54 | 4.51 | 4 | 0 |
| R-35 | 132 | 2 | 3.96 | 1.99 | 8.05 | 21 | 19 |

Median, 10% trimmed and Huber c=1.5 each rank R-14, R-33, R-26. Mean ranks R-14, R-35, R-33. Median tie for third with R-31 (4 minutes) is resolved by route code, an arbitrary tie-break. Removing any single day retains the three median routes, but swaps R-33 and R-26 on three omissions. Trim 5% instead ranks R-14, R-35, R-33; 10% and 20% rank R-14, R-33, R-26. Huber c=1, 1.5, 2 all yield R-14, R-33, R-26.

Including the 18 parseable negative elapsed records as a stress test keeps the robust rankings unchanged; mean is R-14, R-35, R-33. This is sensitivity only, not evidence those impossible arrivals are valid. The 24 unparseable rows cannot be restored without corrected data.

R-35 had 19 valid Wednesday trips, all more than 30 minutes late, with a 52-minute Wednesday median. T1-04521 was 61 minutes late; T1-04508 and T1-04516 were 60 minutes late. These can be real delays, and the Wednesday incident note is contextual, not a verified trip linkage. Median and Huber substantially suppress this concentrated disruption in the weekly ranking. Without independent corroboration, the 10% trimmed mean is a reasonable provisional compromise, but still ranks R-35 fifth and therefore must be accompanied by a severe-delay count and day-level analysis. There is no ground truth proving any estimator optimal. Revisit the ranking after validating the device and applying REC-114.
