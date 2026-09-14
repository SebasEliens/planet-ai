---
type: Event
kind: news
title: EFF Critiques Amazon Ring's New TAKE Encryption as Insufficient Privacy Protection
description: EFF published an analysis of Amazon's newly launched "Throw Away the Key Encryption" (TAKE)
  feature for Ring cameras, arguing that while it limits how long Ring's cloud servers hold decryption
  keys, it still falls far short of true end-to-end encryption and leaves footage vulnerable to law enforcement
  access and company processing.
date: '2026-09-11'
themes:
- ai-human-rights
entities:
- orgs/electronic-frontier-foundation-eff
- orgs/amazon
- tech/ring-take-throw-away-the-key-encryption
tags:
- surveillance
- encryption
- law enforcement access
- smart home cameras
- digital rights
generated:
  by: planetai/openrouter:anthropic/claude-sonnet-5
  at: '2026-09-12T10:19:19Z'
status: stable
sources:
- id: eff-cold-take
  resource: https://www.eff.org/deeplinks/2026/09/cold-take-amazons-new-encryption-method-still-doesnt-deliver-real-privacy
  title: 'Cold TAKE: Amazon''s New Encryption Method Still Doesn''t Deliver Real Privacy'
  author: Erica Portnoy and Thorin Klosowski
  last_modified: '2026-09-11'
---

EFF researchers analyzed Amazon Ring's newly introduced "Throw Away the Key Encryption" (TAKE) feature, which changes how Ring manages encryption keys for camera footage.[^eff-cold-take] Under TAKE, Ring's cloud servers temporarily hold decryption keys for up to 24 hours to enable features like smart alerts and video search, then delete them, but the keys are re-sent to servers whenever a user accesses old footage or smart features.[^eff-cold-take] EFF argues this design still leaves Ring technically capable of complying with law enforcement demands to preserve or access unencrypted video, unlike true end-to-end encryption, which Ring already offers as an opt-in but does not enable by default.[^eff-cold-take] In response to EFF's questions, Ring said it "will not be able to provide encryption keys or decrypted content" under TAKE and that it objects to overbroad legal requests, while also acknowledging it is exploring further independent security review.[^eff-cold-take]
