"use client";
export default function ErrorView({reset}:{error:Error;reset:()=>void}){return <main className="route-error"><h1>The workspace needs a refresh.</h1><p>A view could not be rendered. Your saved evidence remains on the backend.</p><button className="primary-action" onClick={reset}>Try this view again</button><a className="outline-button" href="/">Return to Inbox</a></main>}
