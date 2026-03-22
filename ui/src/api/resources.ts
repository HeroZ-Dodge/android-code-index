import client from './client'

export const getLayouts = (params?: { name?: string; module?: string; view_id?: string; limit?: number }) =>
  client.get('/resources/layouts', { params }).then((r) => r.data)

export const getStrings = (params?: { key?: string; value?: string; module?: string; limit?: number }) =>
  client.get('/resources/strings', { params }).then((r) => r.data)

export const getColors = (params?: { name?: string; value?: string; module?: string; limit?: number }) =>
  client.get('/resources/colors', { params }).then((r) => r.data)

export const getDimens = (params?: { name?: string; value?: string; module?: string; limit?: number }) =>
  client.get('/resources/dimens', { params }).then((r) => r.data)

export const getStyles = (params?: { name?: string; module?: string; limit?: number }) =>
  client.get('/resources/styles', { params }).then((r) => r.data)

export const getManifestComponents = (params?: {
  name?: string
  component_type?: string
  module?: string
  limit?: number
}) => client.get('/manifest/components', { params }).then((r) => r.data)
