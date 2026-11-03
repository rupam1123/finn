"use client";

import {useEffect, useState} from "react";
type InstallEvent = Event & {prompt: () => Promise<void>; userChoice: Promise<{outcome: string}>};

export default function PwaStatus() {
  const [offline, setOffline] = useState(false), [install, setInstall] = useState<InstallEvent | null>(null);
  const [installing, setInstalling] = useState(false), [message, setMessage] = useState("");
  useEffect(() => {
    function network() {setOffline(!navigator.onLine);}
    function offered(event: Event) {event.preventDefault(); setInstall(event as InstallEvent);}
    function installed() {setInstall(null); setMessage("FINN installed");}
    network();
    window.addEventListener("online", network); window.addEventListener("offline", network);
    window.addEventListener("beforeinstallprompt", offered); window.addEventListener("appinstalled", installed);
    if (process.env.NODE_ENV === "production" && "serviceWorker" in navigator)
      void navigator.serviceWorker.register("/sw.js", {scope: "/", updateViaCache: "none"}).catch(() => {
        setMessage("Offline fallback unavailable in this browser.");
      });
    return () => {
      window.removeEventListener("online", network); window.removeEventListener("offline", network);
      window.removeEventListener("beforeinstallprompt", offered); window.removeEventListener("appinstalled", installed);
    };
  }, []);
  return <div className="pwa-status">
    {offline && <p role="status" className="text-xs text-amber-100">Offline · showing only what is already on screen</p>}
    {install && <button type="button" className="citation-pill" disabled={installing} onClick={async () => {
      setInstalling(true);
      try {await install.prompt(); await install.userChoice; setInstall(null);}
      catch {setMessage("Installation unavailable. Use your browser’s Add to Home Screen option.");}
      finally {setInstalling(false);}
    }}>Install FINN</button>}
    {message && <p role="status" className="text-xs text-white/60">{message}</p>}
  </div>;
}
