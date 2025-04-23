import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time

def render_overview():
    """Render the network overview component"""
    
    st.header("Solana Network Overview")
    
    if ('network_stats' not in st.session_state or 
        'validators_df' not in st.session_state or
        st.session_state.validators_df.empty):
        st.info("Loading network data... Please wait or check connection.")
        return
    
    stats = st.session_state.network_stats
    
    # Create metric grid
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Active Validators", 
            f"{stats.get('active_validators', 0):,}",
            f"{stats.get('delinquent_validators', 0)} delinquent"
        )
        
        if 'staking_rate' in stats:
            st.metric(
                "Staking Rate", 
                f"{stats.get('staking_rate', 0):.2f}%"
            )
        
        if 'slot' in stats and 'absoluteSlot' in stats:
            progress = stats.get('slot', 0) / max(stats.get('absoluteSlot', 1), 1) * 100
            st.metric(
                "Current Slot", 
                f"{stats.get('slot', 0):,}",
                f"Epoch Progress: {progress:.1f}%"
            )
    
    with col2:
        if 'total_active_stake' in stats:
            st.metric(
                "Total Active Stake", 
                f"{stats.get('total_active_stake', 0):,.0f} SOL"
            )
        
        if 'epoch' in stats and 'slotIndex' in stats and 'slotsInEpoch' in stats:
            epoch_progress = stats.get('slotIndex', 0) / stats.get('slotsInEpoch', 1) * 100
            st.metric(
                "Current Epoch", 
                f"{stats.get('epoch', 0)}",
                f"Progress: {epoch_progress:.1f}%"
            )
            
            # Epoch Progress Bar
            st.progress(min(epoch_progress / 100, 1.0))
    
    with col3:
        if 'total_supply' in stats:
            st.metric(
                "Total Supply", 
                f"{stats.get('total_supply', 0):,.0f} SOL"
            )
        
        if 'validator' in stats and 'total' in stats:
            st.metric(
                "Inflation Rate", 
                f"{stats.get('validator', 0) * 100:.2f}%",
                f"Total: {stats.get('total', 0) * 100:.2f}%"
            )
    
    # Display stake concentration visualization
    st.subheader("Stake Concentration")
    
    if 'validators_df' in st.session_state and not st.session_state.validators_df.empty:
        # Top 20 validators by stake
        validators_df = st.session_state.validators_df.copy()
        if 'nodePubkey' in validators_df.columns and 'stakeSOL' in validators_df.columns:
            top_validators = validators_df.sort_values('stakeSOL', ascending=False).head(20)
            
            fig = px.bar(
                top_validators,
                x='nodePubkey',
                y='stakeSOL',
                labels={'nodePubkey': 'Validator', 'stakeSOL': 'Stake (SOL)'},
                title='Top 20 Validators by Stake'
            )
            
            fig.update_layout(
                xaxis_title='Validator',
                yaxis_title='Stake (SOL)',
                xaxis_tickangle=-45,
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Display network health indicators
    render_health_indicators()

def render_health_indicators():
    """Render the network health indicators component"""
    
    if 'network_stats' not in st.session_state:
        return
    
    stats = st.session_state.network_stats
    
    st.subheader("Network Health Indicators")
    
    # Create colored indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'stake_concentration_top10' in stats:
            concentration = stats['stake_concentration_top10']
            
            # Define thresholds for stake concentration
            if concentration < 33:
                color = "green"
                status = "Healthy"
            elif concentration < 50:
                color = "orange"
                status = "Moderate"
            else:
                color = "red"
                status = "Concerning"
            
            st.markdown(f"""
            <div style="border-left: 5px solid {color}; padding-left: 10px;">
                <h4>Stake Concentration (Top 10)</h4>
                <p style="font-size: 24px; font-weight: bold;">{concentration:.1f}%</p>
                <p>Status: {status}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if 'delinquent_validators' in stats and 'total_validators' in stats:
            delinquent_pct = (stats['delinquent_validators'] / max(stats['total_validators'], 1)) * 100
            
            # Define thresholds for delinquent validators
            if delinquent_pct < 5:
                color = "green"
                status = "Healthy"
            elif delinquent_pct < 10:
                color = "orange"
                status = "Moderate"
            else:
                color = "red"
                status = "Concerning"
            
            st.markdown(f"""
            <div style="border-left: 5px solid {color}; padding-left: 10px;">
                <h4>Delinquent Validators</h4>
                <p style="font-size: 24px; font-weight: bold;">{delinquent_pct:.1f}%</p>
                <p>Status: {status}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if 'staking_rate' in stats:
            staking_rate = stats['staking_rate']
            
            # Define thresholds for staking rate
            if staking_rate > 70:
                color = "green"
                status = "Healthy"
            elif staking_rate > 50:
                color = "orange"
                status = "Moderate"
            else:
                color = "red"
                status = "Concerning"
            
            st.markdown(f"""
            <div style="border-left: 5px solid {color}; padding-left: 10px;">
                <h4>Staking Rate</h4>
                <p style="font-size: 24px; font-weight: bold;">{staking_rate:.1f}%</p>
                <p>Status: {status}</p>
            </div>
            """, unsafe_allow_html=True)
