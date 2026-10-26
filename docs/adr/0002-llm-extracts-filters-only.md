# ADR 0002: The LLM only extracts filters; code builds SQL with bound parameters
- Status: Accepted · Date: 2026-10-26

**Context:** LLM-written SQL can be wrong or unsafe, and LLMs can invent facilities.
**Decision:** the LLM returns a validated `FacilitySearch` (Pydantic). `repository.search` joins only fixed SQL
fragments and binds every value. Listings come straight from the database.
**Consequences:** no SQL injection, no invented listings, fully testable search. Questions outside the supported
filters can't be answered, which is acceptable for v1.
