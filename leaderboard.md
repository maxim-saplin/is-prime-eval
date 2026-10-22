# Prime-eval leaderboard (compact)

Depths 7–15 only, one row per complete run covering every requested depth (a completed parent+extension appears once).
Scope: 17 complete runs; each row uses only that run's scheduled cases within these depths (30 per depth here, 270 per run).
Accuracy sorts descending; different frozen question sets are not paired comparisons.
The full in-depth tables (per-depth detail, intervals, routes, retry/truncation reasons) are kept in `analysis.md`.
The depth graphs remain at depths 4–15 and select their 'best overall' line by highest overall 4–15 accuracy; this compact ranking is computed independently within 7–15 and may disagree.

| Model | Accuracy | Tokens | Cost | API time |
|---|---:|---:|---:|---:|
| gemini-4-argon-high | 91.1% | 3,831,472 | $38.200 | 12h14m |
| deepseek-v4.1-flash-1017-low | 90.4% | 9,319,178 | $4.676 | 11h34m |
| deepseek-v4.1-flash-1017-medium | 89.6% | 8,720,152 | $4.538 | 11h03m |
| deepseek-v4.1-flash-1017-high | 86.7% | 11,881,493 | $5.812 | 14h39m |
| gpt-6.1-sol-medium | 83.7% | 1,321,029 | $13.160 | 8h58m |
| claude-opus-5.5-high | 82.2% | 1,724,765 | $34.335 | 4h29m |
| gpt-6.1-sol-low | 71.1% | 357,012 | $3.520 | 2h37m |
| claude-haiku-5.5-xhigh | 65.6% | 3,833,346 | $1.913 | 4h18m |
| gpt-6-luna-xhigh | 64.8% | 1,793,365 | $0.894 | 5h33m |
| gpt-6-luna-low | 63.7% | 184,683 | $0.090 | 57m30s |
| claude-haiku-5.5-high | 61.1% | 431,790 | $0.212 | 44m51s |
| claude-haiku-5.5-medium | 60.7% | 250,397 | $0.121 | 32m54s |
| claude-haiku-5.5-low | 59.3% | 172,132 | $0.082 | 27m12s |
| mercury-3 | 58.1% | 8,149,270 | $2.851 | 3h03m |
| gpt-6-luna-high | 57.0% | 992,386 | $0.494 | 3h25m |
| gpt-6-luna-medium | 54.4% | 507,826 | $0.251 | 1h52m |
| gpt-4-turbo | 50.0% | 7,023 | $0.081 | 7m55s |

Coverage: gemini-4-argon-high: tokens 269/271, cost 269/271; deepseek-v4.1-flash-1017-medium: tokens 271/273, cost 271/273; gpt-6-luna-low: tokens 270/271, cost 270/271; gpt-6-luna-medium: tokens 270/271, cost 270/271.

Tokens/cost are reported subtotals where usage is missing; not complete bills.
Accuracy = correct / scheduled cases within the scoped depths (invalid and no-response outcomes count as incorrect).
Tokens = sum of prompt + completion tokens across every attempt within scope, retries included; reasoning tokens are part of completion. Missing usage is never imputed as zero.
Cost is the provider-reported USD summed over every attempt within scope, retries included; amounts are shown as reported subtotals when some attempts lack pricing, never estimated as zero or imputed.
API time = sum of per-attempt request latency within scope (attempt admitted→response/error), retries included; it excludes rate-gate waits, retry backoff delay, and non-request time.
Rows reference only attempts whose case depth falls in the scoped range; whole-run aggregates are never used.
