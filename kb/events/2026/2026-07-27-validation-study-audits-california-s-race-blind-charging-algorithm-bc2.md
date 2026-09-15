---
type: Event
kind: paper
title: Validation Study Audits California's Race-Blind Charging Algorithm bc2
description: Researchers evaluated bc2, an open-source LLM-based redaction tool used by California prosecutors
  to implement the state's race-blind charging mandate in over 119,000 cases during 2025. Testing against
  nearly 5,000 real police reports, they found the latest bc2 version faithfully applies the legal redaction
  requirements 96.7% of the time, improving on earlier versions and outperforming other open-source redaction
  tools. The study also found California's mandate overlooks proxies like location data, and that bc2's
  broader redactions remove 43.1% of the racial predictive signal remaining after minimal compliance.
date: '2026-07-27'
themes:
- ai-human-rights
entities:
- places/california
- tech/bc2-race-blind-redaction-algorithm
tags:
- algorithmic discrimination
- criminal justice
- policy audit
- large language models
generated:
  by: planetai/openrouter:anthropic/claude-sonnet-5
  at: '2026-09-15T10:09:51Z'
status: stable
sources:
- id: arxiv-2609.13174
  resource: https://arxiv.org/abs/2609.13174
  title: 'Algorithm Validation as a Policy Audit: Evidence from Race-blind Charging'
  author: Muskan Walia, Joe Nudell, Alex Chohlas-Wood
  last_modified: '2026-07-27'
---

A new paper validates bc2, an open-source LLM-based redaction algorithm used to implement California's mandatory race-blind charging review, which affected over 119,000 real cases in 2025[^arxiv-2609.13174]. Testing on nearly 5,000 real police reports, the authors found bc2's latest version faithfully implements the state's redaction requirements in 96.7% of narratives, a marked improvement over earlier versions and better than other open-source redaction approaches[^arxiv-2609.13174]. They also identified gaps in the state mandate itself, noting it fails to address proxies such as location information, and showed that bc2's more extensive redactions remove 43.1% of the racial predictive signal left after minimal legal compliance[^arxiv-2609.13174]. The authors argue that this kind of algorithm validation can function as a policy audit, revealing not just technical compliance but whether a policy actually achieves its stated goals[^arxiv-2609.13174].
