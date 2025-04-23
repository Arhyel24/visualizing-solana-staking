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
            # Primary endpoints
            "Mainnet Beta": "https://api.devnet.solana.com",  # Using devnet for testing as it has more lenient rate limits
            "Testnet": "https://api.testnet.solana.com",
            "Devnet": "https://api.devnet.solana.com"
        }
        
        endpoint = endpoints.get(network, endpoints["Devnet"])  # Default to Devnet
        
        # Add retry logic for more reliable connection
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                client = Client(endpoint)
                
                # Test connection
                version = client.get_version()
                
                # For solders.rpc.responses.GetVersionResp type
                if hasattr(version, 'value'):
                    st.success(f"Successfully connected to {network} ({endpoint})")
                    return client
                # For dictionary response type
                elif isinstance(version, dict) and "result" in version:
                    st.success(f"Successfully connected to {network} ({endpoint})")
                    return client
                else:
                    st.warning(f"Unexpected response format from Solana RPC: {type(version)}")
                    if attempt < max_retries - 1:
                        st.info(f"Retrying connection in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(retry_delay)
                    else:
                        st.error("Failed to establish a proper connection after multiple attempts")
                        return None
            except Exception as e:
                if attempt < max_retries - 1:
                    st.warning(f"Connection attempt {attempt+1}/{max_retries} failed: {str(e)}")
                    st.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    st.error(f"Failed to connect to Solana network after {max_retries} attempts: {str(e)}")
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
                    current_dicts = []
                    for v in current:
                        # RpcVoteAccountInfo structure format based on testing
                        v_dict = {}
                        # Node/Vote pubkeys
                        v_dict['nodePubkey'] = str(v.node_pubkey) if hasattr(v, 'node_pubkey') else ''
                        v_dict['votePubkey'] = str(v.vote_pubkey) if hasattr(v, 'vote_pubkey') else ''
                        # Stake and commission
                        v_dict['activatedStake'] = v.activated_stake if hasattr(v, 'activated_stake') else 0
                        v_dict['commission'] = v.commission if hasattr(v, 'commission') else 0
                        # Vote info
                        v_dict['lastVote'] = v.last_vote if hasattr(v, 'last_vote') else 0
                        v_dict['rootSlot'] = v.root_slot if hasattr(v, 'root_slot') else 0
                        # Epoch credits and status
                        v_dict['epochCredits'] = v.epoch_credits if hasattr(v, 'epoch_credits') else []
                        v_dict['epochVoteAccount'] = v.epoch_vote_account if hasattr(v, 'epoch_vote_account') else False
                            
                        current_dicts.append(v_dict)
                    current = current_dicts
                    
                if delinquent and not isinstance(delinquent[0], dict):
                    delinquent_dicts = []
                    for v in delinquent:
                        # RpcVoteAccountInfo structure format based on testing
                        v_dict = {}
                        # Node/Vote pubkeys
                        v_dict['nodePubkey'] = str(v.node_pubkey) if hasattr(v, 'node_pubkey') else ''
                        v_dict['votePubkey'] = str(v.vote_pubkey) if hasattr(v, 'vote_pubkey') else ''
                        # Stake and commission
                        v_dict['activatedStake'] = v.activated_stake if hasattr(v, 'activated_stake') else 0
                        v_dict['commission'] = v.commission if hasattr(v, 'commission') else 0
                        # Vote info
                        v_dict['lastVote'] = v.last_vote if hasattr(v, 'last_vote') else 0
                        v_dict['rootSlot'] = v.root_slot if hasattr(v, 'root_slot') else 0
                        # Epoch credits and status
                        v_dict['epochCredits'] = v.epoch_credits if hasattr(v, 'epoch_credits') else []
                        v_dict['epochVoteAccount'] = v.epoch_vote_account if hasattr(v, 'epoch_vote_account') else False
                            
                        delinquent_dicts.append(v_dict)
                    delinquent = delinquent_dicts
                
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
                # Create a dictionary with the expected fields
                epoch_info = {}
                
                # Map the properties from response.value to our expected dictionary
                if hasattr(response.value, 'epoch'):
                    epoch_info['epoch'] = response.value.epoch
                if hasattr(response.value, 'slot_index'):
                    epoch_info['slotIndex'] = response.value.slot_index
                if hasattr(response.value, 'slots_in_epoch'):
                    epoch_info['slotsInEpoch'] = response.value.slots_in_epoch
                if hasattr(response.value, 'absolute_slot'):
                    epoch_info['absoluteSlot'] = response.value.absolute_slot
                if hasattr(response.value, 'block_height'):
                    epoch_info['blockHeight'] = response.value.block_height
                if hasattr(response.value, 'transaction_count'):
                    epoch_info['transactionCount'] = response.value.transaction_count
                
                return epoch_info
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
                # Create a dictionary with the expected fields
                supply_info = {}
                
                # Extract supply information directly from the response value
                if hasattr(response.value, 'total'):
                    supply_info['total'] = response.value.total
                if hasattr(response.value, 'circulating'):
                    supply_info['circulating'] = response.value.circulating
                if hasattr(response.value, 'non_circulating'):
                    supply_info['nonCirculating'] = response.value.non_circulating
                
                return supply_info
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

def get_largest_accounts(client, filter_type=None):
    """
    This method is disabled due to API compatibility issues.
    
    Args:
        client (Client): Solana RPC client
        filter_type (str, optional): Ignored
        
    Returns:
        list: Empty list
    """
    return []  # Returning an empty list to avoid errors

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
                samples = []
                
                # Extract performance sample information
                for sample in response.value:
                    if hasattr(sample, 'slot'):
                        sample_dict = {
                            'slot': sample.slot,
                            'numTransactions': getattr(sample, 'num_transactions', 0),
                            'numSlots': getattr(sample, 'num_slots', 1),
                            'samplePeriodSecs': getattr(sample, 'sample_period_secs', 60)
                        }
                        samples.append(sample_dict)
                
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
                # Create dictionary with expected fields
                inflation_info = {}
                
                # Extract inflation rate information
                if hasattr(response.value, 'total'):
                    inflation_info['total'] = response.value.total
                if hasattr(response.value, 'validator'):
                    inflation_info['validator'] = response.value.validator
                if hasattr(response.value, 'foundation'):
                    inflation_info['foundation'] = response.value.foundation
                if hasattr(response.value, 'epoch'):
                    inflation_info['epoch'] = response.value.epoch
                    
                return inflation_info
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
