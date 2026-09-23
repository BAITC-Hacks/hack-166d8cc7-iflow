'use client';

import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { employeeMailPath, hrMailPath, mailRequest, type Employees, type EmployeeNotifications, type MailJournal, type MailPolicy, type Preferences, type SettingsView } from '@/lib/notification-api';

const labels: Record<string, string> = {
  proposed: 'Новое предложение', viewed: 'Предложение просмотрено', snoozed: 'Отложено', enrolled: 'Запись подтверждена',
  declined: 'Не подходит', completed: 'Курс завершён', invalidated: 'Предложение устарело', unanswered: 'Решение не принято',
  pending: 'Ожидает', sending: 'Передаётся почте', accepted: 'Принято почтовым сервисом', unknown: 'Результат отправки неизвестен',
  failed: 'Ошибка', cancelled: 'Отменено', connected: 'Подключена', auth_failed: 'Нужно переподключить почту',
  offer: 'Предложение', reminder: 'Напоминание', session: 'Перед занятием', completion: 'Завершение', test: 'Проверка почты',
  global_pause: 'Рассылка выключена', employee_pause: 'Пауза сотрудника', email_missing: 'Нет email', email_blocked: 'Адрес отклонён',
  mail_account_unavailable: 'Почта не подключена', frequency_or_time_window: 'Ожидает разрешённого времени',
  notification_type_disabled: 'Тип письма выключен', already_learning: 'Сотрудник уже учится',
};
const title = (value: string | null) => value ? labels[value] ?? value : '—';
const minutes = (value: number) => `${String(Math.floor(value / 60)).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}`;
const fromTime = (value: string) => { const [h, m] = value.split(':').map(Number); return h * 60 + m; };
// All UI scheduling uses the common company clock; never a browser timezone setting.
const when = (value: string) => new Intl.DateTimeFormat('ru-RU', {timeZone: 'Asia/Almaty', dateStyle: 'short', timeStyle: 'short'}).format(new Date(value));

function useActions() {
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const lifetime = useRef<AbortController | null>(null);
  const locked = useRef(false);
  useEffect(() => { const controller = new AbortController(); lifetime.current = controller; return () => controller.abort(); }, []);
  async function run(action: (signal: AbortSignal) => Promise<void>) {
    const controller = lifetime.current;
    if (!controller || controller.signal.aborted || locked.current) return;
    locked.current = true; setBusy(true); setNotice('');
    try { await action(controller.signal); }
    catch (error) { if (!controller.signal.aborted) setNotice(error instanceof Error ? error.message : 'Не удалось выполнить запрос'); }
    finally { if (!controller.signal.aborted) { locked.current = false; setBusy(false); } }
  }
  return {notice, setNotice, busy, run};
}

export function HRNotificationCenter({token, employees}: {token: string; employees: Employees}) {
  return <HRMail key={token} token={token} employees={employees}/>;
}

function HRMail({token, employees}: {token: string; employees: Employees}) {
  const [view, setView] = useState<SettingsView | null>(null);
  const [policy, setPolicy] = useState<MailPolicy | null>(null);
  const [journal, setJournal] = useState<MailJournal | null>(null);
  const [contactId, setContactId] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [hrPaused, setHRPaused] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [reconciliationNotes, setReconciliationNotes] = useState<Record<string, string>>({});
  const [smtp, setSMTP] = useState({sender_email: '', sender_name: 'Career Quest HR', host: '', port: 465, security: 'ssl', username: '', password: ''});
  const [preview, setPreview] = useState<{subject: string; body: string} | null>(null);
  const commands = useRef(new Map<string, string>());
  const {notice, setNotice, busy, run} = useActions();
  const chosen = contactId || employees[0]?.employee_id || '';
  const refresh = useCallback(async (signal: AbortSignal) => {
    const [settings, log] = await Promise.all([mailRequest<SettingsView>(hrMailPath + '/settings', token, undefined, signal), mailRequest<MailJournal>(hrMailPath + '/journal', token, undefined, signal)]);
    if (!signal.aborted) { setView(settings); setPolicy(settings.settings); setJournal(log); }
  }, [token]);
  useEffect(() => { const controller = new AbortController(); refresh(controller.signal).catch(error => { if (!controller.signal.aborted) setNotice(error.message); }); return () => controller.abort(); }, [refresh, setNotice]);
  useEffect(() => { const contact = journal?.contacts[chosen]; setContactEmail(contact?.preferences.email ?? ''); setHRPaused(contact?.hr_paused ?? false); }, [chosen, journal]);
  const change = <K extends keyof MailPolicy,>(key: K, value: MailPolicy[K]) => setPolicy(current => current ? {...current, [key]: value} : current);
  const submit = (event: FormEvent, action: (signal: AbortSignal) => Promise<void>) => { event.preventDefault(); void run(action); };
  return <section className="panel notification-center">
    <div className="section-title"><div><span className="eyebrow">ПИСЬМА СОТРУДНИКАМ</span><h2>Настройки уведомлений</h2></div><button className="button secondary" disabled={busy} onClick={() => run(refresh)}>Обновить</button></div>
    {notice && <p role="status" className="mail-notice">{notice}</p>}
    {view && <p className="muted">Общее время системы: {when(view.company_now)}. Почта: {view.account ? `${view.account.sender_email} · ${title(view.account.status)}` : 'не подключена'}. AI: {view.ai_ready ? 'подключён' : 'нужно подключить провайдера'}.</p>}
    {policy && <form onSubmit={event => submit(event, async signal => { await mailRequest(hrMailPath + '/settings', token, policy, signal); await refresh(signal); if (!signal.aborted) setNotice('Правила отправки сохранены.'); })}>
      <fieldset disabled={busy}><legend>Расписание и частота</legend>
        <label className="mail-check"><input type="checkbox" checked={policy.enabled} onChange={e => change('enabled', e.target.checked)}/>Рассылка включена</label>
        <div className="mail-grid"><label>Начало отправки<input type="time" required value={minutes(policy.start_minute)} onChange={e => change('start_minute', fromTime(e.target.value))}/></label><label>Окончание отправки<input type="time" required value={minutes(Math.min(policy.end_minute, 1439))} onChange={e => change('end_minute', fromTime(e.target.value))}/></label>
          {([['minimum_interval_hours', 'Минимум часов между письмами', 1, 720], ['weekly_limit', 'Максимум писем за 7 дней', 1, 14], ['reminder_after_days', 'Напомнить через дней', 1, 90], ['maximum_reminders', 'Максимум напоминаний', 0, 5], ['cooldown_days', 'Пауза после отсутствия решения, дней', 1, 180]] as const).map(([key, label, min, max]) => <label key={key}>{label}<input type="number" required min={min} max={max} value={policy[key]} onChange={e => change(key, Number(e.target.value))}/></label>)}
        </div>
      </fieldset>
      <fieldset disabled={busy}><legend>Какие письма отправлять</legend><div className="mail-grid">{([['offer_enabled', 'Предложение курса'], ['reminder_enabled', 'Напоминание о предложении'], ['session_enabled', 'Перед занятием'], ['completion_enabled', 'После завершения']] as const).map(([key, label]) => <label className="mail-check" key={key}><input type="checkbox" checked={policy[key]} onChange={e => change(key, e.target.checked)}/>{label}</label>)}</div></fieldset>
      <details><summary>Шаблоны писем</summary><div className="mail-grid"><label>Тема<input required maxLength={200} value={policy.subject_template} onChange={e => change('subject_template', e.target.value)}/></label><label>Подпись HR<input maxLength={500} value={policy.signature} onChange={e => change('signature', e.target.value)}/></label></div><label>Текст письма<textarea rows={7} required value={policy.body_template} onChange={e => change('body_template', e.target.value)}/></label><small>Поля: {'{name}, {course}, {message}, {explanation}, {link}, {signature}'}. Ссылка на кабинет добавляется автоматически.</small></details>
      <button className="button primary" disabled={busy}>Сохранить правила</button>
    </form>}
    <details><summary>Подключение почты HR</summary>
      {view && !view.encryption_ready && <p role="status">Для подключения почты администратор должен настроить ключ защиты учётных данных на сервере.</p>}
      <form onSubmit={event => submit(event, async signal => { await mailRequest(hrMailPath + '/mail-account', token, {...smtp, username: smtp.username || smtp.sender_email}, signal); if (!signal.aborted) setSMTP(current => ({...current, password: ''})); await refresh(signal); if (!signal.aborted) setNotice('Учётная запись проверена и подключена.'); })}>
        <fieldset disabled={busy || !view?.encryption_ready}><div className="mail-grid">
          <label>Почта HR<input type="email" required value={smtp.sender_email} onChange={e => setSMTP({...smtp, sender_email: e.target.value})}/></label><label>Имя отправителя<input required value={smtp.sender_name} onChange={e => setSMTP({...smtp, sender_name: e.target.value})}/></label>
          <label>SMTP-сервер<input required placeholder="smtp.example.com" value={smtp.host} onChange={e => setSMTP({...smtp, host: e.target.value})}/></label><label>Порт<input type="number" min={1} max={65535} required value={smtp.port} onChange={e => setSMTP({...smtp, port: Number(e.target.value)})}/></label>
          <label>Защита<select value={smtp.security} onChange={e => setSMTP({...smtp, security: e.target.value})}><option value="ssl">TLS</option><option value="starttls">STARTTLS</option></select></label><label>Логин, если отличается от email<input value={smtp.username} onChange={e => setSMTP({...smtp, username: e.target.value})}/></label>
          <label>Пароль приложения почтового сервиса<input type="password" autoComplete="new-password" required value={smtp.password} onChange={e => setSMTP({...smtp, password: e.target.value})}/></label>
        </div><button className="button primary">Проверить и подключить</button></fieldset>
      </form>{view?.account && <button className="button secondary" disabled={busy} onClick={() => run(async signal => { await mailRequest(hrMailPath + '/mail-account/disconnect', token, {}, signal); await refresh(signal); })}>Отключить почту</button>}
    </details>
    <details><summary>Адреса сотрудников и проверка письма</summary><div className="mail-grid">
      <label>Сотрудник<select value={chosen} onChange={e => {setContactId(e.target.value); setPreview(null);}}>{employees.map(employee => <option key={employee.employee_id} value={employee.employee_id}>{employee.full_name} · {employee.employee_id}</option>)}</select></label>
      <label>Email сотрудника<input type="email" value={contactEmail} onChange={e => setContactEmail(e.target.value)}/></label><label className="mail-check"><input type="checkbox" checked={hrPaused} onChange={e => setHRPaused(e.target.checked)}/>Пауза отправок этому сотруднику</label>
    </div><div className="mail-actions"><button className="button secondary" disabled={busy || !chosen} onClick={() => run(async signal => { await mailRequest(`${hrMailPath}/contacts/${encodeURIComponent(chosen)}`, token, {email: contactEmail || null, hr_paused: hrPaused}, signal); await refresh(signal); if (!signal.aborted) setNotice('Адрес и пауза сохранены.'); })}>Сохранить контакт</button>
      <button className="button secondary" disabled={busy || !chosen} onClick={() => run(async signal => { const value = await mailRequest<{subject: string; body: string}>(`${hrMailPath}/preview/${encodeURIComponent(chosen)}`, token, undefined, signal); if (!signal.aborted) setPreview(value); })}>Предпросмотр предложения</button></div>
      {preview && <div className="mail-preview"><strong>{preview.subject}</strong><pre>{preview.body}</pre></div>}
      <form onSubmit={event => submit(event, async signal => { const key = `test:${testEmail}`; const id = commands.current.get(key) ?? crypto.randomUUID(); commands.current.set(key, id); await mailRequest(hrMailPath + '/test', token, {command_id: id, recipient: testEmail}, signal); await refresh(signal); if (!signal.aborted) setNotice('Тестовое письмо добавлено в очередь. Результат появится в журнале.'); })}><label>Адрес для тестового письма<input type="email" required value={testEmail} onChange={e => setTestEmail(e.target.value)}/></label><button className="button secondary" disabled={busy || !view?.account}>Отправить тестовое письмо</button></form>
    </details>
    <details><summary>Журнал отправок ({journal?.deliveries.length ?? 0})</summary><p className="muted">«Принято почтовым сервисом» не означает доставку или прочтение. Статус участия хранится отдельно.</p>
      <div className="connected-table-wrap"><table><thead><tr><th>Сотрудник / письмо</th><th>Статус</th><th>Время</th><th>Действия</th></tr></thead><tbody>{journal?.deliveries.slice().reverse().slice(0, 30).map(row => <tr key={row.id}><td>{row.employee_id ?? 'HR'} · {title(row.kind)}<br/><small>{row.recipient}</small></td><td>{title(row.status)}<br/><small>{title(row.block_reason ?? row.error_code)}</small></td><td>{when(row.next_attempt_at ?? row.due_at)}</td><td>{row.status === 'failed' && <button disabled={busy} onClick={() => run(async signal => { await mailRequest(`${hrMailPath}/deliveries/${encodeURIComponent(row.id)}/retry`, token, {}, signal); await refresh(signal); })}>Повторить</button>}{row.status === 'unknown' && <div><p>Проверьте результат у почтового сервиса. Отсутствие письма в «Отправленных» само по себе не подтверждает ошибку.</p><label>На чём основано подтверждение<input maxLength={500} value={reconciliationNotes[row.id] ?? ''} onChange={e => setReconciliationNotes({...reconciliationNotes, [row.id]: e.target.value})}/></label><div className="mail-actions">{(['accepted', 'failed'] as const).map(outcome => <button key={outcome} disabled={busy || (reconciliationNotes[row.id]?.trim().length ?? 0) < 3} onClick={() => run(async signal => { await mailRequest(`${hrMailPath}/deliveries/${encodeURIComponent(row.id)}/resolve`, token, {outcome, note: reconciliationNotes[row.id].trim()}, signal); await refresh(signal); })}>{outcome === 'accepted' ? 'Подтверждаю отправку' : 'Подтверждаю, что не отправлено'}</button>)}</div></div>}</td></tr>)}</tbody></table></div>
      <p>Предложений: {journal?.offers.length ?? 0}. Подготовлено профилей: {Object.keys(journal?.generations ?? {}).length}.</p>
    </details>
  </section>;
}

export function EmployeeNotificationCenter({token, employeeId}: {token: string; employeeId: string}) {
  return <EmployeeMail key={`${token}:${employeeId}`} token={token} employeeId={employeeId}/>;
}

function EmployeeMail({token, employeeId}: {token: string; employeeId: string}) {
  const [data, setData] = useState<EmployeeNotifications | null>(null);
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [later, setLater] = useState<Record<string, string>>({});
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [expanded, setExpanded] = useState<string | null>(null);
  const initialized = useRef(false);
  const commands = useRef(new Map<string, string>());
  const {notice, setNotice, busy, run} = useActions();
  const base = employeeMailPath(employeeId);
  const load = useCallback(async (signal: AbortSignal) => {
    const response = await mailRequest<EmployeeNotifications>(base + '/notifications', token, undefined, signal);
    if (!signal.aborted) { setData(response); if (!initialized.current) { setPreferences(response.contact.preferences); initialized.current = true; } }
  }, [base, token]);
  useEffect(() => { const controller = new AbortController(); const refresh = () => load(controller.signal).catch(error => { if (!controller.signal.aborted) setNotice(error.message); }); void refresh(); const timer = setInterval(refresh, 15_000); return () => {controller.abort(); clearInterval(timer);}; }, [load, setNotice]);
  async function act(id: string, action: string) {
    await run(async signal => {
      const payload = {action, snoozed_until: action === 'later' && later[id] ? `${later[id]}:00+05:00` : null, reason: action === 'decline' ? reasons[id] || null : null};
      const key = `${id}:${JSON.stringify(payload)}`;
      const command = commands.current.get(key) ?? crypto.randomUUID(); commands.current.set(key, command);
      await mailRequest(`${base}/offers/${encodeURIComponent(id)}/actions`, token, {...payload, command_id: command}, signal);
      if (!signal.aborted && action === 'view') setExpanded(id);
      await load(signal);
    });
  }
  return <section className="panel notification-center"><div className="section-title"><div><span className="eyebrow">СЛЕДУЮЩИЙ ШАГ</span><h2>Предложения и письма</h2></div><button className="button secondary" disabled={busy} onClick={() => run(load)}>Обновить</button></div>
    {notice && <p className="mail-notice" role="status">{notice}</p>}
    {data?.offers.length === 0 && <p>Предложения появятся после подготовки рекомендации. {data.generation?.status === 'failed' ? 'Подготовка временно недоступна.' : ''}</p>}
    {data?.offers.map(offer => <article className="mail-offer" key={offer.id}><div className="section-title"><h3>{offer.title}</h3><span className="badge">{title(offer.status)}</span></div>
      {offer.status === 'proposed' && expanded !== offer.id ? <button className="text-button" disabled={busy} onClick={() => act(offer.id, 'view')}>Посмотреть предложение</button> : <p>{offer.explanation}</p>}
      {['proposed', 'viewed', 'snoozed'].includes(offer.status) && <><div className="mail-actions"><button className="button primary" disabled={busy} onClick={() => act(offer.id, 'enroll')}>Записаться{offer.session_date ? ` · ${offer.session_date}` : ''}</button></div>
        <details><summary>Отложить или отказаться</summary><div className="mail-grid"><label>Напомнить в общее время системы<input type="datetime-local" value={later[offer.id] ?? ''} onChange={e => setLater({...later, [offer.id]: e.target.value})}/></label><button className="button secondary" disabled={busy || !later[offer.id]} onClick={() => act(offer.id, 'later')}>Напомнить позже</button><label>Почему не подходит? Необязательно<input maxLength={1000} value={reasons[offer.id] ?? ''} onChange={e => setReasons({...reasons, [offer.id]: e.target.value})}/></label><button className="button secondary" disabled={busy} onClick={() => act(offer.id, 'decline')}>Не подходит</button></div></details></>}
      {offer.status === 'enrolled' && <p className="muted">Запись сохранена. Завершение курса отмечается на странице события.</p>}
    </article>)}
    {preferences && <details><summary>Моя почта и частота уведомлений</summary><form onSubmit={event => { event.preventDefault(); void run(async signal => { await mailRequest(base + '/notifications/preferences', token, preferences, signal); await load(signal); if (!signal.aborted) setNotice('Настройки уведомлений сохранены.'); }); }}>
      <fieldset disabled={busy}><div className="mail-grid"><label>Email<input type="email" value={preferences.email ?? ''} onChange={e => setPreferences({...preferences, email: e.target.value || null})}/></label><label>Не чаще одного письма за часов<input type="number" required min={1} max={2160} value={preferences.minimum_interval_hours} onChange={e => setPreferences({...preferences, minimum_interval_hours: Number(e.target.value)})}/></label><label>Не больше писем за 7 дней<input type="number" required min={1} max={14} value={preferences.weekly_limit} onChange={e => setPreferences({...preferences, weekly_limit: Number(e.target.value)})}/></label><label className="mail-check"><input type="checkbox" checked={preferences.paused} onChange={e => setPreferences({...preferences, paused: e.target.checked})}/>Поставить все письма на паузу</label></div><p className="muted">Ограничения HR могут дополнительно уменьшать частоту. Время отправки задаёт HR.</p><button className="button primary">Сохранить</button></fieldset></form></details>}
  </section>;
}
