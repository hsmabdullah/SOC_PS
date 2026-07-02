/**
 * Deterministic mock dataset for the SOC dashboard.
 *
 * A seeded PRNG generates a stable population of alerts spanning 180 days;
 * every widget (KPIs, trends, breakdowns, table) is aggregated from that
 * single population, so all numbers on screen agree with each other —
 * exactly as they will once FastAPI serves the real data.
 */

import {
  ALERT_CATEGORIES,
  AlertCategory,
  AlertPage,
  AlertStatus,
  DashboardFilters,
  DashboardSummary,
  DateRange,
  Kpi,
  Severity,
  SEVERITIES,
  SocAlert,
  SystemHealth,
} from '../models/soc.models';

// ── Seeded PRNG (mulberry32) ─────────────────────────────────────────────────

function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pick<T>(rnd: () => number, items: readonly T[]): T {
  return items[Math.floor(rnd() * items.length)];
}

function weighted<T>(rnd: () => number, entries: [T, number][]): T {
  const total = entries.reduce((s, [, w]) => s + w, 0);
  let roll = rnd() * total;
  for (const [item, w] of entries) {
    roll -= w;
    if (roll <= 0) return item;
  }
  return entries[entries.length - 1][0];
}

// ── Alert population ─────────────────────────────────────────────────────────

const TITLES: Record<AlertCategory, string[]> = {
  Malware: [
    'Trojan signature detected on endpoint',
    'Ransomware behaviour blocked by EDR',
    'Suspicious binary executed from temp directory',
    'Known C2 beacon pattern observed',
  ],
  Phishing: [
    'Credential-harvesting email reported by user',
    'Spoofed executive domain in inbound mail',
    'Malicious attachment quarantined at gateway',
    'Mass phishing campaign targeting finance dept',
  ],
  'Intrusion Attempt': [
    'Multiple failed SSH logins from single source',
    'Port scan detected against DMZ segment',
    'Exploit attempt against public web server',
    'Brute-force attack on VPN concentrator',
  ],
  'Data Exfiltration': [
    'Unusual outbound transfer volume from file server',
    'Sensitive data pattern in outbound traffic',
    'Large upload to unsanctioned cloud storage',
    'Database dump copied to removable media',
  ],
  'Policy Violation': [
    'Unauthorized software installation detected',
    'Privileged account used outside change window',
    'USB mass-storage device connected on plant floor',
    'Shadow-IT SaaS access from corporate network',
  ],
  DDoS: [
    'Volumetric flood against dealer portal',
    'SYN flood mitigated at edge',
    'Application-layer flood on API gateway',
    'Amplification attack traffic observed',
  ],
};

const SOURCES: [string, string][] = [
  ['203.99.176.14', 'Karachi, PK'],
  ['91.242.218.90', 'Bucharest, RO'],
  ['45.155.204.7', 'Amsterdam, NL'],
  ['118.91.130.66', 'Singapore, SG'],
  ['185.220.101.34', 'Frankfurt, DE'],
  ['103.148.20.211', 'Lahore, PK'],
  ['64.62.197.152', 'Fremont, US'],
  ['180.178.94.19', 'Tokyo, JP'],
];

const ANALYSTS = ['A. Rehman', 'S. Khan', 'M. Iqbal', 'F. Ahmed', null, null];

const DAY_MS = 24 * 60 * 60 * 1000;
const SPAN_DAYS = 180;

/** Anchor "now" to the current hour so aggregates are stable within a session. */
function anchorNow(): number {
  const d = new Date();
  d.setMinutes(0, 0, 0);
  return d.getTime();
}

let population: SocAlert[] | null = null;
let populationAnchor = 0;

function getPopulation(): SocAlert[] {
  const anchor = anchorNow();
  if (population && populationAnchor === anchor) return population;

  const rnd = mulberry32(0x50c0);
  const alerts: SocAlert[] = [];
  const count = 4200;

  for (let i = 0; i < count; i++) {
    // Bias volume toward recent days so short ranges stay lively.
    const age = Math.pow(rnd(), 1.35) * SPAN_DAYS * DAY_MS;
    const ts = anchor - age;
    const severity = weighted<Severity>(rnd, [
      ['low', 38],
      ['medium', 32],
      ['high', 21],
      ['critical', 9],
    ]);
    const category = weighted<AlertCategory>(rnd, [
      ['Malware', 26],
      ['Phishing', 24],
      ['Intrusion Attempt', 20],
      ['Policy Violation', 14],
      ['Data Exfiltration', 9],
      ['DDoS', 7],
    ]);
    // Older alerts are far more likely to be closed out.
    const ageDays = age / DAY_MS;
    const resolvedBias = Math.min(0.92, 0.35 + ageDays * 0.05);
    const status = weighted<AlertStatus>(rnd, [
      ['resolved', resolvedBias * 100],
      ['contained', 12],
      ['investigating', 14],
      ['open', 16],
    ]);
    const [source, location] = pick(rnd, SOURCES);

    alerts.push({
      id: `AL-${(100000 + i).toString(36).toUpperCase()}`,
      timestamp: new Date(ts).toISOString(),
      title: pick(rnd, TITLES[category]),
      severity,
      category,
      source: `${source} · ${location}`,
      status,
      analyst: pick(rnd, ANALYSTS),
    });
  }

  alerts.sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1));
  population = alerts;
  populationAnchor = anchor;
  return alerts;
}

// ── Filtering & aggregation ──────────────────────────────────────────────────

const RANGE_MS: Record<DateRange, number> = {
  '24h': DAY_MS,
  '7d': 7 * DAY_MS,
  '30d': 30 * DAY_MS,
  '90d': 90 * DAY_MS,
};

function inWindow(a: SocAlert, from: number, to: number): boolean {
  const t = Date.parse(a.timestamp);
  return t >= from && t < to;
}

function matches(a: SocAlert, f: DashboardFilters): boolean {
  if (f.severities.length && !f.severities.includes(a.severity)) return false;
  if (f.categories.length && !(f.categories as string[]).includes(a.category)) return false;
  return true;
}

function slice(f: DashboardFilters, periodsBack = 0): SocAlert[] {
  const now = anchorNow();
  const span = RANGE_MS[f.range];
  const to = now - periodsBack * span;
  const from = to - span;
  return getPopulation().filter((a) => inWindow(a, from, to) && matches(a, f));
}

function bucketize(alerts: SocAlert[], f: DashboardFilters): { labels: string[]; total: number[]; resolved: number[] } {
  const now = anchorNow();
  const span = RANGE_MS[f.range];
  const bucketCount = f.range === '24h' ? 24 : f.range === '7d' ? 7 : f.range === '30d' ? 30 : 13;
  const bucketMs = span / bucketCount;
  const from = now - span;

  const total = new Array(bucketCount).fill(0);
  const resolved = new Array(bucketCount).fill(0);
  for (const a of alerts) {
    const idx = Math.min(bucketCount - 1, Math.floor((Date.parse(a.timestamp) - from) / bucketMs));
    total[idx]++;
    if (a.status === 'resolved') resolved[idx]++;
  }

  const hourFmt = new Intl.DateTimeFormat('en', { hour: 'numeric' });
  const dayFmt = new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' });
  const labels = Array.from({ length: bucketCount }, (_, i) => {
    const t = new Date(from + i * bucketMs);
    return f.range === '24h' ? hourFmt.format(t) : dayFmt.format(t);
  });

  return { labels, total, resolved };
}

function sparkline(alerts: SocAlert[], f: DashboardFilters, metric: (a: SocAlert) => boolean): number[] {
  const now = anchorNow();
  const span = RANGE_MS[f.range];
  const from = now - span;
  const points = new Array(12).fill(0);
  for (const a of alerts) {
    if (!metric(a)) continue;
    const idx = Math.min(11, Math.floor(((Date.parse(a.timestamp) - from) / span) * 12));
    points[idx]++;
  }
  return points;
}

function deltaPct(current: number, previous: number): number | null {
  if (!previous) return null;
  return Math.round(((current - previous) / previous) * 1000) / 10;
}

/** Pseudo-random-but-stable MTTR derived from an alert id. */
function mttrMinutes(a: SocAlert): number {
  let h = 0;
  for (const c of a.id) h = (h * 31 + c.charCodeAt(0)) | 0;
  const base = { critical: 45, high: 90, medium: 220, low: 420 }[a.severity];
  return base + (Math.abs(h) % base);
}

function meanMttr(alerts: SocAlert[]): number {
  const resolved = alerts.filter((a) => a.status === 'resolved');
  if (!resolved.length) return 0;
  return Math.round(resolved.reduce((s, a) => s + mttrMinutes(a), 0) / resolved.length);
}

// ── Public builders (the interceptor calls these) ───────────────────────────

export function buildSummary(f: DashboardFilters): DashboardSummary {
  const current = slice(f);
  const previous = slice(f, 1);
  const buckets = bucketize(current, f);

  const active = current.filter((a) => a.status === 'open' || a.status === 'investigating');
  const activePrev = previous.filter((a) => a.status === 'open' || a.status === 'investigating');
  const critical = current.filter((a) => a.severity === 'critical');
  const criticalPrev = previous.filter((a) => a.severity === 'critical');
  const resolvedRate = current.length ? Math.round((current.filter((a) => a.status === 'resolved').length / current.length) * 100) : 0;
  const resolvedRatePrev = previous.length ? Math.round((previous.filter((a) => a.status === 'resolved').length / previous.length) * 100) : 0;
  const mttr = meanMttr(current);
  const mttrPrev = meanMttr(previous);

  const kpis: Kpi[] = [
    {
      id: 'active',
      label: 'Active alerts',
      value: active.length,
      deltaPct: deltaPct(active.length, activePrev.length),
      goodWhen: 'down',
      trend: sparkline(current, f, (a) => a.status === 'open' || a.status === 'investigating'),
    },
    {
      id: 'critical',
      label: 'Critical incidents',
      value: critical.length,
      deltaPct: deltaPct(critical.length, criticalPrev.length),
      goodWhen: 'down',
      trend: sparkline(current, f, (a) => a.severity === 'critical'),
    },
    {
      id: 'mttr',
      label: 'Mean time to respond',
      value: mttr,
      unit: 'min',
      deltaPct: deltaPct(mttr, mttrPrev),
      goodWhen: 'down',
      trend: sparkline(current, f, (a) => a.status === 'resolved'),
    },
    {
      id: 'resolution',
      label: 'Resolution rate',
      value: resolvedRate,
      unit: '%',
      deltaPct: deltaPct(resolvedRate, resolvedRatePrev),
      goodWhen: 'up',
      trend: sparkline(current, f, (a) => a.status === 'resolved'),
    },
  ];

  const sevCount = (s: Severity) => current.filter((a) => a.severity === s).length;
  const catCount = (c: AlertCategory) => current.filter((a) => a.category === c).length;

  const sourceMap = new Map<string, { location: string; count: number }>();
  for (const a of current) {
    const [ip, location] = a.source.split(' · ');
    const entry = sourceMap.get(ip) ?? { location, count: 0 };
    entry.count++;
    sourceMap.set(ip, entry);
  }
  const topSources = [...sourceMap.entries()]
    .map(([source, v]) => ({ source, location: v.location, count: v.count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);

  const sysRnd = mulberry32(0x5e57 + anchorNow() / DAY_MS);
  const systems: SystemHealth[] = [
    { name: 'SIEM Cluster', state: 'operational' },
    { name: 'EDR Platform', state: 'operational' },
    { name: 'Perimeter Firewall', state: 'operational' },
    { name: 'Email Gateway', state: sysRnd() > 0.7 ? 'degraded' : 'operational' },
    { name: 'IDS / IPS Sensors', state: 'operational' },
    { name: 'Threat Intel Feed', state: sysRnd() > 0.85 ? 'down' : 'operational' },
  ].map((s) => ({
    ...s,
    state: s.state as SystemHealth['state'],
    uptimePct: s.state === 'operational' ? 99.5 + sysRnd() * 0.49 : s.state === 'degraded' ? 96 + sysRnd() * 2 : 82 + sysRnd() * 6,
    latencyMs: Math.round(8 + sysRnd() * 40),
  }));

  return {
    generatedAt: new Date().toISOString(),
    kpis,
    trend: {
      labels: buckets.labels,
      series: [
        { id: 'new', label: 'New alerts', points: buckets.total },
        { id: 'resolved', label: 'Resolved', points: buckets.resolved },
      ],
    },
    severities: SEVERITIES.map((severity) => ({ severity, count: sevCount(severity) })),
    categories: ALERT_CATEGORIES.map((category) => ({ category, count: catCount(category) })).filter((c) => c.count > 0),
    topSources,
    systems,
  };
}

export function buildAlertPage(f: DashboardFilters, limit: number): AlertPage {
  const current = slice(f);
  return { total: current.length, items: current.slice(0, limit) };
}
