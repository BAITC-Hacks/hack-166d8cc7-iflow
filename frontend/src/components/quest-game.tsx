'use client';

import { useEffect, useRef, useState, type CSSProperties } from 'react';
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, ArrowUpRight, BookOpen, Check, CheckCheck, CircleHelp, Clock3, Coins, Compass, Flag, GraduationCap, LocateFixed, LockKeyhole, Maximize2, Minimize2, Minus, MousePointer2, Pause, Play, Plus, Route, Sparkles, Trophy, Users, X } from 'lucide-react';
import type { Event as CatalogEvent, MarketState, RecommendationContext } from '@/lib/types';
import { categories, formats, hours, initials, reasonNames, skillName } from '@/lib/career-data';
import { getEventMedia, HALYK_MEDIA } from '@/lib/halyk-media';
import { useQuestCamera, type Point } from '@/lib/use-quest-camera';

const WORLD = { width: 2400, height: 2000 };
const ROUTE_POINTS = [{ x: 1160, y: 1360 }, { x: 1380, y: 1020 }, { x: 1090, y: 690 }];
const CAMPUS_POINTS = [{ x: 490, y: 420 }, { x: 750, y: 620 }, { x: 420, y: 780 }, { x: 680, y: 1000 }, { x: 370, y: 1150 }, { x: 620, y: 1370 }];
const PEOPLE_POINTS = [{ x: 1720, y: 490 }, { x: 1960, y: 710 }, { x: 1640, y: 870 }, { x: 1920, y: 1070 }, { x: 1630, y: 1260 }, { x: 1930, y: 1450 }];
const HORIZON_POINTS = [{ x: 1130, y: 300 }, { x: 1450, y: 350 }, { x: 1030, y: 1710 }, { x: 1390, y: 1710 }];
const STARS = Array.from({ length: 36 }, (_, i) => ({ x: (i * 37 + 9) % 100, y: (i * 23 + 17) % 100, delay: `${i % 7 * -.8}s` }));
type Sector = 'route' | 'campus' | 'people' | 'horizon';
export interface QuestNode { event: CatalogEvent; point: Point; sector: Sector; }

/** Visual branches are areas to explore, not invented prerequisites. */
export function createQuestNodes(context: RecommendationContext, planned: CatalogEvent[]): QuestNode[] {
  const taken = new Set<string>();
  const nodes: QuestNode[] = [];
  const eligible = new Set(context.candidates.map(item => item.event_id));
  const done = new Set(context.history.filter(item => item.participation.status === 'completed').map(item => item.event.event_id));
  const catalog = [...context.event_catalog].sort((a, b) => Number(eligible.has(b.event_id)) - Number(eligible.has(a.event_id)) || Number(done.has(b.event_id)) - Number(done.has(a.event_id)) || a.event_id.localeCompare(b.event_id));
  const add = (events: CatalogEvent[], points: Point[], sector: Sector) => {
    let i = 0;
    for (const event of events) {
      if (i >= points.length) break;
      if (taken.has(event.event_id)) continue;
      taken.add(event.event_id);
      nodes.push({ event, point: points[i++], sector });
    }
  };
  add(planned, ROUTE_POINTS, 'route');
  add(catalog.filter(event => ['course', 'compliance', 'onboarding'].includes(event.type)), CAMPUS_POINTS, 'campus');
  add(catalog.filter(event => ['workshop', 'mentoring', 'meetup'].includes(event.type)), PEOPLE_POINTS, 'people');
  add(catalog, HORIZON_POINTS, 'horizon');
  return nodes;
}

function pathThrough(points: Point[]) {
  return points.reduce((path, point, i) => {
    if (!i) return `M ${point.x} ${point.y}`;
    const previous = points[i - 1];
    return `${path} C ${previous.x} ${(previous.y + point.y) / 2}, ${point.x} ${(previous.y + point.y) / 2}, ${point.x} ${point.y}`;
  }, '');
}

interface Props {
  context: RecommendationContext;
  nodes: QuestNode[];
  selected?: CatalogEvent;
  market?: MarketState;
  entered: boolean;
  motionStopped: boolean;
  motionLocked: boolean;
  onEnteredChange: (entered: boolean) => void;
  onToggleMotion: () => void;
  onChoose: (id: string) => void;
  onOpen: (event: CatalogEvent) => void;
  onCatalog: () => void;
  onMarket: () => void;
}

export function QuestGame({ context, nodes, selected, market, entered, motionStopped, motionLocked, onEnteredChange, onToggleMotion, onChoose, onOpen, onCatalog, onMarket }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [help, setHelp] = useState(false);
  const [sector, setSector] = useState<Sector>('route');
  const shellRef = useRef<HTMLElement>(null);
  const continueRef = useRef<HTMLButtonElement>(null);
  const helpRef = useRef<HTMLButtonElement>(null);
  const initial = nodes[0]?.point ?? { x: 1200, y: 1000 };
  const { viewportRef, viewportProps, camera, viewport, dragging, pan, zoomBy, focusAt, reset } = useQuestCamera({ worldWidth: WORLD.width, worldHeight: WORLD.height, initialFocus: { x: initial.x, y: initial.y - 85 }, enabled: entered });
  const completed = new Set(context.history.filter(item => item.participation.status === 'completed').map(item => item.event.event_id));
  const available = new Set(context.candidates.map(item => item.event_id));
  const selectedNode = nodes.find(node => node.event.event_id === selected?.event_id);
  const photo = selected ? getEventMedia(selected) : undefined;
  const isDone = !!selected && completed.has(selected.event_id) && !available.has(selected.event_id);
  const isAvailable = !!selected && available.has(selected.event_id);
  const exclusions = context.excluded_events.find(item => item.event_id === selected?.event_id)?.reasons ?? [];
  const sectors = [
    { id: 'route' as const, name: 'ИИ-маршрут', icon: Route, point: initial },
    { id: 'campus' as const, name: 'Кампус знаний', icon: GraduationCap, point: { x: 580, y: 790 } },
    { id: 'people' as const, name: 'Люди и идеи', icon: Users, point: { x: 1760, y: 900 } },
    { id: 'horizon' as const, name: 'Горизонты', icon: Compass, point: { x: 1260, y: 400 } },
  ];
  useEffect(() => {
    if (!entered) return;
    // Entering the world moves keyboard control into the map without scrolling the page.
    viewportRef.current?.focus({ preventScroll: true });
  }, [entered, viewportRef]);
  useEffect(() => {
    if (!expanded) return;
    const previousFocus = document.activeElement as HTMLElement | null;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    viewportRef.current?.focus({ preventScroll: true });
    return () => { document.body.style.overflow = previous; if (previousFocus?.isConnected) previousFocus.focus({ preventScroll: true }); };
  }, [expanded, viewportRef]);
  const choose = (node: QuestNode) => { onChoose(node.event.event_id); setSector(node.sector); };
  const leave = () => { setExpanded(false); setHelp(false); onEnteredChange(false); requestAnimationFrame(() => continueRef.current?.focus({ preventScroll: true })); };
  const open = () => { if (selected) { setExpanded(false); onOpen(selected); } };
  const goToSector = (value: typeof sectors[number]) => { setSector(value.id); focusAt(value.point); };
  const viewX = Math.max(0, -camera.x / camera.zoom);
  const viewY = Math.max(0, -camera.y / camera.zoom);
  const viewWidth = Math.min(WORLD.width - viewX, viewport.width / camera.zoom);
  const viewHeight = Math.min(WORLD.height - viewY, viewport.height / camera.zoom);

  return <section ref={shellRef} className={`gq-shell ${entered ? 'is-playing' : ''} ${expanded ? 'is-expanded' : ''}`} role={expanded ? 'dialog' : undefined} aria-modal={expanded || undefined} aria-label="Halyk Career Quest — пространство развития" onKeyDown={event => {
    if (event.key === 'Escape') {
      if (help) { setHelp(false); helpRef.current?.focus(); }
      else if (expanded) setExpanded(false);
    }
    if (expanded && event.key === 'Tab') {
      const focusable = shellRef.current?.querySelectorAll<HTMLElement>('button:not(:disabled), [tabindex="0"]');
      if (!focusable?.length) return;
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  }}>
    <div className="gq-atmosphere" aria-hidden="true"><div className="gq-nebula a"/><div className="gq-nebula b"/>{STARS.map((star, i) => <i key={i} className="gq-star" style={{ left: `${star.x}%`, top: `${star.y}%`, '--delay': star.delay } as CSSProperties}/>)}</div>
    <header className="gq-header">
      <div className="gq-player"><span className="gq-avatar">{initials(context.employee.full_name)}</span><div><b>{context.employee.full_name}</b><small>{context.employee.grade} · HALYK CAREER QUEST</small></div></div>
      <div className="gq-header-stats"><span title="Завершённые события в истории"><CheckCheck size={16}/>{completed.size}<small>пройдено</small></span>{market?.balance != null && <button type="button" onClick={() => { setExpanded(false); onMarket(); }} title="Открыть Halyk Market"><Coins size={17}/>{market.balance}<small>монет</small></button>}<button type="button" className="gq-icon-button" disabled={motionLocked} aria-pressed={motionStopped} title={motionLocked ? 'Анимация отключена в настройках устройства' : motionStopped ? 'Включить анимацию' : 'Приостановить анимацию'} aria-label={motionLocked ? 'Анимация отключена в настройках устройства' : motionStopped ? 'Включить анимацию' : 'Приостановить анимацию'} onClick={onToggleMotion}>{motionStopped ? <Play size={16}/> : <Pause size={16}/>}</button></div>
    </header>

    {!entered ? <div className="gq-cover">
      <div className="gq-cover-mosaic" aria-hidden="true">{HALYK_MEDIA.map((media, i) => <div className="gq-cover-hex" key={media.id} style={{ '--i': i } as CSSProperties}><img src={media.src} alt="" draggable={false} style={{ objectPosition: media.objectPosition }}/></div>)}</div>
      <div className="gq-cover-content"><span className="gq-eyebrow"><Sparkles size={14}/>ТВОЯ ВСЕЛЕННАЯ ВОЗМОЖНОСТЕЙ</span><h1>Большой путь.<br/><span>Твой следующий ход.</span></h1><p>Исследуй мир Halyk. Открывай новые навыки,<br/>знакомься с командой и забирай награды за развитие.</p><button ref={continueRef} type="button" className="gq-continue" onClick={() => onEnteredChange(true)}>Продолжить<ArrowRight size={21}/></button><span className="gq-cover-hint"><MousePointer2 size={14}/>Свободная карта · твой темп · реальные возможности</span></div>
      <div className="gq-cover-footer"><span><Route size={15}/>{nodes.length} заданий на карте</span><span><Coins size={15}/>Награды в Halyk Market</span><span><Users size={15}/>Развивайся вместе с командой</span></div>
    </div> : <>
      <nav className="gq-sector-nav" aria-label="Зоны игрового мира">{sectors.map(item => <button type="button" key={item.id} className={sector === item.id ? 'is-active' : ''} aria-pressed={sector === item.id} onClick={() => goToSector(item)}><item.icon size={15}/>{item.name}</button>)}<button type="button" onClick={onCatalog}>Все события<ArrowUpRight size={14}/></button></nav>
      <div className="gq-game">
        <div {...viewportProps} ref={viewportRef} tabIndex={0} role="region" aria-roledescription="перемещаемая карта" aria-label="Карта заданий. Стрелки или WASD — движение, плюс и минус — масштаб. Tab — выбор заданий." aria-describedby="quest-map-controls" className={`gq-viewport ${dragging ? 'is-dragging' : ''}`}>
          <div className="gq-world" style={{ width: WORLD.width, height: WORLD.height, transform: `translate(${camera.x}px, ${camera.y}px) scale(${camera.zoom})` }}>
            <svg className="gq-world-paths" width={WORLD.width} height={WORLD.height} aria-hidden="true">
              {sectors.map(item => <path key={item.id} className={item.id === 'route' ? 'gq-path-main' : 'gq-path-side'} d={pathThrough(nodes.filter(node => node.sector === item.id).map(node => node.point))} fill="none"/>)}
              <path className="gq-path-side" d="M 680 1000 Q 900 850 1090 690 M 1380 1020 Q 1510 1140 1630 1260 M 1090 690 Q 1180 530 1130 300 M 1160 1360 Q 1240 1600 1390 1710" fill="none"/>
            </svg>
            <div className="gq-zone" style={{ left: 900, top: 1080 }}><span><Route size={23}/></span><small>01 / ИИ-МАРШРУТ</small><h2>Начни с себя</h2><p>Персональные рекомендации</p></div>
            <div className="gq-zone" style={{ left: 490, top: 170 }}><span><GraduationCap size={23}/></span><small>02 / ЗНАНИЯ</small><h2>Кампус Halyk</h2><p>Осваивай. Пробуй. Расти.</p></div>
            <div className="gq-zone" style={{ left: 1800, top: 220 }}><span><Users size={23}/></span><small>03 / КОМЬЮНИТИ</small><h2>Люди и идеи</h2><p>Сильнее вместе</p></div>
            <div className="gq-zone" style={{ left: 1190, top: 1820 }}><span><Trophy size={23}/></span><small>04 / НОВЫЕ ГОРИЗОНТЫ</small><h2>Дальше — больше</h2></div>
            {[{ photo: HALYK_MEDIA[0], x: 875, y: 1540 }, { photo: HALYK_MEDIA[2], x: 270, y: 540 }, { photo: HALYK_MEDIA[5], x: 2150, y: 1110 }].map(item => <div className="gq-world-photo" key={item.photo.id} style={{ left: item.x, top: item.y }} aria-hidden="true"><img src={item.photo.src} alt="" draggable={false} style={{ objectPosition: item.photo.objectPosition }}/></div>)}
            {nodes.map((node, i) => {
              const event = node.event;
              const ready = available.has(event.event_id);
              const done = !ready && completed.has(event.event_id);
              const Icon = done ? Check : !ready ? LockKeyhole : ['mentoring', 'meetup', 'workshop'].includes(event.type) ? Users : event.type === 'certification' ? Trophy : BookOpen;
              return <button key={event.event_id} type="button" className={`gq-quest ${done ? 'is-complete' : ready ? 'is-available' : 'is-locked'} ${selected?.event_id === event.event_id ? 'is-selected' : ''}`} style={{ left: node.point.x, top: node.point.y }} onClick={() => { choose(node); setExpanded(false); onOpen(node.event); }} onFocus={event => { if (event.currentTarget.matches(':focus-visible')) { choose(node); focusAt(node.point); } }} aria-pressed={selected?.event_id === event.event_id} aria-label={`${event.title}. ${done ? 'Пройдено' : ready ? 'Подходит профилю' : 'Посмотреть требования'}`}>
                <span className="gq-quest-aura"/><span className="gq-quest-orbit"/><span className="gq-quest-hex"><Icon size={29}/><small>{String(i + 1).padStart(2, '0')}</small></span>
                {ready && !event.mandatory && market && <span className="gq-quest-coins"><Coins size={12}/>+{market.coins_per_completion}</span>}
                <span className="gq-quest-label"><small>{done ? 'ПРОЙДЕНО' : ready ? node.sector === 'route' ? 'ВЫБОР ИИ' : 'ДОСТУПНО ТЕБЕ' : 'ТРЕБОВАНИЯ'}</small><b>{event.title}</b><em>{categories[event.type]} · {hours(event.duration_hours)}</em></span>
              </button>;
            })}
          </div>
        </div>
        <div className="gq-world-caption"><small>HALYK / МИР РАЗВИТИЯ</small><b>Исследуй в своём порядке</b></div>
        <div className="gq-world-actions"><button type="button" className="gq-icon-button" onClick={leave} aria-label="Вернуться на стартовый экран" title="На стартовый экран"><ArrowLeft size={17}/></button><button ref={helpRef} type="button" className="gq-icon-button" aria-label="Как управлять картой" aria-expanded={help} onClick={() => setHelp(value => !value)}><CircleHelp size={17}/></button><button type="button" className="gq-icon-button" aria-label={expanded ? 'Свернуть карту' : 'Развернуть карту'} title={expanded ? 'Свернуть карту' : 'Развернуть карту'} aria-pressed={expanded} onClick={() => setExpanded(value => !value)}>{expanded ? <Minimize2 size={17}/> : <Maximize2 size={17}/>}</button></div>
        <div className="gq-navigation"><div className="gq-zoom"><button type="button" aria-label="Уменьшить масштаб" disabled={camera.zoom <= .45} onClick={() => zoomBy(1 / 1.2)}><Minus size={17}/></button><button type="button" aria-label="Сбросить масштаб и положение" onClick={reset}>{Math.round(camera.zoom * 100)}%</button><button type="button" aria-label="Увеличить масштаб" disabled={camera.zoom >= 1.5} onClick={() => zoomBy(1.2)}><Plus size={17}/></button></div><div className="gq-dpad"><button type="button" aria-label="Переместить камеру вверх" onClick={() => pan(0, 150)}><ArrowUp size={17}/></button><button type="button" aria-label="Переместить камеру влево" onClick={() => pan(150, 0)}><ArrowLeft size={17}/></button><button type="button" aria-label="Переместить камеру вниз" onClick={() => pan(0, -150)}><ArrowDown size={17}/></button><button type="button" aria-label="Переместить камеру вправо" onClick={() => pan(-150, 0)}><ArrowRight size={17}/></button></div><button type="button" className="gq-locate" onClick={() => focusAt(selectedNode?.point ?? initial)}><LocateFixed size={15}/>К заданию</button></div>
        <div className="gq-minimap"><label>НАВИГАТОР</label><svg viewBox={`0 0 ${WORLD.width} ${WORLD.height}`} preserveAspectRatio="none" role="img" aria-label="Обзор карты и текущее положение камеры" onClick={event => { const rect = event.currentTarget.getBoundingClientRect(); focusAt({ x: (event.clientX - rect.left) / rect.width * WORLD.width, y: (event.clientY - rect.top) / rect.height * WORLD.height }); }}>
          {nodes.map(node => <circle key={node.event.event_id} cx={node.point.x} cy={node.point.y} r={selected?.event_id === node.event.event_id ? 38 : 23} className={selected?.event_id === node.event.event_id ? 'is-selected' : available.has(node.event.event_id) ? 'is-available' : completed.has(node.event.event_id) ? 'is-complete' : ''}/>)}<rect className="gq-minimap-viewport" x={viewX} y={viewY} width={viewWidth} height={viewHeight} rx="55"/>
        </svg></div>
        <div className="gq-control-hint" id="quest-map-controls"><MousePointer2 size={13}/>Перетаскивай карту · двигайся стрелками</div>
        {help && <aside className="gq-help"><div className="gq-help-card"><button type="button" className="gq-icon-button" aria-label="Закрыть подсказку" onClick={() => { setHelp(false); helpRef.current?.focus(); }}><X size={17}/></button><h3>Это твоя карта</h3><p>Здесь можно двигаться в любом направлении.</p><ul><li>Перетаскивай мышью или пальцем.</li><li>Трекпад и стрелки двигают камеру.</li><li>Кнопки + / − и жест двумя пальцами меняют масштаб.</li><li>Нажми на узел — откроется карточка задания.</li><li>Tab переключает задания. Escape сворачивает большой экран.</li></ul></div></aside>}
      </div>
      {selected && photo ? <div className="gq-mission" aria-live="polite"><div className="gq-mission-photo"><img src={photo.src} alt="" style={{ objectPosition: photo.objectPosition }}/></div><div className="gq-mission-content"><small>{isDone ? 'ЗАДАНИЕ ПРОЙДЕНО' : isAvailable ? 'ТВОЁ СЛЕДУЮЩЕЕ ПРИКЛЮЧЕНИЕ' : 'ОТКРОЙ НОВЫЕ ВОЗМОЖНОСТИ'}</small><h2>{selected.title}</h2><p><Clock3 size={13}/>{hours(selected.duration_hours)} · {formats[selected.format]} · {categories[selected.type]}</p><div className="gq-mission-skills">{selected.develops_skills.slice(0, 3).map(item => <span key={item.skill_id}>{skillName(context, item.skill_id)}</span>)}</div>{!isAvailable && !isDone && <p className="gq-mission-status">{exclusions.length ? exclusions.map(reason => reasonNames[reason] ?? reason).join(' · ') : 'Условия участия — в карточке события'}</p>}</div><div className="gq-mission-action">{isAvailable && !selected.mandatory && market ? <span className="gq-mission-reward"><Coins size={17}/>+{market.coins_per_completion}<small>за завершение</small></span> : isDone ? <span className="gq-mission-reward"><CheckCheck size={17}/>В твоей коллекции</span> : null}<button type="button" onClick={open}>{isDone ? 'Посмотреть результат' : isAvailable ? 'Открыть задание' : 'Узнать условия'}<ArrowUpRight size={17}/></button></div></div> : <div className="gq-mission is-empty"><Flag size={23}/><p>События появятся, когда будет доступен каталог развития.</p><button type="button" onClick={onCatalog}>Открыть каталог</button></div>}
      <footer className="gq-game-footer"><span><i/>Подходит профилю</span><span><i className="is-complete"/>Пройдено</span><span><LockKeyhole size={11}/>Есть условия</span><small>Золотая тропа — рекомендации ИИ</small></footer>
    </>}
  </section>;
}
