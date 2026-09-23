# Claim-to-result manifest

This table is the final transcription check for the ICASSP manuscript. All
reported estimates use source query as the sampling unit and budget 48 unique
rendered prompts unless stated otherwise.

| Manuscript claim | Value | Authoritative artifact |
|---|---|---|
| Registry A sample sizes | 58, 49, 54, 52 | `summary_uan_registry_fair.json` |
| Adapt / StdEnum A ACEM | 1.000 / 1.000 in all four cells | `summary_uan_registry_fair.json` |
| Repeated A ACEM | .905, .904, .913, .931 | `summary_uan_registry_fair.json` |
| Random A ACEM | 1.000, .920, .981, .983 | `summary_uan_registry_fair.json` |
| Registry prompt quotient | 15.7--19.8 of 256; 6.1--7.7% | `summary_uan_registry_fair.json` |
| Adapt--Repeated paired differences | .095, .096, .087, .069 | `stats_ambi_vs_repeated_final.json` |
| U/A/N counts | 56/58/58; 49/49/45; 58/54/60; 53/52/59 | `summary_uan_registry_fair.json` |
| Raw N recall | .552, .511, .383, .492 | `summary_uan_registry_fair.json` |
| StandardEnum incidental N recall | .448, .356, .267, .441; pooled .378 | `safe_ablation_*.jsonl` |
| Residual-audit N recall (10-seed mean) | .943, .922, .943, .980; model-case mean .949 | `uniform_*_test.jsonl` |
| Residual-audit clustered N recall | .952 over 130 clusters (222 model-cases) | `residual_audit_statistics.json` |
| Residual-audit cluster bootstrap 95% interval | [.930, .972] | `residual_audit_statistics.json` |
| Residual Audit--Standard paired clustered gain | .563 [.495,.630] | `residual_audit_statistics.json` |
| News residual-audit N recall | .950 [.929,.968], 123 clusters/207 model-cases | `residual_audit_statistics.json` |
| All-active residual-audit N recall | .814 [.753,.869], 75 clusters/142 model-cases | `residual_audit_statistics.json` |
| Stable-N residual Audit | 20 model-cases/19 clusters; ten-seed recall .968 [.921,1.000] | `uniform_stable_n.json` |
| News A sample sizes | 53, 40, 45, 38 | `summary_uan_news_fair.json` |
| n=10 A sample sizes | 40, 27, 34, 32 | `summary_uan_n10_{qwen,mistral}_fair.json` |
| Independent re-derivation | 224 candidate tables; zero mismatches | `independent_audit_*.json` |
| Realized A cross-path rate | 79--90% | `difficulty_*.json` |
| Realized A planted-exact rate | 4--21% | `difficulty_*.json` |
| All-active candidate A/N, Qwen Hotpot/NQ | 9/119; 5/93 | `uan_*_active_qwen_manifest.json` |
| All-active candidate A/N, Mistral Hotpot/NQ | 4/131; 4/128 | `uan_*_active_mistral_manifest.json` |
| All-active selected A | 6, 5, 3, 4 | `uan_*_active_*_manifest.json` |

Order for four-cell vectors is Hotpot/Qwen, NQ/Qwen, Hotpot/Mistral,
NQ/Mistral. All-active values are explicitly descriptive because their
realized-A denominators are very small.
