export type SymbolKind =
  | 'class'
  | 'interface'
  | 'object'
  | 'function'
  | 'constructor'
  | 'property'
  | 'layout'
  | 'style'
  | 'manifest_component'
  | 'drawable'

export interface Symbol {
  id: number
  name: string
  qualified_name: string
  kind: SymbolKind
  module: string
  file_path: string
  source_set: 'sdk' | 'impl' | 'resource' | 'config'
  line_number: number | null
  signature: string | null
  visibility: 'public' | 'private' | 'protected' | 'internal' | 'package' | null
  is_abstract: 0 | 1
  is_override: 0 | 1
  parent_class: string | null
  interfaces: string | null
  annotations: string | null
  return_type: string | null
  parameters: string | null
  resource_value: string | null
  extra: string | null
  src_code: string | null
}

export interface SearchResult {
  total: number
  items: Symbol[]
}

export interface ProjectStats {
  total_files: number
  total_symbols: number
  modules: number
  last_indexed: string | null
  parse_failures: number
  component_dep_count: number
  project_dep_count: number
}

export interface StatsBreakdown {
  by_kind: Record<string, number>
  by_language: Record<string, number>
  module_ranking: { module: string; symbol_count: number }[]
}

export interface ModuleListItem {
  module: string
  file_count: number
  symbol_count: number
  parse_failures: number
}

export interface ModuleOverview {
  module: string
  sdk_classes: number
  impl_classes: number
  interfaces: number
  functions: number
  files: number
}

export interface DirectDep {
  depends_on: string
  syntax: 'component' | 'project'
  scope: string
}

export interface ModuleDeps {
  sdk_deps: DirectDep[]
  impl_deps: DirectDep[]
}

export interface ModuleFile {
  file_path: string
  file_type: 'kotlin' | 'java' | 'xml' | 'gradle'
  source_set: string
  symbol_count: number
}

export interface ModuleFileGroup {
  dir_path: string
  files: ModuleFile[]
}
