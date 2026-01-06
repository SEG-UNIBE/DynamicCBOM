import numpy as np
import matplotlib.pyplot as plt
from interface.config import settings
import json
from thefuzz import fuzz
from interface.cbomMatcher import CBOMMatcher


class ChartGenerator:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        # -------------------------------
        # Global styling (rcParams)
        # -------------------------------
        plt.rcParams.update({
            "figure.dpi": 300,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "font.family": "serif",
            "font.size": 9,
            "axes.edgecolor": "#333333",
            "axes.linewidth": 0.8,
            "xtick.color": "#333333",
            "ytick.color": "#333333",
        })
    
    def _parse_cbom(self, cbom_path: str) -> dict:
        """ Parse the CBOM JSON file
        Args:
            cbom_path (str): Path to the CBOM JSON file.
        Returns:
            cbom (list): List of CBOM components.
        """
        with open(cbom_path, 'r') as f:
            cbom = json.load(f)
        cbom = [component for component in cbom.get("components", []) if component.get("cryptoProperties").get("assetType") == "algorithm"]
        return cbom
    
    
    def _compare_with_ground_truth(self, cbom: list, gt: list) -> tuple:
        """ Compare the given CBOM with ground truth CBOM and compute precision, recall, F1-score.
        Args:
            cbom (list): The CBOM components to evaluate.
            gt (list): The ground truth CBOM components.
        Returns:
            precision (float)
            recall (float)
            f1_score (float)
        """
        matcher = CBOMMatcher()
        matches, precision, recall, f1_score = matcher.match_assets(
            gt=gt,
            target=cbom,
            threshold=0.6
        )
        return precision * 100, recall * 100, f1_score * 100
    
    def _get_asymmetric_assets(self, cbom: list) -> list:
        return [
            asset for asset in cbom if asset.get('cryptoProperties').get('algorithmProperties').get('primitive') in settings.primitive_mapping.asymmetric
        ]
    
    def _get_symmetric_assets(self, cbom: list) -> list:
        return [
            asset for asset in cbom if asset.get('cryptoProperties').get('algorithmProperties').get('primitive') in settings.primitive_mapping.symmetric
        ]
    
    def _get_hashing_assets(self, cbom: list) -> list:
        return [
            asset for asset in cbom if asset.get('cryptoProperties').get('algorithmProperties').get('primitive') in settings.primitive_mapping.hashing
        ]

    def _get_number_of_assets(self, cbom: list) -> int:
        num_of_total_assets = len(cbom)
        num_of_asymmetric_assets = len(self._get_asymmetric_assets(cbom))
        num_of_symmetric_assets = len(self._get_symmetric_assets(cbom))
        num_of_hashing_assets = len(self._get_hashing_assets(cbom))
        return num_of_total_assets, num_of_asymmetric_assets, num_of_symmetric_assets, num_of_hashing_assets

    def generate_singular(self, gt_path: str, dyn_path: str, output_path: str):
        """
        Generate two charts:
        1. compare the number of assets between dyn-cbom and ground truth
        2. show the prec/recall/f1-score
        """
        gt_cbom = self._parse_cbom(gt_path)
        dyn_cbom = self._parse_cbom(dyn_path)
        
        fig, ax = plt.subplots(1,2, figsize=(7,3))
        
        x = np.arange(4)
        
        hatch_patterns = settings.hatch_patterns # define hatch patterns
        width = settings.bar_width  # the width of the bars
        facecolors = settings.facecolors  # list of colors for the bars
        singular_facecolors = settings.singular_facecolors
        edgecolor = settings.edgecolor    # edge color for the 
        
        gt_cbom_total = gt_cbom
        gt_cbom_asym = self._get_asymmetric_assets(gt_cbom)
        gt_cbom_sym = self._get_symmetric_assets(gt_cbom)
        gt_cbom_hash = self._get_hashing_assets(gt_cbom)
        
        
        dyn_cbom_total = dyn_cbom
        dyn_cbom_asym = self._get_asymmetric_assets(dyn_cbom)
        dyn_cbom_sym = self._get_symmetric_assets(dyn_cbom)
        dyn_cbom_hash = self._get_hashing_assets(dyn_cbom)
        
        
        prec_total, recall_total, f1_score_total = self._compare_with_ground_truth(dyn_cbom_total, gt_cbom_total)
        prec_asym, recall_asym, f1_score_asym = self._compare_with_ground_truth(dyn_cbom_asym, gt_cbom_asym)
        prec_sym, recall_sym, f1_score_sym = self._compare_with_ground_truth(dyn_cbom_sym, gt_cbom_sym)
        prec_hash, recall_hash, f1_score_hash = self._compare_with_ground_truth(dyn_cbom_hash, gt_cbom_hash)
        
        prec = np.array([prec_total, prec_asym, prec_sym, prec_hash])
        recall = np.array([recall_total, recall_asym, recall_sym, recall_hash])
        f1_score = np.array([f1_score_total, f1_score_asym, f1_score_sym, f1_score_hash])
        
        # create the first chart
        bars_gt = ax[0].bar(
            x - width/2,
            np.array(self._get_number_of_assets(gt_cbom_total)),
            width,
            label="Ground Truth",
            facecolor=facecolors[0],
            edgecolor=edgecolor,
            hatch=hatch_patterns[0],
        )
        bars_dyn = ax[0].bar(
            x + width/2,
            np.array(self._get_number_of_assets(dyn_cbom_total)),
            width,
            label="Dynamic CBOM",
            facecolor=facecolors[1],
            edgecolor=edgecolor,
            hatch=hatch_patterns[1],
        )
        
        # create the second chart
        bars_prec = ax[1].bar(
            x - width,
            prec,
            width,
            label="Precision",
            facecolor=singular_facecolors[0],
            edgecolor=edgecolor,
            hatch=hatch_patterns[0]
        )
        bars_recall = ax[1].bar(
            x,
            recall,
            width,
            label="Recall",
            facecolor=singular_facecolors[1],
            edgecolor=edgecolor,
            hatch=hatch_patterns[1]
        )
        bars_f1 = ax[1].bar(
            x + width,
            f1_score,
            width,
            label="F1 Score",
            facecolor=singular_facecolors[2],
            edgecolor=edgecolor,
            hatch=hatch_patterns[2]
        )
        
        
        

        # -------------------------------
        # Axes & grid
        # -------------------------------
        ax[0].set_ylabel("No. of Assets")
        ax[0].set_xticks(x)
        ax[0].set_xticklabels(["Total", "Asym", "Sym", "Hash"], rotation=0)
        ax[1].set_ylabel("Score (%)")
        ax[1].set_xticks(x)
        ax[1].set_xticklabels(["Total", "Asym", "Sym", "Hash"], rotation=0)
        
        # light dashed lines, both x and y, behind the bars
        for i in range(2):
            ax[i].grid(True, axis="y", which="major",
                    linestyle="--", linewidth=0.5, color="0.75", alpha=0.8)
            ax[i].grid(True, axis="x", which="major",
                    linestyle="--", linewidth=0.5, color="0.85", alpha=0.8)
            ax[i].set_axisbelow(True)

            # Full frame box with thin dark-grey spines
            for spine in ax[i].spines.values():
                spine.set_visible(True)
                spine.set_linewidth(0.8)
                spine.set_color("#4d4d4d")

        # -------------------------------
        # Value labels on bars
        # -------------------------------
        ax[0].bar_label(bars_gt, padding=2, fontsize=6, fmt="%.0f")
        ax[0].bar_label(bars_dyn, padding=2, fontsize=6, fmt="%.0f")
        ax[1].bar_label(bars_prec, padding=2, fontsize=6, fmt="%.0f")
        ax[1].bar_label(bars_recall, padding=2, fontsize=6, fmt="%.0f")
        ax[1].bar_label(bars_f1, padding=2, fontsize=6, fmt="%.0f")
        
        max_group_0 = max(
            max(self._get_number_of_assets(gt_cbom_total)),
            max(self._get_number_of_assets(dyn_cbom_total))
        )
        ax[0].set_ylim(0, max_group_0 * 1.15)
        max_group_1 = max(
            prec.max(),
            recall.max(),
            f1_score.max()
        )
        ax[1].set_ylim(0, max_group_1 * 1.15)
        
        
        fig.legend(
            frameon=False,
            ncol=3,
            bbox_to_anchor=(0.5, 1.02),
            loc="upper center",
            borderpad=0.3,
            handlelength=1.6,
        )
        fig.tight_layout(rect=[0, 0, 1, 0.91])

        fig.savefig(output_path, bbox_inches="tight")
        
    
        
    
    
    def generate_comparisons(
        self, 
        gt_path: str, 
        dyn_path: str, 
        ibm_path: str,
        output_path: str
    ):
        gt_cbom = self._parse_cbom(gt_path)
        dyn_cbom = self._parse_cbom(dyn_path)
        ibm_cbom = self._parse_cbom(ibm_path)
        
        
        fig, ax = plt.subplots(2,2)
        self._generate_comparison_of_3(
            np.array(self._get_number_of_assets(gt_cbom)),
            np.array(self._get_number_of_assets(dyn_cbom)),
            np.array(self._get_number_of_assets(ibm_cbom)),
            ax[0,0],
            ["Total", "Asym", "Sym", "Hash"],
            "No. of Assets"
        )
        print("Comparing Dynamic CBOM with Ground Truth:")
        dyn_precision, dyn_recall, dyn_f1 = self._compare_with_ground_truth(dyn_cbom, gt_cbom)
        print("Comparing IBM cbomkit CBOM with Ground Truth:")
        ibm_precision, ibm_recall, ibm_f1 = self._compare_with_ground_truth(ibm_cbom, gt_cbom)
        print("finished comparisons.\n")
        asym_dyn_precision, asym_dyn_recall, asym_dyn_f1 = self._compare_with_ground_truth(
            self._get_asymmetric_assets(dyn_cbom),
            self._get_asymmetric_assets(gt_cbom)
        )
        asym_ibm_precision, asym_ibm_recall, asym_ibm_f1 = self._compare_with_ground_truth(
            self._get_asymmetric_assets(ibm_cbom),
            self._get_asymmetric_assets(gt_cbom)
        )
        sym_dyn_precision, sym_dyn_recall, sym_dyn_f1 = self._compare_with_ground_truth(
            self._get_symmetric_assets(dyn_cbom),
            self._get_symmetric_assets(gt_cbom)
        )
        sym_ibm_precision, sym_ibm_recall, sym_ibm_f1 = self._compare_with_ground_truth(
            self._get_symmetric_assets(ibm_cbom),
            self._get_symmetric_assets(gt_cbom)
        )
        hash_dyn_precision, hash_dyn_recall, hash_dyn_f1 = self._compare_with_ground_truth(
            self._get_hashing_assets(dyn_cbom),
            self._get_hashing_assets(gt_cbom)
        )
        hash_ibm_precision, hash_ibm_recall, hash_ibm_f1 = self._compare_with_ground_truth(
            self._get_hashing_assets(ibm_cbom),
            self._get_hashing_assets(gt_cbom)
        )
            
        self._generate_comparison_of_2(
            np.array([dyn_precision, asym_dyn_precision, sym_dyn_precision, hash_dyn_precision]),
            np.array([ibm_precision, asym_ibm_precision, sym_ibm_precision, hash_ibm_precision]),
            ax[0,1],
            ["Overall", "Asym", "Sym", "Hash"],
            "Precision (%)"
        )
        
        self._generate_comparison_of_2(
            np.array([dyn_recall, asym_dyn_recall, sym_dyn_recall, hash_dyn_recall]),
            np.array([ibm_recall, asym_ibm_recall, sym_ibm_recall, hash_ibm_recall]),
            ax[1,0],
            ["Overall", "Asym", "Sym", "Hash"],
            "Recall (%)"
        )
        
        self._generate_comparison_of_2(
            np.array([dyn_f1, asym_dyn_f1, sym_dyn_f1, hash_dyn_f1]),
            np.array([ibm_f1, asym_ibm_f1, sym_ibm_f1, hash_ibm_f1]),
            ax[1,1],
            ["Overall", "Asym", "Sym", "Hash"],
            "F1-score (%)"
        )
        handles, labels = ax[0, 0].get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            frameon=False,
            ncol=3,
            bbox_to_anchor=(0.5, 1.02),
            loc="upper center",
            borderpad=0.3,
            handlelength=1.6,
        )
        fig.tight_layout(rect=[0, 0, 1, 0.96])

        fig.savefig(output_path, bbox_inches="tight")
        
    def _generate_comparison_of_2(
        self, dyn, ibm, ax, labels, ylabel
    ) -> None:
        """ Generate a comparison bar chart for CBOM results.
        Args:
            dyn (np.array): Dynamic CBOM values.
            ibm (np.array): IBM cbomkit values.
        """
        x = np.arange(len(labels))

        
        hatch_patterns = settings.hatch_patterns # define hatch patterns
        width = settings.bar_width  # the width of the bars
        facecolors = settings.facecolors  # list of colors for the bars
        edgecolor = settings.edgecolor    # edge color for the bars

        bars_dyn = ax.bar(
            x - width/2,
            dyn,
            width,
            label="Dynamic CBOM",
            facecolor=facecolors[1],
            edgecolor=edgecolor,
            hatch=hatch_patterns[1],
        )
        bars_ibm = ax.bar(
            x + width/2,
            ibm,
            width,
            label="IBM cbomkit",
            facecolor=facecolors[2],
            edgecolor=edgecolor,
            hatch=hatch_patterns[2],
        )

        # -------------------------------
        # Axes & grid
        # -------------------------------
        ax.set_ylabel(ylabel)
        # ax.set_xlabel("CBOM Evaluation Metrics")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=0)

        # Y-axis limit: consider stacked bar height AND grouped bars
        max_group = max(dyn.max(), ibm.max())
        ax.set_ylim(0, max_group * 1.15)

        # light dashed lines, both x and y, behind the bars
        ax.grid(True, axis="y", which="major",
                linestyle="--", linewidth=0.5, color="0.75", alpha=0.8)
        ax.grid(True, axis="x", which="major",
                linestyle="--", linewidth=0.5, color="0.85", alpha=0.8)
        ax.set_axisbelow(True)

        # Full frame box with thin dark-grey spines
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.8)
            spine.set_color("#4d4d4d")
        
        ax.bar_label(bars_dyn, padding=2, fontsize=6, fmt="%.0f")
        ax.bar_label(bars_ibm, padding=2, fontsize=6, fmt="%.0f")
        

        

    def _generate_comparison_of_3(
        self, gt, dyn, ibm, ax, labels, ylabel
    ) -> None:
        """ Generate a comparison bar chart for CBOM results.
        Args:
            gt (np.array): Ground truth values.
            dyn (np.array): Dynamic CBOM values.
            ibm (np.array): IBM cbomkit values.
        """
        x = np.arange(len(labels))
        
        hatch_patterns = settings.hatch_patterns # define hatch patterns
        stacked_hatch_patterns = settings.stacked_hatch_patterns  # hatch patterns for stacked bars
        width = settings.bar_width  # the width of the bars
        facecolors = settings.facecolors  # list of colors for the bars
        edgecolor = settings.edgecolor    # edge color for the bars
        stacked_facecolors = settings.stacked_facecolors  # colors for stacked bars

        bars_gt = ax.bar(
            x - width,
            gt,
            width,
            label="Ground Truth",
            facecolor=facecolors[0],
            edgecolor=edgecolor,
            hatch=hatch_patterns[0],
        )
        bars_dyn = ax.bar(
            x,
            dyn,
            width,
            label="Dynamic CBOM",
            facecolor=facecolors[1],
            edgecolor=edgecolor,
            hatch=hatch_patterns[1],
        )
        bars_ibm = ax.bar(
            x + width,
            ibm,
            width,
            label="IBM cbomkit",
            facecolor=facecolors[2],
            edgecolor=edgecolor,
            hatch=hatch_patterns[2],
        )

        # -------------------------------
        # Axes & grid
        # -------------------------------
        ax.set_ylabel(ylabel)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=0)

        # Y-axis limit: consider stacked bar height AND grouped bars
        max_group = max(gt.max(), dyn.max(), ibm.max())
        ax.set_ylim(0, max_group * 1.15)

        # light dashed lines, both x and y, behind the bars
        ax.grid(True, axis="y", which="major",
                linestyle="--", linewidth=0.5, color="0.75", alpha=0.8)
        ax.grid(True, axis="x", which="major",
                linestyle="--", linewidth=0.5, color="0.85", alpha=0.8)
        ax.set_axisbelow(True)

        # Full frame box with thin dark-grey spines
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.8)
            spine.set_color("#4d4d4d")

        
        ax.bar_label(bars_gt, padding=2, fontsize=6, fmt="%.0f")
        ax.bar_label(bars_dyn, padding=2, fontsize=6, fmt="%.0f")
        ax.bar_label(bars_ibm, padding=2, fontsize=6, fmt="%.0f")
       

        







