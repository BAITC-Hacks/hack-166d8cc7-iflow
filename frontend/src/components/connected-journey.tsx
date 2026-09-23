'use client';

import { ArrowRight, ArrowUpRight, Check, Clock3, Gift, Target } from 'lucide-react';
import type { Event as CatalogEvent, RecommendationContext, MarketState, RecommendationResult } from '@/lib/types';
import { formats, hours, planSteps } from '@/lib/career-data';
import { useEffect, useState } from 'react';
import { QuestGame, createQuestNodes } from './quest-game';

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
  onCatalog: () => void;
  entered: boolean;
  onEnteredChange: (entered: boolean) => void;
}

export function ConnectedJourney({ context, recommendation, aiBusy, aiStatus, onRecommend, pace, targetIndex, market, onPace, onTarget, onOpen, onMarket, onCatalog, entered, onEnteredChange }: Props) {
  const [chosen, setChosen] = useState<string | null>(null);
  const [motionPaused, setMotionPaused] = useState(false);
  const [systemReducedMotion, setSystemReducedMotion] = useState(false);
  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setSystemReducedMotion(preference.matches);
    update();
    preference.addEventListener('change', update);
    return () => preference.removeEventListener('change', update);
  }, []);
  const motionStopped = motionPaused || systemReducedMotion;
  const targets = context.role_requirements.filter(item => item.purpose !== 'current_role');
  const target = targets[targetIndex] ?? targets[0];
  const gaps = target?.analysis.gaps ?? [];
  const plan = planSteps(context, recommendation?.recommendations ?? [], pace);
  const emptyMessage = aiBusy ? 'Подбираем самый подходящий шаг…' : aiStatus || (recommendation?.status === 'needs_clarification' ? 'Для выбора нужно уточнение. Ответьте на вопросы ниже.' : recommendation?.status === 'no_candidates' ? 'В каталоге пока нет подходящих активностей.' : 'Активных ИИ-предложений пока нет.');
  const questNodes = createQuestNodes(context, plan.map(item => item.event));
  const selected = questNodes.find(node => node.event.event_id === chosen)?.event ?? questNodes[0]?.event;
  const step = plan.find(item => item.event.event_id === selected?.event_id);
  const reward = market?.rewards.filter(item => !market.redemptions.some(row => row.reward_id === item.id)).sort((a, b) => a.price - b.price)[0];
  const coverage = target ? Math.round(target.analysis.requirement_coverage * 100) : null;
  return <div className={`journey-professional ${motionStopped ? 'is-motion-paused' : ''}`}>
    <QuestGame context={context} nodes={questNodes} selected={selected} market={market} entered={entered} motionStopped={motionStopped} motionLocked={systemReducedMotion} onEnteredChange={onEnteredChange} onToggleMotion={() => setMotionPaused(value => !value)} onChoose={setChosen} onOpen={onOpen} onCatalog={onCatalog} onMarket={onMarket}/>

    <section className="jp-preferences" id="journey-preferences" aria-label="Настройки маршрута">
      <label className="jp-target"><span><Target size={15}/>Карьерная цель</span>{targets.length ? <select aria-label="Карьерный ориентир" value={targetIndex} onChange={event => { setChosen(null); onTarget(Number(event.target.value)); }}>{targets.map((item, index) => <option value={index} key={item.purpose}>{item.purpose === 'explicit_career_goal' ? 'Моя цель' : 'Следующий грейд'}: {item.analysis.grade} · {item.analysis.role}</option>)}</select> : <b>Цель не задана</b>}</label>
      <div className="jp-controls"><div><Clock3 size={16}/><b>Время на развитие</b><span>в неделю</span></div><div className="jp-pace">{[1, 3, 5].map(value => <button type="button" key={value} aria-pressed={pace === value} onClick={() => { setChosen(null); onPace(value); }}>{value} {value === 1 ? 'час' : value === 3 ? 'часа' : 'часов'}{pace === value && <Check size={14}/>}</button>)}</div></div>
    </section>

    <div className="jp-layout">
      <aside className="jp-sidebar">
        <section className="jp-itinerary">
          <div className="jp-section-heading"><h2>Лучшее для тебя сейчас</h2><span>{plan.length}</span></div>
          <p className="jp-subtitle">{pace} ч в неделю · ИИ-подборка</p>
          <div className="jp-step-list" key={`${pace}-${targetIndex}-${context.revision}`} aria-live="polite">{plan.map((item, index) => <button type="button" key={item.event.event_id} aria-pressed={item.event.event_id === selected?.event_id} onClick={() => setChosen(item.event.event_id)}><span className="jp-step-number">{String(index + 1).padStart(2, '0')}</span><span><small>{index === 0 ? 'ОСНОВНОЙ ШАГ' : 'ДОПОЛНИТЕЛЬНО'} · около {item.end} нед.</small><b>{item.event.title}</b><em>{hours(item.event.duration_hours)} · {formats[item.event.format]}</em></span><ArrowUpRight size={15}/></button>)}</div>
          {!plan.length && <div className="jp-empty"><h3>Нет подходящих шагов</h3><p>{emptyMessage}</p></div>}
          <p className="jp-note">Первый шаг — основной. Темп меняет оценку длительности, а не подбор. Даты встреч — в карточках событий.</p><button type="button" className="text-button" disabled={aiBusy} onClick={onRecommend}>{aiBusy ? 'Подбираем…' : 'Проверить рекомендации'}</button>
        </section>

        {selected && <section className="jp-detail" id="journey-detail">
          <span className="jp-kicker">ВЫБРАННОЕ СОБЫТИЕ</span><h2>{selected.title}</h2>
          <div className="jp-detail-meta"><span><Clock3 size={13}/>{hours(selected.duration_hours)}</span><span>{formats[selected.format]}</span></div>
          <h3>{step ? 'Что даст этот шаг' : 'О событии'}</h3>{step ? <ul>{step.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul> : <p>{selected.description}</p>}
          <button type="button" className="button primary full-width" onClick={() => onOpen(selected)}>Подробнее<ArrowRight size={16}/></button>
        </section>}
      </aside>
    </div>

    <div className="jp-bottom">
      <section className="jp-skills">
        <div className="jp-section-heading"><div><h2>Навыки для следующего шага</h2><p className="jp-subtitle">{target ? `${gaps.filter(gap => gap.gap > 0).length} навыков требуют развития` : 'Целевые требования пока не заданы'}</p></div>{coverage != null && <span className="jp-coverage">{coverage}<small>%</small></span>}</div>
        <div className="jp-skill-list">{gaps.map(gap => <div key={gap.skill_id}><span>{gap.name}<b>{gap.current_level}<em> / {gap.required_level}</em></b></span><div role="progressbar" aria-label={gap.name} aria-valuemin={0} aria-valuemax={gap.required_level || 1} aria-valuenow={Math.min(gap.current_level, gap.required_level || 1)}><i className={gap.is_critical ? 'is-critical' : ''} style={{ width: `${gap.required_level ? Math.min(100, gap.current_level / gap.required_level * 100) : 100}%` }}/></div></div>)}</div>
        <p className="jp-note">Покрытие требований к навыкам. Решение о повышении принимается отдельно.</p>
      </section>
      <button type="button" className="jp-reward" onClick={onMarket}><div className="jp-reward-top"><Gift size={19}/><span>HALYK MARKET</span><ArrowUpRight size={17}/></div><h2>{reward?.title ?? 'Награды за развитие'}</h2><p>{market?.balance != null && reward ? market.balance >= reward.price ? 'Доступно за ваши монеты' : `Ещё ${reward.price - market.balance} монет до награды` : 'Выберите награду в каталоге'}</p><span className="jp-reward-meter"><i style={{ width: `${reward && market?.balance != null ? Math.min(100, market.balance / reward.price * 100) : 0}%` }}/></span><span className="jp-reward-bottom"><span>Ваш баланс</span><b>{market?.balance != null ? `${market.balance} монет` : 'Открыть маркет'}</b></span></button>
    </div>
  </div>;
}
