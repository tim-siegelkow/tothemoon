import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

def prepare_data_for_viz(transactions):
    """
    Prepare transaction data for visualization.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        pandas.DataFrame: Processed data for visualization
    """
    data = []
    
    for t in transactions:
        category = t.user_verified_category or t.ai_suggested_category or t.original_category or "Uncategorized"
        
        data.append({
            "date": t.date,
            "month": t.date.strftime("%Y-%m"),
            "month_name": t.date.strftime("%b %Y"),
            "year": t.date.year,
            "description": t.description,
            "amount": t.amount,
            "category": category,
            "transaction_type": "Expense" if t.amount < 0 else "Income"
        })
    
    return pd.DataFrame(data)

def generate_monthly_summary(df):
    """
    Generate monthly summary statistics.
    
    Args:
        df: DataFrame with transaction data
        
    Returns:
        dict: Monthly summary statistics
    """
    # Create a copy of the DataFrame to avoid warnings
    df_copy = df.copy()
    
    # Ensure amount is numeric
    df_copy["amount"] = pd.to_numeric(df_copy["amount"])
    
    # Calculate total income (positive amounts)
    total_income = df_copy[df_copy["amount"] > 0]["amount"].sum()
    
    # Calculate total expense (negative amounts)
    total_expense = abs(df_copy[df_copy["amount"] < 0]["amount"].sum())
    
    # Net savings
    net_savings = total_income - total_expense
    
    # Monthly breakdown
    monthly = df_copy.groupby("month").agg({
        "amount": [
            ("income", lambda x: x[x > 0].sum()),
            ("expense", lambda x: abs(x[x < 0].sum())),
            ("net", "sum")
        ]
    })
    
    # Flatten multi-level column index
    monthly.columns = [f"{col[1]}" for col in monthly.columns]
    
    # Convert to dictionary for easier access
    monthly_dict = monthly.to_dict(orient="index")
    
    # Add month names
    for month, values in monthly_dict.items():
        year, month_num = month.split("-")
        month_name = calendar.month_name[int(month_num)]
        monthly_dict[month]["month_name"] = f"{month_name} {year}"
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_savings": net_savings,
        "monthly": monthly_dict
    }

def create_category_pie_chart(df, transaction_type="Expense"):
    """
    Create a pie chart of transactions by category.
    
    Args:
        df: DataFrame with transaction data
        transaction_type: Type of transactions to include ("Expense" or "Income")
        
    Returns:
        plotly.graph_objects.Figure: Pie chart figure
    """
    # Filter transactions by type
    if transaction_type == "Expense":
        df_filtered = df[df["amount"] < 0].copy()
        df_filtered["amount"] = df_filtered["amount"].abs()
    else:
        df_filtered = df[df["amount"] > 0].copy()
    
    # Group by category
    category_totals = df_filtered.groupby("category")["amount"].sum().reset_index()
    
    # Sort by amount descending
    category_totals = category_totals.sort_values("amount", ascending=False)
    
    # Create pie chart
    fig = px.pie(
        category_totals,
        values="amount",
        names="category",
        title=f"{transaction_type} Distribution by Category",
        hole=0.4
    )
    
    return fig

def create_monthly_trend_chart(df):
    """
    Create a chart showing monthly income and expenses as bars, with net as a line.
    
    Args:
        df: DataFrame with transaction data
        
    Returns:
        plotly.graph_objects.Figure: Combined bar and line chart figure
    """
    # Group by month and calculate income and expense
    monthly = df.groupby(["month", "month_name"]).agg({
        "amount": [
            ("Income", lambda x: x[x > 0].sum()),
            ("Expense", lambda x: abs(x[x < 0].sum())),
            ("Net", "sum")
        ]
    })
    
    # Flatten multi-level column index
    monthly.columns = [f"{col[1]}" for col in monthly.columns]
    monthly = monthly.reset_index()
    
    # Sort by month chronologically
    monthly = monthly.sort_values("month")
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add income bars
    fig.add_trace(go.Bar(
        x=monthly["month_name"],
        y=monthly["Income"],
        name="Income",
        marker_color="green",
        text=monthly["Income"].round(0).astype(int),
        textposition="auto",
    ))
    
    # Add expense bars
    fig.add_trace(go.Bar(
        x=monthly["month_name"],
        y=monthly["Expense"],
        name="Expense",
        marker_color="red",
        text=monthly["Expense"].round(0).astype(int),
        textposition="auto",
    ))
    
    # Add net line
    fig.add_trace(go.Scatter(
        x=monthly["month_name"],
        y=monthly["Net"],
        name="Net",
        line=dict(color="blue", width=2, dash="dash")
    ))
    
    fig.update_layout(
        title="Monthly Income and Expense Trends",
        xaxis_title="Month",
        yaxis_title="Amount",
        legend_title="Type",
        hovermode="x unified",
        barmode="group"  # Group bars side by side
    )
    
    return fig

def create_category_bar_chart(df, months=12, transaction_type="Expense"):
    """
    Create a bar chart of transactions by category for the last N months.
    
    Args:
        df: DataFrame with transaction data
        months: Number of months to include (default: 12)
        transaction_type: Type of transactions to include ("Expense" or "Income")
        
    Returns:
        plotly.graph_objects.Figure: Bar chart figure
    """
    # Get the current date and calculate the date N months ago
    today = datetime.now()
    start_date = today - timedelta(days=30 * months)
    
    # Filter data by date and transaction type
    df_filtered = df[df["date"] >= start_date].copy()
    
    if transaction_type == "Expense":
        df_filtered = df_filtered[df_filtered["amount"] < 0].copy()
        df_filtered["amount"] = df_filtered["amount"].abs()
    else:
        df_filtered = df_filtered[df_filtered["amount"] > 0].copy()
    
    # Group by month and category
    monthly_category = df_filtered.groupby(["month", "month_name", "category"])["amount"].sum().reset_index()
    
    # Calculate monthly totals
    monthly_totals = monthly_category.groupby(["month", "month_name"])["amount"].sum().reset_index()
    
    # Get unique months and sort them chronologically
    unique_months = sorted(monthly_category["month"].unique())
    
    # If we have more months than requested, keep only the latest ones
    if len(unique_months) > months:
        latest_months = unique_months[-months:]
        monthly_category = monthly_category[monthly_category["month"].isin(latest_months)]
        monthly_totals = monthly_totals[monthly_totals["month"].isin(latest_months)]
    
    # Sort by month chronologically
    monthly_category = monthly_category.sort_values("month")
    monthly_totals = monthly_totals.sort_values("month")
    
    # Create bar chart
    fig = px.bar(
        monthly_category,
        x="month_name",
        y="amount",
        color="category",
        title=f"Monthly {transaction_type} by Category (Last {months} Months)",
        barmode="stack"
    )
    
    # Add total values above each stacked bar
    fig.add_trace(go.Scatter(
        x=monthly_totals["month_name"],
        y=monthly_totals["amount"],
        mode="text",
        text=monthly_totals["amount"].round(0).astype(int),
        textposition="top center",
        showlegend=False,
        textfont=dict(size=12)
    ))
    
    # Update layout to ensure chronological order
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Amount",
        legend_title="Category",
        hovermode="x unified",
        xaxis=dict(
            categoryorder='array',
            categoryarray=monthly_totals["month_name"].tolist()
        )
    )
    
    return fig

def create_dining_expenses_chart(df, time_scale="month", categories=None):
    """
    Create a bar chart showing expenses for selected categories aggregated by the selected time scale.
    
    Args:
        df: DataFrame with transaction data
        time_scale: Time aggregation level ("day", "week", "month", or "year")
        categories: List of categories to include (if None, defaults to dining-related categories)
        
    Returns:
        plotly.graph_objects.Figure: Bar chart figure
    """
    if categories is None:
        # Default to dining-related categories
        df_filtered = df[
            (df["category"].str.lower().str.contains("dining|restaurant|food|cafe|coffee|bar")) & 
            (df["amount"] < 0)
        ].copy()
    else:
        # Filter for selected categories (negative amounts)
        df_filtered = df[
            (df["category"].isin(categories)) & 
            (df["amount"] < 0)
        ].copy()
    
    # Convert amounts to absolute values
    df_filtered["amount"] = df_filtered["amount"].abs()
    
    # Create date column for different time scales
    if time_scale == "day":
        df_filtered["period"] = df_filtered["date"].dt.strftime("%Y-%m-%d")
        period_name = "Daily"
    elif time_scale == "week":
        df_filtered["period"] = df_filtered["date"].dt.strftime("%Y-W%U")
        period_name = "Weekly"
    elif time_scale == "month":
        df_filtered["period"] = df_filtered["date"].dt.strftime("%Y-%m")
        period_name = "Monthly"
    else:  # year
        df_filtered["period"] = df_filtered["date"].dt.strftime("%Y")
        period_name = "Yearly"
    
    # Group by period and category
    period_totals = df_filtered.groupby(["period", "category"])["amount"].sum().reset_index()
    
    # Sort chronologically
    period_totals = period_totals.sort_values("period")
    
    # Create stacked bar chart
    fig = px.bar(
        period_totals,
        x="period",
        y="amount",
        color="category",
        title=f"{period_name} Expenses by Category",
        barmode="stack"
    )
    
    # Calculate and add total values above each stacked bar
    total_by_period = period_totals.groupby("period")["amount"].sum().reset_index()
    fig.add_trace(go.Scatter(
        x=total_by_period["period"],
        y=total_by_period["amount"],
        mode="text",
        text=total_by_period["amount"].round(0).astype(int),
        textposition="top center",
        showlegend=False,
        textfont=dict(size=12)
    ))
    
    # Update layout
    fig.update_layout(
        xaxis_title="Period",
        yaxis_title="Amount",
        hovermode="x unified",
        xaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=total_by_period["period"].tolist()
        )
    )
    
    return fig
