import { request } from './api';
import type { EmployeeSummary } from './types';

export interface MailPolicy {
  version: number; enabled: boolean; start_minute: number; end_minute: number;
  minimum_interval_hours: number; weekly_limit: number; reminder_after_days: number;
  maximum_reminders: number; cooldown_days: number;
  offer_enabled: boolean; reminder_enabled: boolean; session_enabled: boolean; completion_enabled: boolean;
  subject_template: string; body_template: string; signature: string;
}
export interface Preferences { email: string | null; paused: boolean; paused_until: string | null; minimum_interval_hours: number; weekly_limit: number }
export interface Contact { preferences: Preferences; hr_paused: boolean; address_blocked: boolean }
export interface Offer { id: string; employee_id: string; event_id: string; title: string; explanation: string; status: string; session_date: string | null; snoozed_until: string | null }
export interface Delivery { id: string; employee_id: string | null; offer_id: string | null; kind: string; status: string; due_at: string; next_attempt_at: string | null; created_at: string; recipient: string | null; subject: string | null; body: string | null; attempts: number; block_reason: string | null; error_code: string | null }
export interface EmployeeNotifications { offers: Offer[]; contact: Contact; company_now: string; generation: {status: string; error_code: string | null} | null }
export interface SettingsView { settings: MailPolicy; account: {sender_email: string; sender_name: string; status: string; host: string} | null; company_now: string; encryption_ready: boolean; ai_ready: boolean }
export interface MailJournal { deliveries: Delivery[]; offers: Offer[]; contacts: Record<string, Contact>; generations: Record<string, {status: string; error_code: string | null}>; total: number }
export type Employees = EmployeeSummary[];

export const mailRequest = <T,>(path: string, token: string, body?: unknown, signal?: AbortSignal) => request<T>(path, token,
  body === undefined ? { signal } : { method: 'POST', signal, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) }, 30_000);
export const employeeMailPath = (id: string) => `/api/employees/${encodeURIComponent(id)}`;
export const hrMailPath = '/api/hr/notifications';
