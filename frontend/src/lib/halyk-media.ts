export type HalykMedia = {
  id: string;
  src: string;
  alt: string;
  sourceUrl: string;
  sourceLabel: string;
  objectPosition: string;
};

// Editorial illustrations of the Halyk ecosystem, not photos of dataset events.
// Original photographs and source details: public/images/halyk/SOURCES.md.
export const HALYK_MEDIA: readonly HalykMedia[] = [
  {
    id: 'headquarters',
    src: '/images/halyk/headquarters.webp',
    alt: 'Штаб-квартира Halyk Bank в Алматы на фоне гор',
    sourceUrl: 'https://halykbank.com/about-us',
    sourceLabel: 'Halyk Bank',
    objectPosition: '60% 55%',
  },
  {
    id: 'academy-session',
    src: '/images/halyk/academy-session.webp',
    alt: 'Встреча со студентами в Halyk Academy КазНУ',
    sourceUrl: 'https://farabi.university/news/91242?lang=en',
    sourceLabel: 'КазНУ имени аль-Фараби',
    objectPosition: '40% 45%',
  },
  {
    id: 'academy-students',
    src: '/images/halyk/academy-students.webp',
    alt: 'Студенты в компьютерной лаборатории Halyk Academy в Satbayev University',
    sourceUrl: 'https://official.satbayev.university/en/information-telecommunication-technologies/csam/laboratoriya-halyk-academy-satbayev-university',
    sourceLabel: 'Satbayev University',
    objectPosition: '50% 45%',
  },
  {
    id: 'academy-lab',
    src: '/images/halyk/academy-lab.webp',
    alt: 'Компьютерные рабочие места в лаборатории Halyk Academy КазНУ',
    sourceUrl: 'https://farabi.university/news/91242?lang=en',
    sourceLabel: 'КазНУ имени аль-Фараби',
    objectPosition: '60% 48%',
  },
  {
    id: 'academy-talk',
    src: '/images/halyk/academy-talk.webp',
    alt: 'Выступление на открытии Halyk Academy в Satbayev University',
    sourceUrl: 'https://satbayev.university/en/news/the-best-professional-environment-a-new-halyk-academy-laboratory-has-been-opened-at-satbayev-university',
    sourceLabel: 'Satbayev University',
    objectPosition: '50% 30%',
  },
  {
    id: 'academy-team',
    src: '/images/halyk/academy-team.webp',
    alt: 'Участники открытия Halyk Academy в Satbayev University',
    sourceUrl: 'https://satbayev.university/en/news/the-best-professional-environment-a-new-halyk-academy-laboratory-has-been-opened-at-satbayev-university',
    sourceLabel: 'Satbayev University',
    objectPosition: '50% 30%',
  },
];

const EVENT_MEDIA_POOLS: Record<string, readonly number[]> = {
  workshop: [2, 1, 3],
  course: [3, 2, 1],
  compliance: [0, 3],
  mentoring: [4, 1],
  onboarding: [0, 5],
  certification: [3, 2],
  meetup: [1, 5],
};

/** Stable covers across catalog, roadmap and event dialog. */
export function getEventMedia(event: { event_id: string; type: string }): HalykMedia {
  const pool = EVENT_MEDIA_POOLS[event.type] ?? [0, 1, 2, 3, 4, 5];
  const ordinal = Number(event.event_id.match(/\d+$/)?.[0]);
  const seed = Number.isFinite(ordinal)
    ? ordinal
    : Array.from(event.event_id).reduce((value, char) => value + char.charCodeAt(0), 0);
  return HALYK_MEDIA[pool[seed % pool.length]];
}
