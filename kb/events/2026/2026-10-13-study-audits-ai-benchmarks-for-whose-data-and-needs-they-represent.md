---
type: Event
kind: paper
title: Study Audits AI Benchmarks for Whose Data and Needs They Represent
description: A new preprint proposes a user-centric framework for auditing AI evaluation benchmarks, distinguishing
  between the people who contribute benchmark content and those whose needs the benchmark results are
  meant to reflect. Analyzing 16 widely used text and image-text benchmarks, the authors find that American-centered
  conventions dominate signals in text benchmarks and that geographic visibility in image-text resources
  correlates strongly with national GDP share. They also show that none of the benchmarks document the
  context of their intended target users, even though all document the context of content contributors,
  and that minor rewordings can sharply change measured accuracy on benchmarks like DROP.
date: '2026-10-13'
themes:
- ai-human-rights
entities:
- tech/user-centric-benchmark-audit-framework
tags:
- benchmark bias
- algorithmic discrimination
- AI evaluation
- cultural representation
generated:
  by: planetai/openrouter:anthropic/claude-sonnet-5
  at: '2026-10-15T10:02:33Z'
status: stable
sources:
- id: arxiv-2610.19268
  resource: https://arxiv.org/abs/2610.19268
  title: Whose Data, Whose Benchmark? A User-Centric Framework for Auditing Evaluation Resources
  author: Mir Tafseer Nayeem, Davood Rafiei
  last_modified: '2026-10-13'
---

A preprint posted on arXiv introduces an audit framework that separates benchmark 'source users' who supply content from 'target users' whose needs the benchmark scores are supposed to represent[^arxiv-2610.19268]. Applying the framework to 16 commonly used AI evaluation resources, the authors found that American-centered conventions made up between 62.4% and 94.4% of matched signals across 11 text benchmarks[^arxiv-2610.19268]. In five image-text benchmarks, the geographic visibility of represented regions was strongly tied to each country's share of global GDP, with correlation measures around 0.78[^arxiv-2610.19268]. The study also found that while every benchmark documented the context of its content contributors, none documented the context of the users its results are meant to serve, and that paraphrased but meaning-preserving answers could cut DROP benchmark accuracy from 100% to 33.3%[^arxiv-2610.19268].
