import os
import json
from typing import Optional, List, Dict, Any
from Bio import Entrez
from langchain_core.tools import tool

# Set your email here or in environment variables
# Entrez requires an email address to be set.
Entrez.email = os.getenv("ENTREZ_EMAIL", "adityachanna04@gmail.com")
Entrez.api_key = os.getenv("ENTREZ_API_KEY")

@tool
def pubmed_search_tool(query: str, max_results: int = 7) -> str:
    """
    Searches PubMed for biomedical literature using the BioPython Entrez API.
    
    Args:
        query (str): The search query (e.g., "COVID-19 vaccine", "cancer immunotherapy").
        max_results (int): The maximum number of results to return. Defaults to 5.
        
    Returns:
        str: A JSON string containing a list of dictionaries, where each dictionary represents a paper
             and contains 'title', 'pub_date', 'authors', 'journal', and 'abstract'.
    """
    try:
        # 1. Search for IDs
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record["IdList"]
        
        if not id_list:
            return json.dumps([{"message": "No results found for the given query."}])

        # 2. Fetch details for the found IDs
        # We use Medline parser or just read as text/xml. 
        # Let's use XML for easier parsing of fields.
        handle = Entrez.efetch(db="pubmed", id=id_list, retmode="xml")
        papers = Entrez.read(handle)
        handle.close()
        
        results = []
        if 'PubmedArticle' not in papers:
             return json.dumps([{"message": "No article details found."}])

        for article in papers['PubmedArticle']:
            medline_citation = article.get('MedlineCitation', {})
            article_data = medline_citation.get('Article', {})
            
            # Extract Title
            title = article_data.get('ArticleTitle', 'No title')
            
            # Extract Abstract
            abstract_list = article_data.get('Abstract', {}).get('AbstractText', [])
            abstract = " ".join(abstract_list) if abstract_list else "No abstract available."
            
            # Extract Authors
            author_list = article_data.get('AuthorList', [])
            authors = []
            for author in author_list:
                last_name = author.get('LastName', '')
                initials = author.get('Initials', '')
                authors.append(f"{last_name} {initials}")
            
            # Extract Journal and Date
            journal = article_data.get('Journal', {}).get('Title', 'Unknown Journal')
            pub_date_data = article_data.get('Journal', {}).get('JournalIssue', {}).get('PubDate', {})
            pub_date = f"{pub_date_data.get('Year', '')} {pub_date_data.get('Month', '')}"
            
            results.append({
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "journal": journal,
                "pub_date": pub_date,
                "pmid": medline_citation.get('PMID', '')
            })
            
        return json.dumps(results)

    except Exception as e:
        return json.dumps([{"error": str(e)}])
