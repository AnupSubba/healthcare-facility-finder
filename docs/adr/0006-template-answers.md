# ADR 0006: Listing answers are fixed templates, not LLM text
- Status: Accepted · Date: 2026-10-26

**Context:** generated summaries of listings could misstate details.
**Decision:** answers about results use fixed English/Hindi templates; the LLM is only used for extraction and
glossary explanations.
**Consequences:** faster, cheaper, no hallucinated details; answers are less conversational.
