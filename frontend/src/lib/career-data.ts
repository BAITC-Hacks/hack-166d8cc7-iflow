import type { Event as CatalogEvent, RecommendationContext, RecommendationItem } from './types';

export const formats: Record<string, string> = { online: 'Онлайн', offline: 'Очно', self_paced: 'В своём темпе' };
export const categories: Record<string, string> = { course: 'Курс', workshop: 'Воркшоп', mentoring: 'Менторство', certification: 'Сертификация', meetup: 'Встреча', compliance: 'Обязательное', onboarding: 'Онбординг' };
export const statusNames: Record<string, string> = { completed: 'Завершено', in_progress: 'В процессе', overdue: 'Просрочено', no_show: 'Пропущено', declined: 'Отказ', dropped: 'Прервано' };
export const reasonNames: Record<string, string> = { mandatory: 'Обязательная активность: доступна через назначение', audience_role: 'Для другой роли', audience_grade: 'Для другого грейда', prerequisites: 'Сначала нужно развить предварительные навыки', unavailable: 'Нет будущих сессий', already_completed: 'Уже пройдено', no_target_gain: 'Не закрывает текущие дефициты навыков' };
export const eventArt = (event: CatalogEvent) => event.type === 'mentoring' || event.type === 'meetup' ? 'people' as const : event.type === 'workshop' ? 'blocks' as const : event.type === 'certification' ? 'code' as const : 'book' as const;
export const eventColor = (event: CatalogEvent) => event.type === 'mentoring' ? 'peach' : event.type === 'workshop' ? 'mint' : event.type === 'certification' ? 'lavender' : 'yellow';
export const hours = (value: number) => `${value.toLocaleString('ru-RU')} ч`;
export const displayDate = (value: string) => new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T12:00:00Z`));
export const initials = (name: string) => name.trim().split(/\s+/).slice(0, 2).map(part => part[0]).join('');
export const skillName = (context: RecommendationContext, id: string) => context.skill_catalog.find(skill => skill.skill_id === id)?.name ?? id;
export const actualGain = (context: RecommendationContext, event: CatalogEvent, id: string) => {
  const change = event.develops_skills.find(skill => skill.skill_id === id);
  return change ? Math.max(0, Math.min(change.max_level, (context.current_skills[id] ?? 0) + change.gain) - (context.current_skills[id] ?? 0)) : 0;
};

export function planSteps(context: RecommendationContext, recommendations: RecommendationItem[], weeklyHours: number) {
  // Presentation only: keep AI order and cardinality; never add catalog fillers.
  return recommendations.slice(0, 3).flatMap(item => {
    const event = context.event_catalog.find(event => event.event_id === item.event_id);
    if (!event || !context.candidates.some(candidate => candidate.event_id === item.event_id)) return [];
    return [{ event, start: 1, end: Math.max(1, Math.ceil(event.duration_hours / Math.max(1, weeklyHours))),
      reasons: [item.explanation, ...(item.additional_value ? [item.additional_value] : [])] }];
  });
}

export interface CompletionOption { key: string; source_record_id: string | null; session_date: string | null; label: string }
export function completionOptions(context: RecommendationContext, event: CatalogEvent): CompletionOption[] {
  const history = context.history.filter(item => item.event.event_id === event.event_id).map(item => item.participation);
  const excluded = context.excluded_events.find(item => item.event_id === event.event_id)?.reasons ?? [];
  if (excluded.includes('already_completed') && !(event.mandatory && event.type === 'compliance')) return [];
  const assignments: CompletionOption[] = history.filter(row => ['in_progress', 'overdue'].includes(row.status) && row.source_record_id && row.date <= context.as_of_date)
    .map(row => ({ key: row.source_record_id!, source_record_id: row.source_record_id, session_date: null, label: `Назначение от ${displayDate(row.date)} · ${statusNames[row.status]}` }));
  if (assignments.length) return assignments;
  if (event.mandatory || excluded.some(reason => ['audience_role', 'audience_grade', 'prerequisites', 'already_completed'].includes(reason))) return [];
  if (event.format === 'self_paced') return history.some(row => row.date === context.as_of_date) ? [] : [{ key: context.as_of_date, source_record_id: null, session_date: null, label: `Самостоятельно · ${displayDate(context.as_of_date)}` }];
  return event.upcoming_sessions.filter(date => date <= context.as_of_date && !history.some(row => row.date === date))
    .map(date => ({ key: date, source_record_id: null, session_date: date, label: `Сессия ${displayDate(date)}` }));
}
