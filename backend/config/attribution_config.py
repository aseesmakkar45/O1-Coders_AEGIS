import numpy as np

class AttributionConfig:
    """
    Core Mathematical Parameters for the Shadow Controller Attribution Engine.
    Adjusting these safely morphs the behavior of the entire underlying topological calculation.
    """
    
    # 1. Temporal Constraints
    # Increased half-life to 10 hours so edges never vanish and the graph accumulates!
    half_life_seconds = 36000 
    lambda_ = np.log(2) / half_life_seconds

    # 2. Final Attribution Consensus Weighting
    alpha = 0.4  # PageRank - Identifies heavily orchestrated Command hubs.
    beta = 0.3   # Betweenness Centrality - Identifies structural proxy bridges resolving internal logic.
    gamma = 0.2  # Behavioral Anomaly - Score synthesized from IsolationForest telemetry vector mappings.
    delta = 0.1  # Normalized Frequency - General activity bounds tracking degree connectivity.

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
