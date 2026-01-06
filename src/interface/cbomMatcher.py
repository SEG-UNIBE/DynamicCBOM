"""CBOM asset matching module.

This module provides functionality to match cryptographic assets between two
CycloneDX Bill of Materials (CBOM) documents using similarity metrics and the
Hungarian algorithm for optimal matching.
"""

from typing import List, Dict, Tuple
import numpy as np
from scipy.optimize import linear_sum_assignment
from thefuzz import fuzz


class CBOMMatcher:
    """Matches assets between target and ground-truth CBOM documents.

    Uses fuzzy string matching for names and Jaccard similarity for crypto
    functions, combined with exact matching for cryptographic primitives and
    parameter sets. Employs the Hungarian algorithm for optimal bipartite matching.
    """

    def __init__(self):
        """Initialize the CBOMMatcher."""
        pass

    def _print_matches(self, matches: List[Dict], gt: List[Dict], target: List[Dict]) -> None:
        """Print formatted matching results for debugging.

        Args:
            matches: List of match dictionaries containing similarity scores.
            gt: Ground truth asset list.
            target: Target asset list to be matched.
        """
        for match in matches:
            bom_ref_gt = match["gt_id"]
            bom_ref_target = match.get("target_id")
            gt_name = next((a["name"] for a in gt if a["bom-ref"] == bom_ref_gt), "Unknown")
            target_name = next((a["name"] for a in target if a["bom-ref"] == bom_ref_target), "None") if bom_ref_target else "None"
            similarity = match["similarity"]
            print(f"GT: ({gt_name}) <-> Target: ({target_name}) | Similarity: {similarity:.2f}")

    def _jaccard(self, a: List[str], b: List[str]) -> float:
        """Calculate Jaccard similarity between two lists.

        Args:
            a: First list of strings.
            b: Second list of strings.

        Returns:
            Jaccard similarity score between 0.0 and 1.0.
        """
        sa, sb = set(a), set(b)
        if not sa and not sb:
            return 1.0
        inter = len(sa & sb)
        union = len(sa | sb)
        return inter / union if union else 0.0

    def _asset_similarity(self, a: Dict, b: Dict) -> float:
        """Calculate similarity score between two cryptographic assets.

        Combines multiple similarity metrics:
        - Name similarity using token-sort fuzzy matching (50% weight)
        - Primitive exact match bonus (50% weight)

        Args:
            a: First asset dictionary.
            b: Second asset dictionary.

        Returns:
            Combined similarity score between 0.0 and 1.0.
        """
        # 1) Name similarity using token-sort fuzzy matching
        name_sim = fuzz.token_sort_ratio(a["name"], b["name"]) / 100.0

        # 2) Cryptographic primitive exact match (binary)
        a_primitive = a.get("cryptoProperties", {}).get("algorithmProperties", {}).get("primitive")
        b_primitive = b.get("cryptoProperties", {}).get("algorithmProperties", {}).get("primitive")
        prim_sim = 1.0 if a_primitive == b_primitive else 0.0

        # Weighted combination (tune these weights as needed)
        return 0.5 * name_sim + 0.5 * prim_sim

    def _build_cost_matrix(self, gt: List[Dict], target: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Build cost matrix for the Hungarian algorithm.

        Creates a square cost matrix (with padding if needed) where each cell
        represents the dissimilarity (1 - similarity) between two assets.

        Args:
            gt: Ground truth asset list.
            target: Target asset list.

        Returns:
            Tuple of (cost matrix, similarity matrix, size array).
        """
        n, m = len(gt), len(target)
        size = max(n, m)
        sim = np.zeros((size, size))

        for i in range(n):
            for j in range(m):
                sim[i, j] = self._asset_similarity(gt[i], target[j])

        # Convert similarities to costs (1 - similarity)
        # Padded cells remain 0 similarity, thus cost is 1.0
        cost = 1.0 - sim
        return cost, sim, np.arange(size)

    def match_assets(
        self, gt: List[Dict], target: List[Dict], threshold: float = 0.6
    ) -> Tuple[List[Dict], float, float, float]:
        """Match assets from target CBOM to ground truth CBOM.

        Uses the Hungarian algorithm to find the optimal bipartite matching,
        then filters matches by similarity threshold.

        Args:
            gt: List of ground truth assets.
            target: List of target assets to match.
            threshold: Minimum similarity score (0.0-1.0) for a valid match.

        Returns:
            Tuple containing:
            - matches: List of matched assets with similarity scores and metadata.
            - precision: Precision of the matching (0.0-1.0).
            - recall: Recall of the matching (0.0-1.0).
            - f1_score: Harmonic mean of precision and recall (0.0-1.0).
        """
        cost, sim, _ = self._build_cost_matrix(gt, target)
        row_ind, col_ind = linear_sum_assignment(cost)

        matches = []
        used_target = set()

        for i, j in zip(row_ind, col_ind):
            if i < len(gt) and j < len(target):
                s = sim[i, j]
                if s >= threshold:
                    matches.append({
                        "gt_id": gt[i]["bom-ref"],
                        "target_id": target[j]["bom-ref"],
                        "similarity": float(s)
                    })
                    used_target.add(j)
                else:
                    # Below threshold: treat as false negative for ground truth
                    matches.append({
                        "gt_id": gt[i]["bom-ref"],
                        "target_id": None,
                        "similarity": float(s),
                        "note": "no good match (FN)"
                    })

        self._print_matches(matches, gt, target)

        # Calculate precision, recall, and F1 score
        true_positives = len(matches) - sum(1 for match in matches if match.get("target_id") is None)
        false_negatives = len(gt) - true_positives
        false_positives = len(target) - len(used_target)
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return matches, precision, recall, f1_score
