import client from './client'
import type { SearchResult } from '@/types'

export const search = (params: {
  keyword: string
  kind?: string
  module?: string
  limit?: number
  offset?: number
}): Promise<SearchResult> => client.get('/search', { params }).then((r) => r.data)
