import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
import streamlit as st

def plot_logest_growth_from_csv(csv_path, category_name):
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        st.warning(f"Unable to read growth data: {e}")
        return None

    if 'Year' not in df.columns or 'Total' not in df.columns:
        st.warning("Required columns 'Year' and 'Total' not found in dataset.")
        return None

    df = df[df['Year'].astype(str).str.match(r"^\\d{4}$")]
    df['Year'] = df['Year'].astype(int)
    df = df[['Year', 'Total']].dropna()
    df.set_index('Year', inplace=True)

    all_years = np.arange(df.index.min(), df.index.max() + 1)
    df = df.reindex(all_years)

    for year in df.index[df['Total'].isnull()]:
        prev_year = max(df.index[df.index < year])
        next_year = min(df.index[df.index > year])
        step = (df.loc[next_year, 'Total'] - df.loc[prev_year, 'Total']) / (next_year - prev_year)
        df.loc[year, 'Total'] = df.loc[prev_year, 'Total'] + step * (year - prev_year)

    min_decade_start = (df.index.min() // 10) * 10 + 1
    decades = []
    year = min_decade_start
    while year + 9 <= df.index.max():
        decades.append((year, year + 9))
        year += 10
    if df.index.min() < min_decade_start:
        decades.insert(0, (df.index.min(), min_decade_start - 1))
    if df.index.max() > decades[-1][1]:
        decades.append((decades[-1][1] + 1, df.index.max()))

    decade_growth_rates = {}
    for start, end in decades:
        mask = (df.index >= start) & (df.index <= end)
        if mask.sum() < 2:
            continue
        x = np.arange(mask.sum())
        y = np.log(df.loc[mask, 'Total'])
        slope, _, _, _, _ = linregress(x, y)
        decade_growth_rates[f"{start}-{end}"] = (np.exp(slope) - 1) * 100

    x_all = np.arange(len(df))
    y_all = np.log(df['Total'])
    slope_all, _, _, _, _ = linregress(x_all, y_all)
    overall = (np.exp(slope_all) - 1) * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(decade_growth_rates.keys(), decade_growth_rates.values(), label="Decade-wise Trend Growth Rate")
    ax.axhline(y=overall, color='red', linestyle='--', label=f'Overall Growth Rate ({overall:.2f}%)')

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval, f"{yval:.2f}%", ha='center', va='bottom')

    ax.set_title(f"Decade-wise Trend Growth Rate for {category_name}")
    ax.set_ylabel("Trend Growth Rate (%)")
    ax.set_xlabel("Decade Range")
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig
