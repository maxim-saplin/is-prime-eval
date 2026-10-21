# Prime-eval leaderboard

## Dataset `prime-v1-fc48a8ff5cee2be5`

Prompt: `prime-label-v1` · Digits: 4, 5, 6, 7, 8, 9, 10 · Samples: 10 prime + 10 non-prime per digit · Max attempts: 6 · Completion token cap: no explicit token cap · Timeout: 600.0s · Retry delay: 1.0s · Effort shown per model

### Model results

| Rank | Model ID | Effort | Provider route | Run | Answered / scheduled | Correct | Approx. 95% Wilson CI | Incorrect | Incorrect reasons |
|---:|---|---|---|---|---:|---:|---:|---:|---|
| 1 | deepseek/deepseek-v4.1-flash-1017 | medium | Alibaba, Cloudflare, Crusoe, Decart, GMICloud, InferenceNet, Morph, Parasail, PrimeIntellect, Relace, Together, Wafer | 4a29e765 | 140/140 | 138/140 (98.6%) | 94.9–99.6% | 2/140 (1.4%) | wrong label 1, invalid 1 (truncated 1, other 0), no response 0 |
| 2 | deepseek/deepseek-v4.1-flash-1017 | low | Alibaba, Crusoe, Decart, GMICloud, InferenceNet, Morph, Parasail, PrimeIntellect, Relace, Together, Wafer | e2e68e4c | 140/140 | 137/140 (97.9%) | 93.9–99.3% | 3/140 (2.1%) | wrong label 2, invalid 1 (truncated 1, other 0), no response 0 |
| 3 | deepseek/deepseek-v4.1-flash-1017 | high | Alibaba, Cloudflare, Crusoe, Decart, DeepInfra, InferenceNet, Morph, PrimeIntellect, Relace, Together, Wafer | 59080548 | 140/140 | 136/140 (97.1%) | 92.9–98.9% | 4/140 (2.9%) | wrong label 3, invalid 1 (truncated 1, other 0), no response 0 |
| 4 | openai/gpt-6.1-sol | low | OpenAI | 779db032 | 140/140 | 133/140 (95.0%) | 90.0–97.6% | 7/140 (5.0%) | wrong label 7, invalid 0 (truncated 0, other 0), no response 0 |
| 5 | openai/gpt-6-luna | xhigh | OpenAI | 42a1f16f | 140/140 | 127/140 (90.7%) | 84.8–94.5% | 13/140 (9.3%) | wrong label 13, invalid 0 (truncated 0, other 0), no response 0 |
| 6 | openai/gpt-6.1-sol | medium | OpenAI | 8627f7ce | 140/140 | 126/140 (90.0%) | 83.9–93.9% | 14/140 (10.0%) | wrong label 14, invalid 0 (truncated 0, other 0), no response 0 |
| 7 | anthropic/claude-haiku-5.5 | xhigh | Claude Platform on AWS | dcfbefa8 | 140/140 | 125/140 (89.3%) | 83.1–93.4% | 15/140 (10.7%) | wrong label 6, invalid 9 (truncated 8, other 1), no response 0 |
| 8 | anthropic/claude-haiku-5.5 | high | Claude Platform on AWS | 812489fb | 140/140 | 118/140 (84.3%) | 77.4–89.4% | 22/140 (15.7%) | wrong label 22, invalid 0 (truncated 0, other 0), no response 0 |
| 9 | anthropic/claude-haiku-5.5 | medium | Claude Platform on AWS | 78b819ef | 140/140 | 116/140 (82.9%) | 75.8–88.2% | 24/140 (17.1%) | wrong label 23, invalid 1 (truncated 0, other 1), no response 0 |
| 10 | openai/gpt-6-luna | low | OpenAI | d6842886 | 140/140 | 116/140 (82.9%) | 75.8–88.2% | 24/140 (17.1%) | wrong label 24, invalid 0 (truncated 0, other 0), no response 0 |
| 11 | openai/gpt-6-luna | high | OpenAI | 61deca31 | 140/140 | 113/140 (80.7%) | 73.4–86.4% | 27/140 (19.3%) | wrong label 27, invalid 0 (truncated 0, other 0), no response 0 |
| 12 | anthropic/claude-haiku-5.5 | low | Claude Platform on AWS | 746fc055 | 140/140 | 106/140 (75.7%) | 68.0–82.1% | 34/140 (24.3%) | wrong label 27, invalid 7 (truncated 0, other 7), no response 0 |
| 13 | openai/gpt-6-luna | medium | OpenAI | 16ecc6c5 | 140/140 | 105/140 (75.0%) | 67.2–81.4% | 35/140 (25.0%) | wrong label 35, invalid 0 (truncated 0, other 0), no response 0 |
| 14 | openai/gpt-4-turbo | omitted (provider default) | OpenAI | e85bb334 | 140/140 | 70/140 (50.0%) | 41.8–58.2% | 70/140 (50.0%) | wrong label 70, invalid 0 (truncated 0, other 0), no response 0 |

### Results by digit

| Model ID | Effort | Run | Digits | Correct | Approx. 95% Wilson CI | Incorrect | Truncated | Primes correctly identified | Non-primes correctly identified |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765 | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765 | 5 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765 | 6 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765 | 7 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765 | 8 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765 | 9 | 18/20 (90.0%) | 69.9–97.2% | 2/20 (10.0%) | 1 | 8/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765 | 10 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c | 5 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c | 6 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c | 7 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c | 8 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c | 9 | 19/20 (95.0%) | 76.4–99.1% | 1/20 (5.0%) | 1 | 9/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c | 10 | 18/20 (90.0%) | 69.9–97.2% | 2/20 (10.0%) | 0 | 9/10 | 9/10 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548 | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548 | 5 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548 | 6 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548 | 7 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548 | 8 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548 | 9 | 19/20 (95.0%) | 76.4–99.1% | 1/20 (5.0%) | 0 | 9/10 | 10/10 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548 | 10 | 17/20 (85.0%) | 64.0–94.8% | 3/20 (15.0%) | 1 | 8/10 | 9/10 |
| openai/gpt-6.1-sol | low | 779db032 | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6.1-sol | low | 779db032 | 5 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6.1-sol | low | 779db032 | 6 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6.1-sol | low | 779db032 | 7 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6.1-sol | low | 779db032 | 8 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6.1-sol | low | 779db032 | 9 | 17/20 (85.0%) | 64.0–94.8% | 3/20 (15.0%) | 0 | 7/10 | 10/10 |
| openai/gpt-6.1-sol | low | 779db032 | 10 | 16/20 (80.0%) | 58.4–91.9% | 4/20 (20.0%) | 0 | 6/10 | 10/10 |
| openai/gpt-6-luna | xhigh | 42a1f16f | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6-luna | xhigh | 42a1f16f | 5 | 19/20 (95.0%) | 76.4–99.1% | 1/20 (5.0%) | 0 | 10/10 | 9/10 |
| openai/gpt-6-luna | xhigh | 42a1f16f | 6 | 19/20 (95.0%) | 76.4–99.1% | 1/20 (5.0%) | 0 | 9/10 | 10/10 |
| openai/gpt-6-luna | xhigh | 42a1f16f | 7 | 19/20 (95.0%) | 76.4–99.1% | 1/20 (5.0%) | 0 | 9/10 | 10/10 |
| openai/gpt-6-luna | xhigh | 42a1f16f | 8 | 18/20 (90.0%) | 69.9–97.2% | 2/20 (10.0%) | 0 | 8/10 | 10/10 |
| openai/gpt-6-luna | xhigh | 42a1f16f | 9 | 18/20 (90.0%) | 69.9–97.2% | 2/20 (10.0%) | 0 | 8/10 | 10/10 |
| openai/gpt-6-luna | xhigh | 42a1f16f | 10 | 14/20 (70.0%) | 48.1–85.5% | 6/20 (30.0%) | 0 | 4/10 | 10/10 |
| openai/gpt-6.1-sol | medium | 8627f7ce | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6.1-sol | medium | 8627f7ce | 5 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6.1-sol | medium | 8627f7ce | 6 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6.1-sol | medium | 8627f7ce | 7 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6.1-sol | medium | 8627f7ce | 8 | 17/20 (85.0%) | 64.0–94.8% | 3/20 (15.0%) | 0 | 7/10 | 10/10 |
| openai/gpt-6.1-sol | medium | 8627f7ce | 9 | 13/20 (65.0%) | 43.3–81.9% | 7/20 (35.0%) | 0 | 3/10 | 10/10 |
| openai/gpt-6.1-sol | medium | 8627f7ce | 10 | 16/20 (80.0%) | 58.4–91.9% | 4/20 (20.0%) | 0 | 7/10 | 9/10 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8 | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8 | 5 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8 | 6 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8 | 7 | 18/20 (90.0%) | 69.9–97.2% | 2/20 (10.0%) | 0 | 8/10 | 10/10 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8 | 8 | 19/20 (95.0%) | 76.4–99.1% | 1/20 (5.0%) | 0 | 9/10 | 10/10 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8 | 9 | 17/20 (85.0%) | 64.0–94.8% | 3/20 (15.0%) | 2 | 7/10 | 10/10 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8 | 10 | 11/20 (55.0%) | 34.2–74.2% | 9/20 (45.0%) | 6 | 2/10 | 9/10 |
| anthropic/claude-haiku-5.5 | high | 812489fb | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| anthropic/claude-haiku-5.5 | high | 812489fb | 5 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| anthropic/claude-haiku-5.5 | high | 812489fb | 6 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| anthropic/claude-haiku-5.5 | high | 812489fb | 7 | 16/20 (80.0%) | 58.4–91.9% | 4/20 (20.0%) | 0 | 6/10 | 10/10 |
| anthropic/claude-haiku-5.5 | high | 812489fb | 8 | 14/20 (70.0%) | 48.1–85.5% | 6/20 (30.0%) | 0 | 4/10 | 10/10 |
| anthropic/claude-haiku-5.5 | high | 812489fb | 9 | 17/20 (85.0%) | 64.0–94.8% | 3/20 (15.0%) | 0 | 7/10 | 10/10 |
| anthropic/claude-haiku-5.5 | high | 812489fb | 10 | 11/20 (55.0%) | 34.2–74.2% | 9/20 (45.0%) | 0 | 1/10 | 10/10 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef | 5 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef | 6 | 19/20 (95.0%) | 76.4–99.1% | 1/20 (5.0%) | 0 | 9/10 | 10/10 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef | 7 | 15/20 (75.0%) | 53.1–88.8% | 5/20 (25.0%) | 0 | 5/10 | 10/10 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef | 8 | 18/20 (90.0%) | 69.9–97.2% | 2/20 (10.0%) | 0 | 8/10 | 10/10 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef | 9 | 13/20 (65.0%) | 43.3–81.9% | 7/20 (35.0%) | 0 | 3/10 | 10/10 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef | 10 | 11/20 (55.0%) | 34.2–74.2% | 9/20 (45.0%) | 0 | 1/10 | 10/10 |
| openai/gpt-6-luna | low | d6842886 | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6-luna | low | d6842886 | 5 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6-luna | low | d6842886 | 6 | 18/20 (90.0%) | 69.9–97.2% | 2/20 (10.0%) | 0 | 8/10 | 10/10 |
| openai/gpt-6-luna | low | d6842886 | 7 | 14/20 (70.0%) | 48.1–85.5% | 6/20 (30.0%) | 0 | 5/10 | 9/10 |
| openai/gpt-6-luna | low | d6842886 | 8 | 15/20 (75.0%) | 53.1–88.8% | 5/20 (25.0%) | 0 | 5/10 | 10/10 |
| openai/gpt-6-luna | low | d6842886 | 9 | 16/20 (80.0%) | 58.4–91.9% | 4/20 (20.0%) | 0 | 6/10 | 10/10 |
| openai/gpt-6-luna | low | d6842886 | 10 | 13/20 (65.0%) | 43.3–81.9% | 7/20 (35.0%) | 0 | 3/10 | 10/10 |
| openai/gpt-6-luna | high | 61deca31 | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6-luna | high | 61deca31 | 5 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6-luna | high | 61deca31 | 6 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6-luna | high | 61deca31 | 7 | 17/20 (85.0%) | 64.0–94.8% | 3/20 (15.0%) | 0 | 7/10 | 10/10 |
| openai/gpt-6-luna | high | 61deca31 | 8 | 13/20 (65.0%) | 43.3–81.9% | 7/20 (35.0%) | 0 | 3/10 | 10/10 |
| openai/gpt-6-luna | high | 61deca31 | 9 | 11/20 (55.0%) | 34.2–74.2% | 9/20 (45.0%) | 0 | 1/10 | 10/10 |
| openai/gpt-6-luna | high | 61deca31 | 10 | 12/20 (60.0%) | 38.7–78.1% | 8/20 (40.0%) | 0 | 2/10 | 10/10 |
| anthropic/claude-haiku-5.5 | low | 746fc055 | 4 | 16/20 (80.0%) | 58.4–91.9% | 4/20 (20.0%) | 0 | 10/10 | 6/10 |
| anthropic/claude-haiku-5.5 | low | 746fc055 | 5 | 18/20 (90.0%) | 69.9–97.2% | 2/20 (10.0%) | 0 | 10/10 | 8/10 |
| anthropic/claude-haiku-5.5 | low | 746fc055 | 6 | 19/20 (95.0%) | 76.4–99.1% | 1/20 (5.0%) | 0 | 10/10 | 9/10 |
| anthropic/claude-haiku-5.5 | low | 746fc055 | 7 | 16/20 (80.0%) | 58.4–91.9% | 4/20 (20.0%) | 0 | 6/10 | 10/10 |
| anthropic/claude-haiku-5.5 | low | 746fc055 | 8 | 13/20 (65.0%) | 43.3–81.9% | 7/20 (35.0%) | 0 | 3/10 | 10/10 |
| anthropic/claude-haiku-5.5 | low | 746fc055 | 9 | 14/20 (70.0%) | 48.1–85.5% | 6/20 (30.0%) | 0 | 4/10 | 10/10 |
| anthropic/claude-haiku-5.5 | low | 746fc055 | 10 | 10/20 (50.0%) | 29.9–70.1% | 10/20 (50.0%) | 0 | 0/10 | 10/10 |
| openai/gpt-6-luna | medium | 16ecc6c5 | 4 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6-luna | medium | 16ecc6c5 | 5 | 20/20 (100.0%) | 83.9–100.0% | 0/20 (0.0%) | 0 | 10/10 | 10/10 |
| openai/gpt-6-luna | medium | 16ecc6c5 | 6 | 19/20 (95.0%) | 76.4–99.1% | 1/20 (5.0%) | 0 | 9/10 | 10/10 |
| openai/gpt-6-luna | medium | 16ecc6c5 | 7 | 13/20 (65.0%) | 43.3–81.9% | 7/20 (35.0%) | 0 | 4/10 | 9/10 |
| openai/gpt-6-luna | medium | 16ecc6c5 | 8 | 13/20 (65.0%) | 43.3–81.9% | 7/20 (35.0%) | 0 | 3/10 | 10/10 |
| openai/gpt-6-luna | medium | 16ecc6c5 | 9 | 10/20 (50.0%) | 29.9–70.1% | 10/20 (50.0%) | 0 | 0/10 | 10/10 |
| openai/gpt-6-luna | medium | 16ecc6c5 | 10 | 10/20 (50.0%) | 29.9–70.1% | 10/20 (50.0%) | 0 | 0/10 | 10/10 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334 | 4 | 10/20 (50.0%) | 29.9–70.1% | 10/20 (50.0%) | 0 | 1/10 | 9/10 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334 | 5 | 10/20 (50.0%) | 29.9–70.1% | 10/20 (50.0%) | 0 | 0/10 | 10/10 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334 | 6 | 10/20 (50.0%) | 29.9–70.1% | 10/20 (50.0%) | 0 | 0/10 | 10/10 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334 | 7 | 10/20 (50.0%) | 29.9–70.1% | 10/20 (50.0%) | 0 | 0/10 | 10/10 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334 | 8 | 10/20 (50.0%) | 29.9–70.1% | 10/20 (50.0%) | 0 | 0/10 | 10/10 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334 | 9 | 10/20 (50.0%) | 29.9–70.1% | 10/20 (50.0%) | 0 | 0/10 | 10/10 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334 | 10 | 10/20 (50.0%) | 29.9–70.1% | 10/20 (50.0%) | 0 | 0/10 | 10/10 |

### Cost per run

| Model ID | Effort | Provider route | Run | Prompt / completion tokens | Provider-reported cost (USD) | Estimated cost without cache discounts (USD) |
|---|---|---|---|---:|---:|---:|
| deepseek/deepseek-v4.1-flash-1017 | medium | Alibaba, Cloudflare, Crusoe, Decart, GMICloud, InferenceNet, Morph, Parasail, PrimeIntellect, Relace, Together, Wafer | 4a29e765 | 6,540 / 2,119,316 (140/140 attempts with token counts) | $1.359489 | $1.272571 |
| deepseek/deepseek-v4.1-flash-1017 | low | Alibaba, Crusoe, Decart, GMICloud, InferenceNet, Morph, Parasail, PrimeIntellect, Relace, Together, Wafer | e2e68e4c | 6,540 / 2,223,241 (140/140 attempts with token counts) | $1.350023 | $1.334926 |
| deepseek/deepseek-v4.1-flash-1017 | high | Alibaba, Cloudflare, Crusoe, Decart, DeepInfra, InferenceNet, Morph, PrimeIntellect, Relace, Together, Wafer | 59080548 | 4,850 / 2,955,622 (140/140 attempts with token counts) | $1.469676 | $1.774101 |
| openai/gpt-6.1-sol | low | OpenAI | 779db032 | 3,040 / 149,531 (140/140 attempts with token counts) | $1.501390 | $1.501390 |
| openai/gpt-6-luna | xhigh | OpenAI | 42a1f16f | 3,040 / 696,112 (140/140 attempts with token counts) | $0.348360 | $0.348360 |
| openai/gpt-6.1-sol | medium | OpenAI | 8627f7ce | 3,054 / 412,697 (141/142 attempts with token counts) | Partial $4.133050 (141/142 requests priced) | Partial $4.133078 (141/142 requests priced) |
| anthropic/claude-haiku-5.5 | xhigh | Claude Platform on AWS | dcfbefa8 | 5,000 / 1,630,973 (140/140 attempts with token counts) | $0.815986 | $0.815986 |
| anthropic/claude-haiku-5.5 | high | Claude Platform on AWS | 812489fb | 5,000 / 195,094 (140/140 attempts with token counts) | $0.098047 | $0.098047 |
| anthropic/claude-haiku-5.5 | medium | Claude Platform on AWS | 78b819ef | 5,000 / 115,797 (140/140 attempts with token counts) | $0.058398 | $0.058398 |
| openai/gpt-6-luna | low | OpenAI | d6842886 | 3,040 / 74,010 (140/140 attempts with token counts) | $0.037309 | $0.037309 |
| openai/gpt-6-luna | high | OpenAI | 61deca31 | 3,040 / 386,029 (140/140 attempts with token counts) | $0.193318 | $0.193318 |
| anthropic/claude-haiku-5.5 | low | Claude Platform on AWS | 746fc055 | 5,000 / 81,415 (140/140 attempts with token counts) | $0.041208 | $0.041208 |
| openai/gpt-6-luna | medium | OpenAI | 16ecc6c5 | 3,040 / 190,898 (140/140 attempts with token counts) | $0.095753 | $0.095753 |
| openai/gpt-4-turbo | omitted (provider default) | OpenAI | e85bb334 | 3,180 / 281 (140/140 attempts with token counts) | $0.040230 | $0.040230 |

Incorrect includes wrong labels, invalid responses, and retry-exhausted no-response items. Invalid and no-response counts are shown separately as reasons; truncated is an invalid-response sub-count. Percentages use all scheduled cases. Approximate 95% Wilson intervals are item-level summaries for this fixed, balanced test set, not population or model-superiority intervals; incomplete runs have no interval. Costs cover all request attempts; partial/unknown coverage is labeled, never treated as $0.
