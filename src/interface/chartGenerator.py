"""Chart generation for CBOM comparison and evaluation visualization.

Provides functionality to generate comparison charts for cryptographic bill of
materials (CBOM) documents, comparing dynamic traces against ground truth and
alternative tools like IBM cbomkit.
"""

import json

import matplotlib.pyplot as plt
import numpy as np

from interface.cbomMatcher import CBOMMatcher
from interface.config import settings


class ChartGenerator:
    """Generates comparison charts for CBOM evaluation and analysis.

    Compares cryptographic assets across multiple CBOM sources and generates
    publication-quality visualizations with precision, recall, and F1-score
    metrics.

    Attributes:
        verbose: Enable verbose logging during chart generation.
    """

    def __init__(self, verbose: bool = False):
        """Initialize chart generator with matplotlib styling.

        Args:
            verbose: If True, print processing information.
        """
        self.verbose = verbose
        self._configure_matplotlib()

    def _configure_matplotlib(self) -> None:
        """Configure matplotlib global styling parameters."""
        plt.rcParams.update(
            {
                "figure.dpi": 300,
                "figure.facecolor": "white",
                "axes.facecolor": "white",
                "font.family": "serif",
                "font.size": 9,
                "axes.edgecolor": "#333333",
                "axes.linewidth": 0.8,
                "xtick.color": "#333333",
                "ytick.color": "#333333",
            }
        )

    def _parse_cbom(self, cbom_path: str) -> list:
        """Parse a CycloneDX CBOM JSON file.

        Args:
            cbom_path: Path to the CBOM JSON file.

        Returns:
            List of cryptographic algorithm components.
        """
        with open(cbom_path, "r") as f:
            cbom = json.load(f)
        cbom = [
            component
            for component in cbom.get("components", [])
            if component.get("cryptoProperties", {}).get("assetType") == "algorithm"
        ]
        return cbom

    def _compare_with_ground_truth(self, cbom: list, gt: list) -> tuple:
        """Compare a CBOM against ground truth using asset matching.

        Computes precision, recall, and F1-score by matching assets between
        the given CBOM and ground truth using the CBOMMatcher.

        Args:
            cbom: Target CBOM components to evaluate.
            gt: Ground truth CBOM components.

        Returns:
            Tuple of (precision %, recall %, f1_score %) values.
        """
        matcher = CBOMMatcher()
        _, precision, recall, f1_score = matcher.match_assets(gt=gt, target=cbom, threshold=0.6)
        return precision * 100, recall * 100, f1_score * 100

    def _filter_assets_by_primitive(self, cbom: list, primitives: list) -> list:
        """Filter CBOM components by cryptographic primitive type.

        Args:
            cbom: List of CBOM components.
            primitives: List of primitive types to include.

        Returns:
            Filtered list of components matching the specified primitives.
        """
        return [
            asset
            for asset in cbom
            if asset.get("cryptoProperties", {}).get("algorithmProperties", {}).get("primitive")
            in primitives
        ]

    def _get_asymmetric_assets(self, cbom: list) -> list:
        """Extract asymmetric cryptography assets from CBOM.

        Args:
            cbom: List of CBOM components.

        Returns:
            List of asymmetric cryptography components.
        """
        return self._filter_assets_by_primitive(cbom, settings.primitive_mapping.asymmetric)

    def _get_symmetric_assets(self, cbom: list) -> list:
        """Extract symmetric cryptography assets from CBOM.

        Args:
            cbom: List of CBOM components.

        Returns:
            List of symmetric cryptography components.
        """
        return self._filter_assets_by_primitive(cbom, settings.primitive_mapping.symmetric)

    def _get_hashing_assets(self, cbom: list) -> list:
        """Extract hashing algorithm assets from CBOM.

        Args:
            cbom: List of CBOM components.

        Returns:
            List of hashing algorithm components.
        """
        return self._filter_assets_by_primitive(cbom, settings.primitive_mapping.hashing)

    def _get_asset_counts(self, cbom: list) -> tuple:
        """Count assets in CBOM by category.

        Args:
            cbom: List of CBOM components.

        Returns:
            Tuple of (total, asymmetric, symmetric, hashing) counts.
        """
        return (
            len(cbom),
            len(self._get_asymmetric_assets(cbom)),
            len(self._get_symmetric_assets(cbom)),
            len(self._get_hashing_assets(cbom)),
        )

    def generate_singular(self, gt_path: str, dyn_path: str, output_path: str) -> None:
        """Generate a comparison chart for dynamic CBOM vs ground truth.

        Creates a two-panel visualization:
        - Left panel: Asset count comparison by type
        - Right panel: Precision, recall, and F1-score metrics

        Args:
            gt_path: Path to ground truth CBOM file.
            dyn_path: Path to dynamic CBOM file.
            output_path: Path where the chart will be saved.
        """
        gt_cbom = self._parse_cbom(gt_path)
        dyn_cbom = self._parse_cbom(dyn_path)

        fig, ax = plt.subplots(1, 2, figsize=(7, 3))

        # Calculate metrics for all categories
        metrics = self._calculate_singular_metrics(gt_cbom, dyn_cbom)

        # Generate visualization panels
        self._plot_asset_counts(ax[0], gt_cbom, dyn_cbom)
        self._plot_metrics(ax[1], metrics)

        # Configure figure layout and save
        self._finalize_figure(fig, output_path)

    def _calculate_singular_metrics(self, gt_cbom: list, dyn_cbom: list) -> dict:
        """Calculate metrics for singular comparison.

        Args:
            gt_cbom: Ground truth CBOM.
            dyn_cbom: Dynamic CBOM.

        Returns:
            Dictionary with precision, recall, and F1-score for each category.
        """
        categories = {
            "total": (dyn_cbom, gt_cbom),
            "asymmetric": (
                self._get_asymmetric_assets(dyn_cbom),
                self._get_asymmetric_assets(gt_cbom),
            ),
            "symmetric": (
                self._get_symmetric_assets(dyn_cbom),
                self._get_symmetric_assets(gt_cbom),
            ),
            "hashing": (self._get_hashing_assets(dyn_cbom), self._get_hashing_assets(gt_cbom)),
        }

        metrics = {}
        for category, (dyn, gt) in categories.items():
            metrics[category] = self._compare_with_ground_truth(dyn, gt)

        return metrics

    def _plot_asset_counts(self, ax, gt_cbom: list, dyn_cbom: list) -> None:
        """Plot asset count comparison.

        Args:
            ax: Matplotlib axis.
            gt_cbom: Ground truth CBOM.
            dyn_cbom: Dynamic CBOM.
        """
        x = np.arange(4)
        width = settings.bar_width
        labels = ["Total", "Asym", "Sym", "Hash"]

        gt_counts = np.array(self._get_asset_counts(gt_cbom))
        dyn_counts = np.array(self._get_asset_counts(dyn_cbom))

        bars_gt = ax.bar(
            x - width / 2,
            gt_counts,
            width,
            label="Ground Truth",
            facecolor=settings.facecolors[0],
            edgecolor=settings.edgecolor,
            hatch=settings.hatch_patterns[0],
        )
        bars_dyn = ax.bar(
            x + width / 2,
            dyn_counts,
            width,
            label="Dynamic CBOM",
            facecolor=settings.facecolors[1],
            edgecolor=settings.edgecolor,
            hatch=settings.hatch_patterns[1],
        )

        ax.set_ylabel("No. of Assets")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, max(gt_counts.max(), dyn_counts.max()) * 1.15)

        self._configure_axis(ax)
        ax.bar_label(bars_gt, padding=2, fontsize=6, fmt="%.0f")
        ax.bar_label(bars_dyn, padding=2, fontsize=6, fmt="%.0f")

    def _plot_metrics(self, ax, metrics: dict) -> None:
        """Plot evaluation metrics (precision, recall, F1-score).

        Args:
            ax: Matplotlib axis.
            metrics: Dictionary with metric values.
        """
        x = np.arange(4)
        width = settings.bar_width
        labels = ["Total", "Asym", "Sym", "Hash"]

        prec = np.array([metrics[k][0] for k in ["total", "asymmetric", "symmetric", "hashing"]])
        recall = np.array([metrics[k][1] for k in ["total", "asymmetric", "symmetric", "hashing"]])
        f1 = np.array([metrics[k][2] for k in ["total", "asymmetric", "symmetric", "hashing"]])

        bars_prec = ax.bar(
            x - width,
            prec,
            width,
            label="Precision",
            facecolor=settings.singular_facecolors[0],
            edgecolor=settings.edgecolor,
            hatch=settings.hatch_patterns[0],
        )
        bars_recall = ax.bar(
            x,
            recall,
            width,
            label="Recall",
            facecolor=settings.singular_facecolors[1],
            edgecolor=settings.edgecolor,
            hatch=settings.hatch_patterns[1],
        )
        bars_f1 = ax.bar(
            x + width,
            f1,
            width,
            label="F1 Score",
            facecolor=settings.singular_facecolors[2],
            edgecolor=settings.edgecolor,
            hatch=settings.hatch_patterns[2],
        )

        ax.set_ylabel("Score (%)")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, max(prec.max(), recall.max(), f1.max()) * 1.15)

        self._configure_axis(ax)
        ax.bar_label(bars_prec, padding=2, fontsize=6, fmt="%.0f")
        ax.bar_label(bars_recall, padding=2, fontsize=6, fmt="%.0f")
        ax.bar_label(bars_f1, padding=2, fontsize=6, fmt="%.0f")

    def _configure_axis(self, ax) -> None:
        """Configure standard axis styling.

        Args:
            ax: Matplotlib axis to configure.
        """
        ax.grid(
            True, axis="y", which="major", linestyle="--", linewidth=0.5, color="0.75", alpha=0.8
        )
        ax.grid(
            True, axis="x", which="major", linestyle="--", linewidth=0.5, color="0.85", alpha=0.8
        )
        ax.set_axisbelow(True)

        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(0.8)
            spine.set_color("#4d4d4d")

    def _finalize_figure(self, fig, output_path: str) -> None:
        """Configure and save the final figure.

        Args:
            fig: Matplotlib figure object.
            output_path: Path where the figure will be saved.
        """
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
        self, gt_path: str, dyn_path: str, ibm_path: str, output_path: str
    ) -> None:
        """Generate a comprehensive comparison chart across three CBOM sources.

        Creates a four-panel visualization comparing Dynamic CBOM, IBM cbomkit,
        and ground truth across multiple metrics.

        Args:
            gt_path: Path to ground truth CBOM file.
            dyn_path: Path to dynamic CBOM file.
            ibm_path: Path to IBM cbomkit CBOM file.
            output_path: Path where the chart will be saved.
        """
        gt_cbom = self._parse_cbom(gt_path)
        dyn_cbom = self._parse_cbom(dyn_path)
        ibm_cbom = self._parse_cbom(ibm_path)

        fig, ax = plt.subplots(2, 2, figsize=(10, 8))

        # Panel 1: Asset counts
        self._plot_comparison_of_three(
            np.array(self._get_asset_counts(gt_cbom)),
            np.array(self._get_asset_counts(dyn_cbom)),
            np.array(self._get_asset_counts(ibm_cbom)),
            ax[0, 0],
            ["Total", "Asym", "Sym", "Hash"],
            "No. of Assets",
        )

        # Calculate metrics for all categories
        if self.verbose:
            print("Comparing Dynamic CBOM with Ground Truth...")
        dyn_prec, dyn_recall, dyn_f1 = self._compare_category_metrics(dyn_cbom, gt_cbom)

        if self.verbose:
            print("Comparing IBM cbomkit CBOM with Ground Truth...")
        ibm_prec, ibm_recall, ibm_f1 = self._compare_category_metrics(ibm_cbom, gt_cbom)

        # Panel 2: Precision comparison
        self._plot_comparison_of_two(
            np.array(dyn_prec),
            np.array(ibm_prec),
            ax[0, 1],
            ["Overall", "Asym", "Sym", "Hash"],
            "Precision (%)",
        )

        # Panel 3: Recall comparison
        self._plot_comparison_of_two(
            np.array(dyn_recall),
            np.array(ibm_recall),
            ax[1, 0],
            ["Overall", "Asym", "Sym", "Hash"],
            "Recall (%)",
        )

        # Panel 4: F1-score comparison
        self._plot_comparison_of_two(
            np.array(dyn_f1),
            np.array(ibm_f1),
            ax[1, 1],
            ["Overall", "Asym", "Sym", "Hash"],
            "F1-score (%)",
        )

        # Configure figure layout and save
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

    def _compare_category_metrics(self, cbom: list, gt: list) -> tuple:
        """Calculate metrics for all asset categories.

        Args:
            cbom: CBOM to evaluate.
            gt: Ground truth CBOM.

        Returns:
            Tuple of (precision, recall, f1_score) lists for each category.
        """
        categories = {
            "total": (cbom, gt),
            "asymmetric": (self._get_asymmetric_assets(cbom), self._get_asymmetric_assets(gt)),
            "symmetric": (self._get_symmetric_assets(cbom), self._get_symmetric_assets(gt)),
            "hashing": (self._get_hashing_assets(cbom), self._get_hashing_assets(gt)),
        }

        prec, recall, f1 = [], [], []
        for _, (test_cbom, test_gt) in categories.items():
            p, r, f = self._compare_with_ground_truth(test_cbom, test_gt)
            prec.append(p)
            recall.append(r)
            f1.append(f)

        return prec, recall, f1

    def _plot_comparison_of_two(
        self, dyn: np.ndarray, ibm: np.ndarray, ax, labels: list, ylabel: str
    ) -> None:
        """Plot comparison chart for two CBOM sources.

        Args:
            dyn: Dynamic CBOM metric values.
            ibm: IBM cbomkit metric values.
            ax: Matplotlib axis.
            labels: Category labels.
            ylabel: Y-axis label.
        """
        x = np.arange(len(labels))
        width = settings.bar_width

        bars_dyn = ax.bar(
            x - width / 2,
            dyn,
            width,
            label="Dynamic CBOM",
            facecolor=settings.facecolors[1],
            edgecolor=settings.edgecolor,
            hatch=settings.hatch_patterns[1],
        )
        bars_ibm = ax.bar(
            x + width / 2,
            ibm,
            width,
            label="IBM cbomkit",
            facecolor=settings.facecolors[2],
            edgecolor=settings.edgecolor,
            hatch=settings.hatch_patterns[2],
        )

        ax.set_ylabel(ylabel)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, max(dyn.max(), ibm.max()) * 1.15)

        self._configure_axis(ax)
        ax.bar_label(bars_dyn, padding=2, fontsize=6, fmt="%.0f")
        ax.bar_label(bars_ibm, padding=2, fontsize=6, fmt="%.0f")

    def _plot_comparison_of_three(
        self, gt: np.ndarray, dyn: np.ndarray, ibm: np.ndarray, ax, labels: list, ylabel: str
    ) -> None:
        """Plot comparison chart for three CBOM sources.

        Args:
            gt: Ground truth metric values.
            dyn: Dynamic CBOM metric values.
            ibm: IBM cbomkit metric values.
            ax: Matplotlib axis.
            labels: Category labels.
            ylabel: Y-axis label.
        """
        x = np.arange(len(labels))
        width = settings.bar_width

        bars_gt = ax.bar(
            x - width,
            gt,
            width,
            label="Ground Truth",
            facecolor=settings.facecolors[0],
            edgecolor=settings.edgecolor,
            hatch=settings.hatch_patterns[0],
        )
        bars_dyn = ax.bar(
            x,
            dyn,
            width,
            label="Dynamic CBOM",
            facecolor=settings.facecolors[1],
            edgecolor=settings.edgecolor,
            hatch=settings.hatch_patterns[1],
        )
        bars_ibm = ax.bar(
            x + width,
            ibm,
            width,
            label="IBM cbomkit",
            facecolor=settings.facecolors[2],
            edgecolor=settings.edgecolor,
            hatch=settings.hatch_patterns[2],
        )

        ax.set_ylabel(ylabel)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, max(gt.max(), dyn.max(), ibm.max()) * 1.15)

        self._configure_axis(ax)
        ax.bar_label(bars_gt, padding=2, fontsize=6, fmt="%.0f")
        ax.bar_label(bars_dyn, padding=2, fontsize=6, fmt="%.0f")
        ax.bar_label(bars_ibm, padding=2, fontsize=6, fmt="%.0f")
