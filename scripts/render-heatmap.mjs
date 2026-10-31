import { readFile, writeFile } from 'node:fs/promises';

const PALETTE = ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353'];
const DAY_MS = 86400000;
const W = 860;
const H = 216;
const CELL = 11;
const GAP = 4;
const PITCH = CELL + GAP;
const GRID_X = 46;
const GRID_Y = 64;

const data = JSON.parse(await readFile(new URL('../data/contributions.json', import.meta.url), 'utf8'));
const { username, total, stats, days } = data;

const first = new Date(`${days[0].date}T00:00:00Z`);
const last = new Date(`${days.at(-1).date}T00:00:00Z`);
const start = new Date(first.getTime() - first.getUTCDay() * DAY_MS);
const cols = Math.floor((last - start) / (7 * DAY_MS)) + 1;
if (cols < 50 || cols > 54) throw new Error(`unexpected week count: ${cols}`);

const colOf = (date) =>
  Math.floor(Math.round((Date.parse(`${date}T00:00:00Z`) - start.getTime()) / DAY_MS) / 7);

const cells = days
  .map((day) => {
    const offset = Math.round((Date.parse(`${day.date}T00:00:00Z`) - start.getTime()) / DAY_MS);
    const col = Math.floor(offset / 7);
    const row = offset % 7;
    const level = Math.min(Math.max(day.level, 0), 4);
    const delay = (col + row) * 12;
    return `<rect class="c" x="${GRID_X + col * PITCH}" y="${GRID_Y + row * PITCH}" width="${CELL}" height="${CELL}" rx="2.5" fill="${PALETTE[level]}" style="animation-delay:${delay}ms"/>`;
  })
  .join('\n    ');

const monthLabels = days
  .filter((day) => day.date.endsWith('-01'))
  .map((day) => {
    const label = new Date(`${day.date}T00:00:00Z`).toLocaleDateString('en-US', {
      month: 'short',
      timeZone: 'UTC',
    });
    return `<text x="${GRID_X + colOf(day.date) * PITCH}" y="56" fill="#8b949e" font-size="11">${label}</text>`;
  })
  .join('\n    ');

const dayLabels = [
  [1, 'Mon'],
  [3, 'Wed'],
  [5, 'Fri'],
]
  .map(
    ([row, label]) =>
      `<text x="${GRID_X - 8}" y="${GRID_Y + row * PITCH + 9}" text-anchor="end" fill="#8b949e" font-size="10">${label}</text>`,
  )
  .join('\n    ');

const legend = PALETTE.map(
  (color, i) => `<rect x="${733 + i * (CELL + GAP)}" y="15" width="${CELL}" height="${CELL}" rx="2.5" fill="${color}"/>`,
).join('');

const bestDate = new Date(`${stats.bestDay.date}T00:00:00Z`).toLocaleDateString('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  timeZone: 'UTC',
});

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="title desc">
  <title id="title">${username} contribution heatmap</title>
  <desc id="desc">${total} contributions in the last year, ${stats.currentStreak}-day current streak, ${stats.longestStreak}-day longest streak.</desc>
  <style>
    text { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
    .c { animation: reveal .45s cubic-bezier(.2, .7, .3, 1) both; }
    @keyframes reveal { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
    @media (prefers-reduced-motion: reduce) { .c { animation: none; } }
  </style>
  <rect x="0.5" y="0.5" width="${W - 1}" height="${H - 1}" rx="12" fill="#0d1117" stroke="#30363d"/>
  <circle cx="20" cy="20" r="5" fill="#ff5f56"/>
  <circle cx="36" cy="20" r="5" fill="#ffbd2e"/>
  <circle cx="52" cy="20" r="5" fill="#27c93f"/>
  <text x="68" y="25" fill="#8b949e" font-size="12">${username}@github: ~/contributions</text>
  <line x1="1" y1="38" x2="${W - 1}" y2="38" stroke="#30363d"/>
  <text x="725" y="24" text-anchor="end" fill="#8b949e" font-size="11">Less</text>
  ${legend}
  <text x="810" y="24" fill="#8b949e" font-size="11">More</text>
  ${monthLabels}
  ${dayLabels}
  <g>
    ${cells}
  </g>
  <text x="${GRID_X}" y="194" font-size="12"><tspan fill="#e6edf3" font-weight="600">${total.toLocaleString('en-US')}</tspan><tspan fill="#8b949e"> contributions in the last year · streak ${stats.currentStreak}d · longest ${stats.longestStreak}d · best ${stats.bestDay.count} (${bestDate})</tspan></text>
</svg>
`;

await writeFile(new URL('../contrib-heatmap.svg', import.meta.url), svg);
console.log(`wrote contrib-heatmap.svg · ${days.length} days · ${cols} weeks · ${total} contributions`);
