# Artifact cleanup receipt — invalid 512-token runs

All listed capped empirical outputs were moved with recoverable `gio trash`; no `rm` was used. The original 115-payload cleanup performed no API calls, source edits, staging, commits, or pushes. The offline recovery follow-up below moved 9 additional payloads and updated documentation alongside the separately QA-approved implementation for a targeted source/tests/docs commit; no API calls or pushes were performed. SHA-256 values are for original file bytes before moving. Every moved payload's SHA-256 and size were checked against its Trash copy. The `prior move verified` flag is a pre-receipt path check: `False` means the move was performed during this cleanup pass, not that the payload checksum failed.

## Inventory summary

- All 41 run-manifest copies explicitly declared `max_completion_tokens=512`, representing 27 unique run IDs; the 14 repo copies duplicated the 14 clean-sweep runs found externally.
- The moved artifact set contains capped ledgers/manifests, run locks, generated leaderboards, preflight/progress/inventory/checksum/stop sidecars, and duplicate or run-specific dataset copies.
- The formerly preserved shared dataset `results/datasets/prime-v1-fc48a8ff5cee2be5.json` was also moved recoverably in the follow-up below; file SHA-256 `4e4fd21d08a5538c985a3f489a47f15e960adc55adc1c074595c56ba393646db`; dataset SHA-256 `fc48a8ff5cee2be50fc87f51916018fba9bb856ea28b3616edfc734e7ebd9652`. No prior dataset remains in active repo results; fresh deterministic generation is deferred to the user's launch.
- The repo copy of run-specific dataset `prime-v1-66a3cb95d6b586fb` and its external duplicate are now both in Trash.
- The formerly deferred `/data/eval-runs/is-prim-eval/2026-10-19/results` directory (8 files including a copied LibreOffice lock) was inspected and successfully moved recoverably in the follow-up. No attempt was made to close/kill LibreOffice. No cleanup paths remain deferred.
- Preserved static checkpoint READMEs, source files (`cases.py`, `prime_stats.py`, `prime-stats.md`, runner/client code/tests), and host lock `/data/eval-runs/is-prim-eval/.13-pair-sweep-live.lock`.
- No capped-run leaderboard remains in active project/result paths; future uncapped actual results are to be written in repo `results/`.

## Recoverable Trash mappings

### Directory: `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep`
Trash info: `/data/.Trash-1000/info/13-pair-sweep.trashinfo`; Trash entry: `/data/.Trash-1000/files/13-pair-sweep`; prior move verified: `True`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/ARCHIVE-SHA256SUMS.txt` | `99d36ebd9cde6e006c6aaeb8bc04e8cd28e46e49034f1698d7c21cfffd29d510` | `/data/.Trash-1000/files/13-pair-sweep/ARCHIVE-SHA256SUMS.txt` | 2468 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/SHA256SUMS.txt` | `373dc7699e2331de7cf951a07a86be313ee83c88ca6b57fffc4558b5320a7f1b` | `/data/.Trash-1000/files/13-pair-sweep/SHA256SUMS.txt` | 2193 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/datasets/prime-v1-fc48a8ff5cee2be5.json` | `4e4fd21d08a5538c985a3f489a47f15e960adc55adc1c074595c56ba393646db` | `/data/.Trash-1000/files/13-pair-sweep/datasets/prime-v1-fc48a8ff5cee2be5.json` | 16028 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/live-tty.log` | `d885413bf9f7af1b60198a13e02f3b36be4f28e7e8f125a25a51cdc98cf25b34` | `/data/.Trash-1000/files/13-pair-sweep/live-tty.log` | 1033192 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T202017Z_b8672e60.jsonl` | `f1cb50facb2d3b6c9a1645f6c46eb603d4b2a7f1d2e9b775aa2aed619e0fa761` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T202017Z_b8672e60.jsonl` | 404661 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T202017Z_b8672e60.jsonl.lock` | `e2bf161ea8e08f1ed3f034963646d3b9baea7ea976bb3f9116cb47c02fff01d8` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T202017Z_b8672e60.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T202017Z_b8672e60.manifest.json` | `6c87247aae39f83d3981e0c7cb9edb29fed06d69a28c52566064f2481c1f643b` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T202017Z_b8672e60.manifest.json` | 2099 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T202017Z_29edd52b.jsonl` | `07699987f1be9ab9d1a8be9ff500b0367f95735b2c82cd0f23f315ef4f163b37` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T202017Z_29edd52b.jsonl` | 403898 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T202017Z_29edd52b.jsonl.lock` | `e2bf161ea8e08f1ed3f034963646d3b9baea7ea976bb3f9116cb47c02fff01d8` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T202017Z_29edd52b.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T202017Z_29edd52b.manifest.json` | `7a3ab5ca72021e115fe9490aa83bea0eb6047633deadd420960e69e47c0c9ac5` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T202017Z_29edd52b.manifest.json` | 2096 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-medium-c082456a77_20261019T202017Z_d629fd74.jsonl` | `8c5591371f0d51a16eb18aa2e6592ee6db019d55c2e875d2ec1aac58066e85a1` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-medium-c082456a77_20261019T202017Z_d629fd74.jsonl` | 386987 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-medium-c082456a77_20261019T202017Z_d629fd74.jsonl.lock` | `e2bf161ea8e08f1ed3f034963646d3b9baea7ea976bb3f9116cb47c02fff01d8` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-medium-c082456a77_20261019T202017Z_d629fd74.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-medium-c082456a77_20261019T202017Z_d629fd74.manifest.json` | `1cfaccd632224b7fbe5a8cfcd9f35c8da3ac6c731d8cafa9b45b2347ca301539` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-medium-c082456a77_20261019T202017Z_d629fd74.manifest.json` | 2105 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-xhigh-b5255978be_20261019T202017Z_95efde4f.jsonl` | `676048468f7e7fe9b4cab256135dedf4e59acce259fbea56c2c2a764d2d1f52e` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-xhigh-b5255978be_20261019T202017Z_95efde4f.jsonl` | 411129 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-xhigh-b5255978be_20261019T202017Z_95efde4f.jsonl.lock` | `e2bf161ea8e08f1ed3f034963646d3b9baea7ea976bb3f9116cb47c02fff01d8` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-xhigh-b5255978be_20261019T202017Z_95efde4f.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/openai-gpt-6-luna__effort-xhigh-b5255978be_20261019T202017Z_95efde4f.manifest.json` | `b6603949682ef5f57ce26b13d1379cfdc5c59fb9f2dc4681a078a353345168a3` | `/data/.Trash-1000/files/13-pair-sweep/openai-gpt-6-luna__effort-xhigh-b5255978be_20261019T202017Z_95efde4f.manifest.json` | 2102 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/partial-batch-inventory.json` | `8fcdc5dea03348086bcd3b9c4354566b86715363b30a4716ed39592a6a2498c2` | `/data/.Trash-1000/files/13-pair-sweep/partial-batch-inventory.json` | 21447 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/partial-batch-inventory.md` | `688d4fe214da5c1585cd53c92c4612b03b33ce7fca8a920498c19386bc1a1147` | `/data/.Trash-1000/files/13-pair-sweep/partial-batch-inventory.md` | 3815 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/preflight.txt` | `63e3bd116c7f1921413ad5fdd6d88d9225bd6087af27bad8ab4baa28f017c358` | `/data/.Trash-1000/files/13-pair-sweep/preflight.txt` | 10018 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/run.pid` | `bb578bdbe9a3b3b55a856ecf929caf6a34e30d88656ac7688aa65c9de1891642` | `/data/.Trash-1000/files/13-pair-sweep/run.pid` | 8 |
| `/data/eval-runs/is-prim-eval/2026-10-19/13-pair-sweep/stop-record.txt` | `2144619dd7a9379cd1b402a6cdf0a251e04432907081b3a4da85f195e63bf28d` | `/data/.Trash-1000/files/13-pair-sweep/stop-record.txt` | 59 |

### Directory: `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results`
Trash info: `/data/.Trash-1000/info/results.trashinfo`; Trash entry: `/data/.Trash-1000/files/results`; prior move verified: `True`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results/datasets/prime-v1-fc48a8ff5cee2be5.json` | `4e4fd21d08a5538c985a3f489a47f15e960adc55adc1c074595c56ba393646db` | `/data/.Trash-1000/files/results/datasets/prime-v1-fc48a8ff5cee2be5.json` | 16028 |
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T184602Z_115c81ae.jsonl` | `06178d09379257f275d5357cc1fc6b5c23bce9441d19c5954fc71fc98f855bcc` | `/data/.Trash-1000/files/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T184602Z_115c81ae.jsonl` | 1021 |
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T184602Z_115c81ae.manifest.json` | `98413ee0297ea8001e2254f673f143ccb1f048aef77a89bb4bf2dd98f50317b1` | `/data/.Trash-1000/files/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T184602Z_115c81ae.manifest.json` | 2099 |
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T184653Z_ced719f0.jsonl` | `ff0e9bebe58c70089220f7a4aa969101d259715c22cd40a4b906d892675b620b` | `/data/.Trash-1000/files/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T184653Z_ced719f0.jsonl` | 11252 |
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T184653Z_ced719f0.manifest.json` | `ec542c3c447a028e4560c3b1124a1997d43d0b6d665ccb9a3997094e1fd3aaa8` | `/data/.Trash-1000/files/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261019T184653Z_ced719f0.manifest.json` | 2099 |
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T184602Z_70723944.jsonl` | `c926c529c71d98ef075dae057d53fc7d966273d4e989745a81228438c1a2b4f3` | `/data/.Trash-1000/files/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T184602Z_70723944.jsonl` | 1019 |
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T184602Z_70723944.manifest.json` | `57f9ec58b29a2592ba4eb55a13961b5a3af3641413f7b7cbb42cac960d0b1e99` | `/data/.Trash-1000/files/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T184602Z_70723944.manifest.json` | 2096 |
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T184653Z_dea741da.jsonl` | `11eb427db08d84f809701c011424349537bcf1c88684e4ccfcc1ad1efe9b0c1f` | `/data/.Trash-1000/files/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T184653Z_dea741da.jsonl` | 11211 |
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T184653Z_dea741da.manifest.json` | `8b8394ec2b47701154a824a8005feaa30283b3a31d10f9bf723c13a9ff10be83` | `/data/.Trash-1000/files/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261019T184653Z_dea741da.manifest.json` | 2096 |
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results/openai-gpt-6-luna__effort-medium-c082456a77_20261019T184653Z_62b47d3e.jsonl` | `b50385bd3e90d95e85608112872297adc9585d468fd15735e921699aa26e7b9c` | `/data/.Trash-1000/files/results/openai-gpt-6-luna__effort-medium-c082456a77_20261019T184653Z_62b47d3e.jsonl` | 15956 |
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/results/openai-gpt-6-luna__effort-medium-c082456a77_20261019T184653Z_62b47d3e.manifest.json` | `7b94c795fb54978408d8707c4d516ce68de5c3edfa17e28e803eabcbd735b078` | `/data/.Trash-1000/files/results/openai-gpt-6-luna__effort-medium-c082456a77_20261019T184653Z_62b47d3e.manifest.json` | 2105 |

### Directory: `/data/eval-runs/is-prim-eval/2026-10-19/parallel-checkpoint/results`
Trash info: `/data/.Trash-1000/info/results.2.trashinfo`; Trash entry: `/data/.Trash-1000/files/results.2`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/data/eval-runs/is-prim-eval/2026-10-19/parallel-checkpoint/results/datasets/prime-v1-fc48a8ff5cee2be5.json` | `4e4fd21d08a5538c985a3f489a47f15e960adc55adc1c074595c56ba393646db` | `/data/.Trash-1000/files/results.2/datasets/prime-v1-fc48a8ff5cee2be5.json` | 16028 |
| `/data/eval-runs/is-prim-eval/2026-10-19/parallel-checkpoint/results/openai-gpt-6-luna__effort-low_20261019T175749Z_d95581dd.jsonl` | `eb31ed3cb4d26b4e14dccfd5bee693d8511e3ab240271922ba85938faffbffd4` | `/data/.Trash-1000/files/results.2/openai-gpt-6-luna__effort-low_20261019T175749Z_d95581dd.jsonl` | 75912 |
| `/data/eval-runs/is-prim-eval/2026-10-19/parallel-checkpoint/results/openai-gpt-6-luna__effort-low_20261019T175749Z_d95581dd.manifest.json` | `9e2daff6bd319ffd202c52b12743a68cf3eb24522fe795e8f8811c73da7de420` | `/data/.Trash-1000/files/results.2/openai-gpt-6-luna__effort-low_20261019T175749Z_d95581dd.manifest.json` | 2085 |
| `/data/eval-runs/is-prim-eval/2026-10-19/parallel-checkpoint/results/openai-gpt-6-luna__effort-medium_20261019T175831Z_cffe5991.jsonl` | `3b11217f15c86601ebb9d38c80fcd8bd045342d844f94d7f0f0f737245e059a9` | `/data/.Trash-1000/files/results.2/openai-gpt-6-luna__effort-medium_20261019T175831Z_cffe5991.jsonl` | 26080 |
| `/data/eval-runs/is-prim-eval/2026-10-19/parallel-checkpoint/results/openai-gpt-6-luna__effort-medium_20261019T175831Z_cffe5991.manifest.json` | `f9c35a364b9292a4adfe74483d0280099fc0f64bf610a5495315f85f6f16a93d` | `/data/.Trash-1000/files/results.2/openai-gpt-6-luna__effort-medium_20261019T175831Z_cffe5991.manifest.json` | 2094 |

### Directory: `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean`
Trash info: `/data/.Trash-1000/info/13-pair-sweep-clean.trashinfo`; Trash entry: `/data/.Trash-1000/files/13-pair-sweep-clean`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.jsonl` | `bef0215fc36ed866633d41f2637ceccf15c4097202f80fda519818aa221363b5` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.jsonl` | 637257 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.manifest.json` | `62b669aac799ffc953be7b2478e085ba1e76013e4d6ad5cdf421fd59ff94f2e4` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.manifest.json` | 2185 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.jsonl` | `6e727023a175a9b36e4da0a42dc322478dba439174dd045ed85a427b0ce1269a` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.jsonl` | 622289 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.manifest.json` | `0dcde64a59d1bbe60cf1178a41bd969584a97ed90475daeed5955a3d0fa9dca6` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.manifest.json` | 2182 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.jsonl` | `29fac96b0e5c21e976776c4759991b13e406300162a8b34d687f348c1ef060ad` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.jsonl` | 632153 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.manifest.json` | `0a35e79707169b2256c5e6140d104e9ac9c96b2cfc638368b13c6bfe8bfd11aa` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.manifest.json` | 2191 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.jsonl` | `e949809442634d4f9cdc4583335b59729b378415176f07525a54d6c077ee0710` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.jsonl` | 643022 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.manifest.json` | `54ff1c93449226ff30fa8a5ede8f4965464a31752126b269d512f7771aba1a25` | `/data/.Trash-1000/files/13-pair-sweep-clean/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.manifest.json` | 2188 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/datasets/prime-v1-fc48a8ff5cee2be5.json` | `4e4fd21d08a5538c985a3f489a47f15e960adc55adc1c074595c56ba393646db` | `/data/.Trash-1000/files/13-pair-sweep-clean/datasets/prime-v1-fc48a8ff5cee2be5.json` | 16028 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.jsonl` | `7417317fa82476b724c133c2a00c1226b227610b53a0c3ad013b179bb4efcbe9` | `/data/.Trash-1000/files/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.jsonl` | 485682 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.manifest.json` | `7b8438869b8b197d63a46a2e855da2f6d6766d8a56c8a483e1d4d84bed5e8a53` | `/data/.Trash-1000/files/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.manifest.json` | 2451 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.jsonl` | `c74b1d7ed6383fd1945da972a1a2d58c9ac2ccabe1672cfbaa5d5a376453bb03` | `/data/.Trash-1000/files/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.jsonl` | 486670 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.manifest.json` | `a07e53206b206b8a6d91adaff4904f7a2959a289d6e5279494d695edd2e2d3d2` | `/data/.Trash-1000/files/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.manifest.json` | 2448 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.jsonl` | `5d3ca977d8e6c7312bff57352fab4a192910431a70eee4c3f310fb72dda558be` | `/data/.Trash-1000/files/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.jsonl` | 491163 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.manifest.json` | `721e261a74c2659add190ba7f2b964d2d6867f0661ca7ffc59fb3f5c8b83c00c` | `/data/.Trash-1000/files/13-pair-sweep-clean/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.manifest.json` | 2457 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/leaderboard.md` | `353bc14749d27564a441ccf95ae9789d49f6b0e1a02af85025eb6750203d9442` | `/data/.Trash-1000/files/13-pair-sweep-clean/leaderboard.md` | 16060 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl` | `4cf1aa6cfa3d7873bcf49a636ee390bdb156daecbdb0cbb4a567b5bff6bbad03` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl` | 349461 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.manifest.json` | `6665e0537ade0f2241e9ad799409cc8cd3aea31b749fe30fd475a646daf2e0d8` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.manifest.json` | 2181 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.jsonl` | `81e587c779d8aba05362337023c301e70471c73bd9bb1defa8a0c62c8be084f1` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.jsonl` | 934459 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.manifest.json` | `71a36525f3874328d12a301b6271bdae124007294b723efa697d216e6a5a7d9b` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.manifest.json` | 2140 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.jsonl` | `18c0c1f1d1f768b70d84daf2c611113a0948c9f0e41f81935025e26074523c18` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.jsonl` | 910156 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.manifest.json` | `c789230abebff7e5124ebd24b7e71ba3a98e96fb515ec08a0f59afec92a583c7` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.manifest.json` | 2137 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.jsonl` | `471a26f8c05eaa39bce0d46229ded73e5eb0ade1bf57977a2069d700dc03197b` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.jsonl` | 919298 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.manifest.json` | `c710bc7a6401e58778f361001b421b6cd7e0677cf9021c29a4c55fc2f3dd57d9` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.manifest.json` | 2146 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.jsonl` | `d1c743db3c705280b67961432dcfafc1891957036119a36e22ddf4e9a7669666` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.jsonl` | 935275 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.manifest.json` | `624616f9a8bd24679497c5054d9aace6cfb10aea68871b71b9a15d3ab2bd3653` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.manifest.json` | 2143 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.jsonl` | `ed5deba14ff9672fb311530fc8b0a820cf02235e34a167554cf008efd76b9b7e` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.jsonl` | 790616 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.manifest.json` | `5b4238ba9ac9fa4953af5ed5e6244c11b38196cc7aca106d093bc2b77613b01e` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.manifest.json` | 2138 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.jsonl` | `603f0e714b67ab35bd180fe18605e659744bd129075a93ae811b66d4da2a8f8f` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.jsonl` | 823675 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.jsonl.lock` | `e751c191debe829fd2e1c54444d22a143c2e96633d2a6a383567a716d5c3f828` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.jsonl.lock` | 12 |
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.manifest.json` | `f21fcca3818b3e7e7a807e0735bc45a2fe6af8a260663a31ba7b00bcaa3d1e43` | `/data/.Trash-1000/files/13-pair-sweep-clean/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.manifest.json` | 2147 |

### File: `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/leaderboard.md`
Trash info: `/data/.Trash-1000/info/leaderboard.md.trashinfo`; Trash entry: `/data/.Trash-1000/files/leaderboard.md`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/data/eval-runs/is-prim-eval/2026-10-19/explicit-effort-cli-checkpoint/leaderboard.md` | `cd756e6404a59f55ed5ea34b7e7fb85c8832a1a666312f09fef94d65aec84fd6` | `/data/.Trash-1000/files/leaderboard.md` | 1825 |

### File: `/data/eval-runs/is-prim-eval/2026-10-19/parallel-checkpoint/leaderboard.md`
Trash info: `/data/.Trash-1000/info/leaderboard.2.md.trashinfo`; Trash entry: `/data/.Trash-1000/files/leaderboard.2.md`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/data/eval-runs/is-prim-eval/2026-10-19/parallel-checkpoint/leaderboard.md` | `05655b1b371af9bb208359e18407eacd4a16d4597984baca6445de7e392810c6` | `/data/.Trash-1000/files/leaderboard.2.md` | 1358 |

### File: `/data/eval-runs/is-prim-eval/2026-10-19/leaderboard-current.md`
Trash info: `/data/.Trash-1000/info/leaderboard-current.md.trashinfo`; Trash entry: `/data/.Trash-1000/files/leaderboard-current.md`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/data/eval-runs/is-prim-eval/2026-10-19/leaderboard-current.md` | `296c6beb239a3fae8f49df49988a0d97ac454d4ada5c1e2a0cf2990cd8f797bb` | `/data/.Trash-1000/files/leaderboard-current.md` | 2127 |

### File: `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean-preflight.txt`
Trash info: `/data/.Trash-1000/info/13-pair-sweep-clean-preflight.txt.trashinfo`; Trash entry: `/data/.Trash-1000/files/13-pair-sweep-clean-preflight.txt`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/data/eval-runs/is-prim-eval/2026-10-20/13-pair-sweep-clean-preflight.txt` | `91720987ca383c7d8aef2d6c669854ca4e3156d4b408373f0b978d98b2911e2a` | `/data/.Trash-1000/files/13-pair-sweep-clean-preflight.txt` | 12502 |

### File: `/home/user/src/is-prime-eval/leaderboard.md`
Trash info: `/home/user/.local/share/Trash/info/leaderboard.md.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/leaderboard.md`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/leaderboard.md` | `353bc14749d27564a441ccf95ae9789d49f6b0e1a02af85025eb6750203d9442` | `/home/user/.local/share/Trash/files/leaderboard.md` | 16060 |

### File: `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.jsonl`
Trash info: `/home/user/.local/share/Trash/info/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.jsonl` | `bef0215fc36ed866633d41f2637ceccf15c4097202f80fda519818aa221363b5` | `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.jsonl` | 637257 |

### File: `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.manifest.json` | `62b669aac799ffc953be7b2478e085ba1e76013e4d6ad5cdf421fd59ff94f2e4` | `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-high-6ef7c9b15e_20261020T081137Z_09a361de.manifest.json` | 2185 |

### File: `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.jsonl`
Trash info: `/home/user/.local/share/Trash/info/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.jsonl` | `6e727023a175a9b36e4da0a42dc322478dba439174dd045ed85a427b0ce1269a` | `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.jsonl` | 622289 |

### File: `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.manifest.json` | `0dcde64a59d1bbe60cf1178a41bd969584a97ed90475daeed5955a3d0fa9dca6` | `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-low-6c1ff09db3_20261020T074442Z_48dec779.manifest.json` | 2182 |

### File: `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.jsonl`
Trash info: `/home/user/.local/share/Trash/info/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.jsonl` | `29fac96b0e5c21e976776c4759991b13e406300162a8b34d687f348c1ef060ad` | `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.jsonl` | 632153 |

### File: `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.manifest.json` | `0a35e79707169b2256c5e6140d104e9ac9c96b2cfc638368b13c6bfe8bfd11aa` | `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-medium-c082456a77_20261020T075105Z_71787c20.manifest.json` | 2191 |

### File: `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.jsonl`
Trash info: `/home/user/.local/share/Trash/info/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.jsonl` | `e949809442634d4f9cdc4583335b59729b378415176f07525a54d6c077ee0710` | `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.jsonl` | 643022 |

### File: `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.manifest.json` | `54ff1c93449226ff30fa8a5ede8f4965464a31752126b269d512f7771aba1a25` | `/home/user/.local/share/Trash/files/anthropic-claude-haiku-5.5__effort-xhigh-b5255978be_20261020T081207Z_dff20151.manifest.json` | 2188 |

### File: `/home/user/src/is-prime-eval/results/datasets/prime-v1-66a3cb95d6b586fb.json`
Trash info: `/home/user/.local/share/Trash/info/prime-v1-66a3cb95d6b586fb.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/prime-v1-66a3cb95d6b586fb.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/datasets/prime-v1-66a3cb95d6b586fb.json` | `a69128b8f2c97a998bb119666680de6b228724f5798f98958c8a3e89844c2bf1` | `/home/user/.local/share/Trash/files/prime-v1-66a3cb95d6b586fb.json` | 476 |

### File: `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.jsonl`
Trash info: `/home/user/.local/share/Trash/info/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.jsonl` | `7417317fa82476b724c133c2a00c1226b227610b53a0c3ad013b179bb4efcbe9` | `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.jsonl` | 485682 |

### File: `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.manifest.json` | `7b8438869b8b197d63a46a2e855da2f6d6766d8a56c8a483e1d4d84bed5e8a53` | `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-high-6ef7c9b15e_20261020T074417Z_314e4351.manifest.json` | 2451 |

### File: `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.jsonl`
Trash info: `/home/user/.local/share/Trash/info/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.jsonl` | `c74b1d7ed6383fd1945da972a1a2d58c9ac2ccabe1672cfbaa5d5a376453bb03` | `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.jsonl` | 486670 |

### File: `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.manifest.json` | `a07e53206b206b8a6d91adaff4904f7a2959a289d6e5279494d695edd2e2d3d2` | `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-low-6c1ff09db3_20261020T071827Z_2df3d4ca.manifest.json` | 2448 |

### File: `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.jsonl`
Trash info: `/home/user/.local/share/Trash/info/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.jsonl` | `5d3ca977d8e6c7312bff57352fab4a192910431a70eee4c3f310fb72dda558be` | `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.jsonl` | 491163 |

### File: `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.manifest.json` | `721e261a74c2659add190ba7f2b964d2d6867f0661ca7ffc59fb3f5c8b83c00c` | `/home/user/.local/share/Trash/files/deepseek-deepseek-v4.1-flash-1017__effort-medium-c082456a77_20261020T071915Z_0fe77106.manifest.json` | 2457 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl` | `4cf1aa6cfa3d7873bcf49a636ee390bdb156daecbdb0cbb4a567b5bff6bbad03` | `/home/user/.local/share/Trash/files/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl` | 349461 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl.lock`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl.lock.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl.lock`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl.lock` | `625b6a3aa9f48b73af3976a831664caf4b320a21a6a0b7abbd1094423d48621e` | `/home/user/.local/share/Trash/files/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.jsonl.lock` | 12 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.manifest.json` | `6665e0537ade0f2241e9ad799409cc8cd3aea31b749fe30fd475a646daf2e0d8` | `/home/user/.local/share/Trash/files/openai-gpt-4-turbo__effort-omitted-74234e98af_20261020T072121Z_94ac1dcb.manifest.json` | 2181 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.jsonl`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.jsonl` | `81e587c779d8aba05362337023c301e70471c73bd9bb1defa8a0c62c8be084f1` | `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.jsonl` | 934459 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.manifest.json` | `71a36525f3874328d12a301b6271bdae124007294b723efa697d216e6a5a7d9b` | `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-high-6ef7c9b15e_20261020T064925Z_c0e77493.manifest.json` | 2140 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.jsonl`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.jsonl` | `18c0c1f1d1f768b70d84daf2c611113a0948c9f0e41f81935025e26074523c18` | `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.jsonl` | 910156 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.manifest.json` | `c789230abebff7e5124ebd24b7e71ba3a98e96fb515ec08a0f59afec92a583c7` | `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-low-6c1ff09db3_20261020T064925Z_c81ae9e3.manifest.json` | 2137 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.jsonl`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.jsonl` | `471a26f8c05eaa39bce0d46229ded73e5eb0ade1bf57977a2069d700dc03197b` | `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.jsonl` | 919298 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.manifest.json` | `c710bc7a6401e58778f361001b421b6cd7e0677cf9021c29a4c55fc2f3dd57d9` | `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-medium-c082456a77_20261020T064925Z_e3ef95ea.manifest.json` | 2146 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.jsonl`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.jsonl` | `d1c743db3c705280b67961432dcfafc1891957036119a36e22ddf4e9a7669666` | `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.jsonl` | 935275 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.manifest.json` | `624616f9a8bd24679497c5054d9aace6cfb10aea68871b71b9a15d3ab2bd3653` | `/home/user/.local/share/Trash/files/openai-gpt-6-luna__effort-xhigh-b5255978be_20261020T071731Z_00f96b17.manifest.json` | 2143 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.jsonl`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.jsonl` | `ed5deba14ff9672fb311530fc8b0a820cf02235e34a167554cf008efd76b9b7e` | `/home/user/.local/share/Trash/files/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.jsonl` | 790616 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.manifest.json` | `5b4238ba9ac9fa4953af5ed5e6244c11b38196cc7aca106d093bc2b77613b01e` | `/home/user/.local/share/Trash/files/openai-gpt-6.1-sol__effort-low-6c1ff09db3_20261020T081905Z_0b085273.manifest.json` | 2138 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.jsonl`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.jsonl.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.jsonl`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.jsonl` | `603f0e714b67ab35bd180fe18605e659744bd129075a93ae811b66d4da2a8f8f` | `/home/user/.local/share/Trash/files/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.jsonl` | 823675 |

### File: `/home/user/src/is-prime-eval/results/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.manifest.json`
Trash info: `/home/user/.local/share/Trash/info/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.manifest.json.trashinfo`; Trash entry: `/home/user/.local/share/Trash/files/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.manifest.json`; prior move verified: `False`.

| Original file | SHA-256 | Trash destination | Bytes |
|---|---|---|---:|
| `/home/user/src/is-prime-eval/results/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.manifest.json` | `f21fcca3818b3e7e7a807e0735bc45a2fe6af8a260663a31ba7b00bcaa3d1e43` | `/home/user/.local/share/Trash/files/openai-gpt-6.1-sol__effort-medium-c082456a77_20261020T083736Z_24cfb2d6.manifest.json` | 2147 |

## Offline recovery follow-up — 2026-10-20

The original 115 moved payload mappings above were left intact and were not re-trashed. This follow-up moved 9 additional payloads with `gio trash` at `2026-10-20T17:47:38+03:00` (`14:47:38Z`). Every payload's SHA-256 and byte count was computed before moving and matched its Trash copy afterward; both source paths are absent. Total recoverably moved payloads: **124**.

### Formerly retained repo dataset

- Original: `/home/user/src/is-prime-eval/results/datasets/prime-v1-fc48a8ff5cee2be5.json`
- Pre-move SHA-256: `4e4fd21d08a5538c985a3f489a47f15e960adc55adc1c074595c56ba393646db`; bytes: `16028`.
- Trash destination: `/home/user/.local/share/Trash/files/prime-v1-fc48a8ff5cee2be5.json`
- Trash info: `/home/user/.local/share/Trash/info/prime-v1-fc48a8ff5cee2be5.json.trashinfo`
- Trash info records `Path=/home/user/src/is-prime-eval/results/datasets/prime-v1-fc48a8ff5cee2be5.json` and `DeletionDate=2026-10-20T17:47:38`.

### Formerly deferred external directory — successfully moved

- Original directory: `/data/eval-runs/is-prim-eval/2026-10-19/results`
- Trash destination: `/data/.Trash-1000/files/results.3`
- Trash info: `/data/.Trash-1000/info/results.3.trashinfo`
- Trash info records mount-relative `Path=eval-runs/is-prim-eval/2026-10-19/results` and `DeletionDate=2026-10-20T17:47:38`.
- Each payload in the pre-move inventory below is at the **same relative path** beneath `/data/.Trash-1000/files/results.3` (including `datasets/` and `.~lock.leaderboard.md#`). All 8 hashes/sizes matched after the move.

Safety inspection: `gio info` reported `access::can-trash: TRUE` and `access::can-delete: TRUE`; all entries were ordinary files/directories, not symlinks. `lsof +D` found no open handles in this copied directory (exit 1; it warned only that unrelated `/sys/kernel/debug/tracing` could not be statted). LibreOffice PID `352893` remained running; its inspected descriptors referenced the repo `PLAN.md` and the deleted original repo `results/leaderboard.md`, not this external copied directory. The external lock file identifies the same user/host and a 2026-10-19 timestamp, but does not establish an active lock on the copied inodes. No LibreOffice process was closed or killed; no lock file was separately removed. `gio trash` succeeded for the entire directory with exit 0 and no stderr. There is no blocked or deferred remainder.

The active repo `results/` now contains no files; `cases.py`, `prime_stats.py`, and `prime-stats.md` are unchanged. The user will launch fresh deterministic generation later; no old symlink was restored and no API/catalog/preflight/live run was executed.

### Pre-move inventory of the formerly deferred 8 files

| Original path | Pre-move SHA-256 | Bytes |
|---|---|---:|
| `/data/eval-runs/is-prim-eval/2026-10-19/results/.~lock.leaderboard.md#` | `28b8c0d5cc0e0ee95d1bbccf09c2a9318ed9515baa092990087c5bce82a03880` | 77 |
| `/data/eval-runs/is-prim-eval/2026-10-19/results/datasets/prime-v1-66a3cb95d6b586fb.json` | `a69128b8f2c97a998bb119666680de6b228724f5798f98958c8a3e89844c2bf1` | 476 |
| `/data/eval-runs/is-prim-eval/2026-10-19/results/datasets/prime-v1-fc48a8ff5cee2be5.json` | `4e4fd21d08a5538c985a3f489a47f15e960adc55adc1c074595c56ba393646db` | 16028 |
| `/data/eval-runs/is-prim-eval/2026-10-19/results/gpt-6-luna-low_20261019T121526Z_ed10a2c0.jsonl` | `a820483c9504db02f440563ef86baeb3690de801f1d0e64ae5a6c14df4df305d` | 10985 |
| `/data/eval-runs/is-prim-eval/2026-10-19/results/gpt-6-luna-low_20261019T121526Z_ed10a2c0.manifest.json` | `e9ec1d2108c8d4ab762dc2bf644ccf233a38bdc5ff969ab38ee07f6948550b38` | 2066 |
| `/data/eval-runs/is-prim-eval/2026-10-19/results/gpt-6-luna-low_20261019T122928Z_5e8a64cf.jsonl` | `05754976bc619471a928c46a78535feee636703268f18ca6da710d040ab52686` | 1223035 |
| `/data/eval-runs/is-prim-eval/2026-10-19/results/gpt-6-luna-low_20261019T122928Z_5e8a64cf.manifest.json` | `805ea53275f40a53b1ab8ebe8b28aada02749b020f7329a91d08bad924ee65a2` | 2180 |
| `/data/eval-runs/is-prim-eval/2026-10-19/results/leaderboard.md` | `fc31965d11bf651a179cb6917bfb9ad5ea7c88de23ade7cf10ed8cce9f565300` | 1858 |
