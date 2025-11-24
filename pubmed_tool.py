# pubmed_tool.py

import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class PubMedTool:
    def __init__(self, timeout=10):
        self.timeout = timeout

    def fetch_data(self, query):
        if not self.validate_input(query):
            logging.error("Invalid input.")
            return None
        
        try:
            logging.info(f"Fetching data for query: {query}")
            response = requests.get(f'https://pubmed.ncbi.nlm.nih.gov/?term={query}', timeout=self.timeout)
            response.raise_for_status()  # Raise an error for bad responses
            
            # XML size validation (e.g., checking length) 
            if len(response.content) > 2**20:  # Let's assume 1MB is the limit for example
                logging.error("Response size too large.")
                return None
            
            return response.content
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data: {e}")
            return None

    def validate_input(self, query):
        return isinstance(query, str) and len(query) > 0
