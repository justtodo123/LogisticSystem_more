import request from './request'
import type {
  CapacityReport,
  CostReport,
  ExceptionReport,
  ReportOverview,
  SlaReport,
} from '@/types/report'

/** SLA 达成率报表 */
export async function getSlaReport(
  dateFrom?: string,
  dateTo?: string,
): Promise<SlaReport> {
  const { data } = await request.get<SlaReport>('/reports/sla', {
    params: { date_from: dateFrom, date_to: dateTo },
  })
  return data
}

/** 成本分析报表 */
export async function getCostReport(): Promise<CostReport> {
  const { data } = await request.get<CostReport>('/reports/cost')
  return data
}

/** 异常统计报表 */
export async function getExceptionReport(): Promise<ExceptionReport> {
  const { data } = await request.get<ExceptionReport>('/reports/exceptions')
  return data
}

/** 运力效率报表 */
export async function getCapacityReport(): Promise<CapacityReport> {
  const { data } = await request.get<CapacityReport>('/reports/capacity')
  return data
}

/** 报表汇总（Dashboard 一次拉取） */
export async function getReportOverview(
  dateFrom?: string,
  dateTo?: string,
): Promise<ReportOverview> {
  const { data } = await request.get<ReportOverview>('/reports/overview', {
    params: { date_from: dateFrom, date_to: dateTo },
  })
  return data
}
