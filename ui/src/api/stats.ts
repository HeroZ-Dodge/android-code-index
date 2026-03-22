import client from './client'
import type { ProjectStats, StatsBreakdown } from '@/types'

export const getStats = (): Promise<ProjectStats> =>
  client.get('/stats').then((r) => r.data)

export const getStatsBreakdown = (): Promise<StatsBreakdown> =>
  client.get('/stats/breakdown').then((r) => r.data)
