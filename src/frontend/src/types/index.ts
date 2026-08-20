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
  product_image?: string;
  alternate_images?: string[];
  actual_image?: string;
  documents?: Record<string, string>;
  confidence_score: number;
  confidence_breakdown: Record<string, number>;
  validation_flags: string[];
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
  overall_scores: {
    exact_match_rate: number;
    normalized_match_rate: number;
    average_levenshtein_similarity: number;
    average_bleu_score: number;
    average_rouge_l_f1: number;
    triplet_attribute_f1: number;
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
