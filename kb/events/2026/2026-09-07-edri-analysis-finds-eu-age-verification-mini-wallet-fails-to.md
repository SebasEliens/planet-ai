---
type: Event
kind: report
title: EDRi analysis finds EU age-verification 'mini-wallet' fails to guarantee privacy
description: EDRi published a technical breakdown of the EU Commission's age-verification 'mini-wallet',
  which underpins a planned EU social media ban proposal to be unveiled at the 2026 State of the European
  Union address. The analysis argues the tool, built on the eID Wallet, weakens legal unlinkability requirements,
  only optionally recommends Zero-Knowledge Proofs, and relies on 'batch issuance' credentials that still
  leave traceable metadata linking users across services. EDRi concludes that even mandatory ZKPs would
  not fully prevent tracking in a centralized system and calls for independently audited, privacy-by-design
  alternatives to mandatory age verification.
date: '2026-09-07'
themes:
- ai-human-rights
- ai-governance
entities:
- orgs/european-digital-rights-edri
- orgs/european-commission
- tech/eid-wallet
- topics/age-verification
tags:
- age verification
- privacy
- biometric verification
- EU digital policy
- zero-knowledge proofs
generated:
  by: planetai/openrouter:anthropic/claude-sonnet-5
  at: '2026-09-08T09:53:17Z'
status: stable
sources:
- id: src1
  resource: https://edri.org/our-work/eu-age-verification-tool-does-not-solve-privacy-concerns
  title: Why the EU age-verification tool does not solve privacy concerns
  author: EDRi
  last_modified: '2026-09-07'
---

EDRi released a technical critique on 2026-09-07 of the EU Commission's age-verification 'mini-wallet', which is set to underpin a legislative proposal for a social media ban to be presented at the 2026 State of the European Union address[^src1]. The report argues the mini-wallet's design, based on the eID Wallet, only recommends rather than mandates privacy-preserving Zero-Knowledge Proofs, using the non-binding term 'SHOULD' instead of 'SHALL'[^src1]. It also finds that the mandatory 'batch issuance' credential scheme still leaves unique identifiers like salts, hashes and timestamps that could let cooperating providers link a user's activity across age-gated services[^src1]. EDRi further notes the EU is reportedly softening the legal requirement to 'ensure' unlinkability into merely 'hindering' it, and warns that even mandatory ZKPs would not guarantee privacy if the issuing authority controls both attestation and verification, quoting concerns raised by '438 security and privacy scientists and researchers' about centralized systems[^src1].
