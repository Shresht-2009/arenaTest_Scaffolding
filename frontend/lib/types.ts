/**
 * RIOS Frontend Types
 */

export interface CognitiveGenome {
  id: string;
  generation: number;
  parent_id: string | null;
  lineage: string[];
  planning_depth: number;
  verification_passes: number;
  reasoning_order: string;
  exploration_factor: number;
  compression_level: number;
  memory_retrieval_strategy: string;
  decomposition_style: string;
  critique_strength: number;
  reflection_depth: number;
  search_width: number;
  confidence_threshold: number;
  self_correction_frequency: number;
  abstraction_level: number;
  information_compression_ratio: number;
  temperature: number;
  max_tokens: number;
  fitness: number;
  fitness_history: number[];
  token_usage: number;
}

export interface ReasoningStep {
  id: string;
  phase: string;
  content: string;
  timestamp: number;
  confidence: number;
  tokens: number;
}

export interface GenerationEvent {
  generation: number;
  winner_id: string;
  winner_fitness: number;
  population_size: number;
  avg_fitness: number;
  best_fitness: number;
  complexity: number;
  improvement: boolean;
  timestamp: number;
  latency_ms: number;
}

export interface DashboardData {
  current_generation: number;
  current_genome: CognitiveGenome | null;
  genome_history: GenerationEvent[];
  fitness_score: number;
  reasoning_depth: number;
  compression_ratio: number;
  memory_usage: any;
  token_usage: {
    requests: number;
    tokens_in: number;
    tokens_out: number;
    total_tokens: number;
    estimated_cost: number;
    avg_latency_ms: number;
  };
  api_requests: number;
  latency: number;
  cost_estimate: number;
  recursive_depth: number;
  benchmark_results: any;
  evolution_timeline: GenerationEvent[];
  checkpoint_history: any[];
  best_answer: string | null;
  best_scaffold: string | null;
  reasoning_tree: ReasoningStep[];
}

export interface BenchmarkTask {
  id: string;
  family: string;
  difficulty: number;
  problem: string;
  solution: string;
}
