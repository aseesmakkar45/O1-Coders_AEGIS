import numpy as np

class AttributionConfig:
    """
    Core Mathematical Parameters for the Shadow Controller Attribution Engine.
    Adjusting these safely morphs the behavior of the entire underlying topological calculation.
    """
    
    # 1. Graph Temporal Model
    # Graph is rebuilt from a pure sliding window (last 200 events) each tick.
    # No time-based decay is applied — edge weights are purely causal (gap-based).
    # This ensures zero historical leakage: only recent events influence attribution.

    # 2. Final Attribution Consensus Weighting (5-signal — closeness excluded from scoring)
    w_propagation = 0.30  # Propagation Score — Primary causal outgoing influence.
    beta = 0.30           # Betweenness Centrality — Structural bridge for lateral movement.
    w_centrality = 0.00   # Closeness Centrality — EXCLUDED: proximity ≠ control.
    alpha = 0.10          # PageRank — Downstream orchestration dominance.
    gamma = 0.10          # Behavioral Anomaly — IsolationForest telemetry fingerprint.
    delta = 0.05          # Normalized Frequency — General activity volume.
    dominance_boost = 0.05  # Tie-breaker for nodes dominant in both propagation and betweenness.

    # 3. Solver Constraints
    # Ensures deterministic mathematical convergence even when solving ultra-sparse isolated botnet chains.
    pr_alpha = 0.85
    pr_max_iter = 100
    pr_tol = 1e-06

def safe_normalize(raw_scores):
    """
    Guaranteed safe Min-Max normalization mapping [0, 1] without the risk of divide-by-zero crashes.
    :param raw_scores: array or list of raw algorithmic scoring floats.
    :return: standardized numpy array bounded cleanly within [0, 1].
    """
    if not len(raw_scores):
        return np.array([])
        
    raw = np.array(raw_scores, dtype=float)
    max_score = np.max(raw)
    min_score = np.min(raw)
    
    denom = (max_score - min_score) if (max_score - min_score) != 0 else 1e-6
    return (raw - min_score) / denom
