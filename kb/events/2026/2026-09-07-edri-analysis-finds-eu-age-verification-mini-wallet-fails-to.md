---
type: Event
kind: report
title: EDRi analysis finds EU age-verification 'mini-wallet' fails to guarantee privacy
description: EDRi published a technical critique of the European Commission's age-verification blueprint
  (the 'mini-wallet'), which underpins a planned EU social media ban proposal to be unveiled at the State
  of the European Union address. The analysis argues the tool weakens legally required unlinkability protections,
  only recommends rather than mandates Zero-Knowledge Proofs, and relies on batch issuance and centralized
  attestation providers that leave room for tracking users across services. EDRi warns that even with
  optional privacy-preserving cryptography, the system's architecture could still let authorities or service
  providers link age credentials back to individuals.
date: '2026-09-07'
themes:
- ai-human-rights
entities:
- orgs/european-commission
- orgs/european-digital-rights-edri
- tech/eu-eid-wallet-age-verification-mini-wallet
tags:
- age verification
- digital identity
- privacy
- content moderation
generated:
  by: planetai/openrouter:anthropic/claude-sonnet-5
  at: '2026-09-07T10:31:19Z'
status: stable
sources:
- id: edri-age-verification-2026
  resource: https://edri.org/our-work/eu-age-verification-tool-does-not-solve-privacy-concerns
  title: Why the EU age-verification tool does not solve privacy concerns
  author: EDRi
  last_modified: '2026-09-07'
---

EDRi published a detailed technical breakdown of the EU Commission's age-verification 'mini-wallet', which is expected to underpin a legislative proposal for a social media ban to be presented at the State of the European Union address[^edri-age-verification-2026]. The group notes that the Commission's blueprint only recommends, rather than requires, Zero-Knowledge Proof mechanisms for both age-verification apps and relying parties, while mandating a weaker 'batch issuance' technique that still leaves identifying metadata like timestamps and signatures. EDRi also flags that the underlying eID Wallet law has been reinterpreted from requiring providers to 'ensure' unlinkability to merely 'hindering' it, undermining anonymity guarantees. The analysis concludes that centralized attestation providers and optional privacy safeguards mean the tool, despite being marketed as privacy-preserving, could still allow tracking of users' online activity if authorities cooperate with or compel service providers.
