# Prime statistics: 4–15 digits

Exact counts for all positive integers in each inclusive digit band.
Percentages use all integers in the band as the denominator and are
rounded to eight decimal places (not sampled or estimated).

| Digits | Minimum | Maximum | Integers | Primes | Prime percentage |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 1,000 | 9,999 | 9,000 | 1,061 | 11.78888889% |
| 5 | 10,000 | 99,999 | 90,000 | 8,363 | 9.29222222% |
| 6 | 100,000 | 999,999 | 900,000 | 68,906 | 7.65622222% |
| 7 | 1,000,000 | 9,999,999 | 9,000,000 | 586,081 | 6.51201111% |
| 8 | 10,000,000 | 99,999,999 | 90,000,000 | 5,096,876 | 5.66319556% |
| 9 | 100,000,000 | 999,999,999 | 900,000,000 | 45,086,079 | 5.00956433% |
| 10 | 1,000,000,000 | 9,999,999,999 | 9,000,000,000 | 404,204,977 | 4.49116641% |
| 11 | 10,000,000,000 | 99,999,999,999 | 90,000,000,000 | 3,663,002,302 | 4.07000256% |
| 12 | 100,000,000,000 | 999,999,999,999 | 900,000,000,000 | 33,489,857,205 | 3.72109524% |
| 13 | 1,000,000,000,000 | 9,999,999,999,999 | 9,000,000,000,000 | 308,457,624,821 | 3.42730694% |
| 14 | 10,000,000,000,000 | 99,999,999,999,999 | 90,000,000,000,000 | 2,858,876,213,963 | 3.17652913% |
| 15 | 100,000,000,000,000 | 999,999,999,999,999 | 900,000,000,000,000 | 26,639,628,671,867 | 2.95995874% |

## Method

Computed with `primecountpy` (libprimecount's exact prime-counting algorithm).
For a band `[L, U]`, the count is `π(U) − π(L − 1)`, where `π(x)` counts
primes less than or equal to `x`. The percentage is `100 × count / (U − L + 1)`.
No individual primes are enumerated or saved.

Regenerate from the repository directory:

```sh
.venv/bin/python prime_stats.py
```
