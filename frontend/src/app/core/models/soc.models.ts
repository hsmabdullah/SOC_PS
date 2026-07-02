/**
 * Domain models shared with the FastAPI layer.
 * These interfaces mirror the Pydantic response models of the backend —
 * keep field names in sync with `/api/v1` contracts.
 */

export type Severity = 'critical' | 'high' | 'medium' | 'low';

export type AlertStatus = 'open' | 'investigating' | 'contained' | 'resolved';

export type DateRange = '24h' | '7d' | '30d' | '90d';

export const SEVERITIES: Severity[] = ['critical', 'high', 'medium', 'low'];

export const ALERT_CATEGORIES = [
  'Malware',
  'Phishing',
  'Intrusion Attempt',
  'Data Exfiltration',
  'Policy Violation',
  'DDoS',
] as const;

export type AlertCategory = (typeof ALERT_CATEGORIES)[number];

export interface DashboardFilters {
  range: DateRange;
  severities: Severity[];   // empty = all
  categories: AlertCategory[]; // empty = all
}

export interface Kpi {
  id: string;
  label: string;
  value: number;
  unit?: string;            // e.g. '%', 'min'
  deltaPct: number | null;  // vs previous period, signed
  goodWhen: 'up' | 'down';  // direction that colors the delta green
  trend: number[];          // 12-point sparkline
}

export interface TrendSeries {
  labels: string[];
  series: {
    id: string;
    label: string;
    points: number[];
  }[];
}

export interface SeverityCount {
  severity: Severity;
  count: number;
}

export interface CategoryCount {
  // string (not AlertCategory): the live database may use category names
  // beyond the fixed filter list
  category: string;
  count: number;
}

export interface SourceCount {
  source: string;
  location: string;
  count: number;
}

export interface SystemHealth {
  name: string;
  state: 'operational' | 'degraded' | 'down';
  uptimePct: number;
  latencyMs: number;
}

export interface SocAlert {
  id: string;
  timestamp: string; // ISO 8601
  title: string;
  severity: Severity;
  category: string;
  source: string;
  status: AlertStatus;
  analyst: string | null;
}

/** Payload of GET /api/v1/dashboard/summary */
export interface DashboardSummary {
  generatedAt: string;
  kpis: Kpi[];
  trend: TrendSeries;
  severities: SeverityCount[];
  categories: CategoryCount[];
  topSources: SourceCount[];
  systems: SystemHealth[];
}

/** Payload of GET /api/v1/alerts */
export interface AlertPage {
  total: number;
  items: SocAlert[];
}
