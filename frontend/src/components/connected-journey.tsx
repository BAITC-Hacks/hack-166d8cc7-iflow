'use client';
import { ArrowRight, ArrowUpRight, Check, CheckCheck, Clock3, Code2, Flag, Gift, LockKeyhole, Route, Settings2, Trophy, Users } from 'lucide-react';
import type { Event as CatalogEvent, RecommendationContext, MarketState, RecommendationResult } from '@/lib/types';
import { eventArt, eventColor, formats, hours, initials, planSteps } from '@/lib/career-data';
import { Terrain } from './atlas-terrain';
import { Art } from './artwork';
import { useState } from 'react';

interface Props {
  context: RecommendationContext;
  recommendation: RecommendationResult | null;
  aiBusy: boolean;
  aiStatus: string;
  onRecommend: () => void;
  pace: number;
  targetIndex: number;
  market?: MarketState;
  onPace: (hours: number) => void;
  onTarget: (index: number) => void;
  onOpen: (event: CatalogEvent) => void;
  onMarket: () => void;
}
const positions = [{ x: 26, y: 39 }, { x: 75, y: 36 }, { x: 25, y: 73 }, { x: 74, y: 70 }, { x: 26, y: 18 }];
export function ConnectedJourney({ context, recommendation, aiBusy, aiStatus, onRecommend, pace, targetIndex, market, onPace, onTarget, onOpen, onMarket }: Props) {
  const [chosen, setChosen] = useState<string | null>(null);
  const targets = context.role_requirements.filter(item => item.purpose !== 'current_role');
  const target = targets[targetIndex] ?? targets[0];
  const gaps = target?.analysis.gaps ?? [];
  const plan = planSteps(context, recommendation?.recommendations ?? [], pace);
  const available = context.candidates.map(candidate => context.event_catalog.find(event => event.event_id === candidate.event_id)!).filter(Boolean);
  const completed = context.history.filter(item => item.participation.status === 'completed');
  const nodes = plan.map(step => step.event);
  const emptyMessage = aiBusy ? 'Подбираем самый подходящий шаг…' : aiStatus || (recommendation?.status === 'needs_clarification' ? 'Для выбора нужно уточнение. Ответьте на вопросы ниже.' : recommendation?.status === 'no_candidates' ? 'В каталоге пока нет подходящих активностей.' : 'Активных AI-предложений пока нет.');
  const selected = nodes.find(event => event.event_id === chosen) ?? nodes[0];
  const step = plan.find(item => item.event.event_id === selected?.event_id);
  const focus = [...gaps].sort((a, b) => Number(b.is_critical) - Number(a.is_critical) || b.gap - a.gap).slice(0, 4);
  const reward = market?.rewards.filter(item => !market.redemptions.some(row => row.reward_id === item.id)).sort((a, b) => a.price - b.price)[0];
  const choose = (id: string) => { setChosen(id); if (window.matchMedia('(max-width:1100px)').matches) requestAnimationFrame(() => document.getElementById('journey-detail')?.scrollIntoView({ behavior: 'smooth', block: 'start' })); };
  return <div className="journey-page">
    <div className="page-heading journey-heading"><div><div className="eyebrow">CAREER QUEST / ТВОЯ ТЕРРИТОРИЯ РОСТА</div><h1>Большое начинается<br/>с твоего <span>следующего шага.</span></h1><p>{context.employee.full_name} · {context.employee.role} · {context.employee.grade}</p></div><div className="journey-goal"><span className="journey-goal-icon"><Flag size={22}/></span><label><small>КАРЬЕРНЫЙ ОРИЕНТИР</small>{targets.length ? <select aria-label="Карьерный ориентир" value={targetIndex} onChange={e => { setChosen(null); onTarget(Number(e.target.value)); }}>{targets.map((item, index) => <option value={index} key={item.purpose}>{item.purpose === 'explicit_career_goal' ? 'Моя цель' : 'Следующий грейд'}: {item.analysis.grade} · {item.analysis.role}</option>)}</select> : <b>Высший грейд · цель не задана</b>}<em>Из профиля и требований роли<Settings2 size={12}/></em></label></div></div>
    <section className="tempo-bar" aria-label="Темп обучения"><div><Clock3 size={21}/><span><b>Сколько времени есть на себя?</b><small>Оценка длительности выбранных AI активностей</small></span></div><div className="tempo-options">{[1, 3, 5].map(value => <button key={value} aria-pressed={pace === value} className={pace === value ? 'active' : ''} onClick={() => { setChosen(null); onPace(value); }}><b>{value} {value === 1 ? 'час' : value === 3 ? 'часа' : 'часов'}<span> / нед.</span></b><small>{value === 1 ? 'Без спешки' : value === 3 ? 'В своём ритме' : 'С погружением'}</small>{pace === value && <Check size={14}/>}</button>)}</div></section>
    <div className="journey-layout"><section className="atlas" aria-label="Карта событий сотрудника"><div className="atlas-heading"><div><span className="atlas-live"/>ТВОЙ МИР ВОЗМОЖНОСТЕЙ</div><span><CheckCheck size={14}/>{completed.length} завершённых участий</span></div><div className="atlas-world"><Terrain/>
      {focus.map((gap, index) => <div className={`district-label district-${['system','python','leadership','communication'][index]}`} style={{ left: `${[7,65,7,61][index]}%`, top: `${[8,18,59,58][index]}%` }} key={gap.skill_id}><span>{gap.name}</span><small>{gap.current_level} / {gap.required_level}{gap.is_critical ? ' · в фокусе' : ''}</small></div>)}
      <div className="atlas-destination"><span><Trophy size={20}/></span><b>{target?.analysis.grade ?? context.employee.grade}</b><small>{target ? 'Карьерный ориентир' : 'Текущий грейд'}</small></div>
      {nodes.map((event, index) => {
        const ready = available.some(item => item.event_id === event.event_id);
        const done = !ready && completed.some(item => item.event.event_id === event.event_id);
        const n = plan.findIndex(item => item.event.event_id === event.event_id);
        const Icon = [Route, Code2, Users, Flag, Trophy][index];
        return <button key={`${event.event_id}-${done}-${ready}`} className={`atlas-node ${done ? 'complete' : ready ? 'available' : 'locked'} ${n >= 0 ? 'recommended' : ''} ${selected?.event_id === event.event_id ? 'chosen' : ''}`} style={{ left: `${positions[index].x}%`, top: `${positions[index].y}%` }} onClick={() => choose(event.event_id)} aria-label={`${event.title}. ${done ? 'Завершено' : ready ? 'Доступно' : 'Пока не подходит'}`} aria-pressed={selected?.event_id === event.event_id}><span className="atlas-platform">{done ? <Check size={27}/> : ready ? <Icon size={26}/> : <LockKeyhole size={23}/>} {n >= 0 && <i>{n + 1}</i>}</span><b>{event.title}</b><small>{done ? 'Пройдено' : `${hours(event.duration_hours)} · ${formats[event.format]}`}</small></button>;
      })}
      {!nodes.length && <div className="atlas-no-nodes"><Flag/><b>Твоя следующая глава впереди</b><p>{emptyMessage}</p></div>}
      <div className="atlas-start"><span>{initials(context.employee.full_name)}</span><b>Ты здесь</b><small>{context.employee.grade} · {context.employee.role}</small></div><div className="atlas-compass" aria-hidden="true"><span>N</span><span>✥</span></div>
    </div><div className="atlas-legend"><span><i className="legend-route"/>Выбор AI</span><small>Только 1–3 обоснованных предложения · история в обзоре</small></div></section>
    <aside className="journey-sidebar"><section className="itinerary"><div className="itinerary-heading"><span className="journey-icon"><Route size={21}/></span><div><h2>Лучшее для тебя сейчас</h2><p>{pace} ч в неделю · предложений: {plan.length}</p></div></div><div className="itinerary-steps" key={`${pace}-${targetIndex}-${context.revision}`} aria-live="polite">{plan.map((item, index) => <button key={item.event.event_id} className={item.event.event_id === selected?.event_id ? 'active' : ''} onClick={() => setChosen(item.event.event_id)}><span className="itinerary-number">{index + 1}</span><span><small>{index === 0 ? 'ОСНОВНОЙ ШАГ' : 'ДОПОЛНИТЕЛЬНО'} · около {item.end} нед.</small><b>{item.event.title}</b><em>{hours(item.event.duration_hours)} · {formats[item.event.format]}</em></span><ArrowUpRight size={16}/></button>)}</div>{!plan.length && <div className="route-empty"><Trophy size={24}/><h3>Подходящих шагов пока нет</h3><p>{emptyMessage}</p></div>}<p className="itinerary-note">Первый шаг — основной. Дополнительные активности показаны только при обоснованной пользе. Темп меняет оценку длительности, а не подбор. Ориентир переключает сравнение навыков; подбор учитывает весь профиль.</p><span className="planner-label">Сохранённая AI-подборка</span><button className="text-button" disabled={aiBusy} onClick={onRecommend}>{aiBusy ? 'Подбираем…' : 'Проверить рекомендации'}</button></section>
      {selected && <section className="journey-detail" id="journey-detail"><div className={`journey-detail-visual ${eventColor(selected)}`}><Art kind={eventArt(selected)}/><span>ТОЧКА РОСТА</span></div><div className="journey-detail-copy"><h2>{selected.title}</h2><div className="journey-detail-meta"><span><Clock3 size={13}/>{hours(selected.duration_hours)}</span><span>{formats[selected.format]}</span></div><h3>{step ? 'Почему этот шаг' : 'О событии'}</h3>{step ? <ul>{step.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul> : <p>{selected.description}</p>}<button className="button primary full-width" onClick={() => onOpen(selected)}>Открыть событие<ArrowRight size={16}/></button></div></section>}
    </aside></div>
    <div className="journey-bottom"><section className="journey-progress"><div><span className="eyebrow">ТВОЙ ЛИЧНЫЙ ПРОГРЕСС</span><h2>Каждый навык открывает больше.</h2><p>{target ? `${Math.round(target.analysis.requirement_coverage * 100)}% требований к навыкам · ${gaps.filter(gap => gap.gap > 0).length} навыков в фокусе` : 'Целевые требования пока не заданы'}</p></div><div className="district-progress">{gaps.map(gap => <div key={gap.skill_id}><span>{gap.name}<b>{gap.current_level} / {gap.required_level}</b></span><div><i style={{ width: `${gap.required_level ? Math.min(100, gap.current_level / gap.required_level * 100) : 100}%`, background: gap.is_critical ? '#087e68' : '#bac878' }}/></div></div>)}</div><small>Покрытие навыков рассчитано сервером. Решение о повышении принимается отдельно.</small></section>
      <button className="journey-reward" onClick={onMarket}><span className="eyebrow">СЛЕДУЮЩАЯ ПРИЯТНОСТЬ</span><div><span className="reward-stamp"><Gift size={26}/></span><span><h3>{reward?.title ?? 'Halyk Market'}</h3><p>{market?.balance != null && reward ? market.balance >= reward.price ? 'Уже хватает монет — можно забрать' : `Ещё ${reward.price - market.balance} монет до награды` : 'Награды за добровольное развитие'}</p></span></div><span className="reward-meter"><i style={{ width: `${reward && market?.balance != null ? Math.min(100, market.balance / reward.price * 100) : 0}%` }}/></span><span className="reward-market-link">Halyk Market <span>{market?.balance != null ? `${market.balance} монет` : 'Открыть'}<ArrowUpRight size={17}/></span></span></button>
    </div>
  </div>;
}
