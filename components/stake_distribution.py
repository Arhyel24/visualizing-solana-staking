import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_processor import get_stake_distribution_data

def render_stake_distribution():
    """Render the stake distribution component"""
    
    st.header("Stake Distribution Analysis")
    
    # Get processed stake distribution data
    df = get_stake_distribution_data()
    
    if df.empty:
        st.info("No stake distribution data available. Please check connection.")
        return
    
    # Distribution analysis options
    analysis_type = st.radio(
        "Select distribution view:",
        ["Stake Concentration", "Distribution by Size", "Gini Coefficient Analysis"],
        horizontal=True
    )
    
    if analysis_type == "Stake Concentration":
        render_concentration_view(df)
    elif analysis_type == "Distribution by Size":
        render_size_distribution(df)
    else:
        render_gini_analysis(df)

def render_concentration_view(df):
    """Render stake concentration visualization"""
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Calculate concentration metrics
        total_validators = len(df)
        
        # Calculate validator thresholds for different percentages of stake
        stake_thresholds = {
            "33% Stake": get_validator_threshold(df, 33),
            "50% Stake": get_validator_threshold(df, 50),
            "66% Stake": get_validator_threshold(df, 66),
            "90% Stake": get_validator_threshold(df, 90),
        }
        
        st.subheader("Stake Concentration Metrics")
        
        # Display metrics
        for label, value in stake_thresholds.items():
            if value is not None:
                percentage = (value / total_validators) * 100
                st.metric(
                    f"Validators controlling {label}",
                    f"{value} validators",
                    f"{percentage:.1f}% of total validators"
                )
    
    with col2:
        # Create cumulative stake distribution curve (Lorenz curve)
        fig = go.Figure()
        
        # Add perfect equality line
        fig.add_trace(go.Scatter(
            x=[0] + list(range(1, len(df) + 1)),
            y=[0] + [i * (100 / len(df)) for i in range(1, len(df) + 1)],
            mode='lines',
            name='Perfect Equality',
            line=dict(color='green', dash='dash')
        ))
        
        # Add actual distribution curve
        fig.add_trace(go.Scatter(
            x=[0] + list(range(1, len(df) + 1)),
            y=[0] + df['cumulative_percentage'].tolist(),
            mode='lines',
            name='Actual Distribution',
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            title="Cumulative Stake Distribution (Lorenz Curve)",
            xaxis_title="Number of Validators (ordered by stake)",
            yaxis_title="Cumulative Stake Percentage",
            yaxis=dict(range=[0, 100]),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_size_distribution(df):
    """Render stake distribution by size buckets"""
    
    # Calculate distribution by stake size buckets
    if 'stake_bucket' in df.columns:
        # Add observed=True to silence the FutureWarning
        size_distribution = df.groupby('stake_bucket', observed=True).agg(
            validator_count=('nodePubkey', 'count'),
            total_stake=('stakeSOL', 'sum'),
        ).reset_index()
        
        # Calculate percentage of total stake
        total_stake = size_distribution['total_stake'].sum()
        size_distribution['stake_percentage'] = (size_distribution['total_stake'] / total_stake) * 100
        
        # Calculate percentage of validators
        total_validators = size_distribution['validator_count'].sum()
        size_distribution['validator_percentage'] = (size_distribution['validator_count'] / total_validators) * 100
        
        # Create dual-axis chart
        fig = go.Figure()
        
        # Bar chart for validator count
        fig.add_trace(go.Bar(
            x=size_distribution['stake_bucket'],
            y=size_distribution['validator_count'],
            name='Validator Count',
            yaxis='y',
            marker_color='royalblue'
        ))
        
        # Line chart for stake percentage
        fig.add_trace(go.Scatter(
            x=size_distribution['stake_bucket'],
            y=size_distribution['stake_percentage'],
            name='Stake Percentage',
            yaxis='y2',
            mode='lines+markers',
            marker=dict(size=10),
            line=dict(color='firebrick', width=3)
        ))
        
        # Update layout with dual y-axes
        fig.update_layout(
            title='Stake Distribution by Size Category',
            xaxis=dict(title='Stake Size Category'),
            yaxis=dict(
                title='Number of Validators',
                side='left',
                showgrid=False
            ),
            yaxis2=dict(
                title='Percentage of Total Stake',
                side='right',
                showgrid=False,
                overlaying='y',
                ticksuffix='%'
            ),
            legend=dict(x=0.01, y=0.99),
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display table of distribution data
        st.subheader("Stake Size Distribution Details")
        
        display_df = size_distribution.copy()
        display_df['total_stake'] = display_df['total_stake'].round(2)
        display_df['stake_percentage'] = display_df['stake_percentage'].round(2)
        display_df['validator_percentage'] = display_df['validator_percentage'].round(2)
        
        display_df.columns = [
            'Stake Size Category', 
            'Validator Count', 
            'Total Stake (SOL)', 
            'Stake Percentage (%)', 
            'Validator Percentage (%)'
        ]
        
        st.dataframe(display_df, use_container_width=True)

def render_gini_analysis(df):
    """Render Gini coefficient analysis for stake distribution"""
    
    st.subheader("Stake Distribution Gini Coefficient")
    
    # Calculate Gini coefficient
    gini = calculate_gini_coefficient(df['stakeSOL'].values)
    
    # Display Gini coefficient with explanation
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Create a gauge chart for the Gini coefficient
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=gini,
            title={'text': "Gini Coefficient"},
            gauge={
                'axis': {'range': [0, 1]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 0.2], 'color': "green"},
                    {'range': [0.2, 0.4], 'color': "lightgreen"},
                    {'range': [0.4, 0.6], 'color': "yellow"},
                    {'range': [0.6, 0.8], 'color': "orange"},
                    {'range': [0.8, 1], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': gini
                }
            }
        ))
        
        fig.update_layout(height=300)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("""
        ### Understanding the Gini Coefficient
        
        The Gini coefficient measures inequality in distribution:
        
        - **0.0 - 0.2**: Very equal distribution
        - **0.2 - 0.4**: Relatively equal distribution
        - **0.4 - 0.6**: Moderate inequality
        - **0.6 - 0.8**: High inequality
        - **0.8 - 1.0**: Extreme inequality
        
        A high Gini coefficient in stake distribution indicates that stake is concentrated among few validators, which may impact decentralization.
        """)
    
    # Display comparative analysis
    st.subheader("Comparative Network Analysis")
    
    # Sample comparison data (in production, this would come from actual historical or cross-network data)
    comparison_data = {
        "Network": ["Solana (Current)", "Solana (6 months ago)", "Ethereum PoS", "Ideal Decentralized"],
        "Gini Coefficient": [gini, min(gini + 0.05, 0.99), 0.7, 0.3],
        "Description": [
            "Current network distribution",
            "Historical reference point",
            "Comparative network",
            "Theoretical ideal target"
        ]
    }
    
    # Create comparison DataFrame
    comparison_df = pd.DataFrame(comparison_data)
    
    # Create horizontal bar chart for comparison
    fig = px.bar(
        comparison_df,
        y="Network",
        x="Gini Coefficient",
        orientation='h',
        color="Gini Coefficient",
        color_continuous_scale=[(0, "green"), (0.5, "yellow"), (1, "red")],
        labels={"Gini Coefficient": "Gini Coefficient (Inequality)"},
        range_x=[0, 1]
    )
    
    fig.update_layout(
        height=300,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("Note: Comparative data is for illustrative purposes. In a production dashboard, this would use actual historical or cross-network data.")

def calculate_gini_coefficient(array):
    """
    Calculate the Gini coefficient for an array of values
    
    Args:
        array: NumPy array of values
        
    Returns:
        float: Gini coefficient between 0 and 1
    """
    import numpy as np
    
    # Make sure array is not empty and contains valid values
    if len(array) == 0 or np.sum(array) == 0:
        return 0
    
    # Sort array in ascending order
    array = np.sort(array)
    
    # Calculate cumulative population and wealth
    n = len(array)
    index = np.arange(1, n + 1)
    
    # Calculate Gini coefficient
    return (np.sum((2 * index - n - 1) * array)) / (n * np.sum(array))

def get_validator_threshold(df, percentage):
    """
    Get the number of validators needed to control a given percentage of stake
    
    Args:
        df: DataFrame with cumulative_percentage column
        percentage: Target percentage of stake
        
    Returns:
        int: Number of validators needed
    """
    if df.empty or 'cumulative_percentage' not in df.columns:
        return None
    
    # Find the first validator index where cumulative percentage exceeds the target
    validators_needed = df[df['cumulative_percentage'] >= percentage].index.min()
    
    # Add 1 to convert from 0-indexed to count
    if pd.notna(validators_needed):
        return validators_needed + 1
    else:
        return len(df)  # If no validator meets the threshold, return total count
