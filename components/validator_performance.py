import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.data_processor import get_validator_performance_data

def render_validator_performance():
    """Render the validator performance component"""
    
    st.header("Validator Performance Analysis")
    
    # Get processed validator performance data
    df = get_validator_performance_data()
    
    if df.empty:
        st.info("No validator performance data available. Please check connection.")
        return
    
    # Add filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_stake = st.slider(
            "Minimum Stake (SOL)",
            min_value=0,
            max_value=int(df['Stake (SOL)'].max() * 0.8),
            value=0,
            step=1000
        )
    
    with col2:
        max_commission = st.slider(
            "Maximum Commission (%)",
            min_value=0,
            max_value=100,
            value=100,
            step=5
        )
    
    with col3:
        show_delinquent = st.checkbox("Show Delinquent Validators", value=True)
    
    # Apply filters
    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df['Stake (SOL)'] >= filter_stake]
    filtered_df = filtered_df[filtered_df['Commission (%)'] <= max_commission]
    
    if not show_delinquent:
        filtered_df = filtered_df[~filtered_df['delinquent']]
    
    # Show validator count after filtering
    st.caption(f"Showing {len(filtered_df)} validators based on filters")
    
    # Create tabs for different analysis views
    tab1, tab2, tab3 = st.tabs([
        "Performance Overview",
        "Detailed Metrics",
        "Commission Analysis"
    ])
    
    # Render different analysis views in tabs
    with tab1:
        render_performance_overview(filtered_df)
    
    with tab2:
        render_detailed_metrics(filtered_df)
    
    with tab3:
        render_commission_analysis(filtered_df)

def render_performance_overview(df):
    """Render performance overview visualization"""
    
    st.subheader("Validator Performance Overview")
    
    # Create a scatter plot for stake vs. commission
    fig = px.scatter(
        df,
        x="Stake (SOL)",
        y="Commission (%)",
        size="Stake (SOL)",
        color="Vote Success Rate",
        hover_name="Validator",
        color_continuous_scale="Viridis",
        title="Validator Performance Overview",
        log_x=True  # Use log scale for stake amount
    )
    
    # Mark delinquent validators
    if 'delinquent' in df.columns:
        delinquent_validators = df[df['delinquent'] == True]
        
        if not delinquent_validators.empty:
            fig.add_trace(
                go.Scatter(
                    x=delinquent_validators["Stake (SOL)"],
                    y=delinquent_validators["Commission (%)"],
                    mode="markers",
                    marker=dict(
                        symbol="x",
                        size=10,
                        color="red",
                        line=dict(width=2, color="DarkRed")
                    ),
                    name="Delinquent"
                )
            )
    
    fig.update_layout(
        xaxis_title="Stake Amount (SOL, log scale)",
        yaxis_title="Commission (%)",
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add tooltip explanation
    st.caption("""
    **Chart Explanation:**
    - **Bubble Size:** Represents the amount of SOL staked with the validator
    - **Color:** Represents vote success rate (darker = higher)
    - **X-axis:** Stake amount in SOL (logarithmic scale)
    - **Y-axis:** Commission percentage
    - **Red X markers:** Delinquent validators
    """)

def render_detailed_metrics(df):
    """Render detailed validator metrics"""
    
    st.subheader("Detailed Validator Metrics")
    
    # Create a table of validators with their metrics
    # Remove delinquent column from display
    display_df = df.drop('delinquent', axis=1).copy()
    
    # Format columns
    display_df['Stake (SOL)'] = display_df['Stake (SOL)'].round(2)
    if 'Vote Success Rate' in display_df.columns:
        display_df['Vote Success Rate'] = display_df['Vote Success Rate'].apply(
            lambda x: f"{x:.4f}" if pd.notna(x) else "N/A"
        )
    
    # Add custom sorting
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        column_config={
            "Validator": st.column_config.TextColumn("Validator"),
            "Stake (SOL)": st.column_config.NumberColumn("Stake (SOL)", format="%.2f"),
            "Commission (%)": st.column_config.NumberColumn("Commission (%)"),
            "Vote Success Rate": st.column_config.NumberColumn("Vote Success Rate")
        }
    )
    
    # Add histograms of key metrics
    col1, col2 = st.columns(2)
    
    with col1:
        # Create histogram of vote success rate
        if 'Vote Success Rate' in df.columns:
            # Convert to numeric, handling any non-numeric values
            vote_success_rate = pd.to_numeric(df['Vote Success Rate'], errors='coerce')
            
            fig = px.histogram(
                vote_success_rate,
                title="Distribution of Vote Success Rate",
                labels={"value": "Vote Success Rate", "count": "Number of Validators"}
            )
            
            fig.update_layout(
                xaxis_title="Vote Success Rate",
                yaxis_title="Number of Validators",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Create histogram of commission rates
        fig = px.histogram(
            df,
            x="Commission (%)",
            title="Distribution of Commission Rates",
            labels={"Commission (%)": "Commission Rate (%)", "count": "Number of Validators"}
        )
        
        fig.update_layout(
            xaxis_title="Commission Rate (%)",
            yaxis_title="Number of Validators",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_commission_analysis(df):
    """Render commission rate analysis"""
    
    st.subheader("Commission Rate Analysis")
    
    # Calculate statistics by commission rate buckets
    commission_buckets = pd.cut(
        df['Commission (%)'],
        bins=[0, 1, 5, 10, 20, 50, 100],
        labels=['0-1%', '1-5%', '5-10%', '10-20%', '20-50%', '50-100%']
    )
    
    # Add observed=True to silence the FutureWarning
    commission_stats = df.groupby(commission_buckets, observed=True).agg(
        validator_count=('Validator', 'count'),
        total_stake=('Stake (SOL)', 'sum'),
        avg_stake=('Stake (SOL)', 'mean')
    ).reset_index()
    
    # Calculate percentage of total stake
    total_stake = commission_stats['total_stake'].sum()
    commission_stats['stake_percentage'] = (commission_stats['total_stake'] / total_stake) * 100
    
    # Calculate percentage of validators
    total_validators = commission_stats['validator_count'].sum()
    commission_stats['validator_percentage'] = (commission_stats['validator_count'] / total_validators) * 100
    
    # Create dual-axis chart
    fig = go.Figure()
    
    # Bar chart for validator count percentage
    fig.add_trace(go.Bar(
        x=commission_stats['Commission (%)'],
        y=commission_stats['validator_percentage'],
        name='% of Validators',
        yaxis='y',
        marker_color='royalblue',
        text=commission_stats['validator_count'].apply(lambda x: f"{x} validators"),
        textposition='auto'
    ))
    
    # Line chart for stake percentage
    fig.add_trace(go.Scatter(
        x=commission_stats['Commission (%)'],
        y=commission_stats['stake_percentage'],
        name='% of Total Stake',
        yaxis='y2',
        mode='lines+markers',
        marker=dict(size=10),
        line=dict(color='firebrick', width=3)
    ))
    
    # Update layout with dual y-axes
    fig.update_layout(
        title='Commission Rate Analysis',
        xaxis=dict(title='Commission Rate Range'),
        yaxis=dict(
            title='% of Validators',
            side='left',
            showgrid=False,
            ticksuffix='%'
        ),
        yaxis2=dict(
            title='% of Total Stake',
            side='right',
            showgrid=False,
            overlaying='y',
            ticksuffix='%'
        ),
        legend=dict(x=0.01, y=0.99),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Additional statistics
    col1, col2 = st.columns(2)
    
    with col1:
        # Average stake by commission rate
        fig = px.bar(
            commission_stats,
            x='Commission (%)',
            y='avg_stake',
            title='Average Stake by Commission Rate',
            labels={'avg_stake': 'Average Stake (SOL)'}
        )
        
        fig.update_layout(
            xaxis_title="Commission Rate Range",
            yaxis_title="Average Stake per Validator (SOL)",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Commission Rate Insights")
        
        # Find most common commission rate
        if not df.empty:
            most_common_commission = df['Commission (%)'].mode().iloc[0]
            commission_weighted_avg = np.average(
                df['Commission (%)'], 
                weights=df['Stake (SOL)']
            )
            
            st.metric(
                "Most Common Commission Rate", 
                f"{most_common_commission}%"
            )
            
            st.metric(
                "Stake-Weighted Average Commission", 
                f"{commission_weighted_avg:.2f}%"
            )
            
            # Calculate correlation between stake and commission
            correlation = df['Stake (SOL)'].corr(df['Commission (%)'])
            
            # Interpret the correlation
            if abs(correlation) < 0.1:
                interpretation = "Very weak or no relationship"
            elif abs(correlation) < 0.3:
                interpretation = "Weak relationship"
            elif abs(correlation) < 0.5:
                interpretation = "Moderate relationship"
            elif abs(correlation) < 0.7:
                interpretation = "Strong relationship"
            else:
                interpretation = "Very strong relationship"
                
            direction = "positive" if correlation > 0 else "negative"
            
            st.metric(
                "Correlation: Stake vs Commission", 
                f"{correlation:.3f}",
                f"{interpretation} ({direction})"
            )
