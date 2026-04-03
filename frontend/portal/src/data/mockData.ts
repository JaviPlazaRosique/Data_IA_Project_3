// All image URLs use picsum.photos with fixed seeds for consistency
const img = (seed: string, w: number, h: number) =>
  `https://picsum.photos/seed/${seed}/${w}/${h}`;

export interface Event {
  id: string;
  title: string;
  venue: string;
  price: string;
  tags: string[];
  date?: string;
  time?: string;
  weather?: string;
  weatherIcon?: string;
  imageUrl: string;
  buttonLabel: string;
  disabled?: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  cards?: ChatCard[];
}

export interface ChatCard {
  id: string;
  icon: string;
  label: string;
  title: string;
  imageUrl?: string;
  badge?: string;
}

export interface MapEvent {
  id: string;
  title: string;
  venue: string;
  distance: string;
  price: string;
  isLive?: boolean;
  startTime?: string;
  friends?: number;
  category: 'music' | 'food' | 'art';
  imageUrl: string;
}

export interface SavedEvent {
  id: string;
  title: string;
  venue: string;
  time: string;
  date: string;
  imageUrl: string;
}

export interface HistoryEvent {
  id: string;
  title: string;
  visitedDate: string;
  rating: number;
  review?: string;
  status: 'reviewed' | 'pending';
  imageUrl: string;
}

export interface MobileEventCard {
  id: string;
  category: string;
  title: string;
  location: string;
  liked: boolean;
  imageUrl: string;
}

export interface Platform {
  name: string;
  count: string;
}

// ─── Discover Page ────────────────────────────────────────────────────────────

export const heroEvent = {
  title: 'Neon Resonance',
  subtitle: 'Underground Electronic • 10 PM',
  temp: '18°C',
  imageUrl: img('concert-neon', 800, 1000),
};

export const featuredEvents: Event[] = [
  {
    id: '1',
    title: 'Rooftop Drift',
    venue: 'Sky Lounge • Manhattan',
    price: '$45',
    tags: ['House', 'Open Bar'],
    weather: '14°C',
    weatherIcon: 'cloud',
    imageUrl: img('rooftop-party', 600, 340),
    buttonLabel: 'Secure Spot',
  },
  {
    id: '2',
    title: 'Midnight Hoops',
    venue: 'The Cage • Brooklyn',
    price: 'FREE',
    tags: ['Live Sports', 'Indoors'],
    weather: '92% Humidity',
    weatherIcon: 'water_drop',
    imageUrl: img('basketball-court', 600, 340),
    buttonLabel: 'Join Watchlist',
  },
  {
    id: '3',
    title: 'Iron Pulse',
    venue: 'Warehouse X • Queens',
    price: '$20',
    tags: ['Techno', 'Sold Out'],
    weather: 'Storm Warning',
    weatherIcon: 'thunderstorm',
    imageUrl: img('warehouse-rave', 600, 340),
    buttonLabel: 'Waitlist Only',
    disabled: true,
  },
];

export const categories = [
  {
    id: 'music',
    label: 'Music',
    vibe: 'Vibe 01',
    color: 'text-[#9c7eff]',
    imageUrl: img('dj-controller', 700, 600),
  },
  {
    id: 'sports',
    label: 'Sports',
    vibe: 'Action 02',
    color: 'text-secondary',
    imageUrl: img('stadium-night', 400, 600),
  },
  {
    id: 'arts',
    label: 'Arts',
    vibe: 'Design 03',
    color: 'text-tertiary',
    imageUrl: img('art-gallery', 400, 600),
  },
  {
    id: 'food',
    label: 'Food',
    vibe: 'Taste 04',
    color: 'text-[#a98fff]',
    imageUrl: img('fine-dining', 700, 600),
  },
];

// ─── AI Planner Chat ───────────────────────────────────────────────────────────

export const chatMessages: ChatMessage[] = [
  {
    id: '1',
    role: 'assistant',
    content:
      "Good evening. I'm ready to curate your next experience. Based on your profile, I've noticed you enjoy rooftop lounges and experimental jazz. Should we start with a theme for Friday night?",
    timestamp: '08:42 PM',
  },
  {
    id: '2',
    role: 'user',
    content: 'Let\'s do a "Neon Noir" night in Tokyo. Start with dinner and then something hidden.',
    timestamp: '08:44 PM',
  },
  {
    id: '3',
    role: 'assistant',
    content:
      "Excellent choice. I've curated a preliminary itinerary for Shibuya and Shinjuku. Here are the core highlights:",
    timestamp: '08:45 PM',
    cards: [
      {
        id: 'c1',
        icon: 'restaurant',
        label: 'Dinner',
        title: "Omakase at 'The Void'",
        imageUrl: img('omakase', 300, 160),
        badge: '¥12,000',
      },
      {
        id: 'c2',
        icon: 'nightlife',
        label: 'Underground',
        title: "Vinyl Bar 'Cipher'",
        imageUrl: img('vinyl-bar', 300, 160),
        badge: '¥2,000',
      },
    ],
  },
];

export const quickActions = [
  { icon: 'map', label: 'Update Location' },
  { icon: 'attach_money', label: 'Adjust Budget' },
  { icon: 'groups', label: 'Add Guests' },
  { icon: 'magic_button', label: 'Suggest a Plan', isPrimary: true },
];

export const itineraryMapImage = img('tokyo-shibuya', 800, 400);
export const userAvatarUrl = img('portrait-man', 300, 300);

// ─── Map Page ─────────────────────────────────────────────────────────────────

export const mapBackgroundUrl = img('city-aerial', 1400, 900);

export const mapEvents: MapEvent[] = [
  {
    id: '1',
    title: 'Neon Dreams: Synthwave Night',
    venue: 'The Void Social Club',
    distance: '0.8km',
    price: '$25',
    isLive: true,
    startTime: '22:00',
    category: 'music',
    imageUrl: img('synthwave-club', 200, 200),
  },
  {
    id: '2',
    title: 'Umami Underground Tasting',
    venue: 'Orizuru Vault',
    distance: '1.4km',
    price: '$$$',
    friends: 4,
    category: 'food',
    imageUrl: img('fine-dining-dark', 200, 200),
  },
  {
    id: '3',
    title: 'Midnight Gallery Tour',
    venue: 'Prism Museum',
    distance: '0.4km',
    price: 'Free',
    category: 'art',
    imageUrl: img('art-museum', 200, 200),
  },
];

export const friendAvatars = [
  img('avatar-f1', 40, 40),
  img('avatar-m1', 40, 40),
];

// ─── Profile / Dashboard Page ─────────────────────────────────────────────────

export const profileAvatarUrl = img('portrait-woman', 300, 300);

export const savedEvents: SavedEvent[] = [
  {
    id: '1',
    title: 'Synthetica: The Underground',
    venue: 'Industrial Hall',
    time: '22:00 PM',
    date: 'Oct 24',
    imageUrl: img('electronic-festival', 600, 400),
  },
  {
    id: '2',
    title: 'Velvet Void Dinner',
    venue: 'The Glass Tower',
    time: '19:30 PM',
    date: 'Nov 02',
    imageUrl: img('gala-dinner', 600, 400),
  },
];

export const historyEvents: HistoryEvent[] = [
  {
    id: '1',
    title: 'Prism Museum Night',
    visitedDate: 'Visited Sept 12, 2024',
    rating: 4,
    review: '"The lighting was impeccable, but the crowd flow could have been smoother."',
    status: 'reviewed',
    imageUrl: img('museum-abstract', 300, 300),
  },
  {
    id: '2',
    title: 'The Alchemist Lounge',
    visitedDate: '',
    rating: 0,
    status: 'pending',
    imageUrl: img('cocktail-bar', 300, 300),
  },
];

// ─── Mobile Explore Page ──────────────────────────────────────────────────────

export const surpriseMeImageUrl = img('neon-festival', 800, 500);
export const featuredMobileImageUrl = img('techno-dj', 900, 600);

export const mobileEventCards: MobileEventCard[] = [
  {
    id: '1',
    category: 'Mixología • €25',
    title: 'Workshop de Coctelería Neo-Futurista',
    location: 'Malasaña, Madrid',
    liked: true,
    imageUrl: img('cocktail-neon', 400, 300),
  },
  {
    id: '2',
    category: 'Concierto • €45',
    title: 'Syntax Error: Live AV Performance',
    location: 'La Riviera, Madrid',
    liked: false,
    imageUrl: img('concert-purple', 400, 300),
  },
  {
    id: '3',
    category: 'Arte • Gratis',
    title: 'Digital Soul: Exposición Inmersiva',
    location: 'Matadero, Madrid',
    liked: false,
    imageUrl: img('digital-art', 400, 300),
  },
  {
    id: '4',
    category: 'Gastro • €60',
    title: 'Cena Clandestina: Sabores del Futuro',
    location: 'Ubicación Secreta',
    liked: true,
    imageUrl: img('secret-dinner', 400, 300),
  },
];

export const platforms: Platform[] = [
  { name: 'Ticketmaster', count: '124 Eventos' },
  { name: 'Eventbrite', count: '89 Eventos' },
  { name: 'DICE', count: '45 Eventos' },
  { name: 'RA', count: '67 Eventos' },
  { name: 'Fever', count: '32 Eventos' },
];
