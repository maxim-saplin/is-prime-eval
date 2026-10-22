# Prime-eval analysis

All discovered results are listed together; each row is one run (a completed parent+extension is shown once). Depth coverage, sample counts, and request policy are shown per run. Rankings sort by raw accuracy; runs with different frozen questions are not paired comparisons.

## Completed runs

| Rank | Model ID | Effort | Run (parent+child) | Depths / cases | Samples | Request policy | Provider route | Answered / scheduled | Correct | Approx. 95% Wilson CI | Incorrect | Incorrect reasons |
|---:|---|---|---|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | google/gemini-4-argon | high | aa41dde4 | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | Google, Google AI Studio | 356/360 | 336/360 (93.3%) | 90.3–95.5% | 24/360 (6.7%) | wrong label 12, invalid 8 (truncated 8, other 0), no response 4 |
| 2 | deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | Alibaba, Cloudflare, Crusoe, Decart, DeepInfra, GMICloud, InferenceNet, Ionstream, Morph, Parasail, PrimeIntellect, Relace, Together, Wafer | 360/360 | 334/360 (92.8%) | 89.6–95.0% | 26/360 (7.2%) | wrong label 14, invalid 12 (truncated 12, other 0), no response 0 |
| 3 | deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | Alibaba, Cloudflare, Crusoe, Decart, DeepInfra, GMICloud, InferenceNet, Ionstream, Morph, Parasail, PrimeIntellect, Reka, Relace, Sail Research, Together, Wafer | 360/360 | 332/360 (92.2%) | 89.0–94.6% | 28/360 (7.8%) | wrong label 23, invalid 5 (truncated 5, other 0), no response 0 |
| 4 | deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | Alibaba, Cloudflare, Crusoe, Decart, DeepInfra, InferenceNet, Ionstream, Morph, Parasail, PrimeIntellect, Reka, Relace, Together, Wafer | 360/360 | 324/360 (90.0%) | 86.5–92.7% | 36/360 (10.0%) | wrong label 16, invalid 20 (truncated 20, other 0), no response 0 |
| 5 | openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | Azure, OpenAI | 360/360 | 316/360 (87.8%) | 84.0–90.8% | 44/360 (12.2%) | wrong label 44, invalid 0 (truncated 0, other 0), no response 0 |
| 6 | anthropic/claude-opus-5.5 | high | eb477281 | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | Amazon Bedrock, Claude Platform on AWS | 360/360 | 300/360 (83.3%) | 79.1–86.8% | 60/360 (16.7%) | wrong label 8, invalid 52 (truncated 4, other 48), no response 0 |
| 7 | openai/gpt-6.1-sol | low | 779db032+238eae8a | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | OpenAI | 360/360 | 282/360 (78.3%) | 73.8–82.3% | 78/360 (21.7%) | wrong label 78, invalid 0 (truncated 0, other 0), no response 0 |
| 8 | anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | Claude Platform on AWS | 360/360 | 267/360 (74.2%) | 69.4–78.4% | 93/360 (25.8%) | wrong label 67, invalid 26 (truncated 23, other 3), no response 0 |
| 9 | openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | OpenAI | 360/360 | 262/360 (72.8%) | 68.0–77.1% | 98/360 (27.2%) | wrong label 98, invalid 0 (truncated 0, other 0), no response 0 |
| 10 | openai/gpt-6-luna | low | d6842886+3825f9e2 | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | OpenAI | 360/360 | 260/360 (72.2%) | 67.4–76.6% | 100/360 (27.8%) | wrong label 100, invalid 0 (truncated 0, other 0), no response 0 |
| 11 | anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | Claude Platform on AWS | 360/360 | 254/360 (70.6%) | 65.7–75.0% | 106/360 (29.4%) | wrong label 104, invalid 2 (truncated 0, other 2), no response 0 |
| 12 | anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | Claude Platform on AWS | 360/360 | 252/360 (70.0%) | 65.1–74.5% | 108/360 (30.0%) | wrong label 106, invalid 2 (truncated 0, other 2), no response 0 |
| 13 | inception/mercury-3 | omitted (provider default) | 8cba26bf | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | Inception | 360/360 | 247/360 (68.6%) | 63.6–73.2% | 113/360 (31.4%) | wrong label 8, invalid 105 (truncated 105, other 0), no response 0 |
| 14 | openai/gpt-6-luna | high | 61deca31+331d709d | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | OpenAI | 360/360 | 244/360 (67.8%) | 62.8–72.4% | 116/360 (32.2%) | wrong label 116, invalid 0 (truncated 0, other 0), no response 0 |
| 15 | anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | Claude Platform on AWS | 360/360 | 239/360 (66.4%) | 61.4–71.1% | 121/360 (33.6%) | wrong label 109, invalid 12 (truncated 0, other 12), no response 0 |
| 16 | openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | OpenAI | 360/360 | 236/360 (65.6%) | 60.5–70.3% | 124/360 (34.4%) | wrong label 124, invalid 0 (truncated 0, other 0), no response 0 |
| 17 | openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 4–15 / 360 cases | 15+15 per digit | 600.0s · 6 attempts · 1.0s retry · no cap · 15 RPM | OpenAI | 360/360 | 183/360 (50.8%) | 45.7–56.0% | 177/360 (49.2%) | wrong label 177, invalid 0 (truncated 0, other 0), no response 0 |

## Results by digit

| Model ID | Effort | Run (parent+child) | Digits | Correct | Approx. 95% Wilson CI | Incorrect | Truncated | Primes correctly identified | Non-primes correctly identified |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| google/gemini-4-argon | high | aa41dde4 | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| google/gemini-4-argon | high | aa41dde4 | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| google/gemini-4-argon | high | aa41dde4 | 6 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| google/gemini-4-argon | high | aa41dde4 | 7 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| google/gemini-4-argon | high | aa41dde4 | 8 | 29/30 (96.7%) | 83.3–99.4% | 1/30 (3.3%) | 0 | 15/15 | 14/15 |
| google/gemini-4-argon | high | aa41dde4 | 9 | 27/30 (90.0%) | 74.4–96.5% | 3/30 (10.0%) | 1 | 13/15 | 14/15 |
| google/gemini-4-argon | high | aa41dde4 | 10 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 2 | 13/15 | 15/15 |
| google/gemini-4-argon | high | aa41dde4 | 11 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 1 | 13/15 | 15/15 |
| google/gemini-4-argon | high | aa41dde4 | 12 | 29/30 (96.7%) | 83.3–99.4% | 1/30 (3.3%) | 1 | 14/15 | 15/15 |
| google/gemini-4-argon | high | aa41dde4 | 13 | 24/30 (80.0%) | 62.7–90.5% | 6/30 (20.0%) | 2 | 11/15 | 13/15 |
| google/gemini-4-argon | high | aa41dde4 | 14 | 27/30 (90.0%) | 74.4–96.5% | 3/30 (10.0%) | 0 | 13/15 | 14/15 |
| google/gemini-4-argon | high | aa41dde4 | 15 | 24/30 (80.0%) | 62.7–90.5% | 6/30 (20.0%) | 1 | 12/15 | 12/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 6 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 7 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 8 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 9 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 2 | 13/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 10 | 27/30 (90.0%) | 74.4–96.5% | 3/30 (10.0%) | 1 | 13/15 | 14/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 11 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 2 | 13/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 12 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 3 | 10/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 13 | 26/30 (86.7%) | 70.3–94.7% | 4/30 (13.3%) | 2 | 12/15 | 14/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 14 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 1 | 10/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 15 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 1 | 10/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 6 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 7 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 8 | 29/30 (96.7%) | 83.3–99.4% | 1/30 (3.3%) | 0 | 14/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 9 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 1 | 13/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 10 | 29/30 (96.7%) | 83.3–99.4% | 1/30 (3.3%) | 0 | 15/15 | 14/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 11 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 2 | 13/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 12 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 1 | 13/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 13 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 0 | 12/15 | 13/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 14 | 24/30 (80.0%) | 62.7–90.5% | 6/30 (20.0%) | 0 | 9/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 15 | 21/30 (70.0%) | 52.1–83.3% | 9/30 (30.0%) | 1 | 6/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 6 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 7 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 8 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 9 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 1 | 13/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 10 | 23/30 (76.7%) | 59.1–88.2% | 7/30 (23.3%) | 3 | 10/15 | 13/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 11 | 27/30 (90.0%) | 74.4–96.5% | 3/30 (10.0%) | 1 | 12/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 12 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 4 | 10/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 13 | 23/30 (76.7%) | 59.1–88.2% | 7/30 (23.3%) | 6 | 9/15 | 14/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 14 | 23/30 (76.7%) | 59.1–88.2% | 7/30 (23.3%) | 3 | 8/15 | 15/15 |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 15 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 2 | 10/15 | 15/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 6 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 7 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 8 | 26/30 (86.7%) | 70.3–94.7% | 4/30 (13.3%) | 0 | 11/15 | 15/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 9 | 20/30 (66.7%) | 48.8–80.8% | 10/30 (33.3%) | 0 | 5/15 | 15/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 10 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 0 | 11/15 | 14/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 11 | 26/30 (86.7%) | 70.3–94.7% | 4/30 (13.3%) | 0 | 11/15 | 15/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 12 | 23/30 (76.7%) | 59.1–88.2% | 7/30 (23.3%) | 0 | 8/15 | 15/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 13 | 24/30 (80.0%) | 62.7–90.5% | 6/30 (20.0%) | 0 | 10/15 | 14/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 14 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 0 | 10/15 | 15/15 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 15 | 27/30 (90.0%) | 74.4–96.5% | 3/30 (10.0%) | 0 | 12/15 | 15/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 4 | 24/30 (80.0%) | 62.7–90.5% | 6/30 (20.0%) | 0 | 15/15 | 9/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 5 | 26/30 (86.7%) | 70.3–94.7% | 4/30 (13.3%) | 0 | 15/15 | 11/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 6 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 0 | 15/15 | 13/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 7 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 0 | 15/15 | 13/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 8 | 29/30 (96.7%) | 83.3–99.4% | 1/30 (3.3%) | 0 | 14/15 | 15/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 9 | 21/30 (70.0%) | 52.1–83.3% | 9/30 (30.0%) | 1 | 10/15 | 11/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 10 | 26/30 (86.7%) | 70.3–94.7% | 4/30 (13.3%) | 0 | 14/15 | 12/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 11 | 24/30 (80.0%) | 62.7–90.5% | 6/30 (20.0%) | 0 | 12/15 | 12/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 12 | 23/30 (76.7%) | 59.1–88.2% | 7/30 (23.3%) | 1 | 11/15 | 12/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 13 | 24/30 (80.0%) | 62.7–90.5% | 6/30 (20.0%) | 2 | 10/15 | 14/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 14 | 24/30 (80.0%) | 62.7–90.5% | 6/30 (20.0%) | 0 | 11/15 | 13/15 |
| anthropic/claude-opus-5.5 | high | eb477281 | 15 | 23/30 (76.7%) | 59.1–88.2% | 7/30 (23.3%) | 0 | 12/15 | 11/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 6 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 7 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 8 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 9 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 0 | 10/15 | 15/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 10 | 23/30 (76.7%) | 59.1–88.2% | 7/30 (23.3%) | 0 | 9/15 | 14/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 11 | 19/30 (63.3%) | 45.5–78.1% | 11/30 (36.7%) | 0 | 4/15 | 15/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 12 | 17/30 (56.7%) | 39.2–72.6% | 13/30 (43.3%) | 0 | 2/15 | 15/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 13 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 14 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 15 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 6 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 7 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 0 | 13/15 | 15/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 8 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 0 | 13/15 | 15/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 9 | 26/30 (86.7%) | 70.3–94.7% | 4/30 (13.3%) | 2 | 11/15 | 15/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 10 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 10 | 3/15 | 13/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 11 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 9 | 1/15 | 14/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 12 | 18/30 (60.0%) | 42.3–75.4% | 12/30 (40.0%) | 1 | 3/15 | 15/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 13 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 1 | 2/15 | 14/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 14 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 1/15 | 14/15 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 15 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 5 | 29/30 (96.7%) | 83.3–99.4% | 1/30 (3.3%) | 0 | 15/15 | 14/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 6 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 0 | 13/15 | 15/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 7 | 27/30 (90.0%) | 74.4–96.5% | 3/30 (10.0%) | 0 | 12/15 | 15/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 8 | 27/30 (90.0%) | 74.4–96.5% | 3/30 (10.0%) | 0 | 12/15 | 15/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 9 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 0 | 10/15 | 15/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 10 | 20/30 (66.7%) | 48.8–80.8% | 10/30 (33.3%) | 0 | 5/15 | 15/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 11 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 12 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 13 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 14 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 15 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 6 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 0 | 13/15 | 15/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 7 | 21/30 (70.0%) | 52.1–83.3% | 9/30 (30.0%) | 0 | 7/15 | 14/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 8 | 24/30 (80.0%) | 62.7–90.5% | 6/30 (20.0%) | 0 | 9/15 | 15/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 9 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 0 | 10/15 | 15/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 10 | 19/30 (63.3%) | 45.5–78.1% | 11/30 (36.7%) | 0 | 4/15 | 15/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 11 | 19/30 (63.3%) | 45.5–78.1% | 11/30 (36.7%) | 0 | 5/15 | 14/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 12 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 13 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 2/15 | 13/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 14 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 2/15 | 14/15 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 15 | 17/30 (56.7%) | 39.2–72.6% | 13/30 (43.3%) | 0 | 2/15 | 15/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 6 | 29/30 (96.7%) | 83.3–99.4% | 1/30 (3.3%) | 0 | 14/15 | 15/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 7 | 23/30 (76.7%) | 59.1–88.2% | 7/30 (23.3%) | 0 | 8/15 | 15/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 8 | 22/30 (73.3%) | 55.6–85.8% | 8/30 (26.7%) | 0 | 7/15 | 15/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 9 | 25/30 (83.3%) | 66.4–92.7% | 5/30 (16.7%) | 0 | 10/15 | 15/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 10 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 11 | 17/30 (56.7%) | 39.2–72.6% | 13/30 (43.3%) | 0 | 3/15 | 14/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 12 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 13 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 14 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 15 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 6 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 0 | 13/15 | 15/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 7 | 23/30 (76.7%) | 59.1–88.2% | 7/30 (23.3%) | 0 | 8/15 | 15/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 8 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 0 | 13/15 | 15/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 9 | 20/30 (66.7%) | 48.8–80.8% | 10/30 (33.3%) | 0 | 5/15 | 15/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 10 | 18/30 (60.0%) | 42.3–75.4% | 12/30 (40.0%) | 0 | 3/15 | 15/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 11 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 12 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 13 | 13/30 (43.3%) | 27.4–60.8% | 17/30 (56.7%) | 0 | 0/15 | 13/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 14 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 15 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 6 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 7 | 27/30 (90.0%) | 74.4–96.5% | 3/30 (10.0%) | 2 | 12/15 | 15/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 8 | 17/30 (56.7%) | 39.2–72.6% | 13/30 (43.3%) | 12 | 2/15 | 15/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 9 | 17/30 (56.7%) | 39.2–72.6% | 13/30 (43.3%) | 11 | 2/15 | 15/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 10 | 14/30 (46.7%) | 30.2–63.9% | 16/30 (53.3%) | 15 | 0/15 | 14/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 11 | 18/30 (60.0%) | 42.3–75.4% | 12/30 (40.0%) | 12 | 3/15 | 15/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 12 | 17/30 (56.7%) | 39.2–72.6% | 13/30 (43.3%) | 12 | 3/15 | 14/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 13 | 14/30 (46.7%) | 30.2–63.9% | 16/30 (53.3%) | 16 | 1/15 | 13/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 14 | 18/30 (60.0%) | 42.3–75.4% | 12/30 (40.0%) | 11 | 3/15 | 15/15 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 15 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 14 | 3/15 | 12/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 6 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 7 | 26/30 (86.7%) | 70.3–94.7% | 4/30 (13.3%) | 0 | 11/15 | 15/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 8 | 20/30 (66.7%) | 48.8–80.8% | 10/30 (33.3%) | 0 | 5/15 | 15/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 9 | 17/30 (56.7%) | 39.2–72.6% | 13/30 (43.3%) | 0 | 2/15 | 15/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 10 | 17/30 (56.7%) | 39.2–72.6% | 13/30 (43.3%) | 0 | 2/15 | 15/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 11 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 12 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 13 | 14/30 (46.7%) | 30.2–63.9% | 16/30 (53.3%) | 0 | 0/15 | 14/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 14 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 15 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 4 | 24/30 (80.0%) | 62.7–90.5% | 6/30 (20.0%) | 0 | 15/15 | 9/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 5 | 27/30 (90.0%) | 74.4–96.5% | 3/30 (10.0%) | 0 | 15/15 | 12/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 6 | 28/30 (93.3%) | 78.7–98.2% | 2/30 (6.7%) | 0 | 15/15 | 13/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 7 | 24/30 (80.0%) | 62.7–90.5% | 6/30 (20.0%) | 0 | 10/15 | 14/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 8 | 19/30 (63.3%) | 45.5–78.1% | 11/30 (36.7%) | 0 | 4/15 | 15/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 9 | 21/30 (70.0%) | 52.1–83.3% | 9/30 (30.0%) | 0 | 6/15 | 15/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 10 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 11 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 12 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 13 | 17/30 (56.7%) | 39.2–72.6% | 13/30 (43.3%) | 0 | 2/15 | 15/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 14 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 15 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 4 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 5 | 30/30 (100.0%) | 88.6–100.0% | 0/30 (0.0%) | 0 | 15/15 | 15/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 6 | 29/30 (96.7%) | 83.3–99.4% | 1/30 (3.3%) | 0 | 14/15 | 15/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 7 | 21/30 (70.0%) | 52.1–83.3% | 9/30 (30.0%) | 0 | 7/15 | 14/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 8 | 20/30 (66.7%) | 48.8–80.8% | 10/30 (33.3%) | 0 | 5/15 | 15/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 9 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 10 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 11 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 12 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 13 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 14 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 15 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 4 | 17/30 (56.7%) | 39.2–72.6% | 13/30 (43.3%) | 0 | 3/15 | 14/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 5 | 16/30 (53.3%) | 36.1–69.8% | 14/30 (46.7%) | 0 | 1/15 | 15/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 6 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 7 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 8 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 9 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 10 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 11 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 12 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 13 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 14 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 15 | 15/30 (50.0%) | 33.2–66.8% | 15/30 (50.0%) | 0 | 0/15 | 15/15 |

## Cost per run

| Model ID | Effort | Run (parent+child) | Prompt / completion tokens | Provider-reported cost (USD) | Estimated cost without cache discounts (USD) |
|---|---|---|---:|---:|---:|
| google/gemini-4-argon | high | aa41dde4 | 18,681 / 4,133,350 (359/361 attempts with token counts) | Partial $41.370862 (359/361 requests priced) | Partial $41.370862 (359/361 requests priced) |
| deepseek/deepseek-v4.1-flash-1017 | low | e2e68e4c+a09208ca | 17,100 / 9,449,512 (360/360 attempts with token counts) | $4.761496 | $10.009619 |
| deepseek/deepseek-v4.1-flash-1017 | medium | 4a29e765+6c380301 | 17,115 / 8,870,717 (361/363 attempts with token counts) | Partial $4.643778 (361/363 requests priced) | Partial $9.377424 (361/363 requests priced) |
| deepseek/deepseek-v4.1-flash-1017 | high | 59080548+892bc742 | 12,758 / 12,055,456 (360/360 attempts with token counts) | $5.927436 | $12.696274 |
| openai/gpt-6.1-sol | medium | 8627f7ce+ac75aa0d | 8,114 / 1,351,321 (361/362 attempts with token counts) | Partial $13.529410 (361/362 requests priced) | Partial $13.529438 (361/362 requests priced) |
| anthropic/claude-opus-5.5 | high | eb477281 | 13,140 / 1,761,811 (360/360 attempts with token counts) | $35.288780 | $35.288780 |
| openai/gpt-6.1-sol | low | 779db032+238eae8a | 8,100 / 384,006 (360/360 attempts with token counts) | $3.856260 | $3.856260 |
| anthropic/claude-haiku-5.5 | xhigh | dcfbefa8+78bbbe1d | 13,140 / 4,006,685 (360/360 attempts with token counts) | $2.004656 | $2.004656 |
| openai/gpt-6-luna | xhigh | 42a1f16f+84585d5e | 8,100 / 1,915,920 (360/360 attempts with token counts) | $0.958770 | $0.958770 |
| openai/gpt-6-luna | low | d6842886+3825f9e2 | 8,100 / 209,759 (360/361 attempts with token counts) | Partial $0.105690 (360/361 requests priced) | Partial $0.105690 (360/361 requests priced) |
| anthropic/claude-haiku-5.5 | high | 812489fb+8c016781 | 13,140 / 516,776 (360/360 attempts with token counts) | $0.259702 | $0.259702 |
| anthropic/claude-haiku-5.5 | medium | 78b819ef+239bfedf | 13,140 / 306,767 (360/360 attempts with token counts) | $0.154698 | $0.154698 |
| inception/mercury-3 | omitted (provider default) | 8cba26bf | 5,940 / 8,258,096 (360/360 attempts with token counts) | $2.890896 | $2.890928 |
| openai/gpt-6-luna | high | 61deca31+331d709d | 8,100 / 1,085,696 (360/360 attempts with token counts) | $0.543658 | $0.543658 |
| anthropic/claude-haiku-5.5 | low | 746fc055+a7a5e156 | 13,140 / 213,599 (360/360 attempts with token counts) | $0.108114 | $0.108114 |
| openai/gpt-6-luna | medium | 16ecc6c5+748b403d | 8,100 / 567,903 (360/361 attempts with token counts) | Partial $0.284762 (360/361 requests priced) | Partial $0.284762 (360/361 requests priced) |
| openai/gpt-4-turbo | omitted (provider default) | e85bb334+00d72f96 | 8,460 / 724 (360/360 attempts with token counts) | $0.106320 | $0.106320 |

Incorrect includes wrong labels, invalid responses, and retry-exhausted no-response items. Truncated is a sub-count of invalid responses. Percentages use every scheduled case. Approximate 95% Wilson intervals are per-run item-level summaries, not population, session-to-session, or model-difference intervals; incomplete runs have no interval. Runs with different question sets or sample counts are shown together for inventory, but their rankings are descriptive, not paired comparisons. Costs cover all request attempts; partial/unknown coverage is labeled, never treated as $0.
