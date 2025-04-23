import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.data_processor import get_performance_metrics

def render_network_stats():
    """Render the network statistics component"""
    
    st.header("Solana Network Statistics")
    
    # Get network stats from session state
    if 'network_stats' not in st.session_state:
        st.info("Loading network data... Please wait or check connection.")
        return
    
    # Get performance metrics
    performance_metrics = get_performance_metrics()
    
    # Create tabs for different network statistics
    tab1, tab2, tab3 = st.tabs([
        "Performance Metrics",
        "Epoch & Staking Stats",
        "Supply & Inflation"
    ])
    
    # Render performance metrics tab
    with tab1:
        render_performance_metrics(performance_metrics)
    
    # Render epoch and staking statistics tab
    with tab2:
        render_epoch_staking_stats()
    
    # Render supply and inflation tab
    with tab3:
        render_supply_inflation()

def render_performance_metrics(metrics):
    """Render performance metrics tab content"""
    
    st.subheader("Network Performance")
    
    # Display key performance metrics in cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Average TPS",
            f"{metrics.get('avg_tps', 0):.2f}"
        )
    
    with col2:
        st.metric(
            "Maximum TPS (Recent)",
            f"{metrics.get('max_tps', 0):.2f}"
        )
    
    with col3:
        st.metric(
            "Slots Per Second",
            f"{metrics.get('avg_slots_per_second', 0):.2f}"
        )
    
    # Display TPS time series if available
    if 'tps_time_series' in metrics and metrics['tps_time_series']:
        st.subheader("Transactions Per Second (TPS) Over Time")
        
        # Convert time series data to DataFrame
        tps_df = pd.DataFrame(metrics['tps_time_series'], columns=['time_index', 'tps'])
        
        # Create time series chart
        fig = px.line(
            tps_df,
            x='time_index',
            y='tps',
            title='TPS Over Recent Samples',
            labels={'time_index': 'Sample Index', 'tps': 'Transactions Per Second'}
        )
        
        fig.update_layout(
            xaxis_title="Sample Index (Recent → Older)",
            yaxis_title="Transactions Per Second",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Add network throughput gauge
    if 'avg_tps' in metrics:
        # Create gauge for TPS
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=metrics.get('avg_tps', 0),
            title={'text': "Network Throughput (TPS)"},
            gauge={
                'axis': {'range': [0, 5000], 'tickwidth': 1},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 1000], 'color': "lightgray"},
                    {'range': [1000, 2000], 'color': "lightgreen"},
                    {'range': [2000, 4000], 'color': "green"},
                    {'range': [4000, 5000], 'color': "darkgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': metrics.get('avg_tps', 0)
                }
            }
        ))
        
        fig.update_layout(height=300)
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption("""
        **TPS Interpretation:**
        - **0-1000:** Low network utilization
        - **1000-2000:** Moderate network utilization
        - **2000-4000:** High network utilization
        - **4000+:** Very high network utilization
        """)
    
    # Add information about historical averages
    st.subheader("Performance Context")
    st.markdown("""
    The performance metrics shown above represent the current network state.
    
    Solana's theoretical maximum TPS is around 50,000-65,000 TPS, but real-world
    performance depends on transaction complexity, network conditions, and validator
    hardware. The values shown here are from recent performance samples.
    
    Average TPS during normal network operation typically ranges from 1,000 to 4,000 TPS.
    """)

def render_epoch_staking_stats():
    """Render epoch and staking statistics tab content"""
    
    if 'network_stats' not in st.session_state:
        return
    
    stats = st.session_state.network_stats
    
    st.subheader("Epoch Information")
    
    # Create epoch info display
    col1, col2 = st.columns(2)
    
    with col1:
        if 'epoch' in stats:
            st.metric(
                "Current Epoch",
                f"{stats.get('epoch', 0)}"
            )
        
        if 'slotIndex' in stats and 'slotsInEpoch' in stats:
            st.metric(
                "Slot Progress",
                f"{stats.get('slotIndex', 0):,} / {stats.get('slotsInEpoch', 0):,}",
                f"{stats.get('slotIndex', 0) / max(stats.get('slotsInEpoch', 1), 1) * 100:.1f}%"
            )
    
    with col2:
        if 'absoluteSlot' in stats:
            st.metric(
                "Absolute Slot",
                f"{stats.get('absoluteSlot', 0):,}"
            )
        
        if 'blockHeight' in stats:
            st.metric(
                "Block Height",
                f"{stats.get('blockHeight', 0):,}"
            )
    
    # Add epoch progress bar
    if 'slotIndex' in stats and 'slotsInEpoch' in stats:
        epoch_progress = stats.get('slotIndex', 0) / stats.get('slotsInEpoch', 1)
        st.progress(min(epoch_progress, 1.0))
        
        # Calculate and display estimated time remaining in epoch
        slots_remaining = stats.get('slotsInEpoch', 0) - stats.get('slotIndex', 0)
        if 'avg_slots_per_second' in stats and stats.get('avg_slots_per_second', 0) > 0:
            seconds_remaining = slots_remaining / stats.get('avg_slots_per_second', 0.5)
            
            # Convert to days, hours, minutes
            days = int(seconds_remaining // (24 * 3600))
            seconds_remaining = seconds_remaining % (24 * 3600)
            hours = int(seconds_remaining // 3600)
            seconds_remaining = seconds_remaining % 3600
            minutes = int(seconds_remaining // 60)
            
            time_remaining = f"{days}d {hours}h {minutes}m"
            
            st.caption(f"Estimated time remaining in epoch: {time_remaining}")
    
    # Staking statistics
    st.subheader("Staking Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'total_active_stake' in stats:
            st.metric(
                "Total Active Stake",
                f"{stats.get('total_active_stake', 0):,.0f} SOL"
            )
        
        if 'stake_concentration_top10' in stats:
            st.metric(
                "Stake Concentration (Top 10)",
                f"{stats.get('stake_concentration_top10', 0):.2f}%"
            )
    
    with col2:
        if 'staking_rate' in stats:
            st.metric(
                "Staking Rate",
                f"{stats.get('staking_rate', 0):.2f}%"
            )
        
        if 'total_validators' in stats and 'active_validators' in stats:
            active_rate = (stats.get('active_validators', 0) / max(stats.get('total_validators', 1), 1)) * 100
            st.metric(
                "Active Validator Rate",
                f"{active_rate:.2f}%",
                f"{stats.get('active_validators', 0)} out of {stats.get('total_validators', 0)}"
            )
    
    # Create staking rewards information
    st.subheader("Staking Rewards")
    
    # Calculate estimated APY based on inflation rate (if available)
    if 'validator' in stats:
        inflation_rate = stats.get('validator', 0)
        estimated_apy = inflation_rate * 100
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=estimated_apy,
            title={'text': "Estimated Staking APY"},
            gauge={
                'axis': {'range': [0, max(10, estimated_apy * 1.5)]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 5], 'color': "lightgray"},
                    {'range': [5, 8], 'color': "lightgreen"},
                    {'range': [8, max(10, estimated_apy * 1.5)], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': estimated_apy
                }
            },
            delta={'reference': 7.0, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}}
        ))
        
        fig.update_layout(height=300)
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption("""
        **Note:** The estimated staking APY is calculated based on the current validator inflation rate.
        Actual returns may vary based on validator performance, commission rates, and network parameters.
        The comparison value of 7.0% represents a historical reference point.
        """)

def render_supply_inflation():
    """Render supply and inflation tab content"""
    
    if 'network_stats' not in st.session_state:
        return
    
    stats = st.session_state.network_stats
    
    st.subheader("Supply Information")
    
    # Create supply info display
    col1, col2 = st.columns(2)
    
    with col1:
        if 'total_supply' in stats:
            st.metric(
                "Total Supply",
                f"{stats.get('total_supply', 0):,.0f} SOL"
            )
        
        if 'total_active_stake' in stats and 'total_supply' in stats:
            staked_percent = (stats.get('total_active_stake', 0) / max(stats.get('total_supply', 1), 1)) * 100
            st.metric(
                "% of Total Supply Staked",
                f"{staked_percent:.2f}%"
            )
    
    with col2:
        if 'staking_rate' in stats:
            st.metric(
                "% of Circulating Supply Staked",
                f"{stats.get('staking_rate', 0):.2f}%"
            )
        
        if 'supply_info' in st.session_state and 'circulating' in st.session_state.supply_info:
            circulating = float(st.session_state.supply_info['circulating']) / 1_000_000_000
            st.metric(
                "Circulating Supply",
                f"{circulating:,.0f} SOL"
            )
    
    # Create supply breakdown visualization
    if ('supply_info' in st.session_state and 
        'total' in st.session_state.supply_info and 
        'circulating' in st.session_state.supply_info and
        'total_active_stake' in stats):
        
        supply_info = st.session_state.supply_info
        total_supply = float(supply_info['total']) / 1_000_000_000
        circulating = float(supply_info['circulating']) / 1_000_000_000
        non_circulating = total_supply - circulating
        
        total_stake = stats.get('total_active_stake', 0)
        liquid_circulating = circulating - total_stake
        
        # Create supply breakdown pie chart
        supply_data = pd.DataFrame([
            {"Category": "Staked SOL", "Amount": total_stake},
            {"Category": "Liquid Circulating SOL", "Amount": liquid_circulating},
            {"Category": "Non-Circulating SOL", "Amount": non_circulating}
        ])
        
        fig = px.pie(
            supply_data,
            values="Amount",
            names="Category",
            title="Solana Supply Breakdown",
            color="Category",
            color_discrete_map={
                "Staked SOL": "blue",
                "Liquid Circulating SOL": "green",
                "Non-Circulating SOL": "gray"
            }
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Inflation information
    st.subheader("Inflation Information")
    
    # Display inflation metrics
    if 'foundation' in stats and 'validator' in stats and 'total' in stats:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Foundation Inflation",
                f"{stats.get('foundation', 0) * 100:.2f}%"
            )
        
        with col2:
            st.metric(
                "Validator Inflation",
                f"{stats.get('validator', 0) * 100:.2f}%"
            )
        
        with col3:
            st.metric(
                "Total Inflation",
                f"{stats.get('total', 0) * 100:.2f}%"
            )
        
        # Create inflation breakdown visualization
        inflation_data = pd.DataFrame([
            {"Component": "Validator Rewards", "Rate": stats.get('validator', 0) * 100},
            {"Component": "Foundation", "Rate": stats.get('foundation', 0) * 100}
        ])
        
        fig = px.bar(
            inflation_data,
            x="Component",
            y="Rate",
            title="Inflation Rate Breakdown",
            labels={"Rate": "Annual Rate (%)"},
            color="Component",
            color_discrete_map={
                "Validator Rewards": "blue",
                "Foundation": "gray"
            }
        )
        
        fig.update_layout(height=300)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Add information about Solana's inflation schedule
    st.subheader("Inflation Schedule")
    st.markdown("""
    Solana's inflation schedule is designed to decrease over time:
    
    - **Initial inflation rate:** 8% annually
    - **Disinflationary rate:** Decreases by 15% per year
    - **Long-term inflation target:** 1.5% annually
    
    The inflation rewards primarily benefit validators and delegators who actively 
    participate in the network through staking. This incentivizes network security
    and participation.
    """)
