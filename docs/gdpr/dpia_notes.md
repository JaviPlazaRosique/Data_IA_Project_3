# DPIA Screening Notes — AI Personalisation Pipeline
**Art. 35 GDPR — Data Protection Impact Assessment**

> **Last reviewed:** April 2026  
> **Status:** Screening completed — full DPIA not required at MVP (see conclusion below)

---

## 1. What is this document?

Art. 35 GDPR requires a full DPIA before processing that is "likely to result in a high risk to
the rights and freedoms of natural persons." This document records the screening assessment for
the AI personalisation pipeline in The Electric Curator.

---

## 2. Processing Description

The AI planner collects the following inputs from authenticated users:

| Data element | Source | Purpose |
|-------------|--------|---------|
| Free-text chat messages | User input | Understand preferences (location, dates, budget, companions) |
| Saved events list | CloudSQL | Personalise recommendations |
| Star ratings and reviews | CloudSQL | Learn post-event preferences |
| Preferred location / budget | User profile | Seed recommendations |
| Weather data | Open-Meteo (no personal data) | Contextual relevance |
| Event catalogue | Ticketmaster / Eventbrite / Google Places (no personal data) | Pool of recommendations |

The AI agent generates event plans. Chat messages are stored in Firestore with a 12-month TTL.
No automated decision-making with legal or similarly significant effects (Art. 22) occurs at MVP.

---

## 3. DPIA Screening — High-Risk Indicators (Art. 35(3) + WP248/17)

| Criterion | Present? | Notes |
|-----------|----------|-------|
| Evaluation / scoring (profiling) | Partial | Preferences inferred from chat and saved events. Not used for legal/contractual decisions. |
| Automated decision-making with legal effects | **No** | Recommendations are suggestions only; user retains full control. |
| Systematic monitoring | No | No background monitoring of user behaviour outside explicit interactions. |
| Sensitive data (Art. 9) or criminal data (Art. 10) | No | No health, biometric, political, or religious data collected at MVP. Chat text _could_ incidentally contain sensitive data — mitigated by minimal retention (12 months). |
| Data processed at large scale | No | MVP — small user base. Revisit at scale. |
| Matching / combining datasets | Partial | Event catalogue + user preferences combined for recommendations. No cross-organisation data matching. |
| Data about vulnerable subjects | No | No children's data (no age verification mechanism — add to roadmap). |
| Innovative use of new technology | Partial | LLM-powered chat is novel. LLM provider is internal / standard cloud AI — no external LLM API at MVP. |
| Processing prevents exercise of a right or service | No | |

**Score: 2 out of 9 criteria partially met.** WP248/17 recommends a full DPIA when 2+ criteria
are present and the combination poses meaningful risk. Assessment: **borderline — full DPIA
recommended before production launch at scale** but not blocking at MVP stage with the
mitigations below.

---

## 4. Necessity & Proportionality

- **Necessity:** Chat storage is necessary to fulfil the service (cross-device session continuity). Without storage, a key feature is broken.
- **Proportionality:** Only the minimum data is stored (messages, title, simple itinerary). No audio, location tracking, or device fingerprinting.
- **Alternative considered:** Session-only storage (in-memory, not persisted). Rejected because cross-device continuity is a core user need.

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigations in place |
|------|-----------|--------|---------------------|
| Chat messages contain sensitive personal information | Low–Medium | Medium | 12-month TTL auto-deletion; users can delete plans at any time; ownership enforced in API |
| Unauthorised access to Firestore plans | Low | High | Firestore security rules + API-layer ownership checks; GCP IAM least-privilege |
| LLM inference leaks one user's data to another | Low | High | No shared LLM context across users at MVP; each plan is isolated |
| Inferred profile used beyond stated purpose | Low | Medium | No secondary use at MVP; purpose limitation documented in RoPA |
| User unable to exercise erasure right | Low | Medium | `DELETE /api/v1/users/me/data` deletes all Firestore plans + CloudSQL rows |

---

## 6. Mitigation Measures

All mitigations are already implemented or documented:

- ✅ 12-month TTL on AI plans via Firestore TTL policy (`expires_at` field)
- ✅ User-initiated deletion: `DELETE /plans/{plan_id}` and full erasure `DELETE /users/me/data`
- ✅ Ownership enforced at API layer (no cross-user access)
- ✅ Data export available: `GET /users/me/export` + `GET /plans`
- ✅ Privacy Notice discloses AI chat persistence and lawful basis
- ✅ In-app disclosure banner shown to authenticated users before first use
- ⚠️ Age verification not implemented — add before collecting data about under-18s
- ⚠️ Full DPIA required before deploying a third-party LLM API (e.g., OpenAI/Anthropic) to process chat data

---

## 7. Conclusion

**Full DPIA not required at MVP** under the current architecture because:
1. No automated decisions with legal or similarly significant effects (Art. 22 not triggered).
2. No special category data collected by design.
3. User base is small; large-scale processing threshold not met.
4. Meaningful mitigations are already in place.

**Revisit this assessment when:**
- A third-party LLM API is integrated to process chat messages
- User base exceeds ~10,000 active users
- Age verification is added (children's data triggers mandatory DPIA)
- Group planning features (v2 roadmap) are added

---

> **⚠️ Legal Advice Disclaimer**: This screening is informational. For high-risk processing or
> before production deployment at scale, commission a full DPIA reviewed by a qualified DPO.
