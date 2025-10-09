"""
Robust web scraping service for entity content extraction.

This module provides a clean, well-tested scraping service with:
- Reliable URL extraction from multiple sources
- Robust HTML parsing with fallback strategies
- Structured content extraction preserving webpage layout
- Comprehensive error handling and logging
- Clear separation of concerns
"""

import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class URLExtractionError(ScraperError):
    """Raised when URL extraction fails."""
    pass


class HTMLFetchError(ScraperError):
    """Raised when fetching HTML content fails."""
    pass


class ContentExtractionError(ScraperError):
    """Raised when extracting structured content fails."""
    pass


class URLExtractor:
    """
    Extracts URLs from various sources with fallback strategies.
    """
    
    # Known entity mappings (fallback for dummy data)
    KNOWN_ENTITY_URLS = {
        "Martha Ballard's Diary Online": "https://dohistory.org/diary/about.html",
        "Atharvaveda Paippalāda": "https://www.atharvavedapaippalada.uzh.ch/en.html",
        "Paippalāda Recension of the Atharvaveda": "https://www.atharvavedapaippalada.uzh.ch/en.html",
    }
    
    # Property ID for URL field (standard in metadata curation system)
    URL_PROPERTY_ID = 2
    
    @staticmethod
    def extract_from_entity(entity: Dict[str, Any], 
                           curation_client,
                           fallback_urls: Optional[List[str]] = None) -> List[str]:
        """
        Extract URLs for an entity using multiple strategies.
        
        Strategy priority:
        1. Check if entity has known URL mapping (for dummy entities)
        2. Fetch suggestions from external API and look for URL property
        3. Extract URLs from entity contexts
        4. Use provided fallback URLs
        5. Return empty list (will generate placeholder content)
        
        Args:
            entity: Entity dictionary with id, entity_name, etc.
            curation_client: Client for external curation API (can be None)
            fallback_urls: Optional list of fallback URLs
            
        Returns:
            List of URLs to scrape (may be empty)
        """
        entity_name = entity.get("entity_name", "")
        entity_id = entity.get("id")
        
        logger.info(f"Extracting URLs for entity '{entity_name}' (ID: {entity_id})")
        
        # Strategy 1: Check known entity mappings
        if entity_name in URLExtractor.KNOWN_ENTITY_URLS:
            url = URLExtractor.KNOWN_ENTITY_URLS[entity_name]
            logger.info(f"Found known URL for entity '{entity_name}': {url}")
            return [url]
        
        # Strategy 2 & 3: Try external API if available
        if curation_client and not entity.get("is_dummy", True):
            try:
                # Try to get URL from suggestions
                url = URLExtractor._extract_from_suggestions(entity_id, curation_client)
                if url:
                    logger.info(f"Found URL in suggestions for entity '{entity_name}': {url}")
                    return [url]
                
                # Try to extract from contexts
                urls = URLExtractor._extract_from_contexts(entity_id, curation_client)
                if urls:
                    logger.info(f"Extracted {len(urls)} URL(s) from contexts for entity '{entity_name}'")
                    return urls
                
                logger.warning(f"No URLs found in suggestions or contexts for entity '{entity_name}'")
            except Exception as e:
                logger.error(f"Error extracting URLs from external API: {e}")
        
        # Strategy 4: Use fallback URLs if provided
        if fallback_urls:
            logger.info(f"Using fallback URLs for entity '{entity_name}': {fallback_urls}")
            return fallback_urls
        
        # Strategy 5: No URLs found
        logger.warning(f"No URLs found for entity '{entity_name}', will use placeholder content")
        return []
    
    @staticmethod
    def _extract_from_suggestions(entity_id: int, curation_client) -> Optional[str]:
        """Extract URL from entity suggestions via external API."""
        try:
            all_suggestions = curation_client.get_suggestions()
            entity_suggestions = [s for s in all_suggestions if s.get('entity_id') == entity_id]
            
            if not entity_suggestions:
                return None
            
            # Look for URL suggestion (property_id == 2)
            for suggestion in entity_suggestions:
                if suggestion.get('property_id') == URLExtractor.URL_PROPERTY_ID:
                    custom_value = suggestion.get('custom_value')
                    if custom_value and URLExtractor._is_valid_url(custom_value):
                        return custom_value
            
            return None
        except Exception as e:
            logger.error(f"Failed to extract URL from suggestions: {e}")
            return None
    
    @staticmethod
    def _extract_from_contexts(entity_id: int, curation_client) -> List[str]:
        """Extract URLs from entity contexts via external API."""
        try:
            contexts = curation_client.get_contexts(entity_id)
            if not contexts:
                return []
            
            logger.info(f"Found {len(contexts)} contexts for entity {entity_id}")
            
            # Extract all URLs from context text
            extracted_urls = []
            for ctx in contexts:
                context_value = ctx.get('value', '')
                # Find URLs in context text (http:// or https://)
                found_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', context_value)
                
                # Validate and clean URLs
                for url in found_urls:
                    # Remove trailing punctuation
                    url = url.rstrip('.,;:!?)')
                    if URLExtractor._is_valid_url(url):
                        extracted_urls.append(url)
            
            return extracted_urls
        except Exception as e:
            logger.error(f"Failed to extract URLs from contexts: {e}")
            return []
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Validate that a string is a reasonable URL."""
        if not url or not isinstance(url, str):
            return False
        
        # Basic URL validation
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Must have a domain
        if len(url) < 10:  # http://a.b is minimum
            return False
        
        # Should not contain obvious errors
        invalid_patterns = [' ', '\n', '\t', '<', '>']
        if any(pattern in url for pattern in invalid_patterns):
            return False
        
        return True


class ContentExtractor:
    """
    Extracts structured content from HTML with robust fallbacks.
    """
    
    # Configuration for content extraction
    MAX_CONTENT_LENGTH = 10000  # Characters
    MAX_SECTIONS = 10
    MAX_PARAGRAPHS_PER_SECTION = 20
    MAX_LISTS_PER_SECTION = 5
    MAX_LIST_ITEMS = 10
    MAX_NAV_LENGTH = 500  # Characters
    MAX_FOOTER_LENGTH = 300  # Characters
    
    @staticmethod
    def fetch_html(url: str, timeout: int = 20) -> str:
        """
        Fetch HTML content from a URL with proper error handling.
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            HTML content as string
            
        Raises:
            HTMLFetchError: If fetching fails
        """
        try:
            logger.info(f"Fetching HTML from: {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) CurationPreview/1.0"
            }
            
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                logger.warning(f"Unexpected content type: {content_type}")
            
            logger.info(f"Successfully fetched {len(response.text)} characters from {url}")
            return response.text
            
        except requests.exceptions.Timeout:
            raise HTMLFetchError(f"Request timeout after {timeout}s: {url}")
        except requests.exceptions.ConnectionError as e:
            raise HTMLFetchError(f"Connection error: {url} - {str(e)}")
        except requests.exceptions.HTTPError as e:
            raise HTMLFetchError(f"HTTP error {e.response.status_code}: {url}")
        except Exception as e:
            raise HTMLFetchError(f"Unexpected error fetching {url}: {str(e)}")
    
    @staticmethod
    def extract_structured_content(html: str, url: str) -> Dict[str, Any]:
        """
        Extract structured content from HTML preserving layout.
        
        Args:
            html: HTML content as string
            url: Source URL (for logging)
            
        Returns:
            Dictionary with structured content sections
            
        Raises:
            ContentExtractionError: If parsing fails critically
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            structured = {
                "navigation": None,
                "header": None,
                "main_sections": [],
                "footer": None,
                "metadata": ContentExtractor._extract_metadata(soup)
            }
            
            # Extract navigation
            structured["navigation"] = ContentExtractor._extract_navigation(soup)
            
            # Extract headers
            structured["header"] = ContentExtractor._extract_headers(soup)
            
            # Extract main content sections
            structured["main_sections"] = ContentExtractor._extract_main_sections(soup)
            
            # Extract footer
            structured["footer"] = ContentExtractor._extract_footer(soup)
            
            logger.info(f"Extracted structured content from {url}: "
                       f"{len(structured['main_sections'])} sections, "
                       f"{len(structured.get('header', []))} headers")
            
            return structured
            
        except Exception as e:
            raise ContentExtractionError(f"Failed to extract structured content: {str(e)}")
    
    @staticmethod
    def _extract_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract page metadata (title, description, etc.)."""
        metadata = {}
        
        # Page title
        if soup.title:
            metadata["title"] = soup.title.string.strip() if soup.title.string else None
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata["description"] = meta_desc['content'].strip()
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            metadata["keywords"] = meta_keywords['content'].strip()
        
        # Language
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata["language"] = html_tag['lang']
        
        return metadata
    
    @staticmethod
    def _extract_navigation(soup: BeautifulSoup) -> Optional[str]:
        """Extract navigation elements."""
        nav_elements = soup.find_all(['nav', 'header'], limit=3)
        if not nav_elements:
            return None
        
        nav_text = []
        for nav in nav_elements:
            text = nav.get_text(separator=' ', strip=True)
            if text and len(text) < ContentExtractor.MAX_NAV_LENGTH:
                nav_text.append(text)
        
        return ' | '.join(nav_text) if nav_text else None
    
    @staticmethod
    def _extract_headers(soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract main headers (h1, h2) from page."""
        headers = []
        for tag in ['h1', 'h2']:
            h_tags = soup.find_all(tag, limit=3)
            for h in h_tags:
                text = h.get_text(strip=True)
                if text:
                    headers.append({"level": tag, "text": text})
        return headers
    
    @staticmethod
    def _extract_main_sections(soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract main content sections with paragraphs and lists."""
        main_container = soup.find('main') or soup.find('article') or soup.find('body')
        
        if not main_container:
            logger.warning("No main content container found")
            return []
        
        # Find section-like structures
        sections = main_container.find_all(['section', 'div'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['content', 'main', 'bio', 'profile', 'info', 'about', 'text']
        ))
        
        if not sections:
            # Fallback: look for divs with substantial text
            sections = main_container.find_all(['div', 'section'], recursive=False)
        
        extracted_sections = []
        for section in sections[:ContentExtractor.MAX_SECTIONS]:
            section_data = ContentExtractor._extract_section_content(section)
            if section_data["paragraphs"] or section_data["lists"]:
                extracted_sections.append(section_data)
        
        return extracted_sections
    
    @staticmethod
    def _extract_section_content(section) -> Dict[str, Any]:
        """Extract content from a single section."""
        # Extract section header
        section_header = section.find(['h1', 'h2', 'h3', 'h4', 'h5'])
        section_title = section_header.get_text(strip=True) if section_header else None
        
        # Extract paragraphs
        paragraphs = []
        for p in section.find_all('p', limit=ContentExtractor.MAX_PARAGRAPHS_PER_SECTION):
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Skip very short paragraphs
                paragraphs.append(text)
        
        # Extract lists
        lists = []
        for ul in section.find_all(['ul', 'ol'], limit=ContentExtractor.MAX_LISTS_PER_SECTION):
            items = []
            for li in ul.find_all('li', limit=ContentExtractor.MAX_LIST_ITEMS):
                item_text = li.get_text(strip=True)
                if item_text:
                    items.append(item_text)
            if items:
                lists.append(items)
        
        return {
            "title": section_title,
            "paragraphs": paragraphs,
            "lists": lists
        }
    
    @staticmethod
    def _extract_footer(soup: BeautifulSoup) -> Optional[str]:
        """Extract footer content."""
        footer = soup.find('footer')
        if not footer:
            return None
        
        footer_text = footer.get_text(separator=' ', strip=True)
        if footer_text and len(footer_text) < ContentExtractor.MAX_FOOTER_LENGTH:
            return footer_text
        
        return None
    
    @staticmethod
    def extract_plain_text(html: str) -> str:
        """
        Extract plain text from HTML as fallback.
        
        Args:
            html: HTML content
            
        Returns:
            Plain text content
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()
            # Normalize whitespace
            text = ' '.join(text.split())
            
            # Truncate if too long
            if len(text) > ContentExtractor.MAX_CONTENT_LENGTH:
                text = text[:ContentExtractor.MAX_CONTENT_LENGTH] + "... [Content truncated]"
            
            return text
        except Exception as e:
            logger.error(f"Failed to extract plain text: {e}")
            return ""


class EntityScraper:
    """
    High-level scraper for entity content.
    
    Orchestrates URL extraction, HTML fetching, and content extraction.
    """
    
    def __init__(self, curation_client=None):
        """
        Initialize scraper.
        
        Args:
            curation_client: Optional client for external curation API
        """
        self.curation_client = curation_client
        self.url_extractor = URLExtractor()
        self.content_extractor = ContentExtractor()
    
    def scrape_entity(self, 
                     entity: Dict[str, Any],
                     source: Dict[str, Any],
                     fallback_urls: Optional[List[str]] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Scrape content for an entity.
        
        Args:
            entity: Entity dictionary
            source: Source dictionary
            fallback_urls: Optional fallback URLs
            
        Returns:
            Tuple of (pages_data, errors) where:
            - pages_data: List of scraped page data dictionaries
            - errors: List of error messages encountered
        """
        errors = []
        pages_data = []
        
        try:
            # Extract URLs
            urls = self.url_extractor.extract_from_entity(
                entity, 
                self.curation_client, 
                fallback_urls
            )
            
            if not urls:
                # Generate placeholder content
                placeholder_data = self._generate_placeholder(entity, source)
                pages_data.append(placeholder_data)
                return pages_data, errors
            
            # Scrape each URL
            for url in urls:
                try:
                    page_data = self._scrape_url(url)
                    pages_data.append(page_data)
                except (HTMLFetchError, ContentExtractionError) as e:
                    error_msg = f"Error processing {url}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    
                    # Add error page data
                    pages_data.append({
                        "url": url,
                        "title": f"Error: {str(e)}",
                        "text_content": f"Failed to fetch: {str(e)}",
                        "structured_content": None,
                        "char_count": 0,
                        "word_count": 0,
                        "error": str(e)
                    })
        
        except Exception as e:
            error_msg = f"Unexpected error scraping entity {entity.get('entity_name')}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return pages_data, errors
    
    def _scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape a single URL and extract content.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with scraped page data
            
        Raises:
            HTMLFetchError: If fetching fails
            ContentExtractionError: If extraction fails
        """
        # Fetch HTML
        html = self.content_extractor.fetch_html(url)
        
        # Parse with BeautifulSoup for title
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title else url
        
        # Extract structured content
        structured_content = self.content_extractor.extract_structured_content(html, url)
        
        # Extract plain text as fallback
        text_content = self.content_extractor.extract_plain_text(html)
        
        page_data = {
            "url": url,
            "title": title,
            "text_content": text_content,
            "structured_content": structured_content,
            "char_count": len(text_content),
            "word_count": len(text_content.split())
        }
        
        logger.info(f"Successfully scraped {url}: {page_data['char_count']} chars, "
                   f"{page_data['word_count']} words")
        
        return page_data
    
    def _generate_placeholder(self, entity: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """Generate placeholder content when no URL is available."""
        placeholder_content = f"""
Entity Information:
- Entity: {entity.get('entity_name', 'Unknown')}
- Source: {source.get('name', 'Unknown')}
- Source ID: {entity.get('source_internal_id', 'N/A')}
- Database ID: {entity.get('id', 'N/A')}

This is a real entity from the external metadata curation API. 
No URL was found and no context content is available for this entity.

You can still curate metadata for this entity manually or with AI suggestions.
The AI will work with this placeholder content to generate suggestions.
        """.strip()
        
        logger.info(f"Generated placeholder content for entity: {entity.get('entity_name')}")
        
        return {
            "url": f"placeholder://entity-{entity.get('id')}",
            "title": f"Entity: {entity.get('entity_name', 'Unknown')}",
            "text_content": placeholder_content,
            "structured_content": None,
            "char_count": len(placeholder_content),
            "word_count": len(placeholder_content.split())
        }

