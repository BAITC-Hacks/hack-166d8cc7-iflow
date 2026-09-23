export function StatusMessage({error}: {error?: string}) { return <p role={error?"alert":"status"}>{error ?? "Loading…"}</p>; }
