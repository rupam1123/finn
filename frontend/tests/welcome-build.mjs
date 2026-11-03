import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const html=readFileSync(new URL('../.next/server/app/index.html',import.meta.url),'utf8');
assert.ok(html.includes('class="welcome-page"')&&html.includes('Open workspace')&&html.includes('Meet FINN.'),'Welcome content must be present in production HTML before hydration');
console.log('Production welcome content is present before hydration.');
