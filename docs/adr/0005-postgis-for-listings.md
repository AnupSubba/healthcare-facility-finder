# ADR 0005: PostGIS for listings, Chroma only for the glossary
- Status: Accepted · Date: 2026-10-26

**Context:** "within 5 km" and filters are spatial and relational queries, not semantic similarity.
**Decision:** PostgreSQL + PostGIS (Neon free tier in production) for facilities; a small Chroma index only for
glossary explanations.
**Consequences:** fast, exact geo search with indexes; two stores to maintain, but each fits its job.
