# ADR 0003: Emergency check in plain code before any LLM call
- Status: Accepted · Date: 2026-10-26

**Context:** safety must not depend on a model's judgement or an API being available.
**Decision:** `agent/safety.py` matches English, Hinglish and Hindi phrases before extraction. If it fires, the
answer always starts with 112 / 108 and the search is forced to hospitals, even if the LLM call fails.
**Consequences:** some false alarms are possible and accepted; recall is tested on the whole evaluation set in CI.
