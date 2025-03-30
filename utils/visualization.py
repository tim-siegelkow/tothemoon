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
    Create a line chart of monthly income and expenses.
    
    Args:
        df: DataFrame with transaction data
        
    Returns:
        plotly.graph_objects.Figure: Line chart figure
    """
    # Group by month and calculate income and expense
    monthly = df.groupby("month_name").agg({
        "amount": [
            ("Income", lambda x: x[x > 0].sum()),
            ("Expense", lambda x: abs(x[x < 0].sum())),
            ("Net", "sum")
        ]
    })
    
    # Flatten multi-level column index
    monthly.columns = [f"{col[1]}" for col in monthly.columns]
    monthly = monthly.reset_index()
    
    # Create line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly["month_name"],
        y=monthly["Income"],
        name="Income",
        line=dict(color="green", width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly["month_name"],
        y=monthly["Expense"],
        name="Expense",
        line=dict(color="red", width=2)
    ))
    
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
        hovermode="x unified"
    )
    
    return fig

def create_category_bar_chart(df, months=3, transaction_type="Expense"):
    """
    Create a bar chart of transactions by category for the last N months.
    
    Args:
        df: DataFrame with transaction data
        months: Number of months to include
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
    monthly_category = df_filtered.groupby(["month_name", "category"])["amount"].sum().reset_index()
    
    # Create bar chart
    fig = px.bar(
        monthly_category,
        x="month_name",
        y="amount",
        color="category",
        title=f"Monthly {transaction_type} by Category (Last {months} Months)",
        barmode="stack"
    )
    
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Amount",
        legend_title="Category",
        hovermode="x unified"
    )
    
    return fig
