import os
import streamlit as st
from solana.rpc.api import Client
import time
import base64
import requests
import json

# Cache the client to avoid reconnecting on each rerun
@st.cache_resource
def get_solana_client(network="Mainnet Beta"):
    """
    Create and return a Solana RPC client based on the selected network.
    
    Args:
        network (str): The Solana network to connect to (Mainnet Beta, Testnet, or Devnet)
        
    Returns:
        Client: A Solana RPC client instance
    """
    try:
        endpoints = {
            "Mainnet Beta": "https://api.mainnet-beta.solana.com",
            "Testnet": "https://api.testnet.solana.com",
            "Devnet": "https://api.devnet.solana.com"
        }
        
        endpoint = endpoints.get(network, endpoints["Mainnet Beta"])
        client = Client(endpoint)
        
        # Test connection
        version = client.get_version()
        if not version or "result" not in version:
            return None
            
        return client
    except Exception as e:
        st.error(f"Failed to connect to Solana network: {str(e)}")
        return None

def get_validators(client):
    """
    Get the current validators and their info from the Solana blockchain.
    
    Args:
        client (Client): Solana RPC client
        
    Returns:
        list: List of validator data
    """
    try:
        response = client.get_vote_accounts()
        if "result" in response:
            # Combine current and delinquent validators
            current = response["result"]["current"]
            delinquent = response["result"]["delinquent"]
            for v in delinquent:
                v["delinquent"] = True
            for v in current:
                v["delinquent"] = False
                
            return current + delinquent
        else:
            st.warning("Failed to retrieve validator data")
            return []
    except Exception as e:
        st.error(f"Error fetching validators: {str(e)}")
        return []

def get_epoch_info(client):
    """
    Get information about the current epoch.
    
    Args:
        client (Client): Solana RPC client
        
    Returns:
        dict: Current epoch information
    """
    try:
        response = client.get_epoch_info()
        if "result" in response:
            return response["result"]
        else:
            st.warning("Failed to retrieve epoch information")
            return {}
    except Exception as e:
        st.error(f"Error fetching epoch info: {str(e)}")
        return {}

def get_supply_info(client):
    """
    Get the current supply information from Solana.
    
    Args:
        client (Client): Solana RPC client
        
    Returns:
        dict: Supply information
    """
    try:
        response = client.get_supply()
        if "result" in response:
            return response["result"]["value"]
        else:
            st.warning("Failed to retrieve supply information")
            return {}
    except Exception as e:
        st.error(f"Error fetching supply info: {str(e)}")
        return {}

def get_largest_accounts(client, filter_type="stake"):
    """
    Get the largest accounts of a specified type from Solana.
    
    Args:
        client (Client): Solana RPC client
        filter_type (str): Type of accounts to filter (e.g., "stake")
        
    Returns:
        list: Largest accounts data
    """
    try:
        response = client.get_largest_accounts(filter=filter_type)
        if "result" in response:
            return response["result"]["value"]
        else:
            st.warning(f"Failed to retrieve largest {filter_type} accounts")
            return []
    except Exception as e:
        st.error(f"Error fetching largest accounts: {str(e)}")
        return []

def get_recent_performance(client):
    """
    Get recent performance samples for the network.
    
    Args:
        client (Client): Solana RPC client
        
    Returns:
        list: Performance samples
    """
    try:
        response = client.get_recent_performance_samples(limit=60)  # Last 60 samples
        if "result" in response:
            return response["result"]
        else:
            st.warning("Failed to retrieve performance samples")
            return []
    except Exception as e:
        st.error(f"Error fetching performance samples: {str(e)}")
        return []

def get_inflation_info(client):
    """
    Get current inflation information.
    
    Args:
        client (Client): Solana RPC client
        
    Returns:
        dict: Inflation information
    """
    try:
        response = client.get_inflation_rate()
        if "result" in response:
            return response["result"]
        else:
            st.warning("Failed to retrieve inflation information")
            return {}
    except Exception as e:
        st.error(f"Error fetching inflation info: {str(e)}")
        return {}

def get_total_stake(validators):
    """
    Calculate the total active stake from validator data.
    
    Args:
        validators (list): List of validator data
        
    Returns:
        float: Total active stake in SOL
    """
    total_stake = 0
    for validator in validators:
        try:
            total_stake += float(validator.get("activatedStake", 0)) / 1_000_000_000  # Convert lamports to SOL
        except (ValueError, TypeError):
            pass
    return total_stake
