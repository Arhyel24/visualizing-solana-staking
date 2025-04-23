import streamlit as st
import pandas as pd
import numpy as np
from utils.solana_client import (
    get_validators, get_epoch_info, get_supply_info, 
    get_largest_accounts, get_recent_performance, 
    get_inflation_info, get_total_stake
)

@st.cache_data(ttl=60)  # Cache for 60 seconds
def cache_data(_client, network):
    """
    Fetch and cache all necessary data from Solana blockchain
    
    Args:
        _client: Solana RPC client (underscore prefix to prevent hashing)
        network: Network name for reference
        
    Returns:
        None (data is cached in session state)
    """
    # Fetch basic network information
    validators = get_validators(_client)
    epoch_info = get_epoch_info(_client)
    supply_info = get_supply_info(_client)
    # Skip largest accounts since it's causing issues with the API
    largest_stake_accounts = []
    performance_samples = get_recent_performance(_client)
    inflation_info = get_inflation_info(_client)
    
    # Process and store the data
    st.session_state.validators_df = process_validators_data(validators)
    st.session_state.epoch_info = epoch_info
    st.session_state.supply_info = supply_info
    st.session_state.largest_stake_accounts = largest_stake_accounts
    st.session_state.performance_df = process_performance_data(performance_samples)
    st.session_state.inflation_info = inflation_info
    st.session_state.network_stats = calculate_network_stats(
        validators, epoch_info, supply_info, inflation_info
    )

def process_validators_data(validators):
    """
    Process raw validator data into a pandas DataFrame with additional metrics
    
    Args:
        validators (list): List of validator data from Solana RPC
        
    Returns:
        pd.DataFrame: Processed validator data
    """
    if not validators:
        return pd.DataFrame()
    
    df = pd.DataFrame(validators)
    
    # Convert activated stake from lamports to SOL
    if 'activatedStake' in df.columns:
        df['stakeSOL'] = df['activatedStake'].astype(float) / 1_000_000_000
    
    # Calculate vote success rate
    if 'epochVoteAccount' in df.columns and 'commission' in df.columns:
        # Calculate metrics
        df['voteSuccessRate'] = 0
        for idx, row in df.iterrows():
            if row.get('epochCredits'):
                # Get the most recent epoch credits
                try:
                    # Extract most recent epoch credits (last item in list)
                    recent_credits = row['epochCredits'][-1] if row['epochCredits'] else [0, 0, 0]
                    # Calculate vote success rate
                    prev_credits = recent_credits[1]
                    current_credits = recent_credits[2]
                    
                    if prev_credits > 0:
                        df.at[idx, 'voteSuccessRate'] = (current_credits - prev_credits) / prev_credits
                    else:
                        df.at[idx, 'voteSuccessRate'] = 0
                except (IndexError, TypeError):
                    df.at[idx, 'voteSuccessRate'] = 0
    
    # Sort by stake amount descending
    if 'stakeSOL' in df.columns:
        df = df.sort_values('stakeSOL', ascending=False)
    
    return df

def process_performance_data(performance_samples):
    """
    Process raw performance samples into a pandas DataFrame
    
    Args:
        performance_samples (list): List of performance data from Solana RPC
        
    Returns:
        pd.DataFrame: Processed performance data
    """
    if not performance_samples:
        return pd.DataFrame()
    
    df = pd.DataFrame(performance_samples)
    
    # Convert slot to time index
    if 'slot' in df.columns:
        df = df.sort_values('slot')
        # Use slot numbers as relative time points
        df['time_index'] = range(len(df))
    
    return df

def calculate_network_stats(validators, epoch_info, supply_info, inflation_info):
    """
    Calculate aggregated network statistics
    
    Args:
        validators (list): List of validator data
        epoch_info (dict): Epoch information
        supply_info (dict): Supply information
        inflation_info (dict): Inflation information
        
    Returns:
        dict: Calculated network statistics
    """
    stats = {}
    
    # Calculate basic validator stats
    if validators:
        stats['total_validators'] = len(validators)
        stats['active_validators'] = sum(1 for v in validators if not v.get('delinquent', False))
        stats['delinquent_validators'] = sum(1 for v in validators if v.get('delinquent', False))
        
        # Calculate total stake
        stats['total_active_stake'] = get_total_stake(validators)
        
        # Calculate stake concentration (percentage held by top 10 validators)
        total_stake = stats['total_active_stake']
        if total_stake > 0:
            # Sort validators by stake
            sorted_validators = sorted(validators, key=lambda v: float(v.get('activatedStake', 0)), reverse=True)
            top10_stake = sum(float(v.get('activatedStake', 0)) for v in sorted_validators[:10]) / 1_000_000_000
            stats['stake_concentration_top10'] = (top10_stake / total_stake) * 100
        else:
            stats['stake_concentration_top10'] = 0
    
    # Add epoch information
    if epoch_info:
        stats.update(epoch_info)
    
    # Calculate staking rate
    if supply_info and 'total_active_stake' in stats:
        if 'circulating' in supply_info:
            circulating_supply = float(supply_info['circulating']) / 1_000_000_000  # Convert lamports to SOL
            stats['staking_rate'] = (stats['total_active_stake'] / circulating_supply) * 100
        
        if 'total' in supply_info:
            total_supply = float(supply_info['total']) / 1_000_000_000  # Convert lamports to SOL
            stats['total_supply'] = total_supply
    
    # Add inflation information
    if inflation_info:
        stats.update(inflation_info)
    
    return stats

def get_stake_distribution_data():
    """
    Calculate stake distribution across validators
    
    Returns:
        pd.DataFrame: Processed stake distribution data
    """
    if 'validators_df' not in st.session_state or st.session_state.validators_df.empty:
        return pd.DataFrame()
    
    df = st.session_state.validators_df.copy()
    
    if 'stakeSOL' not in df.columns:
        return pd.DataFrame()
    
    # Calculate cumulative stake percentage
    total_stake = df['stakeSOL'].sum()
    df = df.sort_values('stakeSOL', ascending=False).reset_index(drop=True)
    df['stake_percentage'] = (df['stakeSOL'] / total_stake * 100)
    df['cumulative_percentage'] = df['stake_percentage'].cumsum()
    
    # Create stake distribution buckets
    df['stake_bucket'] = pd.cut(
        df['stakeSOL'], 
        bins=[0, 1000, 10000, 100000, 1000000, float('inf')],
        labels=['<1K SOL', '1K-10K SOL', '10K-100K SOL', '100K-1M SOL', '>1M SOL']
    )
    
    return df

def get_validator_performance_data():
    """
    Get and process validator performance metrics
    
    Returns:
        pd.DataFrame: Processed validator performance data
    """
    if 'validators_df' not in st.session_state or st.session_state.validators_df.empty:
        return pd.DataFrame()
    
    df = st.session_state.validators_df.copy()
    
    # Select and rename relevant columns for performance analysis
    if 'nodePubkey' in df.columns and 'stakeSOL' in df.columns and 'commission' in df.columns:
        perf_df = df[['nodePubkey', 'stakeSOL', 'commission', 'delinquent']]
        if 'voteSuccessRate' in df.columns:
            perf_df['voteSuccessRate'] = df['voteSuccessRate']
        else:
            perf_df['voteSuccessRate'] = 0
        
        perf_df.rename(columns={
            'nodePubkey': 'Validator',
            'stakeSOL': 'Stake (SOL)',
            'commission': 'Commission (%)',
            'voteSuccessRate': 'Vote Success Rate'
        }, inplace=True)
        
        # Sort by stake amount
        perf_df = perf_df.sort_values('Stake (SOL)', ascending=False)
        
        return perf_df
    
    return pd.DataFrame()

def get_performance_metrics():
    """
    Process performance sample data to get network performance metrics
    
    Returns:
        dict: Performance metrics
    """
    metrics = {}
    
    if 'performance_df' not in st.session_state or st.session_state.performance_df.empty:
        return metrics
    
    df = st.session_state.performance_df.copy()
    
    if 'numTransactions' in df.columns and 'numSlots' in df.columns and 'samplePeriodSecs' in df.columns:
        # Calculate TPS (transactions per second)
        df['tps'] = df['numTransactions'] / df['samplePeriodSecs']
        
        # Calculate recent averages
        metrics['avg_tps'] = df['tps'].mean() if not df['tps'].empty else 0
        metrics['max_tps'] = df['tps'].max() if not df['tps'].empty else 0
        metrics['avg_slots_per_second'] = (df['numSlots'] / df['samplePeriodSecs']).mean() if not df.empty else 0
        
        # Get TPS time series for plotting
        metrics['tps_time_series'] = df[['time_index', 'tps']].values.tolist() if 'time_index' in df.columns else []
    
    return metrics
