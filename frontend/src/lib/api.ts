import type {
  CompletionCommand,
  CompletionResult,
  EmployeeDetail,
  EmployeeList,
  HRDashboard,
  ImportResult,
  MarketState,
  Principal,
  RecommendationContext,
  RecommendationResult,
  RedeemCommand,
  Redemption,
  Trajectory,
} from "./types";

// The default uses Next's same-origin rewrite; the browser never needs backend CORS.
const base = (process.env.NEXT_PUBLIC_API_URL ?? "/backend").replace(/\/$/, "");

export interface ApiErrorDetail {
  code: string;
  message: string;
  details: unknown[];
}

export class ApiError extends Error {
  constructor(public status: number, public error: ApiErrorDetail) {
    super(error.message);
    this.name = "ApiError";
  }
}

function responseError(body: unknown, status: number): ApiErrorDetail {
  if (body && typeof body === "object" && "error" in body) {
    const error = body.error;
    if (error && typeof error === "object") {
      return {
        code: "code" in error && typeof error.code === "string" ? error.code : "unexpected",
        message: "message" in error && typeof error.message === "string"
          ? error.message : `Сервер вернул ошибку ${status}.`,
        details: "details" in error && Array.isArray(error.details) ? error.details : [],
      };
    }
  }
  // Keep FastAPI validation details available as well as domain error envelopes.
  const detail = body && typeof body === "object" && "detail" in body ? body.detail : undefined;
  return {
    code: "unexpected",
    message: typeof detail === "string" ? detail : `Сервер вернул ошибку ${status}.`,
    details: Array.isArray(detail) ? detail : [],
  };
}

export async function request<T>(
  path: string,
  token: string,
  init: RequestInit = {},
  timeoutMs = 12_000,
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  headers.set("Accept", "application/json");
  const controller = new AbortController();
  const callerSignal = init.signal;
  let timedOut = false;
  const cancel = () => controller.abort();
  if (callerSignal?.aborted) cancel();
  else callerSignal?.addEventListener("abort", cancel, { once: true });
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  try {
    const response = await fetch(`${base}${path}`, {
      ...init,
      headers,
      signal: controller.signal,
      cache: "no-store",
    });
    const text = await response.text();
    let body: unknown;
    let validJson = false;
    if (text) {
      try {
        body = JSON.parse(text);
        validJson = true;
      } catch {
        // A stopped backend may produce a proxy HTML error instead of API JSON.
      }
    }
    if (!response.ok) throw new ApiError(response.status, responseError(body, response.status));
    if (response.status === 204) return undefined as T;
    if (!validJson) {
      throw new ApiError(response.status, {
        code: "invalid_response",
        message: "Сервер вернул некорректный ответ. Повторите запрос.",
        details: [],
      });
    }
    return body as T;
  } catch (error) {
    // Cancellation during navigation should not appear as a connection failure.
    if (callerSignal?.aborted) throw new DOMException("Запрос отменён.", "AbortError");
    if (timedOut) {
      throw new ApiError(0, {
        code: "timeout",
        message: "Сервер не успел ответить. Повторите запрос.",
        details: [],
      });
    }
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, {
      code: "network_error",
      message: "Не удалось связаться с сервером. Проверьте подключение и повторите запрос.",
      details: [],
    });
  } finally {
    clearTimeout(timer);
    callerSignal?.removeEventListener("abort", cancel);
  }
}

const employeePath = (id: string) => `/api/employees/${encodeURIComponent(id)}`;
const jsonCommand = (body: unknown, signal?: AbortSignal): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
  signal,
});

export const getSession = (token: string, signal?: AbortSignal) =>
  request<Principal>("/api/session", token, { signal });

export const listEmployees = (token: string, signal?: AbortSignal) =>
  request<EmployeeList>("/api/employees", token, { signal });

export const getEmployee = (id: string, token: string, signal?: AbortSignal) =>
  request<EmployeeDetail>(employeePath(id), token, { signal });

export const getTrajectory = (id: string, token: string, signal?: AbortSignal) =>
  request<Trajectory>(`${employeePath(id)}/trajectory`, token, { signal });

export const getRecommendationContext = (id: string, token: string, signal?: AbortSignal) =>
  request<RecommendationContext>(`${employeePath(id)}/recommendations/context`, token, { signal });

export const requestRecommendations = (id: string, token: string, signal?: AbortSignal) =>
  request<RecommendationResult>(`${employeePath(id)}/recommendations`, token, { method: "POST", signal }, 15_000);

export const completeActivity = (
  id: string,
  eventId: string,
  command: CompletionCommand,
  token: string,
  signal?: AbortSignal,
) => request<CompletionResult>(
  `${employeePath(id)}/activities/${encodeURIComponent(eventId)}/complete`, token, jsonCommand(command, signal),
);

export const getHRDashboard = (token: string, signal?: AbortSignal) =>
  request<HRDashboard>("/api/hr/dashboard", token, { signal });

export function importDataset(files: { employees?: File; history?: File }, token: string, signal?: AbortSignal) {
  const form = new FormData();
  if (files.employees) form.append("employees", files.employees);
  if (files.history) form.append("history", files.history);
  return request<ImportResult>("/api/dataset/import", token, { method: "POST", body: form, signal });
}

export const getMarket = (token: string, signal?: AbortSignal) =>
  request<MarketState>("/api/market", token, { signal });

export const redeemReward = (command: RedeemCommand, token: string, signal?: AbortSignal) =>
  request<Redemption>("/api/market/redeem", token, jsonCommand(command, signal));
