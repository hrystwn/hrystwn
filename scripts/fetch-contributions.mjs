import { mkdir, writeFile } from 'node:fs/promises';

const USERNAME = 'hrystwn';
const ENDPOINT = `https://github.com/users/${USERNAME}/contributions`;

const fail = (message) => {
  console.error(message);
  process.exit(1);
};

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

console.log(
  `wrote ${days.length} days (${days[0].date} → ${days.at(-1).date}) · ${total} contributions · current ${currentStreak} · longest ${longestStreak} · best ${bestDay.count} on ${bestDay.date}`,
);
