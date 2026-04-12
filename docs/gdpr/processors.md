# Third-Party Processors & DPA Tracking
**Art. 28 GDPR — Data Processing Agreements**

> **Last reviewed:** April 2026  
> Status key: ✅ In place | ⚠️ Pending | ❌ Not applicable

---

## Processor Register

| Processor | Role | Personal Data Shared | DPA Status | Transfer Mechanism |
|-----------|------|----------------------|------------|-------------------|
| **Google Cloud Platform** | Infrastructure — CloudSQL (PostgreSQL), Cloud Run, Secret Manager | User account data, saved events, reviews (stored in CloudSQL) | ✅ Google Cloud DPA — accept at [console.cloud.google.com](https://console.cloud.google.com) → IAM → Data Processing | EU region `europe-west1` (Belgium). US processing covered by EU-US Data Privacy Framework (Art. 45) |
| **Google Firestore** | Database — AI planning conversations | Plan messages, plan metadata (user IDs, chat text) | ✅ Covered by Google Cloud DPA above | Firestore `eur3` multi-region Europe |
| **Ticketmaster** | Event catalogue data source | **None** — only event metadata fetched | ❌ No personal data transmitted; standard API T&Cs apply. Review whether joint controller relationship exists for ticket purchase flows (out of scope MVP) | N/A |
| **Eventbrite** | Event catalogue data source | **None** — only event metadata fetched | ❌ No personal data transmitted; review T&Cs for any analytics tracking if embedded widgets are used | N/A |
| **Google Places API** | Venue information | **None** — location coordinates sent, no personal data | ❌ No personal data; covered by Google Maps Platform T&Cs | N/A |
| **Open-Meteo** | Weather data | **None** — only location coordinates | ❌ Open-source, no personal data; no DPA required | N/A |

---

## Google Cloud Platform — Configuration Notes

- **CloudSQL region:** `europe-west1` (Belgium) — confirm in GCP Console → SQL → Instance details
- **Cloud Run region:** `europe-west1` — confirm in GCP Console → Cloud Run → Service details
- **Firestore location:** `eur3` (multi-region Europe, covers `europe-west1` and `europe-west4`) — set at database creation, cannot be changed; confirm in Firestore → Database settings
- **Firestore TTL policy:** Enable on field `expires_at` in collection `plans` — GCP Console → Firestore → Indexes → TTL

### DPA Acceptance Steps (Google Cloud)
1. Log in to [Google Cloud Console](https://console.cloud.google.com)
2. Go to IAM & Admin → Settings → Data Processing Amendment
3. Accept the Google Cloud DPA on behalf of your organisation
4. Save the confirmation (screenshot or export) for compliance records

---

## Ticketmaster — Pending Review

Ticketmaster may act as a **joint controller** if:
- Your app links to Ticketmaster ticket purchase flows
- You embed Ticketmaster widgets that set cookies or collect analytics

**Action required:** Review Ticketmaster API T&Cs and determine if a joint controller agreement (Art. 26 GDPR) is needed. At MVP, if only fetching event metadata via server-side API calls with no user data sent, no DPA is needed.

---

## Eventbrite — Pending Review

Same analysis as Ticketmaster. If only server-side metadata fetching, no DPA required.

---

## Sub-processors

Google Cloud Platform may use sub-processors for infrastructure services. The current list is maintained at:  
https://cloud.google.com/terms/subprocessors

---

## Placeholders to Complete

- [ ] Confirm GCP region for CloudSQL and Cloud Run
- [ ] Accept Google Cloud DPA and save confirmation
- [ ] Review Ticketmaster T&Cs re: joint controller
- [ ] Review Eventbrite T&Cs re: joint controller
- [ ] Enable Firestore TTL policy on `expires_at` field
- [ ] Review this document with a qualified DPO or data protection lawyer
