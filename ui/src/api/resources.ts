import client from './client'

export const getLayouts = (params?: { name?: string; module?: string; limit?: number }) =>
  client.get('/resources/layouts', { params }).then((r) => r.data)

export const getStyles = (params?: { name?: string; module?: string; limit?: number }) =>
  client.get('/resources/styles', { params }).then((r) => r.data)

export const getDrawables = (params?: { name?: string; module?: string; limit?: number }) =>
  client.get('/resources/drawables', { params }).then((r) => r.data)

export const getManifestComponents = (params?: {
  name?: string
  component_type?: string
  module?: string
  limit?: number
}) => client.get('/manifest/components', { params }).then((r) => r.data)
