export type Lang = 'es' | 'en';

export interface I18n {
  nav: { discover: string; planner: string; map: string; profile: string; roadmap: string };
  brand_tagline: string;
  cta_plan: string;
  cta_surprise: string;
  cta_explore: string;
  weather_hero_prefix: string;
  weather_hero_suffix: string;
  weather_hero_rain: string;
  tonight: string;
  weekend: string;
  next_week: string;
  curated: string;
  curated_sub: string;
  sources: string;
  sources_sub: string;
  categories: string;
  see_details: string;
  save: string;
  saved: string;
  price_free: string;
  now: string;
  planner_greeting: string;
  planner_sub: string;
  planner_placeholder: string;
  planner_slots_title: string;
  slot_people: string;
  slot_type: string;
  slot_place: string;
  slot_date: string;
  slot_budget: string;
  slot_empty: string;
  generate_plan: string;
  regenerate: string;
  plan_card_title: string;
  plan_weather_note: string;
  map_title: string;
  map_sub: string;
  map_legend: string;
  map_weather_overlay: string;
  event_weather: string;
  event_book: string;
  event_save: string;
  event_share: string;
  event_about: string;
  event_similar: string;
  profile_title: string;
  profile_prefs: string;
  profile_saved: string;
  profile_history: string;
  profile_pending_rate: string;
  rate_placeholder: string;
  submit_rating: string;
  roadmap_title: string;
  roadmap_sub: string;
  coming_soon: string;
  weather: {
    sunny: string;
    partly: string;
    cloudy: string;
    rain: string;
    storm: string;
    clear_night: string;
  };
}

const es: I18n = {
  nav: { discover: '¿Sí o No?', planner: 'Discover', map: 'Mapa', profile: 'Perfil', roadmap: 'Próximo' },
  brand_tagline: 'Planes que encajan con tu día, tu gente y el tiempo que hace.',
  cta_plan: 'Planéame la noche',
  cta_surprise: 'Sorpréndeme',
  cta_explore: 'Ver todo',
  weather_hero_prefix: 'Con',
  weather_hero_suffix: 'he priorizado planes al aire libre',
  weather_hero_rain: 'he priorizado planes bajo techo',
  tonight: 'Esta noche',
  weekend: 'Fin de semana',
  next_week: 'Próxima semana',
  curated: 'Curado para hoy',
  curated_sub: 'Cruzamos tus gustos con el clima en tiempo real.',
  sources: 'Fuentes',
  sources_sub: 'Combinamos datos en un solo plan.',
  categories: 'Qué te apetece',
  see_details: 'Ver detalles',
  save: 'Guardar',
  saved: 'Guardado',
  price_free: 'Gratis',
  now: 'Ahora',
  planner_greeting: 'Hola. ¿Qué te apetece hacer?',
  planner_sub: 'Cuéntame en lenguaje natural. Yo cruzo clima, agenda y tus gustos.',
  planner_placeholder: 'Ej. "cena el viernes, presupuesto 40€, algo tranquilo"',
  planner_slots_title: 'Lo que tengo de ti',
  slot_people: 'Personas',
  slot_type: 'Tipo de plan',
  slot_place: 'Zona',
  slot_date: 'Cuándo',
  slot_budget: 'Presupuesto',
  slot_empty: 'sin definir',
  generate_plan: 'Generar plan',
  regenerate: 'Otra propuesta',
  plan_card_title: 'Tu plan',
  plan_weather_note: 'Clima cruzado con el horario del plan.',
  map_title: 'Explora en el mapa',
  map_sub: 'Chinchetas por categoría. Los filtros cruzan con el clima actual.',
  map_legend: 'Leyenda',
  map_weather_overlay: 'Capa de clima',
  event_weather: 'Clima previsto para el evento',
  event_book: 'Reservar',
  event_save: 'Guardar',
  event_share: 'Compartir',
  event_about: 'Sobre el evento',
  event_similar: 'Planes parecidos',
  profile_title: 'Tu perfil',
  profile_prefs: 'Preferencias',
  profile_saved: 'Guardados',
  profile_history: 'Historial',
  profile_pending_rate: 'Valora estos planes',
  rate_placeholder: '¿Cómo fue? Tu valoración afina los próximos planes.',
  submit_rating: 'Enviar valoración',
  roadmap_title: 'Próximamente',
  roadmap_sub: 'Construyendo en esta dirección. No están en el MVP.',
  coming_soon: 'Próximamente',
  weather: {
    sunny: 'Soleado',
    partly: 'Parcialmente nublado',
    cloudy: 'Nublado',
    rain: 'Lluvia',
    storm: 'Tormenta',
    clear_night: 'Despejado',
  },
};

const en: I18n = {
  nav: { discover: 'Discover', planner: 'AI Planner', map: 'Map', profile: 'Profile', roadmap: 'Roadmap' },
  brand_tagline: 'Plans that match your day, your crew, and the weather outside.',
  cta_plan: 'Plan my night',
  cta_surprise: 'Surprise me',
  cta_explore: 'Explore all',
  weather_hero_prefix: 'With',
  weather_hero_suffix: 'I prioritised outdoor plans',
  weather_hero_rain: 'I prioritised indoor plans',
  tonight: 'Tonight',
  weekend: 'This weekend',
  next_week: 'Next week',
  curated: 'Curated for today',
  curated_sub: 'Your taste crossed with live weather.',
  sources: 'Sources',
  sources_sub: 'Four feeds, one coherent plan.',
  categories: 'What are you in the mood for',
  see_details: 'See details',
  save: 'Save',
  saved: 'Saved',
  price_free: 'Free',
  now: 'Now',
  planner_greeting: 'Hi. What are you in the mood for?',
  planner_sub: 'Tell me in plain language. I handle weather, calendar, and your taste.',
  planner_placeholder: 'e.g. "dinner Friday, €40 budget, low key"',
  planner_slots_title: 'What I have so far',
  slot_people: 'People',
  slot_type: 'Plan type',
  slot_place: 'Area',
  slot_date: 'When',
  slot_budget: 'Budget',
  slot_empty: 'not set',
  generate_plan: 'Generate plan',
  regenerate: 'Try another',
  plan_card_title: 'Your plan',
  plan_weather_note: 'Weather cross-checked with the plan time.',
  map_title: 'Explore on the map',
  map_sub: 'Pins by category. Filters cross with live weather.',
  map_legend: 'Legend',
  map_weather_overlay: 'Weather layer',
  event_weather: 'Forecast at event time',
  event_book: 'Book',
  event_save: 'Save',
  event_share: 'Share',
  event_about: 'About',
  event_similar: 'Similar plans',
  profile_title: 'Your profile',
  profile_prefs: 'Preferences',
  profile_saved: 'Saved',
  profile_history: 'History',
  profile_pending_rate: 'Rate these plans',
  rate_placeholder: 'How did it go? Your rating tunes the next plans.',
  submit_rating: 'Submit rating',
  roadmap_title: 'Coming next',
  roadmap_sub: 'Where we are heading. Not in the MVP.',
  coming_soon: 'Coming soon',
  weather: {
    sunny: 'Sunny',
    partly: 'Partly cloudy',
    cloudy: 'Cloudy',
    rain: 'Rain',
    storm: 'Storm',
    clear_night: 'Clear night',
  },
};

export const STRINGS: Record<Lang, I18n> = { es, en };
