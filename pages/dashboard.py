import streamlit as st
import pandas as pd
import os
from datetime import datetime

from database.db import get_session, get_all_transactions
from utils.visualization import (
    prepare_data_for_viz, generate_monthly_summary, 
    create_category_pie_chart, create_monthly_trend_chart, create_category_bar_chart, create_dining_expenses_chart
)
from utils.csv_handler import export_transactions_to_csv
from config import DEFAULT_CATEGORIES, DATA_DIR

def dashboard_page():
    st.title("Financial Dashboard")
    
    # Get all transactions
    session = get_session()
    transactions = get_all_transactions(session)
    
    # If no transactions, show message
    if not transactions:
        st.info("No transactions found. Please import data to view the dashboard.")
        return
    
    # Prepare data for visualization
    df = prepare_data_for_viz(transactions)
    
    # Generate summary statistics
    summary = generate_monthly_summary(df)
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Income", f"${summary['total_income']:.2f}")
    
    with col2:
        st.metric("Total Expenses", f"${summary['total_expense']:.2f}")
    
    with col3:
        st.metric("Net Savings", f"${summary['net_savings']:.2f}")
        
    # Add filters
    st.subheader("Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=st.session_state.filter_start_date,
            key="dashboard_start_date"
        )
        st.session_state.filter_start_date = datetime.combine(start_date, datetime.min.time())
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=st.session_state.filter_end_date,
            key="dashboard_end_date"
        )
        st.session_state.filter_end_date = datetime.combine(end_date, datetime.max.time())
    
    # Filter data
    df_filtered = df[
        (df["date"] >= st.session_state.filter_start_date) &
        (df["date"] <= st.session_state.filter_end_date)
    ]
    
    # If no filtered data, show message
    if df_filtered.empty:
        st.info("No transactions found for the selected date range.")
        return
    
    # Monthly trend chart
    st.subheader("Monthly Income vs Expense Trends")
    monthly_trend_chart = create_monthly_trend_chart(df_filtered)
    st.plotly_chart(monthly_trend_chart, use_container_width=True)
    
    # Category charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Expense Distribution by Category")
        expense_pie_chart = create_category_pie_chart(df_filtered, "Expense")
        st.plotly_chart(expense_pie_chart, use_container_width=True)
    
    with col2:
        st.subheader("Income Distribution by Category")
        income_pie_chart = create_category_pie_chart(df_filtered, "Income")
        st.plotly_chart(income_pie_chart, use_container_width=True)
    
    # Monthly category breakdown
    st.subheader("Monthly Expense Breakdown by Category")
    months_to_show = st.slider("Number of months to display", 1, 12, 3)
    category_bar_chart = create_category_bar_chart(df_filtered, months=months_to_show)
    st.plotly_chart(category_bar_chart, use_container_width=True)
    
    # Category Expenses Over Time Chart
    st.subheader("Category Expenses Over Time")
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_categories = st.multiselect(
            "Select categories to display",
            DEFAULT_CATEGORIES,
            default=["Dining"],
            key="category_time_select"
        )
    with col2:
        time_scale = st.radio(
            "Select time scale",
            ["day", "week", "month", "year"],
            horizontal=True,
            index=2  # Default to monthly view
        )
    
    if selected_categories:
        dining_chart = create_dining_expenses_chart(df_filtered, time_scale=time_scale, categories=selected_categories)
        st.plotly_chart(dining_chart, use_container_width=True)
    else:
        st.warning("Please select at least one category to display the chart.")
    
    # Export button
    if st.button("Export Filtered Data to CSV"):
        export_path = os.path.join(DATA_DIR, f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if export_transactions_to_csv([t for t in transactions if t.date >= st.session_state.filter_start_date and t.date <= st.session_state.filter_end_date], export_path):
            st.success(f"Data exported to {export_path}")
        else:
            st.error("Error exporting data") 