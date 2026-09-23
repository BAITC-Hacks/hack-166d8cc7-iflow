"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { ApiError, getHRDashboard, importDataset, listEmployees } from "../lib/api";
import type { EmployeeList, HRDashboard, ImportResult } from "../lib/types";
import { HRNotificationCenter } from './notification-center';

type Props = {
  token: string;
  onSelectEmployee: (id: string) => void;
  onImported: () => void;
};
type LoadState = {
  token: string;
  dashboard: HRDashboard;
  employees: EmployeeList;
};
type DisplayError = { message: string; code?: string; details?: unknown[] };

const statusLabels: Record<string, string> = {
  completed: "Завершено",
  in_progress: "В процессе",
  overdue: "Просрочено",
  dropped: "Прервано",
  no_show: "Не посетили",
  declined: "Отклонили",
};
const statusColors: Record<string, string> = {
  completed: "#087f64",
  in_progress: "#e4bd4f",
  overdue: "#d68764",
  dropped: "#8b7ca2",
  no_show: "#a3af9c",
  declined: "#647d83",
};
const number = new Intl.NumberFormat("ru-RU");

function describeError(error: unknown): DisplayError {
  if (error instanceof ApiError) {
    return { message: error.message, code: `${error.status} · ${error.error.code}`, details: error.error.details };
  }
  return { message: error instanceof Error ? error.message : "Не удалось связаться с сервером. Попробуйте ещё раз." };
}

function ErrorNotice({ error, title, onRetry }: { error: DisplayError; title: string; onRetry?: () => void }) {
  return (
    <div className="chr-error" role="alert">
      <strong>{title}</strong>
      <p>{error.message}</p>
      {error.code && <small>{error.code}</small>}
      {!!error.details?.length && (
        <details open>
          <summary>Подробности от сервера</summary>
          <pre>{JSON.stringify(error.details, null, 2)}</pre>
        </details>
      )}
      {onRetry && <button type="button" className="button secondary" onClick={onRetry}>Повторить загрузку</button>}
    </div>
  );
}

function Arrow() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>;
}

export default function ConnectedHR(props: Props) {
  return <HRContent key={props.token} {...props} />;
}

function HRContent({ token, onSelectEmployee, onImported }: Props) {
  const [loaded, setLoaded] = useState<LoadState | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<DisplayError | null>(null);
  const [search, setSearch] = useState("");
  const [visibleEmployees, setVisibleEmployees] = useState(20);
  const [files, setFiles] = useState<{ employees?: File; history?: File }>({});
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState<DisplayError | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const loadController = useRef<AbortController | null>(null);
  const importController = useRef<AbortController | null>(null);
  const identity = useRef(0);
  const formRef = useRef<HTMLFormElement>(null);
  const importedCallback = useRef(onImported);
  importedCallback.current = onImported;

  const load = useCallback(async () => {
    loadController.current?.abort();
    const controller = new AbortController();
    loadController.current = controller;
    const currentIdentity = identity.current;
    setLoading(true);
    setLoadError(null);
    try {
      const [dashboard, employees] = await Promise.all([
        getHRDashboard(token, controller.signal),
        listEmployees(token, controller.signal),
      ]);
      if (controller.signal.aborted || currentIdentity !== identity.current) return;
      setLoaded({ token, dashboard, employees });
    } catch (error) {
      if (controller.signal.aborted || currentIdentity !== identity.current) return;
      setLoadError(describeError(error));
    } finally {
      if (!controller.signal.aborted && currentIdentity === identity.current) setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    identity.current += 1;
    setLoaded(null);
    setFiles({});
    setImportError(null);
    setImportResult(null);
    setImporting(false);
    setSearch("");
    setVisibleEmployees(20);
    formRef.current?.reset();
    void load();
    return () => {
      identity.current += 1;
      loadController.current?.abort();
      importController.current?.abort();
    };
  }, [load]);

  const data = loaded?.token === token ? loaded : null;
  const dashboard = data?.dashboard;
  const employees = data?.employees.items ?? [];
  const employeeMap = useMemo(() => new Map(employees.map(employee => [employee.employee_id, employee])), [employees]);
  const query = search.trim().toLocaleLowerCase("ru-RU");
  const filteredEmployees = employees.filter(employee => `${employee.full_name} ${employee.employee_id} ${employee.role} ${employee.grade}`.toLocaleLowerCase("ru-RU").includes(query));
  const gaps = [...(dashboard?.skill_gap_counts ?? [])].sort((a, b) => b.employee_count - a.employee_count || a.name.localeCompare(b.name, "ru")).slice(0, 8);
  const participation = [...(dashboard?.participation_by_event ?? [])].map(event => ({ ...event, total: Object.values(event.status_counts).reduce((sum, value) => sum + value, 0) })).sort((a, b) => b.total - a.total || a.title.localeCompare(b.title, "ru"));
  const statusTotals = participation.reduce<Record<string, number>>((totals, event) => {
    Object.entries(event.status_counts).forEach(([status, count]) => { totals[status] = (totals[status] ?? 0) + count; });
    return totals;
  }, {});
  const totalParticipations = Object.values(statusTotals).reduce((sum, value) => sum + value, 0);
  const completed = statusTotals.completed ?? 0;
  const completionPercent = totalParticipations ? Math.round(completed / totalParticipations * 100) : 0;
  const orderedStatuses = Array.from(new Set([...Object.keys(statusLabels), ...Object.keys(statusTotals)]));

  async function handleImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (importing || (!files.employees && !files.history)) return;
    setImportError(null);
    setImportResult(null);
    const totalSize = (files.employees?.size ?? 0) + (files.history?.size ?? 0);
    if (totalSize > 10 * 1024 * 1024) {
      setImportError({ message: "Размер файлов превышает лимит сервера: 10 МиБ на запрос." });
      return;
    }
    const controller = new AbortController();
    importController.current?.abort();
    importController.current = controller;
    const currentIdentity = identity.current;
    setImporting(true);
    try {
      const result = await importDataset(files, token, controller.signal);
      if (controller.signal.aborted || currentIdentity !== identity.current) return;
      setImportResult(result);
      setFiles({});
      formRef.current?.reset();
      importedCallback.current();
      void load();
    } catch (error) {
      if (controller.signal.aborted || currentIdentity !== identity.current) return;
      setImportError(describeError(error));
    } finally {
      if (!controller.signal.aborted && currentIdentity === identity.current) setImporting(false);
    }
  }

  return (
    <div className="connected-hr">
      <header className="page-heading">
        <div><div className="eyebrow">КОМАНДА И ВОЗМОЖНОСТИ</div><h1>Развитие в масштабе команды <span className="chr-flower" aria-hidden="true">✳</span></h1><p>Навыки, участие и доступные следующие шаги — по данным сотрудников.</p></div>
        <button type="button" className="button secondary" disabled={loading || importing} onClick={() => void load()}>{loading ? "Обновляем…" : "Обновить данные"}</button>
      </header>

      {loadError && <ErrorNotice title="Не удалось загрузить HR-данные" error={loadError} onRetry={() => void load()} />}
      {loading && <div className="chr-loading" role="status"><span className="chr-spinner" />{data ? "Обновляем показатели команды…" : "Собираем данные о развитии команды…"}</div>}

      {dashboard && (
        <>
          <div className="chr-data-stamp">Данные на {dashboard.as_of_date} <span>·</span> Версия {dashboard.revision}{data?.employees.revision !== dashboard.revision && <strong>Данные изменились во время загрузки. Нажмите «Обновить данные».</strong>}</div>
          <div className="chr-metrics">
            <div className="chr-metric chr-metric-green"><span>Сотрудников</span><strong>{number.format(employees.length)}</strong><small>в доступном наборе данных</small><svg width="65" height="65" viewBox="0 0 65 65" fill="none" aria-hidden="true"><circle cx="23" cy="20" r="9" fill="currentColor"/><circle cx="45" cy="25" r="7" fill="currentColor" opacity=".5"/><path d="M5 54c0-20 36-20 36 0M35 55c0-15 26-15 26 0" fill="currentColor"/></svg></div>
            <div className="chr-metric"><span>Записей участия</span><strong>{number.format(totalParticipations)}</strong><small>по всем мероприятиям и статусам</small></div>
            <div className="chr-metric"><span>Завершённых участий</span><strong>{number.format(completed)}</strong><small>{completionPercent}% от записей участия</small></div>
            <div className="chr-metric chr-metric-yellow"><span>Без подходящих событий</span><strong>{number.format(dashboard.employees_without_candidate.length)}</strong><small>сейчас нет кандидатов в каталоге</small></div>
          </div>

          <div className="chr-chart-grid">
            <section className="chr-panel">
              <div className="chr-section-head"><div><span className="eyebrow">ГДЕ НУЖНА ПОДДЕРЖКА</span><h2>Потребность в навыках</h2><p>Топ-8 разрывов до следующего грейда. Число сотрудников с дефицитом навыка.</p></div><span className="chr-panel-mark" aria-hidden="true">↗</span></div>
              {gaps.length ? <div className="chr-gap-chart">{gaps.map((gap, index) => <div className="chr-gap-row" key={gap.skill_id}><div><span>{gap.name}</span><strong>{number.format(gap.employee_count)} <small>сотр.</small></strong></div><div className="chr-gap-track"><span style={{ width: `${employees.length ? Math.min(100, gap.employee_count / employees.length * 100) : 0}%`, background: index === 0 ? "#087f64" : index < 3 ? "#84ad82" : "#ccd8ac" }} /></div></div>)}</div> : <div className="chr-empty">В данных нет разрывов навыков до следующего грейда.</div>}
            </section>
            <section className="chr-panel">
              <div className="chr-section-head"><div><span className="eyebrow">ОТ ПЛАНА К ДЕЙСТВИЮ</span><h2>Участие в развитии</h2><p>Распределение записей по текущему статусу.</p></div></div>
              <div className="chr-donut-wrap"><svg className="chr-donut" viewBox="0 0 180 180" role="img" aria-label={`${completionPercent}% участий завершено, всего записей ${totalParticipations}`}><circle cx="90" cy="90" r="72" fill="none" stroke="#edf0e5" strokeWidth="17" />{(() => { let offset = 0; return orderedStatuses.filter(status => statusTotals[status] > 0).map(status => { const length = statusTotals[status] / totalParticipations * 100; const segment = <circle key={status} cx="90" cy="90" r="72" fill="none" stroke={statusColors[status] ?? "#8c998e"} strokeWidth="17" pathLength="100" strokeDasharray={`${length} ${100 - length}`} strokeDashoffset={-offset} transform="rotate(-90 90 90)" />; offset += length; return segment; }); })()}<text x="90" y="87" textAnchor="middle" className="chr-donut-value">{completionPercent}%</text><text x="90" y="109" textAnchor="middle" className="chr-donut-caption">завершено</text></svg></div>
              <div className="chr-status-legend">{orderedStatuses.map(status => <div key={status}><span><i style={{ background: statusColors[status] ?? "#8c998e" }} />{statusLabels[status] ?? status}</span><b>{number.format(statusTotals[status] ?? 0)}</b></div>)}</div>
              <p className="chr-chart-note">У одного сотрудника может быть несколько участий. Это число записей, а не уникальных людей.</p>
            </section>
          </div>

          <section className="chr-recommendation-note"><div className="chr-note-icon" aria-hidden="true">✦</div><div><h2>ИИ-рекомендации: метрика пока недоступна</h2><p>Бэкенд ещё не рассчитывает число сотрудников без ИИ-рекомендаций. Ниже показаны сотрудники, для которых в каталоге нет подходящих мероприятий.</p></div><span>В разработке</span></section>

          <section className="chr-panel">
            <div className="chr-section-head"><div><span className="eyebrow">ТОЧКИ ВНИМАНИЯ</span><h2>Нет подходящего следующего шага <span className="chr-count">{dashboard.employees_without_candidate.length}</span></h2><p>Откройте профиль, чтобы посмотреть цели и дефициты навыков.</p></div></div>
            {dashboard.employees_without_candidate.length ? <div className="chr-candidate-list">{dashboard.employees_without_candidate.map(id => { const employee = employeeMap.get(id); return <button type="button" key={id} onClick={() => onSelectEmployee(id)}><span className="chr-person-icon">{employee?.full_name.split(" ").slice(0, 2).map(part => part[0]).join("") ?? id.slice(-2)}</span><span><strong>{employee?.full_name ?? id}</strong><small>{employee ? `${employee.role} · ${employee.grade}` : id}</small></span><Arrow /></button>; })}</div> : <div className="chr-empty chr-empty-positive">Для каждого сотрудника есть хотя бы одно подходящее мероприятие.</div>}
          </section>

          <section className="chr-panel">
            <div className="chr-section-head"><div><span className="eyebrow">КАРТИНА ПО МЕРОПРИЯТИЯМ</span><h2>Как участвует команда</h2><p>Количество записей участия по каждому мероприятию.</p></div></div>
            <div className="chr-table-scroll" tabIndex={0} role="region" aria-label="Участие по мероприятиям"><table className="chr-table"><thead><tr><th scope="col">Мероприятие</th><th scope="col">Всего</th>{orderedStatuses.map(status => <th scope="col" key={status}>{statusLabels[status] ?? status}</th>)}</tr></thead><tbody>{participation.map(event => <tr key={event.event_id}><th scope="row"><strong>{event.title}</strong><small>{event.event_id}</small></th><td><b>{number.format(event.total)}</b></td>{orderedStatuses.map(status => <td key={status}>{number.format(event.status_counts[status] ?? 0)}</td>)}</tr>)}</tbody></table>{!participation.length && <div className="chr-empty">В каталоге пока нет мероприятий.</div>}</div>
          </section>

          <section className="chr-panel">
            <div className="chr-section-head chr-employee-head"><div><span className="eyebrow">ИНДИВИДУАЛЬНЫЙ МАРШРУТ</span><h2>Сотрудники <span className="chr-count">{employees.length}</span></h2></div><label className="chr-search"><span className="chr-sr-only">Поиск сотрудников по имени, роли или ID</span><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><circle cx="10" cy="10" r="6"/><path d="m15 15 5 5"/></svg><input type="search" value={search} onChange={event => { setSearch(event.target.value); setVisibleEmployees(20); }} placeholder="Имя, роль или ID" /></label></div>
            <div className="chr-employee-list">{filteredEmployees.slice(0, visibleEmployees).map(employee => <button type="button" key={employee.employee_id} onClick={() => onSelectEmployee(employee.employee_id)}><span className="chr-person-icon">{employee.full_name.split(" ").slice(0, 2).map(part => part[0]).join("")}</span><span className="chr-person-main"><strong>{employee.full_name}</strong><small>{employee.employee_id} · {employee.role}</small></span><span className="chr-grade">{employee.grade}</span><Arrow /></button>)}</div>
            {!filteredEmployees.length && <div className="chr-empty">{query ? "По вашему запросу сотрудники не найдены." : "Сотрудников в наборе данных пока нет."}</div>}
            <div className="chr-list-footer"><span>Показано {Math.min(visibleEmployees, filteredEmployees.length)} из {filteredEmployees.length}</span>{filteredEmployees.length > visibleEmployees && <button className="button secondary" type="button" onClick={() => setVisibleEmployees(count => count + 20)}>Показать ещё 20</button>}</div>
          </section>
        </>
      )}

      <HRNotificationCenter token={token} employees={loaded?.employees.items ?? []}/>
      <section className="chr-import chr-panel">
        <div className="chr-import-copy"><div className="chr-import-mark" aria-hidden="true"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M12 16V3m-5 5 5-5 5 5M4 15v5a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5" /></svg></div><span className="eyebrow">НОВЫЕ ДАННЫЕ — НОВЫЕ ВОЗМОЖНОСТИ</span><h2>Добавьте сотрудников и историю</h2><p>Загрузите один или оба файла в исходной схеме датасета. Сервер проверит записи и обновит показатели команды.</p><small>JSON для сотрудников · CSV для истории<br />Лимит запроса — 10 МиБ</small></div>
        <div className="chr-import-form-wrap"><form ref={formRef} onSubmit={handleImport} className="chr-import-form"><label><span>Сотрудники <small>employees.json</small></span><input type="file" accept=".json,application/json" disabled={importing} onChange={event => { const file = event.target.files?.[0]; setFiles(current => ({ ...current, employees: file })); setImportError(null); setImportResult(null); }} /></label><label><span>История участия <small>activity_history.csv</small></span><input type="file" accept=".csv,text/csv" disabled={importing} onChange={event => { const file = event.target.files?.[0]; setFiles(current => ({ ...current, history: file })); setImportError(null); setImportResult(null); }} /></label><button type="submit" className="button primary" disabled={importing || (!files.employees && !files.history)}>{importing ? "Загружаем и проверяем…" : importError ? "Повторить импорт" : "Импортировать данные"}<Arrow /></button></form>
          {importError && <ErrorNotice title="Импорт не выполнен" error={importError} />}
          {importResult && <div className="chr-import-success" role="status"><strong>Данные импортированы · версия {importResult.revision}</strong><p>Сотрудников добавлено: {importResult.added_employees}, без изменений: {importResult.unchanged_employees}.</p><p>Записей истории добавлено: {importResult.added_history}, без изменений: {importResult.unchanged_history}.</p></div>}
        </div>
      </section>
    </div>
  );
}
