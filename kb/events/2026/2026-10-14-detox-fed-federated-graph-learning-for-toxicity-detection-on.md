---
type: Event
kind: paper
title: 'DeTox-Fed: Federated Graph Learning for Toxicity Detection on Fediverse Platforms'
description: Researchers introduce DeTox-Fed, a federated graph neural network approach for flagging toxic
  conversations across decentralized social networks like Pleroma and Mastodon. The method lets individual
  instances train a shared toxicity classifier collaboratively without exchanging raw posts or moderation
  labels, addressing the content moderation challenges posed by fragmented, independently-run Fediverse
  servers. The approach models conversations as graphs capturing structure, user interactions, and sentiment,
  and was tested on Pleroma and Mastodon datasets, with the latest revision adding more LLM baselines
  and a GraphNLI comparison.
date: '2026-10-14'
themes:
- ai-human-rights
entities:
- tech/detox-fed
tags:
- content moderation
- federated learning
- fediverse
- graph neural networks
- decentralized social networks
generated:
  by: planetai/openrouter:anthropic/claude-sonnet-5
  at: '2026-10-15T10:03:23Z'
status: stable
sources:
- id: arxiv-2605.21054
  resource: https://arxiv.org/abs/2605.21054
  title: 'DeTox-Fed: Detecting Toxic Conversations in the Fediverse with Federated Graph Neural Networks'
  author: Pantelitsa Leonidou, Nikos Salamanos, Sotiris Gypsiotis, Michael Sirivianos
  last_modified: '2026-10-14'
---

A team of researchers proposed DeTox-Fed, a federated graph-learning system designed to detect toxic conversations across decentralized social networks such as Pleroma and Mastodon[^arxiv-2605.21054]. The system lets independently operated instances collaboratively train a shared toxicity classifier while keeping raw conversation data and moderation labels local, addressing the content-moderation gaps created by fragmented governance and partial visibility across Fediverse servers. It represents conversations as graphs incorporating structural, interaction, and sentiment signals rather than relying on text alone. The latest revision expands testing to include a Mastodon dataset alongside the original Pleroma data, plus comparisons against additional language models and the GraphNLI baseline.
