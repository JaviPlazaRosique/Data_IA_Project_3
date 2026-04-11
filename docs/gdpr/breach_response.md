# Data Breach Response Procedure
**Art. 33–34 GDPR — Breach Notification**

> **Last reviewed:** April 2026  
> **Owner:** [DPO / Data Protection Contact]  
> **Contact for reporting:** [privacy@yourdomain.com]

---

## Overview

Under GDPR Art. 33, a personal data breach that is likely to result in a risk to the rights and
freedoms of individuals must be notified to the supervisory authority **within 72 hours** of
becoming aware of it. If the breach is likely to result in a **high risk**, affected individuals
must also be notified without undue delay (Art. 34).

---

## Step 1 — Detection & Initial Assessment (within 24 hours)

**Who:** Any team member who discovers or suspects a breach.

**Actions:**
1. Do not attempt to cover up or delay reporting internally.
2. Record the date and time of discovery in the [Incident Log](#incident-log-template).
3. Immediately notify [DPO / responsible person] at [privacy@yourdomain.com].
4. Preserve evidence: logs, error messages, screenshots — do not delete.
5. Determine initial scope:
   - What data may be affected? (categories, approximate number of records / users)
   - Is it ongoing (e.g., active intrusion) or historic (e.g., misconfiguration)?
   - What systems are involved? (CloudSQL, Firestore, Cloud Run, frontend)

**Breach triggers (non-exhaustive):**
- Unauthorised access to the CloudSQL database
- Firestore data exposed without authentication
- Refresh tokens or hashed passwords exfiltrated
- Cloud Run service returning user data to wrong users
- Lost or stolen credentials with access to production

---

## Step 2 — Containment (within 24–48 hours)

1. Revoke compromised credentials immediately (GCP IAM, API keys, JWT secrets).
2. Rotate affected secrets in GCP Secret Manager.
3. Force-invalidate all refresh tokens: `UPDATE users SET refresh_token = NULL, refresh_token_expires_at = NULL`.
4. If data exposure in Firestore: audit Firestore security rules and re-apply least-privilege.
5. Block malicious IPs at Cloud Armor / load balancer level if applicable.
6. Preserve audit logs from Cloud Logging before they rotate.

---

## Step 3 — Risk Assessment (within 48 hours)

Assess the breach against four GDPR criteria:

| Criterion | Questions to answer |
|-----------|---------------------|
| **Nature** | Confidentiality breach? Integrity breach? Availability breach? |
| **Sensitivity** | What categories of data? (passwords, emails, plan content, ratings) |
| **Volume** | How many data subjects affected? |
| **Consequences** | What harm could result? (identity theft, discrimination, reputational damage) |

**Risk levels:**
- **Low risk** → internal record only (Art. 33(5)); no SA notification required
- **Risk to individuals** → notify AEPD within 72 hours (Art. 33)
- **High risk to individuals** → notify AEPD + notify affected users (Art. 33 + Art. 34)

---

## Step 4 — Supervisory Authority Notification (within 72 hours of awareness)

**SA:** Agencia Española de Protección de Datos (AEPD)  
**Notification portal:** https://sedeagpd.gob.es/sede-electronica-web/  
**AEPD breach notification guidance:** https://www.aepd.es/

**Required information (Art. 33(3)):**
1. Nature of the breach (categories and approximate number of data subjects and records)
2. Name and contact of the DPO or data protection contact
3. Likely consequences of the breach
4. Measures taken or proposed to address the breach and mitigate adverse effects

If full information is not available within 72 hours, submit an initial notification and provide
additional information in phases (Art. 33(4)).

---

## Step 5 — User Notification (if high risk)

**Trigger:** Breach is likely to result in high risk to the rights and freedoms of individuals
(Art. 34(1)), e.g., exposure of plaintext passwords, sensitive plan content, or large-scale
data exfiltration.

**Communication channel:** Email to affected users + in-app notice.

**Required content (Art. 34(2)):**
1. Clear description of the nature of the breach
2. DPO or contact point details
3. Likely consequences
4. Measures taken to address the breach
5. Steps users should take (e.g., change password, monitor accounts)

**Template subject:** `Important: Security notice regarding your The Electric Curator account`

---

## Step 6 — Post-Incident Review

Within 2 weeks of resolution:
1. Root cause analysis
2. Update incident log with full timeline
3. Identify process or technical gaps
4. Implement fixes and document in changelog
5. Update this procedure if gaps found

---

## Incident Log Template

Maintain a record of all breaches (even those not requiring SA notification) per Art. 33(5).

```
Incident ID:        [INC-YYYY-NNN]
Date discovered:    [YYYY-MM-DD HH:MM UTC]
Date of breach:     [known or estimated]
Reported by:        [name/role]
Description:        [brief description]
Data categories:    [e.g., email addresses, plan content]
Records affected:   [approximate number]
Users affected:     [approximate number]
Risk level:         [low / medium / high]
SA notified:        [yes/no — date if yes]
Users notified:     [yes/no — date if yes]
Containment steps:  [summary]
Root cause:         [summary]
Remediation:        [summary]
Closed:             [YYYY-MM-DD]
```

---

> **⚠️ Legal Advice Disclaimer**: This procedure is a starting template. For matters involving
> significant compliance risk or supervisory authority interaction, consult a qualified data
> protection lawyer or your DPO.
