export interface AttributeTriple {
  label: string;
  value: string;
  uom?: string;
}

export interface PhysicalDimensions {
  length?: string;
  length_uom?: string;
  height?: string;
  height_uom?: string;
  width?: string;
  width_uom?: string;
  weight?: string;
  weight_uom?: string;
  volume?: string;
  volume_uom?: string;
}

export interface RawProduct {
  mfg_part_num: string;
  part_desc: string;
  e1_brand?: string;
  unilog_brand?: string;
  dib_brand?: string;
  part_manuf?: string;
  row_id?: number;
}

export interface ProductListItem {
  id: string;
  row_id: number;
  part_number: string;
  sku: string;
  mfg_part_number: string;
  brand_name: string;
  manufacturer_name: string;
  classpath: string;
  product_name: string;
  dept: string;
  invoice_desc: string;
  invoice_desc_len: number;
  mobile_desc: string;
  mobile_desc_len: number;
  short_desc: string;
  confidence_score: number;
  status: 'Validated' | 'Enriched' | 'Flagged' | 'Draft';
  validation_flags: string[];
}

export interface ProductListResponse {
  items: ProductListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface EvidenceRecord {
  field_name: string;
  candidate_value?: string;
  normalized_value?: string;
  source_url?: string;
  source_type: 'manufacturer_page' | 'manufacturer_pdf' | 'supplier_input' | 'reference_dictionary' | 'manual_review' | string;
  source_title?: string;
  source_page_or_section?: string;
  evidence_excerpt?: string;
  extraction_method: 'deterministic_rule' | 'document_parser' | 'manual_review' | string;
  retrieved_at: string;
  confidence: number;
  verification_status: 'verified' | 'candidate' | 'rejected' | 'missing_evidence' | string;
  dictionary_identity?: string;
}

export interface ProductProvenanceSummary {
  total_fields_tracked: number;
  verified_fields_count: number;
  candidate_fields_count: number;
  missing_evidence_count: number;
  rejected_fields_count: number;
  verification_score: number;
  primary_sources_breakdown: Record<string, number>;
}

export interface FieldProvenance {
  field_name: string;
  source_url?: string;
  source_type: string;
  extraction_method: string;
  section_or_rule?: string;
  timestamp: string;
  confidence: number;
  verified: boolean;
}

export interface ProductDetail {
  id: string;
  row_id: number;
  part_number: string;
  sku: string;
  mfg_part_number: string;
  alternate_part_number?: string;
  upc?: string;
  ean?: string;
  gtin?: string;
  unspsc: string;
  raw: RawProduct;
  dept: string;
  class_name: string;
  fine: string;
  manufacturer_name: string;
  brand_name: string;
  trade_name?: string;
  mfr_url?: string;
  ref_urls?: string[];
  classpath: string;
  product_name: string;
  invoice_desc: string;
  invoice_desc_len: number;
  mobile_desc: string;
  mobile_desc_len: number;
  short_desc: string;
  long_desc1: string;
  retail_desc: string;
  marketing_description: string;
  item_features: string[];
  with_spec?: string;
  standard_approvals?: string;
  prop_65?: string;
  application?: string;
  includes?: string;
  attributes: AttributeTriple[];
  dimensions: PhysicalDimensions;
  warranty?: string;
  list_price?: string;
  selling_qty?: string;
  selling_uom?: string;
  country_of_origin?: string;
  product_image?: string;
  alternate_images?: string[];
  actual_image?: string;
  documents?: Record<string, string>;
  confidence_score: number;
  confidence_breakdown: Record<string, number>;
  validation_flags: string[];
  field_evidence?: Record<string, EvidenceRecord[]>;
  provenance_summary?: ProductProvenanceSummary;
  field_provenance?: Record<string, FieldProvenance>;
  status: string;
  delivery_columns?: Record<string, string>;
}

export interface CatalogStats {
  total_items: number;
  enriched_count: number;
  validated_count: number;
  flagged_count: number;
  draft_count: number;
  mean_confidence: number;
  median_confidence: number;
  invoice_compliance_pct: number;
  mobile_compliance_pct: number;
  lov_compliance_pct: number;
  schema_columns_count: number;
  status_counts: Record<string, number>;
  dept_counts: Record<string, number>;
  top_brands: Record<string, number>;
  sources_registered_count?: number;
  verified_fields_count?: number;
  candidate_fields_count?: number;
  unsupported_fields_withheld?: number;
}

export interface FilterOptionItem {
  label: string;
  value: string;
  count: number;
}

export interface FilterOptions {
  statuses: FilterOptionItem[];
  departments: FilterOptionItem[];
  brands: FilterOptionItem[];
}

export interface TransformRequest {
  part_desc: string;
  mfg_part_num?: string;
  e1_brand?: string;
  unilog_brand?: string;
  dib_brand?: string;
  part_manuf?: string;
  row_id?: number;
}

export interface PipelineStageOutput {
  stage_id: number;
  stage_name: string;
  description: string;
  duration_ms: number;
  output: Record<string, any>;
}

export interface TransformResponse {
  invoice_desc: string;
  invoice_desc_len: number;
  mobile_desc: string;
  mobile_desc_len: number;
  short_desc: string;
  long_desc1: string;
  retail_desc: string;
  marketing_description: string;
  brand_name: string;
  manufacturer_name: string;
  classpath: string;
  product_name: string;
  unspsc: string;
  item_features: string[];
  attributes: AttributeTriple[];
  dimensions: PhysicalDimensions;
  confidence_score: number;
  confidence_breakdown: Record<string, number>;
  validation_flags: string[];
  status: string;
  stages: PipelineStageOutput[];
  total_latency_ms: number;
  delivery_columns: Record<string, string>;
}

export interface PlaygroundPreset {
  id: string;
  name: string;
  category: string;
  mfg_part_num: string;
  part_desc: string;
  part_manuf: string;
  e1_brand?: string;
  unilog_brand?: string;
  dib_brand?: string;
}

export interface ReviewItem {
  id: string;
  row_id: number;
  part_number: string;
  mfg_part_num: string;
  brand_name: string;
  manufacturer_name: string;
  classpath: string;
  invoice_desc: string;
  mobile_desc: string;
  short_desc: string;
  confidence_score: number;
  status: string;
  anomaly_flags: string[];
  raw_part_desc: string;
  raw_manufacturer: string;
  provenance_summary?: ProductProvenanceSummary;
}

export interface ReviewQueueResponse {
  items: ReviewItem[];
  total: number;
  flagged_count: number;
  low_confidence_count: number;
}

export interface ColumnMetricResult {
  column_name: string;
  column_index: number;
  exact_match_rate: number;
  normalized_match_rate: number;
  levenshtein_similarity: number;
  non_null_rate_enriched: number;
  non_null_rate_expected: number;
  sample_expected?: string;
  sample_enriched?: string;
}

export interface DescriptionTierMetric {
  tier_name: string;
  exact_match_rate: number;
  normalized_match_rate: number;
  levenshtein_similarity: number;
  token_jaccard: number;
  token_cosine: number;
  bleu_1: number;
  bleu_2: number;
  bleu_4: number;
  rouge_1_f1: number;
  rouge_2_f1: number;
  rouge_l_f1: number;
  avg_length_enriched: number;
  avg_length_expected: number;
  length_compliance_rate: number;
}

export interface BenchmarkReport {
  timestamp: string;
  total_catalog_records: number;
  total_ground_truth_records: number;
  matched_benchmark_records: number;
  schema_column_count: number;
  is_ground_truth_calibrated?: boolean;
  calibration_note?: string;
  overall_scores: {
    exact_match_rate: number | null;
    normalized_match_rate: number | null;
    average_levenshtein_similarity: number | null;
    average_bleu_score: number | null;
    average_rouge_l_f1: number | null;
    triplet_attribute_f1: number | null;
    mean_confidence_score: number;
  };
  hard_rule_gates: {
    all_passed: boolean;
    total_gates: number;
    passed_gates_count: number;
    failed_gates_count: number;
    summary_table: Array<{
      Gate: string;
      Status: string;
      Compliance: string;
      Target: string;
      Evaluated: number;
      Violations: number;
    }>;
  };
  confidence_summary: {
    total_evaluated: number;
    mean_confidence: number;
    median_confidence: number;
    min_confidence: number;
    max_confidence: number;
    status_counts: Record<string, number>;
    needs_review_count: number;
    needs_review_pct: number;
    anomaly_code_counts: Record<string, number>;
  };
  description_tier_metrics: Record<string, DescriptionTierMetric>;
  column_metrics: ColumnMetricResult[];
  missing_fields_summary: Record<string, number>;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'specialist' | 'reviewer' | 'viewer';
  avatar_color: string;
  created_at: number;
}

export interface AuthResponse {
  token: string;
  token_type: string;
  user: User;
}

export interface AuditRecord {
  id: string;
  field_name: string;
  reviewer: string;
  timestamp: string;
  previous_value?: string;
  new_value?: string;
  action: 'edit' | 'approve' | 'reject' | 'mark_unknown' | string;
  reason: string;
}

export interface FieldReviewItem {
  field_name: string;
  display_label: string;
  raw_supplier_input?: string;
  candidate_value?: string;
  normalized_value?: string;
  source_citation?: string;
  source_excerpt?: string;
  source_url?: string;
  source_type: string;
  confidence: number;
  validation_flags: string[];
  verification_status: 'verified' | 'candidate' | 'rejected' | 'unknown' | 'missing_evidence' | string;
  dictionary_identity?: string;
  is_high_risk: boolean;
  is_resolved: boolean;
  audit_history: AuditRecord[];
}

export interface ProductFieldReview {
  product_id: string;
  row_id: number;
  mfg_part_number: string;
  brand_name: string;
  manufacturer_name: string;
  status: string;
  confidence_score: number;
  high_risk_unresolved_count: number;
  can_promote_to_validated: boolean;
  fields: FieldReviewItem[];
  audit_trail: AuditRecord[];
}

export interface FieldActionPayload {
  field_name: string;
  action: 'approve' | 'edit' | 'reject' | 'mark_unknown';
  new_value?: string;
  reason: string;
  reviewer_notes?: string;
}

export interface PromoteValidatedResponse {
  success: boolean;
  product_id: string;
  status: string;
  message: string;
  unresolved_high_risk_fields: string[];
}

export interface SourceRegistryEntry {
  source_id: string;
  url?: string;
  mpn: string;
  brand: string;
  manufacturer: string;
  source_type: string;
  retrieved_at: string;
  file_hash: string;
  source_status: 'ACTIVE' | 'UNAVAILABLE' | 'REJECTED_UNTRUSTED' | 'PENDING_REVIEW' | string;
  raw_file_path?: string;
  processed_file_path?: string;
  chunks_count: number;
  error_message?: string;
  title?: string;
}

export interface SourceRegistrationRequest {
  url?: string;
  mpn: string;
  brand: string;
  manufacturer: string;
  source_type?: string;
  title?: string;
  raw_content?: string;
}

export interface SourceRegistrationResponse {
  success: boolean;
  source_id: string;
  source_status: string;
  chunks_count: number;
  file_hash: string;
  message: string;
  validation_flags: string[];
}

export interface EvidenceChunk {
  chunk_id: string;
  source_id: string;
  mpn: string;
  brand: string;
  manufacturer: string;
  section_title: string;
  page_number?: number;
  text_content: string;
  key_value_specs: Record<string, string>;
  chunk_hash: string;
}

export interface ExtractedCandidate {
  field_name: string;
  candidate_value: string;
  normalized_value: string;
  source_url?: string;
  source_type: string;
  source_title: string;
  source_page_or_section: string;
  evidence_excerpt: string;
  extraction_method: string;
  retrieved_at: string;
  confidence: number;
  verification_status: string;
  dictionary_identity?: string;
  chunk_id?: string;
  model_name?: string;
  prompt_version?: string;
  source_hash?: string;
  conflicts?: string[];
  extraction_reason?: string;
  unresolved_reason?: string;
  ai_extraction_unavailable?: boolean;
}

export type BatchProductStatus = 'queued' | 'retrieving' | 'extracting' | 'validating' | 'review_required' | 'completed' | 'failed';
export type BatchJobOverallStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface ProductJobState {
  mpn: string;
  brand: string;
  manufacturer: string;
  status: BatchProductStatus;
  stage_message: string;
  started_at?: string;
  completed_at?: string;
  duration_ms: number;
  is_cached: boolean;
  extraction_method: string;
  verified_fields: number;
  candidate_fields: number;
  missing_evidence_fields: number;
  rejected_fields: number;
  conflicts_count: number;
  conflicts: string[];
  error_message?: string;
  retry_count: number;
  estimated_tokens: number;
}

export interface BatchTokenUsage {
  prompt_tokens: number;
  candidate_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

export interface BatchReport {
  job_id: string;
  status: BatchJobOverallStatus;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds: number;
  total_products: number;
  evidence_backed_products: number;
  processed_products: number;
  completed_products: number;
  review_required_products: number;
  failed_products: number;
  cache_hits: number;
  cache_misses: number;
  verified_fields: number;
  candidate_fields: number;
  missing_evidence_fields: number;
  rejected_fields: number;
  gemini_failures: number;
  token_usage: BatchTokenUsage;
  product_states: Record<string, ProductJobState>;
}

export interface BatchStartRequest {
  mpns?: string[];
  max_concurrency?: number;
  force_refresh?: boolean;
}

export interface CacheStats {
  total_entries: number;
  hits: number;
  misses: number;
  total_requests: number;
  hit_ratio_percent: number;
  tokens_saved_estimate: number;
  cost_saved_usd_estimate: number;
  file_size_bytes: number;
  cache_file_path: string;
}

export interface ProductTimelineEvent {
  id: string;
  timestamp: string;
  actor: string;
  role: string;
  event_type: 'AUDIT_LOG' | 'REVIEW_ACTION' | 'JOB_EVENT' | 'EVIDENCE_INGESTED' | string;
  action: string;
  field_name?: string;
  old_value?: string;
  new_value?: string;
  reason?: string;
  source_url?: string;
  request_id?: string;
}

export interface ProductTimelineResponse {
  product_id: string;
  mpn: string;
  total_events: number;
  timeline: ProductTimelineEvent[];
}

export interface ExportHistoryRecord {
  id: string;
  user_email: string;
  role?: string;
  schema_version: string;
  product_count: number;
  checksum_sha256: string;
  filters: Record<string, any>;
  created_at: number;
}

export interface ExportHistoryResponse {
  total_exports: number;
  exports: ExportHistoryRecord[];
}

export interface SystemHealthData {
  status: string;
  app: string;
  version: string;
  request_id: string;
  environment: string;
  database: {
    status: string;
    type: string;
    products_count: number;
  };
  gemini: {
    model: string;
    configured: boolean;
    schema_version: string;
    lov_version: string;
  };
  cache: {
    total_entries: number;
    hit_ratio_percent: number;
    cost_saved_usd: number;
  };
  catalog: {
    total_records: number;
    enriched: number;
    validated: number;
    flagged: number;
    mean_confidence: number;
  };
  hard_gates_compliant: boolean;
}


