"""Internet search tool for Werewolf game research capabilities."""

import requests
import urllib.parse
import re
import time
import logging
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InternetSearchTool:
    """
    Internet search tool for gathering strategic information.
    Uses DuckDuckGo API and Wikipedia for reliable results.
    """
    
    def __init__(self):
        """Initialize the search tool."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_duckduckgo(self, query: str) -> Dict[str, Any]:
        """Search using DuckDuckGo Instant Answer API.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary containing search results
        """
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'abstract': data.get('Abstract', ''),
                'abstract_url': data.get('AbstractURL', ''),
                'answer': data.get('Answer', ''),
                'answer_type': data.get('AnswerType', ''),
                'related_topics': data.get('RelatedTopics', [])[:3]
            }
            
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            return {}
    
    def search_wikipedia(self, query: str) -> Dict[str, Any]:
        """Search Wikipedia for information.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary containing Wikipedia results
        """
        try:
            search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'title': data.get('title', ''),
                    'extract': data.get('extract', ''),
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', '')
                }
        except Exception as e:
            logger.warning(f"Wikipedia search failed: {e}")
        
        return {}
    
    def search(self, query: str) -> str:
        """Main search function.
        
        Args:
            query: Search query string
            
        Returns:
            Formatted search results
        """
        try:
            logger.info(f"Searching for: '{query}'")
            
            result = f"Search Results for: {query}\n"
            result += "=" * 50 + "\n\n"
            
            # Try DuckDuckGo
            ddg_data = self.search_duckduckgo(query)
            
            if ddg_data.get('abstract'):
                result += f"Summary: {ddg_data['abstract']}\n"
                if ddg_data.get('abstract_url'):
                    result += f"Source: {ddg_data['abstract_url']}\n"
                result += "\n"
            
            if ddg_data.get('answer'):
                result += f"Quick Answer: {ddg_data['answer']}\n"
                result += "\n"
            
            if ddg_data.get('related_topics'):
                result += "Related Information:\n"
                for i, topic in enumerate(ddg_data['related_topics'], 1):
                    if isinstance(topic, dict) and 'Text' in topic:
                        result += f"{i}. {topic['Text'][:150]}...\n"
                        if 'FirstURL' in topic:
                            result += f"   URL: {topic['FirstURL']}\n"
                result += "\n"
            
            # If DuckDuckGo didn't return much, try Wikipedia
            if len(result) < 200:
                wiki_data = self.search_wikipedia(query)
                if wiki_data.get('extract'):
                    result += f"Wikipedia: {wiki_data['title']}\n"
                    result += f"Summary: {wiki_data['extract']}\n"
                    if wiki_data.get('url'):
                        result += f"URL: {wiki_data['url']}\n"
            
            return result if len(result) > 100 else f"Limited results found for: {query}"
            
        except Exception as e:
            error_msg = f"Search error: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def fetch_url(self, url: str) -> str:
        """Fetch content from a specific URL.
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Formatted web page content
        """
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            content = response.text
            
            # Extract title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else "No title"
            
            # Clean HTML
            content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
            content = re.sub(r'<style.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', '', content)
            
            # Clean whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            result = f"Title: {title}\nURL: {url}\nContent:\n{'-'*40}\n"
            result += clean_text[:2000]
            
            if len(clean_text) > 2000:
                result += "\n... [Content truncated]"
            
            return result
            
        except Exception as e:
            return f"Error fetching {url}: {str(e)}"


def internet_search(query: str) -> str:
    """
    Standalone function for internet search.
    
    Args:
        query: The search query
        
    Returns:
        Search results as formatted string
    """
    tool = InternetSearchTool()
    return tool.search(query)


def simple_research_agent(query: str) -> str:
    """
    Simple research agent that performs web search.
    
    Args:
        query: Research query
        
    Returns:
        Research results
    """
    search_tool = InternetSearchTool()
    
    # Perform search
    results = search_tool.search(query)
    
    # Format results for agent use
    formatted_results = f"Research Results:\n{'-'*30}\n"
    formatted_results += results
    formatted_results += f"\n{'-'*30}\n"
    formatted_results += "This information can be used to inform strategic decisions.\n"
    
    return formatted_results


if __name__ == "__main__":
    # Test the search tool
    tool = InternetSearchTool()
    result = tool.search("werewolf mafia game strategy")
    print(result)
