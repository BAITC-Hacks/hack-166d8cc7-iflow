'use client';

import { useState } from 'react';
import { ArrowUpRight } from 'lucide-react';
import type { Event as CatalogEvent } from '@/lib/types';
import { categories } from '@/lib/career-data';
import { getEventMedia } from '@/lib/halyk-media';

type CoverEvent = Pick<CatalogEvent, 'event_id' | 'type'>;

export function EventCover({ event, expanded = false }: { event: CoverEvent; expanded?: boolean }) {
  const media = getEventMedia(event);
  const [failedSrc, setFailedSrc] = useState<string | null>(null);
  return <div className={`event-cover cover-${event.type}${expanded ? ' is-expanded' : ''}`}>
    {failedSrc !== media.src && <img
      src={media.src}
      alt={expanded ? media.alt : ''}
      width={960}
      height={640}
      loading={expanded ? 'eager' : 'lazy'}
      decoding="async"
      style={{ objectPosition: media.objectPosition ?? 'center' }}
      onError={() => setFailedSrc(media.src)}
    />}
    <span className="event-cover-tint" aria-hidden="true"/>
    <span className="event-cover-brand" aria-hidden="true"><span>Halyk</span><small>PEOPLE & GROWTH</small></span>
    <span className="event-cover-category">{categories[event.type] ?? 'Событие'}</span>
    {!expanded && <span className="event-cover-arrow" aria-hidden="true"><ArrowUpRight size={18}/></span>}
    <span className="event-cover-line" aria-hidden="true"/>
  </div>;
}

export function EventPhotoCredit({ event }: { event: CoverEvent }) {
  const media = getEventMedia(event);
  return <div className="event-photo-credit">Фото для иллюстрации · <a href={media.sourceUrl} target="_blank" rel="noopener noreferrer">{media.sourceLabel}<ArrowUpRight size={11}/></a></div>;
}
