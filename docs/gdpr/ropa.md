# Record of Processing Activities (RoPA)
**Art. 30 GDPR — maintained by the data controller**

> **Controller:** [Organisation Name], [Address], Spain  
> **DPO / Contact:** [privacy@yourdomain.com]  
> **Last reviewed:** April 2026

---

## Processing Activities

### 1. User Account Management

| Field | Detail |
|-------|--------|
| **Purpose** | Create and manage user accounts; authenticate users |
| **Lawful basis** | Contract — Art. 6(1)(b) |
| **Data subjects** | Registered users |
| **Personal data** | Email, username, bcrypt-hashed password, full name, avatar URL, preferred location, preferred budget, `is_active` flag, hashed refresh token, token expiry |
| **Special categories** | None |
| **Recipients** | Internal only; Google Cloud Platform (processor) |
| **Third-country transfers** | GCP EU region (`europe-west1`). US transfers (if any) covered by EU-US Data Privacy Framework or SCCs |
| **Retention** | Until user requests erasure (`DELETE /api/v1/users/me/data`) or account is deleted |
| **Security measures** | bcrypt password hashing; SHA-256 hashed refresh tokens; HTTPS in transit; CloudSQL private VPC; access controls |

---

### 2. Saved Events

| Field | Detail |
|-------|--------|
| **Purpose** | Allow users to bookmark events for later reference |
| **Lawful basis** | Contract — Art. 6(1)(b) |
| **Data subjects** | Registered users |
| **Personal data** | User ID (FK), event ID, event title, event venue, event date/time, event image URL |
| **Special categories** | None |
| **Recipients** | Internal only; Google Cloud Platform (processor) |
| **Third-country transfers** | GCP EU region |
| **Retention** | Until user deletes the bookmark or requests account erasure |
| **Security measures** | CloudSQL private VPC; row-level ownership enforced in API layer; HTTPS in transit |

---

### 3. Event Reviews

| Field | Detail |
|-------|--------|
| **Purpose** | Allow users to rate and review attended events |
| **Lawful basis** | Contract — Art. 6(1)(b) |
| **Data subjects** | Registered users |
| **Personal data** | User ID (FK), event ID, star rating (1–5), free-text review, timestamps |
| **Special categories** | None |
| **Recipients** | Internal only; Google Cloud Platform (processor) |
| **Third-country transfers** | GCP EU region |
| **Retention** | Until user deletes the review or requests account erasure |
| **Security measures** | CloudSQL private VPC; ownership enforced in API; HTTPS |

---

### 4. AI Planning Conversations

| Field | Detail |
|-------|--------|
| **Purpose** | Save AI planner chat sessions so users can resume across devices/sessions |
| **Lawful basis** | Contract — Art. 6(1)(b) |
| **Data subjects** | Registered users |
| **Personal data** | User ID, chat messages (may contain preferences: location, dates, budget, companions), plan title, itinerary structure |
| **Special categories** | None expected at MVP; potential indirect inference of lifestyle preferences |
| **Recipients** | Internal only; Google Cloud Platform / Firestore (processor) |
| **Third-country transfers** | Firestore `eur3` multi-region Europe |
| **Retention** | 12 months from last activity; `expires_at` TTL field managed by Firestore TTL policy |
| **Security measures** | Firestore security rules; ownership enforced in API layer; HTTPS; access controls |

---

### 5. Event & Venue Catalogue

| Field | Detail |
|-------|--------|
| **Purpose** | Generate personalised event recommendations |
| **Lawful basis** | Legitimate interest — Art. 6(1)(f). LIA: purpose is to provide the core service; data is publicly available catalogue data; no personal data is transmitted to external APIs |
| **Data subjects** | N/A — no personal data; data is event/venue metadata |
| **Personal data** | None |
| **Special categories** | None |
| **Recipients** | Ticketmaster API, Eventbrite API, Google Places API (data sources, not processors of personal data) |
| **Third-country transfers** | API calls to US-based services; no personal data transmitted |
| **Retention** | Cached per pipeline schedule; not linked to individual users |
| **Security measures** | API keys stored in environment variables / Secret Manager; no personal data in requests |

---

### 6. Weather Data

| Field | Detail |
|-------|--------|
| **Purpose** | Enhance recommendations with real-time weather conditions |
| **Lawful basis** | Legitimate interest — Art. 6(1)(f). No personal data transmitted. |
| **Data subjects** | N/A |
| **Personal data** | None — only location coordinates sent to Open-Meteo |
| **Special categories** | None |
| **Recipients** | Open-Meteo (open-source API, no DPA required) |
| **Third-country transfers** | Open-Meteo servers (EU-based); no personal data |
| **Retention** | Not stored; fetched at request time |
| **Security measures** | HTTPS |

---

## Placeholders to Complete Before Publishing

- [ ] Fill in Organisation Name, address, DPO contact
- [ ] Confirm GCP region(s) in use for CloudSQL and Firestore
- [ ] Confirm Firestore TTL policy is active on `expires_at` field
- [ ] Review Ticketmaster and Eventbrite T&Cs — determine if joint controller relationship applies
- [ ] Have this RoPA reviewed by a qualified DPO or data protection lawyer
