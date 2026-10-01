"""Create portfolio-ready visualizations for the Palmer Penguins dataset.

Run from the project root:
    python src/visualize_penguins.py

The script reads data/penguins.csv, prepares the data with pandas, saves six
high-resolution PNG charts in output/, and prints a concise data story.  It is
written as a beginner-friendly example: each chart has one analytical question
and a matching visualization type.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

# A non-interactive backend lets the script run in a terminal, CI, or server.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Project paths work regardless of the current terminal folder.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "penguins.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Columns that are numeric measurements rather than labels.
MEASUREMENT_COLUMNS = [
    "bill_length_mm",
    "bill_depth_mm",
    "flipper_length_mm",
    "body_mass_g",
]

SPECIES_ORDER = ["Adelie", "Chinstrap", "Gentoo"]
SPECIES_PALETTE = {
    "Adelie": "#3B82F6",     # blue
    "Chinstrap": "#F59E0B",  # amber
    "Gentoo": "#10B981",     # green
}
SEX_PALETTE = {"FEMALE": "#C084FC", "MALE": "#2563EB"}


def configure_style() -> None:
    """Apply one consistent, readable visual style to every chart."""
    sns.set_theme(style="whitegrid", context="notebook", font_scale=1.05)
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "axes.titleweight": "bold",
            "axes.labelweight": "semibold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "axes.facecolor": "#FAFAFA",
        }
    )


def load_and_prepare_data(path: Path) -> pd.DataFrame:
    """Load the CSV and perform only necessary type conversion and validation."""
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. Keep penguins.csv in the data/ folder."
        )

    data = pd.read_csv(path)
    expected_columns = {
        "species",
        "island",
        "bill_length_mm",
        "bill_depth_mm",
        "flipper_length_mm",
        "body_mass_g",
        "sex",
    }
    missing_columns = expected_columns.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing_columns)}")

    for column in MEASUREMENT_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    # Standardize label values while preserving missing values for transparent handling.
    data["species"] = data["species"].astype("string").str.strip()
    data["island"] = data["island"].astype("string").str.strip()
    data["sex"] = data["sex"].astype("string").str.strip().str.upper()

    return data


def save_figure(filename: str) -> None:
    """Save the current chart at publication-quality resolution and close it."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


def add_bar_labels(axis: plt.Axes, suffix: str = "", decimals: int = 0) -> None:
    """Add readable values to a vertical bar chart."""
    for container in axis.containers:
        labels = [f"{bar.get_height():,.{decimals}f}{suffix}" for bar in container]
        axis.bar_label(container, labels=labels, padding=3, fontsize=9, fontweight="semibold")


def plot_average_body_mass_by_species(data: pd.DataFrame) -> pd.Series:
    """Bar chart: Which species has the highest average body mass?"""
    averages = (
        data.dropna(subset=["body_mass_g"])
        .groupby("species", observed=True)["body_mass_g"]
        .mean()
        .reindex(SPECIES_ORDER)
        .dropna()
    )

    fig, axis = plt.subplots(figsize=(8.5, 5.5))
    bars = axis.bar(
        averages.index,
        averages.values,
        color=[SPECIES_PALETTE[species] for species in averages.index],
        width=0.62,
    )
    axis.set_title("Average Body Mass by Penguin Species")
    axis.set_xlabel("Species")
    axis.set_ylabel("Average body mass (g)")
    axis.set_ylim(0, averages.max() * 1.18)
    axis.grid(axis="y", alpha=0.3)
    axis.bar_label(bars, labels=[f"{value:,.0f} g" for value in averages], padding=3)
    save_figure("01_average_body_mass_by_species.png")

    heaviest = averages.idxmax()
    print(
        "1. Bar chart — Average body mass: "
        f"{heaviest} penguins have the highest average body mass "
        f"({averages.loc[heaviest]:,.0f} g)."
    )
    return averages


def plot_species_by_island(data: pd.DataFrame) -> pd.DataFrame:
    """Stacked bar chart: How are species observations distributed across islands?"""
    composition = pd.crosstab(data["island"], data["species"]).reindex(columns=SPECIES_ORDER, fill_value=0)
    composition = composition.sort_index()

    fig, axis = plt.subplots(figsize=(9, 5.8))
    bottom = pd.Series(0, index=composition.index)
    for species in SPECIES_ORDER:
        if species not in composition.columns:
            continue
        values = composition[species]
        axis.bar(
            composition.index,
            values,
            bottom=bottom,
            label=species,
            color=SPECIES_PALETTE[species],
            width=0.62,
        )
        for x_position, value, prior in zip(range(len(values)), values, bottom):
            if value > 0:
                axis.text(
                    x_position,
                    prior + value / 2,
                    str(int(value)),
                    ha="center",
                    va="center",
                    color="white",
                    fontsize=10,
                    fontweight="bold",
                )
        bottom += values

    axis.set_title("Penguin Observations by Island and Species")
    axis.set_xlabel("Island")
    axis.set_ylabel("Number of observations")
    axis.legend(title="Species", frameon=True, loc="upper right")
    axis.grid(axis="y", alpha=0.3)
    save_figure("02_species_composition_by_island.png")

    largest_group = composition.stack().idxmax()
    largest_count = int(composition.stack().max())
    print(
        "2. Stacked bar chart — Island composition: "
        f"the largest island-species group is {largest_group[1]} on {largest_group[0]} "
        f"({largest_count} observations)."
    )
    return composition


def plot_body_mass_distribution(data: pd.DataFrame) -> None:
    """Histogram: What does the body-mass distribution look like by species?"""
    chart_data = data.dropna(subset=["body_mass_g", "species"])
    fig, axis = plt.subplots(figsize=(9.5, 5.8))
    sns.histplot(
        data=chart_data,
        x="body_mass_g",
        hue="species",
        hue_order=SPECIES_ORDER,
        palette=SPECIES_PALETTE,
        bins=22,
        multiple="layer",
        element="step",
        stat="count",
        common_norm=False,
        alpha=0.32,
        edgecolor=None,
        ax=axis,
    )
    axis.set_title("Distribution of Body Mass by Penguin Species")
    axis.set_xlabel("Body mass (g)")
    axis.set_ylabel("Number of observations")
    axis.grid(axis="y", alpha=0.3)
    legend = axis.get_legend()
    if legend:
        legend.set_title("Species")
    save_figure("03_body_mass_distribution.png")

    print(
        "3. Histogram — Body-mass distribution: the species groups occupy different "
        "mass ranges, so a single overall average would conceal useful variation."
    )


def plot_body_mass_by_species_and_sex(data: pd.DataFrame) -> None:
    """Box plot: How does body mass vary by species and recorded sex?"""
    chart_data = data.dropna(subset=["body_mass_g", "species", "sex"])
    fig, axis = plt.subplots(figsize=(10, 6))
    sns.boxplot(
        data=chart_data,
        x="species",
        y="body_mass_g",
        hue="sex",
        order=SPECIES_ORDER,
        hue_order=["FEMALE", "MALE"],
        palette=SEX_PALETTE,
        width=0.66,
        linewidth=1.2,
        fliersize=3,
        ax=axis,
    )
    axis.set_title("Body-Mass Variation by Species and Recorded Sex")
    axis.set_xlabel("Species")
    axis.set_ylabel("Body mass (g)")
    axis.legend(title="Recorded sex", frameon=True, loc="upper left")
    axis.grid(axis="y", alpha=0.3)
    save_figure("04_body_mass_by_species_and_sex.png")

    medians = chart_data.groupby(["species", "sex"], observed=True)["body_mass_g"].median()
    widest_group = (medians.groupby(level=0).max() - medians.groupby(level=0).min()).idxmax()
    median_gap = (
        medians[widest_group].max() - medians[widest_group].min()
        if widest_group in medians.index.get_level_values(0)
        else 0
    )
    print(
        "4. Box plot — Variation by recorded sex: "
        f"{widest_group} has the largest difference between the displayed group medians "
        f"({median_gap:,.0f} g)."
    )


def plot_flipper_vs_body_mass(data: pd.DataFrame) -> float:
    """Scatter plot: Is flipper length associated with body mass?"""
    chart_data = data.dropna(subset=["flipper_length_mm", "body_mass_g", "species"])
    fig, axis = plt.subplots(figsize=(9.5, 6.3))
    sns.scatterplot(
        data=chart_data,
        x="flipper_length_mm",
        y="body_mass_g",
        hue="species",
        hue_order=SPECIES_ORDER,
        palette=SPECIES_PALETTE,
        s=62,
        alpha=0.78,
        edgecolor="white",
        linewidth=0.45,
        ax=axis,
    )
    correlation = chart_data["flipper_length_mm"].corr(chart_data["body_mass_g"])
    axis.set_title("Flipper Length and Body Mass by Penguin Species")
    axis.set_xlabel("Flipper length (mm)")
    axis.set_ylabel("Body mass (g)")
    axis.legend(title="Species", frameon=True, loc="upper left")
    axis.text(
        0.98,
        0.04,
        f"Overall Pearson r = {correlation:.2f}",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#CBD5E1"},
    )
    axis.grid(alpha=0.25)
    save_figure("05_flipper_length_vs_body_mass.png")

    print(
        "5. Scatter plot — Flipper length vs. body mass: "
        f"the overall relationship is positive (Pearson r = {correlation:.2f}), "
        "with visible species-level clusters."
    )
    return correlation


def plot_correlation_heatmap(data: pd.DataFrame) -> pd.DataFrame:
    """Correlation heatmap: Which physical measurements move together?"""
    correlations = data[MEASUREMENT_COLUMNS].corr()
    fig, axis = plt.subplots(figsize=(8.5, 6.8))
    sns.heatmap(
        correlations,
        annot=True,
        fmt=".2f",
        cmap="vlag",
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=1,
        linecolor="white",
        cbar_kws={"label": "Pearson correlation"},
        ax=axis,
    )
    axis.set_title("Correlation Between Penguin Measurements")
    axis.set_xlabel("Measurement")
    axis.set_ylabel("Measurement")
    axis.set_xticklabels([label.replace("_", " ").replace(" mm", " (mm)").replace(" g", " (g)") for label in MEASUREMENT_COLUMNS], rotation=28, ha="right")
    axis.set_yticklabels([label.replace("_", " ").replace(" mm", " (mm)").replace(" g", " (g)") for label in MEASUREMENT_COLUMNS], rotation=0)
    save_figure("06_measurement_correlation_heatmap.png")

    # Compare only each unique pair below, so self-correlations and duplicate
    # matrix entries are not treated as findings.
    strongest_pair = None
    strongest_value = 0.0
    for index, first in enumerate(MEASUREMENT_COLUMNS):
        for second in MEASUREMENT_COLUMNS[index + 1 :]:
            value = correlations.loc[first, second]
            if abs(value) > abs(strongest_value):
                strongest_pair = (first, second)
                strongest_value = value
    if strongest_pair is not None:
        print(
            "6. Correlation heatmap — Measurement relationships: "
            f"the strongest non-duplicate relationship is between "
            f"{strongest_pair[0].replace('_', ' ')} and {strongest_pair[1].replace('_', ' ')} "
            f"(r = {strongest_value:.2f})."
        )
    return correlations


def print_data_story(
    data: pd.DataFrame,
    averages: pd.Series,
    flipper_mass_correlation: float,
    correlations: pd.DataFrame,
) -> None:
    """Print the connected, data-only narrative that concludes the project."""
    complete_measurements = data.dropna(subset=MEASUREMENT_COLUMNS)
    lightest = averages.idxmin()
    heaviest = averages.idxmax()
    mass_difference = averages.loc[heaviest] - averages.loc[lightest]

    strongest_pair = max(
        (
            (first, second, correlations.loc[first, second])
            for i, first in enumerate(MEASUREMENT_COLUMNS)
            for second in MEASUREMENT_COLUMNS[i + 1 :]
        ),
        key=lambda item: abs(item[2]),
    )

    print("\nDATA STORY / KEY INSIGHTS")
    print("- Scope: the CSV contains " f"{len(data)} observations; {len(complete_measurements)} have all four measurements.")
    print(
        "- Species comparison: "
        f"{heaviest} has the highest mean body mass and is about {mass_difference:,.0f} g "
        f"heavier on average than {lightest}."
    )
    print(
        "- Segmentation: island composition and the body-mass plots show that the "
        "observations are not one homogeneous population; reporting results by species "
        "is more informative than relying on a grand average."
    )
    print(
        "- Relationship: flipper length and body mass have a positive overall association "
        f"(r = {flipper_mass_correlation:.2f}). The strongest measurement association in "
        f"this dataset is {strongest_pair[0].replace('_', ' ')} versus "
        f"{strongest_pair[1].replace('_', ' ')} (r = {strongest_pair[2]:.2f})."
    )
    print(
        "- Decision use: for a future field-summary or comparison workflow, retain species, "
        "island, and sex as context before comparing measurements; otherwise the distinct "
        "groups visible in the charts can be masked."
    )
    print(
        "- No line chart was created because this dataset has no observation date, year, "
        "or other time variable."
    )


def main() -> None:
    """Run the complete data-preparation, visualization, and story workflow."""
    configure_style()
    data = load_and_prepare_data(DATA_PATH)

    print("Palmer Penguins Data Visualization Project")
    print(f"Loaded {len(data)} rows and {len(data.columns)} columns from {DATA_PATH.name}.")
    print("Missing values by column:")
    print(data.isna().sum().to_string())
    print()

    averages = plot_average_body_mass_by_species(data)
    plot_species_by_island(data)
    plot_body_mass_distribution(data)
    plot_body_mass_by_species_and_sex(data)
    flipper_mass_correlation = plot_flipper_vs_body_mass(data)
    correlations = plot_correlation_heatmap(data)
    print_data_story(data, averages, flipper_mass_correlation, correlations)
    print(f"\nSaved six high-resolution charts to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
