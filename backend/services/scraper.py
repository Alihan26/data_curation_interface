"""
Robust web scraping service for entity content extraction.

This module provides a clean, well-tested scraping service with:
- Reliable URL extraction from multiple sources
- Robust HTML parsing with fallback strategies
- Structured content extraction preserving webpage layout
- Comprehensive error handling and logging
- Clear separation of concerns
- Modular content extractors for different content types
"""

import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from bs4 import BeautifulSoup, Tag
import requests

from services.content_extractors import (
    ParagraphExtractor, 
    ListExtractor, 
    TableExtractor,
    SectionExtractor
)
from services.content_types import get_config

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
            
            # Extract all URLs from contexts
            extracted_urls = []
            for ctx in contexts:
                context_type = ctx.get('type', '')
                context_value = ctx.get('value', '')
                
                # Strategy 1: Check if context type is 'website' or 'url'
                if context_type.lower() in ('website', 'url', 'link', 'homepage'):
                    if URLExtractor._is_valid_url(context_value):
                        extracted_urls.append(context_value)
                        logger.info(f"Found URL in context type '{context_type}': {context_value}")
                        continue
                
                # Strategy 2: Extract URLs from context text using regex
                found_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', context_value)
                
                # Validate and clean URLs
                for url in found_urls:
                    # Remove trailing punctuation
                    url = url.rstrip('.,;:!?)')
                    if URLExtractor._is_valid_url(url):
                        extracted_urls.append(url)
                        logger.info(f"Extracted URL from context value: {url}")
            
            logger.info(f"Extracted {len(extracted_urls)} total URLs from contexts")
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
    
    # Configuration for content extraction - Less restrictive
    MAX_CONTENT_LENGTH = 20000  # Characters - Increased
    MAX_SECTIONS = 15  # Increased
    MAX_PARAGRAPHS_PER_SECTION = 30  # Increased
    MAX_LISTS_PER_SECTION = 8  # Increased
    MAX_LIST_ITEMS = 20  # Increased
    MAX_NAV_LENGTH = 800  # Characters - Increased
    MAX_FOOTER_LENGTH = 500  # Characters - Increased
    
    # Contact section keywords for merging
    CONTACT_SECTION_KEYWORDS = (
        'contact', 'contact information', 'kontakt',
        'address', 'adresse', 'email', 'e-mail',
        'telefon', 'tel', 'phone', 'room', 'raum', 'office', 'büro'
    )
    
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
            
            # Auto-detect content type and get appropriate config
            config = get_config(url, soup)
            logger.debug(f"Detected content type: {config.content_type.value}")
            
            # Extract main content sections using modular extractor with config
            section_extractor = SectionExtractor(config)
            structured["main_sections"] = section_extractor.extract(soup)
            
            # Extract footer
            structured["footer"] = ContentExtractor._extract_footer(soup)
            
            # Extract contact information from the entire page as a final pass
            logger.info("Extracting contact information...")
            contact_tables = ContentExtractor._extract_page_contact_info(soup)
            logger.info(f"Contact info extraction result: {contact_tables}")
            
            if contact_tables:
                ContentExtractor._inject_contact_info(structured, contact_tables)
                logger.info("Merged/added contact information into structured content")
            else:
                logger.info("No contact information found")
            
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
    
    # NOTE: The old extraction methods (_extract_main_sections, _extract_section_content, etc.)
    # are no longer used. We now use SectionExtractor from content_extractors.py which provides
    # better handling of different website structures and is configured per content type.
    
    @staticmethod
    def _extract_simple_table(table: Tag) -> Optional[Dict[str, Any]]:
        """Extract table with minimal filtering."""
        rows = []
        for tr in table.find_all('tr'):
            cells = tr.find_all(['td', 'th'])
            non_empty = [c for c in cells if c.get_text(strip=True) and c.get_text(strip=True) != '\xa0']
            
            if len(non_empty) >= 2:
                label = non_empty[0].get_text(strip=True)
                value_cell = non_empty[1]
                
                # Preserve newlines for addresses
                value = value_cell.get_text(separator='\n', strip=True)
                value = '\n'.join(line.strip() for line in value.split('\n') if line.strip())
                
                # Extract from mailto/tel links
                for a in value_cell.find_all('a', href=True):
                    href = a['href'].strip()
                    if href.lower().startswith('mailto:'):
                        value = href.split(':', 1)[1].split('?', 1)[0]
                        break
                    elif href.lower().startswith('tel:'):
                        value = href.split(':', 1)[1]
                        break
                
                # Clean obfuscation
                value = value.replace(' AT ', '@').replace(' at ', '@')
                value = value.replace(' DOT ', '.').replace(' dot ', '.')
                
                if label and value:
                    rows.append({'label': label, 'value': value})
        
        return {'rows': rows} if rows else None
    
    @staticmethod
    def _extract_simple_dl(dl: Tag) -> Optional[Dict[str, Any]]:
        """Extract definition list with minimal filtering."""
        rows = []
        dts = dl.find_all('dt', recursive=False)
        dds = dl.find_all('dd', recursive=False)
        
        for i in range(min(len(dts), len(dds))):
            label = dts[i].get_text(strip=True)
            dd = dds[i]
            
            value = dd.get_text(separator='\n', strip=True)
            value = '\n'.join(line.strip() for line in value.split('\n') if line.strip())
            
            # Extract from links
            for a in dd.find_all('a', href=True):
                href = a['href'].strip()
                if href.lower().startswith('mailto:'):
                    value = href.split(':', 1)[1].split('?', 1)[0]
                    break
                elif href.lower().startswith('tel:'):
                    value = href.split(':', 1)[1]
                    break
            
            value = value.replace(' AT ', '@').replace(' at ', '@')
            value = value.replace(' DOT ', '.').replace(' dot ', '.')
            
            if label and value:
                rows.append({'label': label, 'value': value})
        
        return {'rows': rows} if rows else None
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
    def _extract_page_contact_info(soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract contact information from attributes, links, and obfuscated data."""
        import re, json
        contact_rows = []
        seen = set()
        
        def add_row(label: str, value: str):
            if not value:
                return
            label = (label or '').strip() or 'Contact'
            value = value.strip()
            key = (label.lower(), value.lower())
            if key not in seen:
                seen.add(key)
                contact_rows.append({'label': label, 'value': value})
                logger.info(f"Added contact: {label} = {value}")
        
        # 0) First, extract from ALL tables on the page using simple extraction
        logger.info("Extracting contact info from tables...")
        for table in soup.find_all('table'):
            # Skip tables in nav/footer
            if table.find_parent(['nav', 'footer', 'aside']):
                continue
            
            table_data = ContentExtractor._extract_simple_table(table)
            if table_data:
                # Add all rows that look like contact info
                for row in table_data['rows']:
                    label = row['label']
                    value = row['value']
                    # Only add if it's contact-related
                    if any(keyword in label.lower() for keyword in ['email', 'e-mail', 'phone', 'tel', 'address', 'adresse', 'room', 'office', 'kontakt', 'website', 'homepage', 'orcid', 'linkedin', 'profiles']):
                        add_row(label, value)
        
        # Extract from ALL definition lists
        logger.info("Extracting contact info from definition lists...")
        for dl in soup.find_all('dl'):
            if dl.find_parent(['nav', 'footer', 'aside']):
                continue
            
            dl_data = ContentExtractor._extract_simple_dl(dl)
            if dl_data:
                for row in dl_data['rows']:
                    label = row['label']
                    value = row['value']
                    if any(keyword in label.lower() for keyword in ['email', 'e-mail', 'phone', 'tel', 'address', 'adresse', 'room', 'office', 'kontakt']):
                        add_row(label, value)
        
        # 1) Mailto/tel links anywhere in the page (incl. obfuscation)
        for a in soup.find_all('a', href=True):
            href = (a['href'] or '').strip()
            if href.lower().startswith('mailto:'):
                email = href.split(':', 1)[1].split('?', 1)[0].strip()
                # Try to decode Cloudflare obfuscation if present
                cf = a.get('data-cfemail')
                if cf:
                    decoded = ContentExtractor._decode_cf_email(cf)
                    if decoded:
                        email = decoded
                email = (email
                         .replace('(at)', '@')
                         .replace('[at]', '@')
                         .replace(' at ', '@')
                         .replace(' AT ', '@')
                         .replace('(dot)', '.')
                         .replace('[dot]', '.')
                         .replace(' dot ', '.'))
                add_row('Email', email)
            elif href.lower().startswith('tel:'):
                phone = href.split(':', 1)[1]
                add_row('Phone', phone)
        
        # 2) Cloudflare obfuscation spans (not inside an <a>)
        for el in soup.find_all(attrs={'data-cfemail': True}):
            decoded = ContentExtractor._decode_cf_email(el.get('data-cfemail'))
            if decoded:
                add_row('Email', decoded)
        
        # 3) Common data attributes used for emails
        for el in soup.find_all(True):
            attrs = {k.lower(): (v if isinstance(v, str) else ' '.join(v) if isinstance(v, list) else str(v))
                     for k, v in el.attrs.items()}
            if 'data-email' in attrs:
                add_row('Email', attrs['data-email'])
            # Combine user/domain patterns
            user = None
            domain = None
            for k, v in attrs.items():
                lk = k.lower()
                if any(p in lk for p in ('data-user', 'data-mail-user', 'data-local', 'data-name', 'data-account')):
                    user = user or v
                if any(p in lk for p in ('data-domain', 'data-mail-domain', 'data-host')):
                    domain = domain or v
            if user and domain:
                add_row('Email', f'{user}@{domain}')
        
        # 4) <address> tags
        for addr in soup.find_all('address'):
            text = addr.get_text(separator=' ', strip=True)
            if text and len(text) > 5:
                add_row('Address', ' '.join(text.split()))
        
        # 5) JSON-LD (schema.org Person/Organization/PostalAddress)
        for script in soup.find_all('script', type=lambda t: t and 'ld+json' in t):
            try:
                data = json.loads(script.string or '')
            except Exception:
                continue
            def handle(obj):
                if not isinstance(obj, dict):
                    return
                t = (obj.get('@type') or '').lower()
                if t in ('person', 'organization'):
                    if obj.get('email'):
                        # email may be like "mailto:email@domain"
                        email = obj['email']
                        if isinstance(email, str):
                            email = email.replace('mailto:', '').strip()
                            add_row('Email', email)
                    if obj.get('telephone'):
                        tel = obj['telephone']
                        if isinstance(tel, str):
                            add_row('Phone', tel)
                    if obj.get('address'):
                        addr = obj['address']
                        if isinstance(addr, dict):
                            parts = [addr.get(k, '') for k in ('streetAddress', 'postalCode', 'addressLocality', 'addressRegion', 'addressCountry')]
                            addr_text = ' '.join([p for p in parts if p]).strip()
                            if addr_text:
                                add_row('Address', addr_text)
                elif t == 'postaladdress':
                    parts = [obj.get(k, '') for k in ('streetAddress', 'postalCode', 'addressLocality', 'addressRegion', 'addressCountry')]
                    addr_text = ' '.join([p for p in parts if p]).strip()
                    if addr_text:
                        add_row('Address', addr_text)
            if isinstance(data, list):
                for item in data:
                    handle(item)
            else:
                handle(data)
        
        # 6) Visible text fallback (including obfuscated emails)
        page_text = soup.get_text(separator=' ', strip=True)
        
        # Regular emails with @
        email_re = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        for email in re.findall(email_re, page_text):
            add_row('Email', email)
        
        # Obfuscated emails (e.g., "juergen.bernard AT uzh.ch")
        obfuscated_email_re = r'\b[A-Za-z0-9._%+-]+\s+(?:AT|at)\s+[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        for obfuscated in re.findall(obfuscated_email_re, page_text):
            email = obfuscated.replace(' AT ', '@').replace(' at ', '@')
            add_row('Email', email)
        
        # Phone numbers
        phone_re = r'(\+41\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}|\d{3}\s?\d{3}\s?\d{2}\s?\d{2}|\+\d{1,3}\s?\d{1,4}\s?\d{1,4}\s?\d{1,4})'
        for phone in re.findall(phone_re, page_text):
            add_row('Phone', phone)
        
        logger.info(f"Total contact rows extracted: {len(contact_rows)}")
        return [{'rows': contact_rows}] if contact_rows else []
    
    @staticmethod
    def _decode_cf_email(cfemail: str) -> Optional[str]:
        """Decode Cloudflare obfuscated email."""
        try:
            r = bytes.fromhex(cfemail)
            key = r[0]
            decoded = ''.join(chr(b ^ key) for b in r[1:])
            return decoded
        except Exception:
            return None
    
    @staticmethod
    def _inject_contact_info(structured: Dict[str, Any], contact_tables: List[Dict[str, Any]]) -> None:
        """Inject contact information into structured content, merging with existing contact sections."""
        # Find an existing contact-like section
        target_idx = None
        for i, sec in enumerate(structured.get('main_sections', [])):
            title = (sec.get('title') or '').strip().lower()
            if any(k in title for k in ContentExtractor.CONTACT_SECTION_KEYWORDS):
                target_idx = i
                break
        
        # If found, merge into its tables; otherwise, create a new section at the top
        if target_idx is None:
            structured['main_sections'].insert(0, {
                'title': 'Contact Information',
                'paragraphs': [],
                'lists': [],
                'tables': contact_tables
            })
            logger.info("Created new contact information section")
            return
        
        # Merge rows, avoiding duplicates
        sec = structured['main_sections'][target_idx]
        logger.info(f"Merging contact info into existing section: {sec.get('title')}")
        
        if 'tables' not in sec or not isinstance(sec['tables'], list):
            sec['tables'] = []
        existing_rows_keyset = set()
        for tbl in sec['tables']:
            for row in tbl.get('rows', []):
                key = (row.get('label', '').strip().lower(), row.get('value', '').strip().lower())
                existing_rows_keyset.add(key)
        
        for tbl in contact_tables:
            for row in tbl.get('rows', []):
                key = (row.get('label', '').strip().lower(), row.get('value', '').strip().lower())
                if key not in existing_rows_keyset:
                    # Add into the first table if exists, otherwise append a new table
                    if sec['tables']:
                        sec['tables'][0].setdefault('rows', []).append(row)
                    else:
                        sec['tables'].append({'rows': [row]})
                    existing_rows_keyset.add(key)
                    logger.info(f"Added new contact row: {row.get('label')} = {row.get('value')}")
    


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
        
        # Generate clean text from structured content (not from raw HTML!)
        text_content = self._generate_text_from_structured(structured_content)
        
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
    
    def _generate_text_from_structured(self, structured_content: Dict[str, Any]) -> str:
        """
        Generate clean, readable text from structured content.
        
        This creates text from the cleaned structured content instead of raw HTML,
        ensuring that navigation, scripts, and other noise is excluded.
        
        Args:
            structured_content: The structured content dictionary
            
        Returns:
            Clean text representation of the content
        """
        text_parts = []
        
        # Add page headers
        if structured_content.get('header'):
            for header in structured_content['header']:
                text_parts.append(header['text'])
                text_parts.append('')  # blank line
        
        # Add main content sections
        if structured_content.get('main_sections'):
            for section in structured_content['main_sections']:
                # Add section title if present
                if section.get('title'):
                    text_parts.append(section['title'])
                    text_parts.append('')
                
                # Add paragraphs
                for paragraph in section.get('paragraphs', []):
                    text_parts.append(paragraph)
                    text_parts.append('')
                
                # Add lists
                for list_items in section.get('lists', []):
                    for item in list_items:
                        text_parts.append(f"• {item}")
                    text_parts.append('')
                
                # Add tables (contact info, etc.)
                for table in section.get('tables', []):
                    for row in table.get('rows', []):
                        label = row.get('label', '')
                        value = row.get('value', '')
                        if label and value:
                            text_parts.append(f"{label}: {value}")
                    text_parts.append('')
        
        # Join all parts with newlines and clean up
        text = '\n'.join(text_parts)
        
        # Remove excessive blank lines (more than 2 in a row)
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        
        return text.strip()
    
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


