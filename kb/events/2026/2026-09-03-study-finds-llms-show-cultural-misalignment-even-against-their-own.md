---
type: Event
kind: paper
title: Study Finds LLMs Show Cultural Misalignment Even Against Their Own Home Countries, Fine-Tuning
  Reduces but Redistributes Bias
description: Researchers tested three open-weight language models—Gemma3-12B, Bielik-11B-v3, and Qwen3-4B—against
  World Values Survey data covering 63 demographic personas across three countries, measuring how far
  each model's simulated responses diverge from real population attitudes. Contrary to assumptions that
  models would be most aligned with their home country's population, the China-built Qwen3-4B showed its
  worst misalignment on Chinese respondents. The team then applied targeted LoRA fine-tuning to the worst-performing
  personas, cutting bias for Bielik-11B by 16.8% with under 1,200 training examples, but found the correction
  shifted which demographic groups were most misrepresented rather than eliminating the underlying bias.
date: '2026-09-03'
themes:
- ai-human-rights
entities:
- tech/gemma3-12b
- tech/bielik-11b-v3
- tech/qwen3-4b
tags:
- algorithmic bias
- cultural alignment
- large language models
- fine-tuning
generated:
  by: planetai/openrouter:anthropic/claude-sonnet-5
  at: '2026-09-07T10:32:30Z'
status: stable
sources:
- id: arxiv-2609.04485
  resource: https://arxiv.org/abs/2609.04485
  title: 'Cultural Misalignment in Large Language Models: Detection, Measurement, and Mitigation Through
    Targeted Fine-Tuning'
  author: Antoni Czolgowski, Abel Iyasele
  last_modified: '2026-09-03'
---

A new arXiv paper evaluates three open-weight LLMs—Gemma3-12B (USA), Bielik-11B-v3 (Poland), and Qwen3-4B (China)—against World Values Survey Wave 7 data for 63 demographic personas, using normalized Wasserstein distance to measure how far each model's outputs diverge from real-world attitudes[^arxiv-2609.04485]. Surprisingly, none of the models most closely matched their own home-country population; Qwen3-4B showed its worst misalignment on Chinese respondents, the highest mismatch score across the entire model-country matrix[^arxiv-2609.04485]. The authors then applied targeted LoRA fine-tuning on the five worst-case personas, using fewer than 1,200 training pairs and under 15 minutes of GPU time, which reduced bias for Bielik-11B by 16.8%[^arxiv-2609.04485]. However, the fine-tuning did not remove bias so much as redistribute it—Bielik's worst-represented personas shifted entirely from American to Chinese elderly respondents with no overlap before and after correction[^arxiv-2609.04485].
