export const preferenceKeys=['finn.theme','finn.telemetry','finn.window','finn.price','finn.volume','finn.watches','finn.saved'] as const;
export function resetBrowserPreferences(storage:Storage){for(const key of preferenceKeys)storage.removeItem(key);}
export function csvCell(value:unknown){const text=String(value??'');return '"'+(/^[\s\u0000-\u001f]*[=+@-]/.test(text)||/^[\t\r\n]/.test(text)?"'":'')+text.replaceAll('"','""')+'"';}
