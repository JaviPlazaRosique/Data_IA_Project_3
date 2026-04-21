import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="bg-surface border-t border-outline-variant/20 py-12 px-4 md:px-8 mt-24">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
        <div className="text-on-surface/40 text-xs font-medium font-body">
          © {new Date().getFullYear()} NextPlan. Powered by Neon Nocturne.
        </div>
        <div className="flex flex-wrap justify-center gap-4 md:gap-8">
          <Link to="/privacy" className="text-on-surface/40 hover:text-primary text-xs font-medium transition-opacity">Privacy Policy</Link>
          <a href="#" className="text-on-surface/40 hover:text-primary text-xs font-medium transition-opacity">Terms of Service</a>
          <a href="#" className="text-on-surface/40 hover:text-primary text-xs font-medium transition-opacity">Open-Meteo Data</a>
          <a href="#" className="text-on-surface/40 hover:text-primary text-xs font-medium transition-opacity">Contact</a>
        </div>
      </div>
    </footer>
  );
}
