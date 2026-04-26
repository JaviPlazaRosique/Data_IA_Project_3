import TopNav from '../components/layout/TopNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import QuickMatch from '../components/QuickMatch';

export default function SwipePage() {
  return (
    <div className="bg-surface text-on-surface min-h-screen">
      <TopNav />
      <main className="pt-6 pb-24 px-4 md:px-12">
        <div className="max-w-4xl mx-auto">
          <QuickMatch />
        </div>
      </main>
      <BottomNav />
      <Footer />
    </div>
  );
}
