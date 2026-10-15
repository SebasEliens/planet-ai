---
type: Event
kind: paper
title: 'MemeTrace: Multimodal LLM Agent for Tracing Unsafe Meme Provenance'
description: Researchers introduced MemeTrace, a multimodal large language model-based agent designed
  to trace how online memes originate and spread, rather than just classifying individual images as safe
  or unsafe. The system analyzes contextual and cultural signals to flag memes carrying disinformation
  or propaganda, and was tested on a new 100-meme dataset called Meme100, where it outperformed a vision-language
  model baseline and stayed robust to visual perturbations. The paper has implications for content moderation
  practices on platforms grappling with rapidly evolving meme-based disinformation.
date: '2026-10-13'
themes:
- ai-human-rights
entities:
- tech/memetrace
- tech/meme100
tags:
- content moderation
- disinformation
- multimodal LLM
- meme analysis
generated:
  by: planetai/openrouter:anthropic/claude-sonnet-5
  at: '2026-10-15T10:02:21Z'
status: stable
sources:
- id: arxiv-2610.19267
  resource: https://arxiv.org/abs/2610.19267
  title: 'MemeTrace: A Multimodal LLM-Based Agent for Safety-Aware Meme Provenance Analysis'
  author: Bo Shao, Yihan Ma, Yiting Qu, Michael Backes, Yang Zhang
  last_modified: '2026-10-13'
---

A team of researchers released MemeTrace, a multimodal LLM-based agent built to trace the origin, spread, and potential societal risks of online memes rather than simply labeling individual images as safe or unsafe[^arxiv-2610.19267]. The system addresses a gap in current moderation research, which typically lacks the ability to perform broader provenance analysis of how memes evolve in response to news events and carry disinformation or propaganda[^arxiv-2610.19267]. The authors evaluated MemeTrace against a vision-language model baseline using Meme100, a new dataset of 100 real-world memes, combining human annotation with automatic metrics[^arxiv-2610.19267]. MemeTrace showed higher accuracy at detecting unsafe content, particularly disinformation and sensitive material, and remained robust under visual perturbations[^arxiv-2610.19267]. The paper was accepted to the Findings of EMNLP 2026 and submitted to arXiv on October 13, 2026[^arxiv-2610.19267].
