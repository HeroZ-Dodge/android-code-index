import client from './client'
import type { SearchResult } from '@/types'

export const searchCode = (params: {
  keyword: string
  kind?: string
  module?: string
  use_tokens?: boolean
  limit?: number
  offset?: number
}): Promise<SearchResult> => client.get('/search/code', { params }).then((r) => r.data)

export const searchResource = (params: {
  keyword: string
  kind?: string
  module?: string
  use_tokens?: boolean
  limit?: number
  offset?: number
}): Promise<SearchResult> => client.get('/search/resource', { params }).then((r) => r.data)
