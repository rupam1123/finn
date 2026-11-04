import Toasts from './Toasts';
import {Suspense} from 'react';
import Workspace from './workspace/Workspace';
import type { Metadata, Viewport } from "next";
import "@fontsource/dm-sans/400.css";
import "@fontsource/dm-sans/500.css";
import "@fontsource/dm-sans/600.css";
import "./globals.css";
import "./identity.css";
import "./review.css";
import "./workspace/workspace.css";
import "./workspace/glass.css";
import "./workspace/swiftz.css";
import "./workspace/welcome.css";
import "./workspace/picker.css";
import "./workspace/assistant.css";
import "./workspace/details-polish.css";
import "./workspace/chrome-refinements.css";
import "./workspace/typography.css";

export const metadata: Metadata = {title: "FINN — Research workspace", description: "Assessment prototype for reviewing saved financial sources and AI-assisted analysis.", robots:{index:false,follow:false},manifest: "/manifest.webmanifest",
  appleWebApp: {capable: true, statusBarStyle: "black-translucent", title: "FINN"},
  icons: {icon: "/brand/finn-mark.png", apple: "/brand/finn-mark.png"}};
export const viewport: Viewport = {width: "device-width", initialScale: 1, themeColor: "#ffffff", viewportFit: "cover"};

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{__html:`try{var v=JSON.parse(localStorage.getItem('finn.theme')||'null');var t=v==='dark'||v==='light'?v:matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';document.documentElement.dataset.theme=t;document.documentElement.style.colorScheme=t}catch{document.documentElement.dataset.theme='light'}`}}/></head><body><Suspense><Workspace>{children}</Workspace><Toasts/></Suspense></body></html>;
}
