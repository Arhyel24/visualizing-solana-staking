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
        try:
            version = client.get_version()
            # For solders.rpc.responses.GetVersionResp type
            if hasattr(version, 'value'):
                return client
            # For dictionary response type
            elif isinstance(version, dict) and "result" in version:
                return client
            else:
                st.error(f"Unexpected response format from Solana RPC: {type(version)}")
                return None
        except Exception as e:
            st.error(f"Error testing Solana connection: {str(e)}")
            return None
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
        
        # Handle solders.rpc.responses type
        if hasattr(response, 'value'):
            try:
                # Access vote accounts from value attribute
                current = getattr(response.value, 'current', [])
                delinquent = getattr(response.value, 'delinquent', [])
                
                # Convert to dictionaries if they're not already
                if current and not isinstance(current[0], dict):
                    current = [v.__dict__ for v in current]
                if delinquent and not isinstance(delinquent[0], dict):
                    delinquent = [v.__dict__ for v in delinquent]
                
                # Mark delinquent status
                for v in delinquent:
                    v["delinquent"] = True
                for v in current:
                    v["delinquent"] = False
                    
                return current + delinquent
            except Exception as e:
                st.error(f"Error processing validators response: {str(e)}")
                return []
                
        # Handle dictionary response type
        elif isinstance(response, dict) and "result" in response:
            # Combine current and delinquent validators
            current = response["result"]["current"]
            delinquent = response["result"]["delinquent"]
            
            for v in delinquent:
                v["delinquent"] = True
            for v in current:
                v["delinquent"] = False
                
            return current + delinquent
        else:
            st.warning(f"Unexpected response format from get_vote_accounts: {type(response)}")
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
        
        # Handle solders.rpc.responses type
        if hasattr(response, 'value'):
            try:
                # Convert the response.value object to a dictionary
                if hasattr(response.value, '__dict__'):
                    return {k: v for k, v in response.value.__dict__.items() 
                            if not k.startswith('_') and k != 'inner'}
                else:
                    st.warning("Unexpected epoch info response structure")
                    return {}
            except Exception as e:
                st.error(f"Error processing epoch info response: {str(e)}")
                return {}
        
        # Handle dictionary response type
        elif isinstance(response, dict) and "result" in response:
            return response["result"]
        else:
            st.warning(f"Unexpected response format from get_epoch_info: {type(response)}")
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
        
        # Handle solders.rpc.responses type
        if hasattr(response, 'value'):
            try:
                # Access supply info from value attribute
                if hasattr(response.value, 'value'):
                    supply_value = response.value.value
                    # Convert to dictionary if it's not already
                    if hasattr(supply_value, '__dict__'):
                        return {k: v for k, v in supply_value.__dict__.items() 
                                if not k.startswith('_') and k != 'inner'}
                    elif isinstance(supply_value, dict):
                        return supply_value
                    else:
                        st.warning(f"Unexpected supply value type: {type(supply_value)}")
                        return {}
                else:
                    st.warning("Supply response missing 'value' attribute")
                    return {}
            except Exception as e:
                st.error(f"Error processing supply info response: {str(e)}")
                return {}
                
        # Handle dictionary response type
        elif isinstance(response, dict) and "result" in response:
            return response["result"]["value"]
        else:
            st.warning(f"Unexpected response format from get_supply: {type(response)}")
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
        
        # Handle solders.rpc.responses type
        if hasattr(response, 'value'):
            try:
                # Access largest accounts from value attribute
                if hasattr(response.value, 'value'):
                    accounts = response.value.value
                    # Convert accounts to list of dictionaries if they're not already
                    if accounts and not isinstance(accounts[0], dict):
                        try:
                            return [a.__dict__ if hasattr(a, '__dict__') else a for a in accounts]
                        except Exception as e:
                            st.error(f"Error converting accounts to dictionaries: {str(e)}")
                            return []
                    else:
                        return accounts
                else:
                    st.warning("Largest accounts response missing 'value' attribute")
                    return []
            except Exception as e:
                st.error(f"Error processing largest accounts response: {str(e)}")
                return []
                
        # Handle dictionary response type
        elif isinstance(response, dict) and "result" in response:
            return response["result"]["value"]
        else:
            st.warning(f"Unexpected response format from get_largest_accounts: {type(response)}")
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
        
        # Handle solders.rpc.responses type
        if hasattr(response, 'value'):
            try:
                samples = response.value
                # Convert samples to list of dictionaries if they're not already
                if samples and not isinstance(samples[0], dict):
                    try:
                        return [s.__dict__ if hasattr(s, '__dict__') else s for s in samples]
                    except Exception as e:
                        st.error(f"Error converting performance samples to dictionaries: {str(e)}")
                        return []
                else:
                    return samples
            except Exception as e:
                st.error(f"Error processing performance samples response: {str(e)}")
                return []
                
        # Handle dictionary response type
        elif isinstance(response, dict) and "result" in response:
            return response["result"]
        else:
            st.warning(f"Unexpected response format from get_recent_performance_samples: {type(response)}")
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
        
        # Handle solders.rpc.responses type
        if hasattr(response, 'value'):
            try:
                # Convert the response.value object to a dictionary
                if hasattr(response.value, '__dict__'):
                    return {k: v for k, v in response.value.__dict__.items() 
                            if not k.startswith('_') and k != 'inner'}
                elif isinstance(response.value, dict):
                    return response.value
                else:
                    st.warning(f"Unexpected inflation info value type: {type(response.value)}")
                    return {}
            except Exception as e:
                st.error(f"Error processing inflation info response: {str(e)}")
                return {}
                
        # Handle dictionary response type
        elif isinstance(response, dict) and "result" in response:
            return response["result"]
        else:
            st.warning(f"Unexpected response format from get_inflation_rate: {type(response)}")
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
