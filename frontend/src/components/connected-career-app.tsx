'use client';

import { useEffect, useRef, useState, type ReactNode } from 'react';
import { ArrowRight, ArrowUpRight, Bell, BookOpen, CalendarDays, Check, CheckCheck, ChevronRight, CircleHelp, Clock3, Flag, Gift, LayoutDashboard, LogOut, Map as MapIcon, Menu, RefreshCw, Search, ShieldCheck, ShoppingBag, Users, X } from 'lucide-react';
import { ApiError, completeActivity, getMarket, getRecommendationContext, getSession, listEmployees, redeemReward, requestRecommendations } from '@/lib/api';
import type { Event as CatalogEvent, CompletionCommand, EmployeeSummary, MarketReward, MarketState, Principal, RecommendationContext, RecommendationResult } from '@/lib/types';
import { actualGain, categories, completionOptions, displayDate, formats, hours, initials, reasonNames, skillName, statusNames } from '@/lib/career-data';
import { RewardVisual } from './reward-visual';
import { EventCover, EventPhotoCredit } from './event-cover';
import { ConnectedJourney } from './connected-journey';
import ConnectedHR from './connected-hr';
import { EmployeeNotificationCenter } from './notification-center';
import { mailRequest, employeeMailPath, type EmployeeNotifications } from '@/lib/notification-api';

type Page = 'roadmap' | 'home' | 'events' | 'market' | 'hr';
interface Session { token: string; principal: Principal; employees: EmployeeSummary[] }
const labels: Record<Page, string> = { roadmap: 'Карта развития', home: 'Мой обзор', events: 'События', market: 'Halyk Market', hr: 'HR-панель' };
const navigation = [{ id: 'roadmap', icon: MapIcon }, { id: 'home', icon: LayoutDashboard }, { id: 'events', icon: CalendarDays }, { id: 'market', icon: ShoppingBag }] as const;
const message = (error: unknown) => error instanceof Error ? error.message : 'Не удалось выполнить запрос. Попробуй ещё раз.';
function Coin() { return <span className="coin" aria-label="монеты">h</span>; }
function Empty({ title, children }: { title: string; children?: ReactNode }) { return <div className="empty-state"><Flag size={30}/><h3>{title}</h3><p>{children}</p></div>; }
function ErrorBox({ error, retry }: { error: string; retry?: () => void }) { return <div className="connection-error" role="alert"><span>{error}</span>{retry && <button className="text-button" onClick={retry}>Повторить<RefreshCw size={14}/></button>}</div>; }

function Modal({ title, close, children }: { title: string; close: () => void; children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const closeRef = useRef(close); closeRef.current = close;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow; document.body.style.overflow = 'hidden'; ref.current?.focus();
    const key = (event: KeyboardEvent) => {
      if (event.key === 'Escape') closeRef.current();
      if (event.key !== 'Tab') return;
      const nodes = ref.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),a[href],summary,[tabindex="0"]');
      if (!nodes?.length) return;
      const first = nodes[0], last = nodes[nodes.length - 1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === ref.current)) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && (document.activeElement === last || document.activeElement === ref.current)) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener('keydown', key);
    return () => { document.body.style.overflow = overflow; document.removeEventListener('keydown', key); if (previous?.isConnected) previous.focus(); };
  }, []);
  return <div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) close(); }}><div ref={ref} tabIndex={-1} className="dialog wide" role="dialog" aria-modal="true" aria-label={title}><div className="dialog-heading"><h2>{title}</h2><button className="icon-button" aria-label="Закрыть" onClick={close}><X size={20}/></button></div>{children}</div></div>;
}

function Login({ onLogin }: { onLogin: (session: Session) => void }) {
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const active = useRef<AbortController | null>(null);
  const loginLock = useRef(false);
  const [loginChoice, setLoginChoice] = useState<'employee' | 'hr' | 'custom' | null>(null);
  useEffect(() => () => active.current?.abort(), []);
  async function login(value: string, choice: 'employee' | 'hr' | 'custom' = 'custom') {
    if (loginLock.current || !value.trim()) return;
    loginLock.current = true; setLoginChoice(choice);
    active.current?.abort(); const controller = new AbortController(); active.current = controller;
    setBusy(true); setError('');
    try {
      const [principal, employees] = await Promise.all([getSession(value.trim(), controller.signal), listEmployees(value.trim(), controller.signal)]);
      if (!controller.signal.aborted) onLogin({ token: value.trim(), principal, employees: employees.items });
    } catch (error) { if (!controller.signal.aborted) setError(message(error)); }
    finally { loginLock.current = false; if (!controller.signal.aborted) { setBusy(false); setLoginChoice(null); } }
  }
  const identities = [
    { token: 'demo-active', choice: 'employee' as const, name: 'Сотрудник', text: 'Личный маршрут, события и награды', icon: Flag },
    { token: 'demo-hr', choice: 'hr' as const, name: 'HR-команда', text: 'Аналитика навыков и управление данными', icon: Users },
  ];
  return <main className="login-page">
    <section className="login-story">
      <div className="login-brand"><img src="/halyk-logo.png" alt="Halyk"/><span>Career Quest</span></div>
      <div className="login-story-copy"><span className="eyebrow">ПРОФЕССИОНАЛЬНОЕ РАЗВИТИЕ</span><h1>Следующий шаг.<br/>С ясной целью.</h1><p>Навыки, обучение и карьерные возможности<br/>в одном рабочем пространстве.</p></div>
      <div className="login-path" aria-label="Профиль, маршрут, развитие">{[['01', 'Ваш профиль', 'Опыт и текущие навыки'], ['02', 'Личный маршрут', 'Обучение под карьерную цель'], ['03', 'Измеримый прогресс', 'Результат каждого шага']].map(([n, title, description]) => <div key={n}><span>{n}</span><div><b>{title}</b><small>{description}</small></div></div>)}</div>
      <span className="login-caption">HALYK / CAREER QUEST</span>
    </section>
    <section className="login-panel"><div><span className="eyebrow">ДОБРО ПОЖАЛОВАТЬ</span><h2>Вход в пространство</h2><p>Выберите роль для демонстрации или войдите с персональным токеном.</p>
      <div className="identity-options">{identities.map(item => <button key={item.token} type="button" aria-busy={busy && loginChoice === item.choice} disabled={busy} onClick={() => login(item.token, item.choice)}><span><item.icon size={22}/></span><div><b>{busy && loginChoice === item.choice ? 'Входим…' : item.name}</b><small>{item.text}</small></div><ArrowUpRight size={18}/></button>)}</div>
      {busy && <div className="login-progress" role="status"><RefreshCw size={16}/>{loginChoice === 'hr' ? 'Открываем HR-панель…' : 'Открываем профиль…'}</div>}
      <form onSubmit={event => { event.preventDefault(); void login(token); }}><label htmlFor="access-token">Персональный доступ</label><div><input id="access-token" type="password" autoComplete="off" value={token} onChange={event => setToken(event.target.value)} placeholder="Токен доступа" disabled={busy}/><button className="button primary" disabled={busy || !token.trim()}>{busy ? 'Входим…' : 'Войти'}<ArrowRight size={16}/></button></div></form>
      {error && <ErrorBox error={error}/>}<p className="login-note"><ShieldCheck size={16}/>Демонстрационная среда. Доступ определяется ролью, токен действует в пределах текущей сессии.</p>
    </div></section>
  </main>;
}

export default function ConnectedCareerApp({ initialPage = 'roadmap', requestedEmployee }: { initialPage?: Page; requestedEmployee?: string }) {
  const [session, setSession] = useState<Session | null>(null);
  return session ? <Workspace key={session.token} session={session} initialPage={initialPage} requestedEmployee={requestedEmployee} onLogout={() => setSession(null)}/> : <Login onLogin={next => { window.location.hash = requestedEmployee ? 'roadmap' : next.principal.role === 'hr' ? 'hr' : 'roadmap'; setSession(next); }}/>;
}

function Workspace({ session, initialPage, requestedEmployee, onLogout }: { session: Session; initialPage: Page; requestedEmployee?: string; onLogout: () => void }) {
  const { token, principal } = session;
  const isHR = principal.role === 'hr';
  const [page, setPage] = useState<Page>(initialPage);
  const [employeeId, setEmployeeId] = useState(principal.role === 'employee' ? principal.employee_id ?? '' : requestedEmployee ?? session.employees[0]?.employee_id ?? '');
  const [employees, setEmployees] = useState(session.employees);
  const [context, setContext] = useState<RecommendationContext | null>(null);
  const [market, setMarket] = useState<MarketState>();
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState('');
  const [marketError, setMarketError] = useState('');
  const [revision, setRevision] = useState(0);
  const [menu, setMenu] = useState(false);
  const [pace, setPace] = useState(3);
  const [targetIndex, setTargetIndex] = useState(0);
  const [journeyEntries, setJourneyEntries] = useState<Record<string, boolean>>({});
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('Все');
  const [rewardFilter, setRewardFilter] = useState('Все');
  const [affordable, setAffordable] = useState(false);
  const [selected, setSelected] = useState<CatalogEvent | null>(null);
  const [reward, setReward] = useState<MarketReward | null>(null);
  const [help, setHelp] = useState(false);
  const [optionKey, setOptionKey] = useState('');
  const [mutationError, setMutationError] = useState('');
  const [mutating, setMutating] = useState(false);
  const mutationLock = useRef(false);
  const commands = useRef(new Map<string, CompletionCommand>());
  const redemptions = useRef(new Map<string, string>());
  const [notice, setNotice] = useState('');
  const [ai, setAI] = useState<RecommendationResult | null>(null);
  const [aiStatus, setAIStatus] = useState('');
  const [aiBusy, setAIBusy] = useState(false);
  const [aiRequest, setAIRequest] = useState(0);
  const aiController = useRef<AbortController | null>(null);
  const active = useRef(true);
  const selectionVersion = useRef(0);
  const currentContext = useRef(context); currentContext.current = context;
  const currentEmployee = useRef(employeeId); currentEmployee.current = employeeId;
  const refresh = () => setRevision(value => value + 1);

  useEffect(() => { active.current = true; return () => { active.current = false; aiController.current?.abort(); }; }, []);
  useEffect(() => {
    const hash = () => { const next = window.location.hash.slice(1); setPage(Object.hasOwn(labels, next) ? next as Page : initialPage); };
    hash(); window.addEventListener('hashchange', hash); return () => window.removeEventListener('hashchange', hash);
  }, [initialPage]);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setContext(null); setLoadError(''); setAI(null); setAIStatus(''); aiController.current?.abort(); setAIBusy(false);
    if (!employeeId) { setContext(null); setLoading(false); return () => controller.abort(); }
    getRecommendationContext(employeeId, token, controller.signal).then(data => { if (!controller.signal.aborted) setContext(data); })
      .catch(error => { if (!controller.signal.aborted) { setContext(null); setLoadError(message(error)); } })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [employeeId, token, revision]);
  useEffect(() => {
    const controller = new AbortController(); setMarketError('');
    getMarket(token, controller.signal).then(data => { if (!controller.signal.aborted) setMarket(data); }).catch(error => { if (!controller.signal.aborted) { setMarket(undefined); setMarketError(message(error)); } });
    return () => controller.abort();
  }, [token, revision]);
  useEffect(() => {
    const controller = new AbortController();
    listEmployees(token, controller.signal).then(data => { if (!controller.signal.aborted) setEmployees(data.items); }).catch(() => { /* Employee list refresh can be retried by the visible reload action. */ });
    return () => controller.abort();
  }, [token, revision]);

  const navigate = (next: Page) => { setPage(next); window.location.hash = next; setMenu(false); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  const selectEmployee = (id: string) => { selectionVersion.current++; setEmployeeId(id); setContext(null); setTargetIndex(0); setSelected(null); setMutationError(''); setNotice(''); navigate('roadmap'); };
  const openEvent = (event: CatalogEvent) => { setSelected(event); setOptionKey(''); setMutationError(''); };
  const options = selected && context ? completionOptions(context, selected) : [];
  const option = options.find(item => item.key === optionKey) ?? options[0];
  const targets = context?.role_requirements.filter(item => item.purpose !== 'current_role') ?? [];
  const target = targets[targetIndex] ?? targets[0];
  const visibleContext = context?.employee_id === employeeId ? context : null;

  async function complete() {
    if (!selected || !option || !context || isHR || loading || mutationLock.current) return;
    mutationLock.current = true; setMutating(true); setMutationError('');
    const identity = employeeId, selectedVersion = selectionVersion.current;
    const event = selected;
    const key = `${employeeId}:${event.event_id}:${option.key}`;
    const command = commands.current.get(key) ?? { command_id: crypto.randomUUID(), source_record_id: option.source_record_id, session_date: option.session_date };
    commands.current.set(key, command);
    try {
      const result = await completeActivity(employeeId, event.event_id, command, token);
      commands.current.delete(key);
      if (!active.current || identity !== currentEmployee.current || selectedVersion !== selectionVersion.current) return;
      setSelected(null); refresh(); navigate('roadmap');
      setNotice(`Шаг завершён: ${event.title}. ${result.skill_changes.length ? result.skill_changes.map(change => `${skillName(context, change.skill_id)}: ${change.before} → ${change.after}`).join('; ') : 'Участие сохранено; уровни навыков не изменились.'}${!event.mandatory ? ' Награда учтена сервером в Market.' : ''}`);
    } catch (error) { if (active.current && identity === currentEmployee.current) setMutationError(`${message(error)} Повторная попытка использует тот же номер операции.`); }
    finally { mutationLock.current = false; if (active.current) setMutating(false); }
  }
  async function redeem() {
    if (!reward || isHR || mutationLock.current || !market || market.balance === null || market.balance < reward.price) return;
    mutationLock.current = true; setMutating(true); setMutationError('');
    const command_id = redemptions.current.get(reward.id) ?? crypto.randomUUID(); redemptions.current.set(reward.id, command_id);
    try {
      await redeemReward({ command_id, reward_id: reward.id }, token);
      redemptions.current.delete(reward.id);
      if (active.current) { setReward(null); refresh(); setNotice('Награда добавлена в твою коллекцию. Обмен сохранён на сервере.'); }
    } catch (error) { if (active.current) setMutationError(`${message(error)} Повтори запрос: номер операции сохранён.`); }
    finally { mutationLock.current = false; if (active.current) setMutating(false); }
  }
  const askAI = () => setAIRequest(value => value + 1);
  useEffect(() => {
    if (!context || context.employee_id !== employeeId) return;
    const original = context;
    const controller = new AbortController(); aiController.current = controller;
    setAIBusy(true); setAIStatus(''); setAI(null);
    async function loadSelection() {
      try {
        const result = await requestRecommendations(employeeId, token, controller.signal);
        const saved = await mailRequest<EmployeeNotifications>(employeeMailPath(employeeId) + '/notifications', token, undefined, controller.signal);
        if (controller.signal.aborted || currentContext.current !== original) return;
        if (result.employee_id !== original.employee_id || result.revision !== original.revision || result.as_of_date !== original.as_of_date) {
          setAIStatus('Данные изменились. Обнови профиль.'); return;
        }
        const activeEvents = new Set(saved.offers.filter(offer => ['proposed', 'viewed', 'snoozed', 'enrolled'].includes(offer.status)).map(offer => offer.event_id));
        setAI({...result, recommendations: result.recommendations.filter(item => activeEvents.has(item.event_id))});
      } catch (error) {
        if (!controller.signal.aborted && currentContext.current === original) setAIStatus(error instanceof ApiError && error.status === 501 ? 'AI-подбор пока недоступен: провайдер не подключён. Доступные мероприятия можно посмотреть в каталоге.' : message(error));
      } finally { if (!controller.signal.aborted) setAIBusy(false); }
    }
    void loadSelection();
    return () => controller.abort();
  }, [context, employeeId, token, aiRequest]);

  const events = visibleContext?.event_catalog.filter(event => `${event.title} ${event.description}`.toLowerCase().includes(search.toLowerCase()) && (filter === 'Все' || filter === 'Подходят мне' && visibleContext.candidates.some(item => item.event_id === event.event_id) || filter === 'Мои назначения' && visibleContext.history.some(item => item.event.event_id === event.event_id && ['in_progress', 'overdue'].includes(item.participation.status)) || categories[event.type] === filter)) ?? [];
  const profile = visibleContext?.employee;
  const name = isHR ? 'HR-команда' : profile?.full_name ?? 'Мой профиль';
  const identityName = isHR ? 'HR' : profile ? initials(profile.full_name) : 'CQ';
  return <div className="app-shell connected-shell">
    {menu && <button className="sidebar-shade" aria-label="Закрыть меню" onClick={() => setMenu(false)}/>}
    <aside className={`sidebar ${menu ? 'open' : ''}`}><button className="brand" onClick={() => navigate('roadmap')} aria-label="Halyk Career Quest — главная"><img src="/halyk-logo.png" alt="Halyk"/><span>Career Quest</span></button><div className="workspace-label">РАБОЧЕЕ ПРОСТРАНСТВО</div><nav aria-label="Основная навигация">{navigation.map(item => <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => navigate(item.id)} aria-current={page === item.id ? 'page' : undefined}><item.icon size={19}/><span>{labels[item.id]}</span>{item.id === 'events' && context && <span className="nav-count">{context.event_catalog.length}</span>}</button>)}</nav><div className="sidebar-bottom">{isHR && <button className={`nav-item ${page === 'hr' ? 'active' : ''}`} onClick={() => navigate('hr')}><Users size={19}/><span>HR-панель</span></button>}<button className="nav-item" onClick={() => setHelp(true)}><CircleHelp size={19}/><span>Как это работает</span></button><button className="nav-item" onClick={onLogout}><LogOut size={18}/><span>Сменить профиль</span></button><button className="sidebar-profile" onClick={() => navigate(isHR ? 'hr' : 'home')}><span className="avatar">{identityName}</span><span><b>{name}</b><small>{isHR ? 'Доступ HR' : profile?.role ?? 'Сотрудник'}</small></span></button></div></aside>
    <div className="main-shell"><header className="topbar"><div className="breadcrumb"><button className="icon-button mobile-menu" aria-label="Открыть меню" onClick={() => setMenu(true)}><Menu size={22}/></button><span>Моё развитие</span><ChevronRight size={14}/><strong>{labels[page]}</strong></div><div className="header-actions"><span className="demo-status"><span/>Демо</span>{market?.balance != null && <button className="balance-pill" onClick={() => navigate('market')} aria-label={`Баланс ${market.balance} монет`}><Coin/><b>{market.balance}</b></button>}<button className="icon-button" aria-label="Обновить данные" disabled={loading || mutating} onClick={refresh}><RefreshCw size={18}/></button><button className="icon-button bell" aria-label="Мои назначения" onClick={() => { setFilter('Мои назначения'); navigate('events'); }}><Bell size={20}/></button><button className="avatar header-avatar" aria-label="Открыть профиль" onClick={() => navigate(isHR ? 'hr' : 'home')}>{identityName}</button></div></header>
    <main className="main-content" id="main-content">
      {!isHR && (page === 'home' || page === 'roadmap') && <EmployeeNotificationCenter token={token} employeeId={employeeId} onChanged={refresh}/>}
      {notice && <div className="journey-celebration" role="status"><CheckCheck size={20}/><div><b>Прогресс обновлён</b><p>{notice}</p></div><button className="icon-button" aria-label="Закрыть уведомление" onClick={() => setNotice('')}><X size={17}/></button></div>}
      {isHR && page !== 'hr' && page !== 'market' && <div className="employee-switch"><Users size={18}/><label htmlFor="employee-choice">Просмотр сотрудника</label><select id="employee-choice" value={employeeId} onChange={event => selectEmployee(event.target.value)}>{employees.map(employee => <option key={employee.employee_id} value={employee.employee_id}>{employee.full_name} · {employee.role} · {employee.grade}</option>)}</select><small>Режим HR: только просмотр</small></div>}
      {page === 'hr' ? isHR ? <ConnectedHR token={token} onSelectEmployee={selectEmployee} onImported={refresh}/> : <Empty title="Здесь нужен доступ HR">Смени профиль, чтобы открыть командную аналитику.</Empty> : page === 'market' ? <>
        <div className="page-heading"><div><div className="eyebrow">ПРОГРАММА ПРИЗНАНИЯ</div><h1>Halyk Market</h1><p>Обменивайте монеты за обучение на награды.</p></div><span className="badge">ДЕМО-НАГРАДЫ</span></div>
        {marketError && <ErrorBox error={marketError} retry={refresh}/>}
        {!market && !marketError && <Empty title="Загружаем награды…"/>}
        {market && <><section className="market-hero"><div><span className="badge">CAREER QUEST REWARDS</span><h2>Ваше развитие.<br/><span>Заслуженные награды.</span></h2><p>{market.coins_per_completion} монет за завершение добровольной активности<br/>в приложении. Выберите награду в каталоге.</p></div><div className="wallet"><span>{isHR ? 'КАТАЛОГ НАГРАД' : 'ТВОЙ БАЛАНС'}</span><div><Coin/>{market.balance ?? '—'}</div><p>{isHR ? 'HR не участвует в обмене' : `Заработано ${market.earned} · потрачено ${market.spent}`}</p><button onClick={() => navigate('events')}>К событиям<ArrowUpRight size={15}/></button></div></section><div className="filter-bar"><div className="filter-tabs">{['Все', ...new Set(market.rewards.map(item => item.category)), 'Мои награды'].map(value => <button key={value} className={rewardFilter === value ? 'selected' : ''} aria-pressed={rewardFilter === value} onClick={() => setRewardFilter(value)}>{value}</button>)}</div>{!isHR && <label className="toggle-label"><input type="checkbox" checked={affordable} onChange={event => setAffordable(event.target.checked)}/><span className="switch"/>Хватает монет</label>}</div><div className="reward-grid">{market.rewards.filter(item => (rewardFilter === 'Все' || rewardFilter === item.category || rewardFilter === 'Мои награды' && market.redemptions.some(row => row.reward_id === item.id)) && (!affordable || item.price <= (market.balance ?? 0))).map(item => <button className="reward-card" key={item.id} onClick={() => { setReward(item); setMutationError(''); }}><div className="reward-art"><span className="badge">{item.category}</span><RewardVisual kind={item.art}/>{market.redemptions.some(row => row.reward_id === item.id) && <span className="owned-label"><Check size={13}/>Твоя награда</span>}</div><div className="reward-info"><h3>{item.title}</h3><p>{item.description}</p><div><strong><Coin/>{item.price}</strong><span className="reward-arrow"><ArrowUpRight size={19}/></span></div></div></button>)}</div>{!market.rewards.some(item => (rewardFilter === 'Все' || rewardFilter === item.category || rewardFilter === 'Мои награды' && market.redemptions.some(row => row.reward_id === item.id)) && (!affordable || item.price <= (market.balance ?? 0))) && <Empty title="Награды ещё впереди">Измени фильтр или заверши добровольную активность.</Empty>}<div className="market-note"><ShieldCheck size={18}/><p>Обмен сохраняется в приложении и не создаёт реальную покупку или доставку. Исторические и обязательные активности не приносят монет. Обучение бесплатно.</p></div></>}
      </> : <>
        {loadError && <ErrorBox error={loadError} retry={refresh}/>}
        {loading && <div className="data-loading" role="status"><RefreshCw size={18}/>Загружаем профиль и навыки…</div>}
        {!loading && !visibleContext && !loadError && <Empty title="Сотрудник не выбран">Выбери профиль, чтобы увидеть карту развития.</Empty>}
        {visibleContext && !loading && <>
          {page === 'roadmap' && <ConnectedJourney recommendation={ai} aiBusy={aiBusy} aiStatus={aiStatus} onRecommend={askAI} context={visibleContext} pace={pace} targetIndex={targetIndex} market={market} onPace={setPace} onTarget={setTargetIndex} onOpen={openEvent} onMarket={() => navigate('market')} onCatalog={() => navigate('events')} entered={journeyEntries[employeeId] ?? false} onEnteredChange={entered => setJourneyEntries(previous => ({ ...previous, [employeeId]: entered }))}/>}
          {page === 'home' && <><div className="page-heading"><div><div className="eyebrow">ПРОФИЛЬ · {visibleContext.employee_id}</div><h1>{visibleContext.employee.full_name}</h1><p>{visibleContext.employee.role} · {visibleContext.employee.grade} · {visibleContext.employee.department}</p></div></div><section className="connected-overview"><div className="journey-hero"><div className="hero-copy"><span className="badge">ПЕРСОНАЛЬНЫЙ МАРШРУТ</span><h2>План развития</h2><p>{target ? `Ориентир: ${target.analysis.grade} ${target.analysis.role}` : 'Исследуй доступные возможности развития'}</p><button className="button yellow-button" onClick={() => navigate('roadmap')}>На карту развития<ArrowUpRight size={18}/></button></div></div><div className="panel"><h2>Мой прогресс</h2><div className="profile-stats"><span><b>{visibleContext.history.filter(item => item.participation.status === 'completed').length}</b>завершённых участий</span><span><b>{visibleContext.candidates.length}</b>подходящих событий</span><span><b>{target ? `${Math.round(target.analysis.requirement_coverage * 100)}%` : '—'}</b>покрытие цели</span></div><p className="muted">Текущие навыки рассчитаны по последней оценке и завершениям после неё.</p></div></section><section className="panel profile-skills"><div className="section-title"><h2>Мои навыки</h2><span className="badge">ШКАЛА 0–5</span></div><div className="district-progress">{Object.entries(visibleContext.current_skills).sort(([a], [b]) => skillName(visibleContext, a).localeCompare(skillName(visibleContext, b), 'ru')).map(([id, value]) => <div key={id}><span>{skillName(visibleContext, id)}<b>{value} / 5</b></span><div><i style={{ width: `${value / 5 * 100}%`, background: '#16866a' }}/></div></div>)}</div></section><section className="panel history-panel"><h2>Моя история</h2><div className="connected-table-wrap"><table><thead><tr><th>Активность</th><th>Дата</th><th>Статус</th></tr></thead><tbody>{[...visibleContext.history].sort((a, b) => b.participation.date.localeCompare(a.participation.date)).map((row, index) => <tr key={`${row.participation.source_record_id}-${index}`}><td><button className="text-button" onClick={() => openEvent(row.event)}>{row.event.title}<ArrowUpRight size={13}/></button></td><td>{displayDate(row.participation.date)}</td><td>{statusNames[row.participation.status] ?? row.participation.status}</td></tr>)}</tbody></table></div></section></>}
          {page === 'events' && <>
            <div className="page-heading catalog-heading"><div><div className="eyebrow">HALYK / LEARNING EXPERIENCE</div><h1>События и <span>обучение</span></h1><p>{visibleContext.event_catalog.length} возможностей · {visibleContext.candidates.length} подходят профилю</p></div><div className="catalog-count"><b>{visibleContext.event_catalog.length}</b><span>ВОЗМОЖНОСТЕЙ<br/>ДЛЯ РАЗВИТИЯ</span></div></div>
            <div className="filter-bar catalog-filters"><div className="filter-tabs">{['Все', 'Подходят мне', 'Мои назначения', 'Курс', 'Воркшоп', 'Менторство', 'Встреча'].map(value => <button className={filter === value ? 'selected' : ''} aria-pressed={filter === value} key={value} onClick={() => setFilter(value)}>{value}</button>)}</div><label className="search-field"><Search size={17}/><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Найти событие" aria-label="Поиск событий"/></label></div>
            <div className="event-grid catalog">{events.map(event => <button className="event-card" key={event.event_id} onClick={() => openEvent(event)}>
              <EventCover event={event}/>
              <div className="event-content"><div className="event-eyebrow">{visibleContext.candidates.some(item => item.event_id === event.event_id) ? <><Check size={13}/>Подходит профилю</> : event.mandatory ? 'Обязательное назначение' : 'Посмотреть требования'}</div><h3>{event.title}</h3><p>{event.develops_skills.length ? event.develops_skills.map(item => skillName(visibleContext, item.skill_id)).join(' · ') : event.description}</p><div className="event-meta"><span><Clock3 size={13}/>{hours(event.duration_hours)}</span><span>{formats[event.format]}</span>{!event.mandatory && market && <strong><Coin/>+{market.coins_per_completion}</strong>}</div></div>
            </button>)}</div>
            {!events.length && <Empty title="Пока ничего не найдено">Измени запрос или фильтр.</Empty>}
          </>}
          {(page === 'roadmap' || page === 'home') && <section className="ai-panel"><div className="section-title"><div><span className="eyebrow">ПЕРСОНАЛЬНЫЙ ПОДБОР</span><h2>Рекомендации ИИ</h2><p>Рекомендации по профилю, навыкам и истории участия.</p></div><button className="button primary" disabled={aiBusy || loading} onClick={askAI}><BookOpen size={17}/>{aiBusy ? 'Готовим рекомендации…' : 'Получить рекомендации'}</button></div>{aiStatus && <p className="ai-status" role="status">{aiStatus}</p>}{ai?.status === 'no_candidates' && <Empty title="Подходящих событий пока нет">Нужны новые мероприятия для текущих требований к навыкам.</Empty>}{ai?.recommendations.map(item => { const event = visibleContext.event_catalog.find(event => event.event_id === item.event_id); return <article className="ai-recommendation" key={item.event_id}><h3>{event?.title ?? item.event_id}</h3><p>{item.explanation}</p><details><summary>Факторы выбора ({item.evidence.length})</summary><ul>{item.evidence.map((factor, index) => <li key={index}><b>{factor.kind}</b>: {Object.entries(factor.values).map(([key, value]) => `${key}: ${value ?? 'не указано'}`).join(' · ')}</li>)}</ul></details>{event && <button className="text-button" onClick={() => openEvent(event)}>Открыть событие<ArrowRight size={14}/></button>}</article>; })}{ai?.hypotheses.map((item, index) => <div className="ai-hypothesis" key={index}><b>Предположение · нужно подтвердить</b><p>{item.statement}</p></div>)}{!!ai?.clarifying_questions.length && <div className="ai-questions"><h3>Вопросы для уточнения</h3><ul>{ai.clarifying_questions.map(item => <li key={item}>{item}</li>)}</ul><small>Сохранение ответов и повторный диалог пока не поддерживаются API.</small></div>}</section>}
        </>}
      </>}
      <footer className="footer"><span>Halyk / Career Quest</span><span>{context ? `Данные на ${context.as_of_date} · ревизия ${context.revision}` : 'HackAlem AI'}</span></footer>
    </main></div>
    {selected && visibleContext && <Modal title="Информация о событии" close={() => { if (!mutating) setSelected(null); }}><EventCover event={selected} expanded/><div className="dialog-content"><EventPhotoCredit event={selected}/><h2>{selected.title}</h2><p className="event-description">{selected.description}</p><div className="dialog-meta"><span><Clock3 size={16}/>{hours(selected.duration_hours)}</span><span>{formats[selected.format]}</span><span>{selected.mandatory ? 'Обязательная активность' : 'Добровольная активность'}</span></div><div className="reason-box"><h4>Что изменится в навыках</h4><ul>{selected.develops_skills.map(change => <li key={change.skill_id}>{skillName(visibleContext, change.skill_id)}: {visibleContext.current_skills[change.skill_id] ?? 0} → {(visibleContext.current_skills[change.skill_id] ?? 0) + actualGain(visibleContext, selected, change.skill_id)} (предел события: {change.max_level})</li>)}</ul><small>Повторное завершение обычного курса не начисляет прирост повторно.</small></div>{!!Object.keys(selected.prerequisites).length && <div className="event-requirements"><h3>Предварительные навыки</h3>{Object.entries(selected.prerequisites).map(([id, value]) => <p key={id}>{skillName(visibleContext, id)} ≥ {value} · сейчас {visibleContext.current_skills[id] ?? 0}</p>)}</div>}{selected.format !== 'self_paced' && <div className="event-requirements"><h3>Сессии</h3><p>{selected.upcoming_sessions.length ? selected.upcoming_sessions.map(date => `${displayDate(date)}${date > visibleContext.as_of_date ? ' (впереди)' : ''}`).join(' · ') : 'Нет запланированных сессий'}</p></div>}{visibleContext.excluded_events.find(item => item.event_id === selected.event_id)?.reasons.map(reason => <p className="event-restriction" key={reason}>{reasonNames[reason] ?? reason}</p>)}{mutationError && <ErrorBox error={mutationError}/>}<div className="completion-controls">{isHR ? <p className="muted">HR просматривает профиль. Завершать активности может только сам сотрудник.</p> : options.length ? <><label htmlFor="completion-session">Подтвердить завершение</label><select id="completion-session" value={option?.key ?? ''} onChange={event => setOptionKey(event.target.value)} disabled={mutating}>{options.map(item => <option key={item.key} value={item.key}>{item.label}</option>)}</select><button className="button primary full-width" disabled={mutating || loading} onClick={complete}><CheckCheck size={17}/>{mutating ? 'Сохраняем…' : 'Я завершил активность'}</button><p className="dialog-footnote">Подтверждай только пройденное событие. Сервер проверит дату, назначение и повторное начисление.</p></> : <p className="muted">Сейчас завершение недоступно: событие уже пройдено, не подходит профилю или его сессия ещё не наступила. Дата приложения: {displayDate(visibleContext.as_of_date)}.</p>}</div></div></Modal>}
    {reward && market && <Modal title="Награда" close={() => { if (!mutating) setReward(null); }}><div className="reward-preview"><RewardVisual kind={reward.art}/></div><div className="dialog-content"><h2>{reward.title}</h2><p>{reward.description}</p><div className="checkout-row"><span>Стоимость</span><b><Coin/>{reward.price}</b></div><div className="checkout-row"><span>Твой баланс</span><b>{market.balance ?? '—'} монет</b></div>{mutationError && <ErrorBox error={mutationError}/>}<div className="dialog-actions">{market.redemptions.some(item => item.reward_id === reward.id) ? <div className="completed-message"><Check/><div><b>В твоей коллекции</b><span>Обмен сохранён на сервере.</span></div></div> : isHR ? <p className="muted">HR может просматривать каталог. Обмен доступен сотрудникам.</p> : <button className="button primary full-width" disabled={mutating || market.balance === null || market.balance < reward.price} onClick={redeem}>{mutating ? 'Сохраняем обмен…' : market.balance !== null && market.balance < reward.price ? `Ещё ${reward.price - market.balance} монет до награды` : `Обменять ${reward.price} монет`}<Gift size={17}/></button>}</div><p className="dialog-footnote">Демонстрационная награда. Реальная доставка и списание денег не производятся.</p></div></Modal>}
    {help && <Modal title="Как работает Career Quest" close={() => setHelp(false)}><div className="dialog-content help-content">{[['01','Выбери ориентир','Следующий грейд и карьерная цель берутся из профиля на сервере.'],['02','Найди свой темп','AI выбирает один основной шаг и до двух дополнительных при обоснованной пользе. Темп помогает оценить длительность.'],['03','Замечай свой прогресс','Заверши пройденную активность: сервер обновит навыки, историю и маршрут. Будущие сессии завершить нельзя.'],['04','Порадуй себя','За новые добровольные завершения начисляются монеты. Обмен в Market сохраняется на сервере.']].map(([number,title,description]) => <div className="help-step" key={number}><span>{number}</span><div><h3>{title}</h3><p>{description}</p></div></div>)}<p className="muted">Демонстрационная авторизация. Запись на новые мероприятия и изменение карьерной цели пока не поддерживаются API. Данные навыков и истории доступны в рамках роли.</p></div></Modal>}
  </div>;
}
