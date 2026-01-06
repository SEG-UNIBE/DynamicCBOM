from typing import List, Dict, Tuple
import numpy as np
from scipy.optimize import linear_sum_assignment
from thefuzz import fuzz

class CBOMMatcher:
    def __init__(self):
        pass
    
    def _print_matches(self, matches: List[Dict], gt: List[Dict], target: List[Dict]) -> None:
        for match in matches:
            bom_ref_gt = match["gt_id"]
            bom_ref_target = match.get("target_id")
            gt_name = next((a["name"] for a in gt if a["bom-ref"] == bom_ref_gt), "Unknown")
            target_name = next((a["name"] for a in target if a["bom-ref"] == bom_ref_target), "None") if bom_ref_target else "None"
            similarity = match["similarity"]
            print(f"GT: ({gt_name}) <-> Target: ({target_name}) | Similarity: {similarity:.2f}")
            
    def _jaccard(self, a: List[str], b: List[str]) -> float:
        sa, sb = set(a), set(b)
        if not sa and not sb:
            return 1.0
        inter = len(sa & sb)
        union = len(sa | sb)
        return inter / union if union else 0.0

    def _asset_similarity(self, a: Dict, b: Dict) -> float:
        # 1) name similarity
        name_sim = fuzz.token_sort_ratio(a["name"], b["name"]) / 100.0
    

        # 2) primitive (exact match bonus)
        prim_sim = 1.0 if a.get('cryptoProperties').get('algorithmProperties').get('primitive') == b.get('cryptoProperties').get('algorithmProperties').get('primitive') else 0.0

        # 3) crypto functions overlap
        func_sim = self._jaccard(a.get('cryptoProperties').get('algorithmProperties').get('cryptoFunctions', []), b.get('cryptoProperties').get('algorithmProperties').get('cryptoFunctions', []))

        # 4) parameter set / key size / curve etc.
        param_sim = 1.0 if a.get('cryptoProperties').get('algorithmProperties').get('parameterSetIdentifier') == b.get('cryptoProperties').get('algorithmProperties').get('parameterSetIdentifier') else 0.0

        # weighted sum – tune these weights for thesis
        return (
            0.5 * name_sim +
            0.5 * prim_sim
        )

    def _build_cost_matrix(self, gt: List[Dict], target: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        n, m = len(gt), len(target)
        size = max(n, m)
        sim = np.zeros((size, size))

        for i in range(n):
            for j in range(m):
                sim[i, j] = self._asset_similarity(gt[i], target[j])

        # similarities for padded cells remain 0 (i.e. cost 1)
        cost = 1.0 - sim
        return cost, sim, np.arange(size)

    def match_assets(self, gt: List[Dict], target: List[Dict], threshold: float = 0.6) -> Tuple[List[Dict], float, float, float]:
        """ Match assets from target CBOM to ground truth CBOM using Hungarian algorithm.
        Args:
            gt (List[Dict]): List of ground truth assets.
            target (List[Dict]): List of target assets to match.
            threshold (float): Similarity threshold for a valid match.
        Returns:
            matches (List[Dict]): List of matched assets with similarity scores.
            precision (float): Precision of the matching.
            recall (float): Recall of the matching.
            f1_score (float): F1 score of the matching.
        """
        cost, sim, _ = self._build_cost_matrix(gt, target)
        row_ind, col_ind = linear_sum_assignment(cost)

        matches = []
        used_target = set()
        # print(f"zip(row_ind, col_ind): {list(zip(row_ind, col_ind))}")
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
                    # below threshold -> treat as miss for gt[i]
                    matches.append({
                        "gt_id": gt[i]["bom-ref"],
                        "target_id": None,
                        "similarity": float(s),
                        "note": "no good match (FN)"
                    })

        self._print_matches(matches, gt, target)
        # Any target asset not in used_target is a FP
        # false_positives = [
        #     target[j]["id"] for j in range(len(target)) if j not in used_target
        # ]
        
        # compute precision, recall, f1_score
        true_positives = len(matches) - sum(1 for match in matches if match.get("target_id") is None)
        false_negatives = len(gt) - true_positives
        false_positives = len(target) - len(used_target)
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        return matches, precision, recall, f1_score
