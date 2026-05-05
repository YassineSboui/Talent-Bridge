import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from wordcloud import WordCloud
from collections import Counter
import io

sns.set_theme(style="whitegrid")


def salary_distribution(df: pd.DataFrame):
    if "salary" not in df.columns:
        return None
    fig, ax = plt.subplots(figsize=(8, 5))
    sal = df["salary"].dropna()
    sal = sal[sal > 0]
    if sal.empty:
        plt.close(fig)
        return None
    sns.histplot(sal, kde=True, ax=ax, bins=50, color="#4C72B0", edgecolor="white")
    ax.set_title("Salary Distribution", fontsize=14)
    ax.set_xlabel("Salary ($)")
    ax.set_ylabel("Count")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf


def job_type_breakdown(df: pd.DataFrame):
    if "job_type" not in df.columns:
        return None
    fig, ax = plt.subplots(figsize=(8, 5))
    jt = df["job_type"].value_counts()
    if jt.empty:
        plt.close(fig)
        return None
    colors = sns.color_palette("Set2", len(jt))
    ax.pie(jt.values, labels=jt.index, autopct="%1.1f%%", colors=colors, startangle=90)
    ax.set_title("Job Type Breakdown", fontsize=14)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf


def experience_vs_salary(df: pd.DataFrame):
    if "experience_years" not in df.columns or "salary" not in df.columns:
        return None
    fig, ax = plt.subplots(figsize=(8, 5))
    valid = df.dropna(subset=["experience_years", "salary"])
    valid = valid[valid["salary"] > 0]
    if valid.empty:
        plt.close(fig)
        return None
    sns.scatterplot(data=valid, x="experience_years", y="salary", alpha=0.6, ax=ax, color="#DD8452")
    sns.regplot(data=valid, x="experience_years", y="salary", scatter=False, ax=ax, color="#55A868")
    ax.set_title("Experience vs Salary", fontsize=14)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf


def top_locations(df: pd.DataFrame, n: int = 10):
    if "location" not in df.columns:
        return None
    fig, ax = plt.subplots(figsize=(8, 5))
    loc = df["location"].value_counts().head(n)
    if loc.empty:
        plt.close(fig)
        return None
    sns.barplot(x=loc.values, y=loc.index, ax=ax, palette="viridis")
    ax.set_title(f"Top {n} Locations", fontsize=14)
    ax.set_xlabel("Number of Job Postings")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf


def skills_wordcloud(df: pd.DataFrame):
    if "skills" not in df.columns:
        return None
    text = df["skills"].fillna("").str.cat(sep=",")
    tokens = [t.strip() for t in text.split(",") if t.strip()]
    if not tokens:
        return None
    freq = Counter(tokens)
    wc = WordCloud(width=800, height=400, background_color="white", colormap="viridis", max_words=100)
    wc.generate_from_frequencies(freq)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Skills Word Cloud", fontsize=14)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf


def correlation_heatmap(df: pd.DataFrame):
    numeric = df.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        return None
    fig, ax = plt.subplots(figsize=(10, 8))
    corr = numeric.corr()
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax, linewidths=0.5)
    ax.set_title("Feature Correlation Heatmap", fontsize=14)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf
