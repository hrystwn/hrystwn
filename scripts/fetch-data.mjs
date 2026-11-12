import { mkdir, readFile, writeFile } from 'node:fs/promises';

const USERNAME = 'hrystwn';
const APP_ID = '6822785836';
const BLOG = 'https://tenangmail.com/blog/';
const ENDPOINT = `https://github.com/users/${USERNAME}/contributions`;

const fail = (message) => {
  console.error(message);
  process.exit(1);
};

// The cards claim "live on the App Store" and "N posts". Check both instead of
// trusting a string someone has to remember to edit after launch.
async function siteFacts() {
  const facts = {};
  try {
    const res = await fetch(`https://itunes.apple.com/lookup?id=${APP_ID}&country=us`);
    const body = await res.json();
    facts.appStore = body.resultCount > 0;
  } catch (error) {
    console.error(`app store lookup skipped: ${error.message}`);
  }
  try {
    const res = await fetch(BLOG, { headers: { 'user-agent': `${USERNAME}-profile-cards` } });
    const html = await res.text();
    const slugs = new Set([...html.matchAll(/href="\/blog\/([a-z0-9-]+)\.html"/g)].map(([, s]) => s));
    slugs.delete('index');
    if (slugs.size) facts.posts = slugs.size;
  } catch (error) {
    console.error(`blog count skipped: ${error.message}`);
  }
  return facts;
}

const res = await fetch(ENDPOINT, {
  headers: { accept: 'text/html', 'user-agent': `${USERNAME}-profile-heatmap` },
});
if (!res.ok) fail(`fetch failed: ${res.status} ${res.statusText}`);
const html = await res.text();

const attr = (tag, name) => tag.match(new RegExp(`\\b${name}="([^"]*)"`))?.[1];

const cells = [...html.matchAll(/<td\b[^>]*\bclass="[^"]*ContributionCalendar-day[^"]*"[^>]*>/g)].map(([tag]) => ({
  id: attr(tag, 'id'),
  date: attr(tag, 'data-date'),
  level: Number(attr(tag, 'data-level')),
}));
if (cells.length < 300) fail(`parsed only ${cells.length} day cells — GitHub markup changed?`);

const tooltips = new Map(
  [...html.matchAll(/<tool-tip\b[^>]*\bfor="([^"]+)"[^>]*>([^<]*)<\/tool-tip>/g)].map(([, id, text]) => [id, text.trim()]),
);

const parseCount = (text) => {
  const match = text.match(/^(\d[\d,]*|No) contributions?\b/);
  if (!match) return null;
  return match[1] === 'No' ? 0 : Number(match[1].replaceAll(',', ''));
};

const days = cells
  .map(({ id, date, level }) => {
    const count = parseCount(tooltips.get(id) ?? '');
    if (!date || !Number.isInteger(level) || count === null) {
      fail(`could not parse day ${id ?? '(no id)'}`);
    }
    return { date, level, count };
  })
  .sort((a, b) => a.date.localeCompare(b.date));

const total = days.reduce((sum, day) => sum + day.count, 0);

// GitHub's calendar ends today. A stale CDN copy or a half-rendered page would
// otherwise be committed as if it were current, quietly shrinking the graph.
const newest = days.at(-1).date;
const ageDays = (Date.now() - Date.parse(`${newest}T00:00:00Z`)) / 86_400_000;
if (ageDays > 2) fail(`calendar looks stale: newest day is ${newest} (${ageDays.toFixed(1)} days old)`);

let longestStreak = 0;
let run = 0;
for (const day of days) {
  run = day.count > 0 ? run + 1 : 0;
  longestStreak = Math.max(longestStreak, run);
}

let currentStreak = 0;
for (let i = days.length - 1; i >= 0; i--) {
  if (days[i].count === 0 && i === days.length - 1) continue;
  if (days[i].count === 0) break;
  currentStreak++;
}

let bestDay = days[0];
for (const day of days) if (day.count > bestDay.count) bestDay = day;

const payload = {
  username: USERNAME,
  total,
  stats: {
    currentStreak,
    longestStreak,
    bestDay: { date: bestDay.date, count: bestDay.count },
  },
  days,
};

await mkdir(new URL('../data/', import.meta.url), { recursive: true });
await writeFile(new URL('../data/contributions.json', import.meta.url), `${JSON.stringify(payload, null, 2)}\n`);

const facts = await siteFacts();
// A failed lookup must not overwrite what the last good run learned — otherwise
// the hero would quietly regress to "private beta" after the app ships.
const sitePath = new URL('../data/site.json', import.meta.url);
const previous = await readFile(sitePath, 'utf8').then(JSON.parse).catch(() => ({}));
await writeFile(sitePath, `${JSON.stringify({ ...previous, ...facts }, null, 2)}\n`);

console.log(`site: appStore=${facts.appStore} posts=${facts.posts ?? '?'}`);
console.log(
  `wrote ${days.length} days (${days[0].date} → ${days.at(-1).date}) · ${total} contributions · current ${currentStreak} · longest ${longestStreak} · best ${bestDay.count} on ${bestDay.date}`,
);
