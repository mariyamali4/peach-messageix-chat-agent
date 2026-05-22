#analysis_intake_layer.py
import pandas as pd
import numpy as np
import json


YEAR_COLS = [2025, 2030, 2035, 2040, 2045, 2050, 2055, 2060, 2070]

# --------------------------------------------------------------------------------------
#STEP 1 — PARSE
# --------------------------------------------------------------------------------------

def parse(df):
    """Extract unique metadata present in the scenario file."""
    root_variables = [var.split("|")[0].strip() for var in df["Variable"]]
    unique_root_vars = list(set(root_variables))
    return {
        "model":      df["Model"].unique().tolist(),
        "scenarios":  df["Scenario"].unique().tolist(),
        "regions":    df["Region"].unique().tolist(),
        "time_horizon": [col for col in YEAR_COLS if col in df.columns],
        "variable_count": len(df["Variable"].unique()),
        "root_variables": unique_root_vars,
    }


# --------------------------------------------------------------------------------------
# STEP 2 — FILTER
# --------------------------------------------------------------------------------------

def filter_into_families(df, root_variables):
    """Split the df into per-family sub-df.
        {"root_var1": df_family1}
    """
    root_families = {}
    for root_var in root_variables:
        mask = df["Variable"].str.startswith(root_var + "|") | (df["Variable"] == root_var)
        family_df = df[mask]
        if not family_df.empty:
            root_families[root_var] = family_df.copy()
    return root_families


# --------------------------------------------------------------------------------------
# STEP 3 — AGGREGATE
# --------------------------------------------------------------------------------------

def aggregate(root_families: dict, year_cols: list) -> dict:
    results = {}

    for family, family_df in root_families.items():
        available_years = [y for y in year_cols if y in family_df.columns]
        if not available_years:
            continue

        first_year, last_year = available_years[0], available_years[-1]
        n_years = last_year - first_year

        # Total volume per year
        totals = family_df[available_years].sum(axis=0)
        total_start, total_end = totals[first_year], totals[last_year]

        abs_delta = round(total_end - total_start, 3)
        rel_delta = round((abs_delta / total_start * 100), 2) if total_start != 0 else None

        # CAGR, calculate only if both values are strictly positive
        if total_start > 0 and total_end > 0 and n_years > 0:
            cagr_pct = round(((total_end / total_start) ** (1 / n_years) - 1) * 100, 2)
        else:
            cagr_pct = None

        # Peak year and value, to undersand each family's peak
        peak_year = int(totals.idxmax())
        peak_value = round(totals[peak_year], 3)

        # Mid-century snapshot — 2050 is a key policy milestone in climate policies
        mid_century = round(totals[2050], 3) if 2050 in totals.index else None

        # Market shares in the final year — group by second pipe segment (secondary family level)
        family_df = family_df.copy()
        family_df["_sub"] = family_df["Variable"].apply(
            lambda var: var.split("|")[1].strip() if "|" in var else var
        )
        sub_totals = family_df.groupby("_sub")[last_year].sum().sort_values(ascending=False)
        total_for_share = sub_totals.sum()

        market_shares = {}
        if total_for_share != 0:
            for sub, val in sub_totals.items():
                share = round(val / total_for_share * 100, 2)
                if share > 0.01:
                    market_shares[sub] = share


        results[family] = {
            "total_volume":             {str(y): round(totals[y], 3) for y in available_years},
            "absolute_delta":           abs_delta,
            "relative_delta_pct":       rel_delta,
            "cagr_percentage":          cagr_pct,
            "peak_year":                peak_year,
            "peak_value":               peak_value,
            "mid_century_value":        mid_century,
            "market_shares_final_year": market_shares
        }

    return results

# --------------------------------------------------------------------------------------


def build_scenario_summary(input_path) -> dict:
    """
    Full pipeline: Parse → Filter → Aggregate.
    Reads an IAMC scenario XLSX and returns a compact JSON-serialisable dict ready for LLM context.
    Input: input_path (str) — path to the IAMC-format Excel file
    Output: dict with 2 keys: metadata: of full df, families_summaries: summary stats for each root variable family
    """
    df = pd.read_excel(input_path)

    # Ensure year columns are int (they may be read as strings from the input_file)
    df.columns = [int(c) if str(c).isdigit() else c for c in df.columns]
    available_years = [y for y in YEAR_COLS if y in df.columns]

    metadata  = parse(df)
    root_families  = filter_into_families(df, metadata["root_variables"])
    metrics   = aggregate(root_families, available_years)

    summary = {
        "metadata": metadata,
        "families_summaries": metrics,
    }

    return df, json.dumps(summary, indent=2)


# # Local testing
# import time
# #input_file = r"D:\lums-python-programming\engg562\thesis-notebooks\MESSAGEix-Pakistan_CM.xlsx"
# input_file = r"D:\lums-python-programming\thesis\project\data\analysis-knowledgebase\MESSAGEix-Pakistan_baseline_2026-03-17--11-37.xlsx"
# user_query = "explain this scenario to me"
# start = time.time()
# summary = build_scenario_summary(input_file)
# analysis_type_specific_task = "Explaining the scenario, highlighting key trends, and insights."
# print(synthesize(summary, user_query, analysis_type_specific_task))
# print("Execution time:", time.time() - start)