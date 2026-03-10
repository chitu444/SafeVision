"""
utils/charts.py
===============
Reusable chart helpers (currently: PPE compliance pie chart).
"""

import numpy as np
import matplotlib.pyplot as plt


def ppe_pie_chart(safe: int, unsafe: int) -> plt.Figure:
    """
    Return a matplotlib Figure showing the Safe/Unsafe split.
    Handles edge cases: negative values and all-zero totals.
    """
    def _clean(v):
        try:
            n = float(v)
            return n if (n >= 0 and not np.isnan(n) and not np.isinf(n)) else 0.0
        except Exception:
            return 0.0

    s, u = _clean(safe), _clean(unsafe)
    fig, ax = plt.subplots(figsize=(4, 4))

    if s + u <= 0:
        ax.pie([1], labels=["No Data"], colors=["#CFD8DC"], startangle=90)
    else:
        ax.pie(
            [s, u],
            labels=["Safe", "Unsafe"],
            autopct="%1.1f%%",
            startangle=90,
            colors=["#4CAF50", "#F44336"],
        )
    ax.axis("equal")
    return fig
