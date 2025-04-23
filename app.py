import streamlit as st
import time
from components.overview import render_overview
from components.stake_distribution import render_stake_distribution
from components.validator_performance import render_validator_performance
from components.network_stats import render_network_stats
from utils.solana_client import get_solana_client
from utils.data_processor import cache_data

# Set page configuration
st.set_page_config(
    page_title="Solana Staking Dashboard",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for storing data across reruns
if 'data_timestamp' not in st.session_state:
    st.session_state.data_timestamp = None
    st.session_state.refresh_rate = 120  # Default refresh of 2 minutes as requested
    st.session_state.auto_refresh = False  # Auto-refresh off by default as requested

# App Header
st.title("🌞 Solana Staking Ecosystem Dashboard")
st.markdown("Monitor the health of Solana's staking ecosystem with real-time metrics and interactive visualizations.")

# Sidebar configuration
with st.sidebar:
    st.title("Dashboard Controls")
    
    # Network selector
    network = st.selectbox(
        "Solana Network",
        options=["Mainnet Beta", "Testnet", "Devnet"],
        index=0  # Default to Mainnet Beta as requested
    )
    
    # Connection Status
    solana_client = get_solana_client(network)
    if solana_client:
        st.success(f"Connected to Solana {network} 🌐")
    else:
        st.error(f"Failed to connect to Solana {network} ❌")
        st.stop()
    
    # Refresh rate settings
    st.subheader("Data Refresh Settings")
    st.session_state.refresh_rate = st.slider(
        "Refresh rate (seconds)", 
        min_value=30, 
        max_value=300, 
        value=st.session_state.refresh_rate,
        step=30
    )
    
    st.session_state.auto_refresh = st.checkbox(
        "Auto-refresh data", 
        value=st.session_state.auto_refresh
    )
    
    if st.button("Refresh Now"):
        st.session_state.data_timestamp = None
        st.rerun()
    
    # Help information
    with st.expander("About this dashboard"):
        st.markdown("""
        This dashboard provides real-time information about Solana's staking ecosystem.
        
        **Data shown includes:**
        - Stake distribution across validators
        - Validator performance metrics
        - Network participation statistics
        - Overall health indicators
        
        Data is fetched directly from the Solana blockchain using the Solana Web3.js API.
        """)

# Auto-refresh mechanism
current_time = time.time()
if (st.session_state.data_timestamp is None or 
    (st.session_state.auto_refresh and 
     current_time - st.session_state.data_timestamp > st.session_state.refresh_rate)):
    with st.spinner("Fetching latest data from Solana blockchain..."):
        # Get and cache the data
        cache_data(solana_client, network)
        st.session_state.data_timestamp = current_time

# Display last updated time
if st.session_state.data_timestamp:
    st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.session_state.data_timestamp))}")

# Main dashboard tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Network Overview", 
    "Stake Distribution", 
    "Validator Performance", 
    "Network Statistics"
])

# Render each tab
with tab1:
    render_overview()
    
with tab2:
    render_stake_distribution()
    
with tab3:
    render_validator_performance()
    
with tab4:
    render_network_stats()

# Footer
st.markdown("---")
st.caption("Data is fetched directly from the Solana blockchain. All metrics are calculated based on current blockchain state.")
