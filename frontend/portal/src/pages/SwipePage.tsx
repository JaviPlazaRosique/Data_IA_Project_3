import TopNav from '../components/layout/TopNav';
import Footer from '../components/layout/Footer';
import BottomNav from '../components/layout/BottomNav';
import QuickMatch from '../components/QuickMatch';

export default function SwipePage() {
  return (
    <div className="bg-surface text-on-surface h-screen flex flex-col overflow-hidden">
      <TopNav />
      <main className="flex-1 min-h-0 overflow-hidden px-4 md:px-12 pt-2 pb-[calc(72px+env(safe-area-inset-bottom))] md:pb-2">
        <div className="max-w-4xl mx-auto h-full">
          <QuickMatch />
        </div>
      </main>
      <BottomNav />
    </div>
  );
}
