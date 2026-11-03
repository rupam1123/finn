# Sites navigation and touch follow-up — 3 November 2026

The user reported that the published Inbox loaded saved data but navigation links did nothing. In the actual deployed browser, clicking Radar reproduced `TypeError: e is not a function` from the compiled Link navigation handler. Prefetch also failed with `getPrefetchInterceptionContext` undefined. Settings still opened, separating this from a general hydration or API failure.

The original Sites starter used Vite 8.0.13 with Rolldown 1.0.1. Its built dynamic navigation import pointed at a shared chunk without the namespace properties expected by the router. Changing export-name minification alone did not restore those missing exports. The port now uses Vite 8.3.0 and its locked Rolldown 1.2.16 dependency, preserving the dynamic navigation namespace. A production-output regression check verifies that both navigation and prefetch entry points remain available; hosted CI runs that check after building.

The canonical frontend now adds delegated press-and-slide selection for the mobile dock, filing windows, category filters, feed tabs, chart ranges/modes, research tabs, company tabs, Radar filters and company shortcuts. Highlight changes coalesce into one animation frame; a gesture commits one final choice on release. Vertical scroll intent, cancellation, disabled controls, normal taps and keyboard activation retain their behavior. Reduced motion and forced-color states are included. No financial logic or saved data is changed by this interaction work.

Verification completed locally:

- 60 existing frontend checks plus nine new gesture checks passed.
- Original and hosted TypeScript checks passed.
- Sites production build passed with the corrected dependency pair.
- The production router namespace contract passed.
- All 240 saved-data API comparisons still passed.
- Nine hosted read-only/decimal/calendar/security checks passed.

The corrected code is on the private GitHub repository's `sites` branch. `main` retains the original Python application and links the hosted checkout. Future interface pushes to main run checks and synchronize the hosted branch; scheduled Sites publication checks that branch hourly. The source synchronization successfully produced a commit in GitHub after the FETCH_HEAD repair. The first unattended Sites publication has not been certified.

At this checkpoint, publication and final browser verification are blocked by changed desktop account settings: the current Sites account returns NOT_FOUND for FINN's exact existing project ID and lists a different owner's projects; local browser control also reports disabled. Closing browser windows does not repair these account permissions. No replacement Site or database was created, and no private token was used to bypass the missing owner access.

The existing FINN Site belongs to `kush5251dhar@gmail.com`. Restore that account's Sites connection and enable Browser in desktop Settings to finish actual navigation/drag checks and publish the fix to the same URL. The user has also requested public sharing; that change remains pending owner access. Public access will expose the saved research and evidence to anyone with the URL. Source and licensing gates in the main handoff remain separate.

Existing URL: https://finn-research-rupam1123-20261103.quaintmoon4.chatgpt.site/inbox

Project identity is preserved in `hosting/.openai/hosting.json`. Deployment helpers and credentials must follow the current Sites skill; secrets and the `.deployment-data` directory remain outside Git.
