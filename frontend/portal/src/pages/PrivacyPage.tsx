import { Link } from 'react-router-dom';
import BottomNav from '../components/layout/BottomNav';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-surface text-on-surface">
      <header className="border-b border-outline-variant/20 px-4 md:px-8 py-5 flex items-center justify-between">
        <Link to="/" className="text-xl font-extrabold tracking-tighter font-headline text-on-surface">
          NextPlan
        </Link>
        <Link to="/" className="text-sm text-primary font-bold hover:underline">
          ← Back
        </Link>
      </header>

      <main className="max-w-3xl mx-auto px-4 md:px-8 py-16 pb-28 md:pb-16 space-y-12">
        <div>
          <h1 className="text-4xl font-black font-headline tracking-tighter mb-3">Privacy Notice</h1>
          <p className="text-on-surface-variant text-sm">Last updated: April 2026</p>
        </div>

        {/* 1. Controller */}
        <section className="space-y-3">
          <h2 className="text-xl font-bold">1. Who we are</h2>
          <p className="text-on-surface-variant leading-relaxed">
            NextPlan is operated by <strong>[Organisation Name]</strong>, located at{' '}
            <strong>[Address]</strong>, Spain. For data protection enquiries contact us at{' '}
            <strong>[privacy@yourdomain.com]</strong>.
          </p>
          <p className="text-on-surface-variant leading-relaxed">
            We act as the <strong>data controller</strong> for the personal data described in this notice (GDPR Art. 4(7)).
          </p>
        </section>

        {/* 2. Data we collect */}
        <section className="space-y-4">
          <h2 className="text-xl font-bold">2. Personal data we collect</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-outline-variant/20">
                  <th className="text-left py-3 pr-4 font-bold text-on-surface-variant uppercase tracking-wider text-xs">Data</th>
                  <th className="text-left py-3 pr-4 font-bold text-on-surface-variant uppercase tracking-wider text-xs">Purpose</th>
                  <th className="text-left py-3 font-bold text-on-surface-variant uppercase tracking-wider text-xs">Lawful basis</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/10">
                {[
                  ['Email, username, password', 'Account authentication', 'Contract (Art. 6(1)(b))'],
                  ['Full name, avatar', 'Profile display', 'Contract (Art. 6(1)(b))'],
                  ['Preferred location & budget', 'Personalised recommendations', 'Contract (Art. 6(1)(b))'],
                  ['Saved events & reviews', 'Core service features', 'Contract (Art. 6(1)(b))'],
                  ['AI planning conversations', 'Saving your plans for later', 'Contract (Art. 6(1)(b))'],
                  ['Event and weather data', 'Recommendation generation', 'Legitimate interest (Art. 6(1)(f))'],
                ].map(([data, purpose, basis]) => (
                  <tr key={data}>
                    <td className="py-3 pr-4 text-on-surface">{data}</td>
                    <td className="py-3 pr-4 text-on-surface-variant">{purpose}</td>
                    <td className="py-3 text-on-surface-variant">{basis}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* 3. AI planning */}
        <section className="space-y-3">
          <h2 className="text-xl font-bold">3. AI planning conversations</h2>
          <p className="text-on-surface-variant leading-relaxed">
            When you use the AI Planner, your messages (including preferences about location, dates,
            budget, and companions) are saved to your account in Google Firestore. This allows you to
            continue a planning session across devices and sessions. Conversations are automatically
            deleted after <strong>12 months of inactivity</strong>.
          </p>
          <p className="text-on-surface-variant leading-relaxed">
            The lawful basis is contract performance (Art. 6(1)(b)) — saving your plans is necessary
            to provide the service you requested.
          </p>
        </section>

        {/* 4. Retention */}
        <section className="space-y-3">
          <h2 className="text-xl font-bold">4. How long we keep your data</h2>
          <ul className="text-on-surface-variant space-y-2 leading-relaxed list-disc list-inside">
            <li>Account data: until you request erasure or your account is deleted.</li>
            <li>Saved events and reviews: until you delete them or request account erasure.</li>
            <li>AI planning conversations: 12 months from the last activity on a plan.</li>
            <li>Authentication tokens: 7 days (refresh) / 15 minutes (access), then automatically expired.</li>
          </ul>
        </section>

        {/* 5. Third parties */}
        <section className="space-y-3">
          <h2 className="text-xl font-bold">5. Third-party processors</h2>
          <p className="text-on-surface-variant leading-relaxed">
            We share data with the following processors under data processing agreements:
          </p>
          <ul className="text-on-surface-variant space-y-2 leading-relaxed list-disc list-inside">
            <li><strong>Google Cloud Platform</strong> — database, compute, and storage infrastructure (EU region)</li>
            <li><strong>Ticketmaster / Eventbrite</strong> — event catalogue data (no personal data sent)</li>
            <li><strong>Google Places</strong> — venue information (no personal data sent)</li>
            <li><strong>Open-Meteo</strong> — weather data (no personal data sent)</li>
          </ul>
        </section>

        {/* 6. International transfers */}
        <section className="space-y-3">
          <h2 className="text-xl font-bold">6. International transfers</h2>
          <p className="text-on-surface-variant leading-relaxed">
            Your data is stored in Google Cloud Platform's <strong>EU region</strong>. Where any
            processing occurs in the US, it is covered by the EU-US Data Privacy Framework (Art. 45 GDPR)
            or Standard Contractual Clauses (Art. 46 GDPR).
          </p>
        </section>

        {/* 7. Your rights */}
        <section className="space-y-4">
          <h2 className="text-xl font-bold">7. Your rights</h2>
          <p className="text-on-surface-variant leading-relaxed">
            Under GDPR Chapter III you have the right to:
          </p>
          <ul className="text-on-surface-variant space-y-2 leading-relaxed list-disc list-inside">
            <li><strong>Access</strong> (Art. 15) — request a copy of your data via your profile settings or <code className="text-primary">GET /api/v1/users/me/export</code></li>
            <li><strong>Rectification</strong> (Art. 16) — update your profile at any time in settings</li>
            <li><strong>Erasure</strong> (Art. 17) — permanently delete your account and all data from your profile settings</li>
            <li><strong>Portability</strong> (Art. 20) — download your data as JSON from your profile settings</li>
            <li><strong>Objection</strong> (Art. 21) — object to processing based on legitimate interest by contacting us</li>
            <li><strong>Withdraw consent</strong> — where processing is based on consent, you may withdraw at any time</li>
          </ul>
          <p className="text-on-surface-variant leading-relaxed">
            To exercise any right, email <strong>[privacy@yourdomain.com]</strong>. We will respond within
            one month (Art. 12(3)).
          </p>
          <p className="text-on-surface-variant leading-relaxed">
            You also have the right to lodge a complaint with the Spanish data protection authority:{' '}
            <strong>Agencia Española de Protección de Datos (AEPD)</strong>,{' '}
            <a href="https://www.aepd.es" className="text-primary hover:underline" target="_blank" rel="noreferrer">
              www.aepd.es
            </a>{' '}
            (Art. 77 GDPR).
          </p>
        </section>

        {/* 8. Security */}
        <section className="space-y-3">
          <h2 className="text-xl font-bold">8. Security</h2>
          <p className="text-on-surface-variant leading-relaxed">
            We protect your data using bcrypt password hashing, hashed session tokens, HTTPS in
            transit, and access controls on all infrastructure (Art. 32 GDPR). In the event of a
            data breach that is likely to result in risk to your rights, we will notify you and the
            AEPD within 72 hours (Art. 33–34 GDPR).
          </p>
        </section>

        {/* 9. Changes */}
        <section className="space-y-3">
          <h2 className="text-xl font-bold">9. Changes to this notice</h2>
          <p className="text-on-surface-variant leading-relaxed">
            If we make material changes, we will notify you by email or in-app notice at least 30 days
            before the change takes effect.
          </p>
        </section>

        <div className="border-t border-outline-variant/20 pt-8">
          <p className="text-xs text-on-surface-variant/50">
            ⚠️ Placeholders marked [like this] must be completed with real organisation details before publishing.
            This notice should be reviewed by a qualified data protection lawyer or DPO prior to launch.
          </p>
        </div>
      </main>
      <BottomNav />
    </div>
  );
}
