---
type: Event
kind: paper
title: Study Quantifies Noise Floors Confounding Fairness Audits of Clinical LLM Agents
description: Researchers introduce FairMedAgent, an open-source audit harness that measures how much of
  a clinical LLM agent's counterfactual 'flip rate' is caused by ordinary output noise rather than demographic
  bias. Testing six models from five vendors on synthetic vignettes, they found stochastic instability
  alone changed agent actions in roughly 2.5% to 23.7% of cases depending on the model and decoding settings,
  meaning flip rates below this noise floor cannot be read as evidence of fairness. The team provides
  a four-step reporting method and releases the code, vignettes and analysis scripts so other teams can
  compute their own agents' instability floor before interpreting bias audits.
date: '2026-09-02'
themes:
- ai-human-rights
entities:
- tech/fairmedagent
tags:
- algorithmic discrimination
- healthcare AI
- fairness audit
- clinical LLM agents
generated:
  by: planetai/openrouter:anthropic/claude-sonnet-5
  at: '2026-10-01T11:42:31Z'
status: stable
sources:
- id: arxiv-2609.03221
  resource: https://arxiv.org/abs/2609.03221
  title: 'Instability Floors: Separating Bias from Noise in Fairness Audits of Clinical LLM Agents with
    FairMedAgent'
  author: Rohith Reddy Bellibatlu, Manpreet Singh, Deepak Parashar, Rahul Joshi
  last_modified: '2026-09-29'
---

A new arXiv paper argues that counterfactual fairness audits of clinical language-model agents can be misleading because stochastic output variation alone can flip an agent's recommended action even when nothing about the patient changes [^arxiv-2609.03221]. By rerunning identical clinical vignettes ten times each across six models from five vendors, the authors found 'instability floors' ranging from 2.5% to 23.7% of replicate pairs showing different actions, with controlled-substance caution outputs especially volatile [^arxiv-2609.03221]. They show mathematically that an observed flip rate inside this floor cannot be treated as proof of fairness, and that majority voting over multiple draws can cut the floor by about 39%. The team releases FairMedAgent, an open harness with protocol, vignettes and analysis code, to let other researchers measure and correct for this noise before drawing conclusions about demographic bias in clinical AI agents [^arxiv-2609.03221].
