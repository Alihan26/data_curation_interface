"""
Modular content extraction strategies.

This module provides pluggable extractors for different content types.
Each extractor is focused and composable.
Uses configuration to adapt to different website structures.
"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
import logging
from services.content_types import ContentConfig, RESEARCHER_PROFILE_CONFIG

logger = logging.getLogger(__name__)


class BaseExtractor:
    """Base class for all content extractors."""
    
    def extract(self, element: Tag) -> Any:
        """Extract content from an HTML element."""
        raise NotImplementedError


class ParagraphExtractor(BaseExtractor):
    """Extracts paragraphs from <p> tags and text-containing divs."""
    
    def __init__(self, config: ContentConfig = RESEARCHER_PROFILE_CONFIG):
        self.config = config
        self.min_length = config.min_paragraph_length
        self.deduplicate = config.deduplicate
        self.seen = set() if self.deduplicate else None
    
    def extract(self, element: Tag) -> List[str]:
        """Extract all unique paragraphs from <p> tags and text-rich divs."""
        paragraphs = []
        
        # Strategy 0: Check if element ITSELF is a high-value content div without nested divs
        # If so, extract text directly from it
        element_classes = element.get('class', [])
        is_content_div = any(
            keyword in str(element_classes).lower() 
            for keyword in self.config.content_div_patterns  # Use config patterns
        )
        
        if is_content_div and len(element.find_all('div')) == 0 and not element.find_all('p'):
            text = element.get_text(strip=True)
            if len(text) >= self.min_length:
                normalized = ' '.join(text.lower().split())
                if not self.deduplicate or normalized not in self.seen:
                    paragraphs.append(text)
                    if self.deduplicate:
                        self.seen.add(normalized)
                    return paragraphs  # Return early if we extracted from element itself
        
        # Strategy 1: Extract from <p> tags
        for p in element.find_all('p'):
            text = p.get_text(strip=True)
            if len(text) < self.min_length:
                continue
            
            # Deduplicate if enabled
            if self.deduplicate:
                normalized = ' '.join(text.lower().split())
                if normalized in self.seen:
                    continue
                self.seen.add(normalized)
            
            paragraphs.append(text)
        
        # Strategy 2: ALSO look for text in high-value content divs
        # Uses configured patterns to support different website structures
        content_divs = element.find_all('div', class_=lambda x: x and any(
            keyword in str(x).lower() 
            for keyword in self.config.content_div_patterns  # Use config patterns
        ))
        
        for div in content_divs:
            # Skip if the div has <p> tags (they'll be caught by Strategy 1)
            if div.find_all('p'):
                continue
            
            # Skip if too many nested divs (it's a container, not content)
            if len(div.find_all('div')) > 3:
                continue
            
            text = div.get_text(strip=True)
            if len(text) < self.min_length:
                continue
            
            # Deduplicate if enabled
            if self.deduplicate:
                normalized = ' '.join(text.lower().split())
                if normalized in self.seen:
                    continue
                self.seen.add(normalized)
            
            paragraphs.append(text)
        
        return paragraphs


class ListExtractor(BaseExtractor):
    """Extracts list items from <ul> and <ol> tags."""
    
    def __init__(self, config: ContentConfig = RESEARCHER_PROFILE_CONFIG, max_items: int = 20):  # Increased from 10
        self.config = config
        self.max_items = max_items
        self.deduplicate = config.deduplicate
        self.seen = set() if self.deduplicate else None
    
    def extract(self, element: Tag) -> List[List[str]]:
        """Extract all lists with their items."""
        lists = []
        
        for list_elem in element.find_all(['ul', 'ol']):
            items = []
            for li in list_elem.find_all('li', recursive=False)[:self.max_items]:
                text = li.get_text(strip=True)
                if not text:
                    continue
                
                # Deduplicate if enabled
                if self.deduplicate:
                    normalized = ' '.join(text.lower().split())
                    if normalized in self.seen:
                        continue
                    self.seen.add(normalized)
                
                items.append(text)
            
            if items:
                lists.append(items)
        
        return lists


class TableExtractor(BaseExtractor):
    """Extracts structured data from tables and definition lists."""
    
    def extract_tables(self, element: Tag) -> List[Dict[str, Any]]:
        """Extract data from <table> elements."""
        tables = []
        
        for table in element.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = tr.find_all(['td', 'th'])
                
                # Filter out empty cells
                non_empty = [c for c in cells if c.get_text(strip=True)]
                
                if len(non_empty) >= 2:
                    label = non_empty[0].get_text(strip=True)
                    value = non_empty[1].get_text(separator=' | ', strip=True)
                    value = ' '.join(value.split())  # Normalize whitespace
                    
                    if label and value:
                        rows.append({"label": label, "value": value})
            
            if rows:
                tables.append({"rows": rows})
        
        return tables
    
    def extract_definition_lists(self, element: Tag) -> List[Dict[str, Any]]:
        """Extract data from <dl> elements."""
        lists = []
        
        for dl in element.find_all('dl'):
            rows = []
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')
            
            for i in range(min(len(dts), len(dds))):
                label = dts[i].get_text(strip=True)
                value = dds[i].get_text(separator=' | ', strip=True)
                value = ' '.join(value.split())
                
                if label and value:
                    rows.append({"label": label, "value": value})
            
            if rows:
                lists.append({"rows": rows})
        
        return lists
    
    def extract(self, element: Tag) -> List[Dict[str, Any]]:
        """Extract all structured data (tables + definition lists)."""
        return self.extract_tables(element) + self.extract_definition_lists(element)


class SectionExtractor(BaseExtractor):
    """Extracts content sections - SIMPLIFIED to capture everything."""
    
    def __init__(self, config: ContentConfig = RESEARCHER_PROFILE_CONFIG):
        self.config = config
    
    def extract(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extract ALL content, organized by h2 headings.
        SIMPLE ALGORITHM: No complex logic, no filtering.
        """
        # Find main container
        main = soup.find('main') or soup.find('article') or soup.find('body')
        if not main:
            return []
        
        # Clean up
        main_copy = BeautifulSoup(str(main), 'html.parser')
        for tag in main_copy.find_all(['script', 'style', 'nav', 'footer', 'aside']):
            tag.decompose()
        
        sections = []
        
        # Find all h2 headings
        h2_tags = main_copy.find_all('h2')
        
        # Filter obvious navigation headings
        skip_words = ['navigation', 'menu', 'quicklinks', 'footer', 'sprachwahl',
                     'wichtige seiten', 'rechtliches', 'impressum', 'weiterführende',
                     'sie sind hier', 'hauptnavigation', 'weitere informationen']
        h2_content = [h for h in h2_tags 
                      if not any(kw in h.get_text(strip=True).lower() for kw in skip_words)]
        
        # STEP 1: Extract content BEFORE first h2 (bio, contact, etc.)
        if h2_content:
            before_section = self._extract_all_before_heading(main_copy, h2_content[0])
            if before_section:
                sections.append(before_section)
        
        # STEP 2: Extract content for each h2 section
        for i, h2 in enumerate(h2_content):
            next_h2 = h2_content[i + 1] if i + 1 < len(h2_content) else None
            section = self._extract_section_between_headings(h2, next_h2)
            if section:
                sections.append(section)
        
        # STEP 3: If no h2 headings, extract everything
        if not sections:
            sections = [self._extract_everything(main_copy)]
        
        return sections
    
    def _extract_all_before_heading(self, container: Tag, first_heading: Tag) -> Optional[Dict[str, Any]]:
        """Extract ALL content before the first h2 heading."""
        section = {
            'title': None,
            'paragraphs': [],
            'lists': [],
            'tables': []
        }
        
        all_elements = list(container.descendants)
        heading_index = all_elements.index(first_heading)
        
        # Get ALL paragraphs before the heading
        for p in container.find_all('p'):
            try:
                if all_elements.index(p) < heading_index:
                    text = p.get_text(strip=True)
                    if text and len(text) > 1:
                        section['paragraphs'].append(text)
            except:
                pass
        
        # IMPORTANT: Also check for content in divs (not just <p> tags)
        # Some sites put bio content directly in divs
        for div in container.find_all('div', recursive=True):
            try:
                if all_elements.index(div) < heading_index:
                    # Skip if div contains <p> tags (they're handled above)
                    if div.find('p'):
                        continue
                    
                    # Skip if div has too many nested divs (it's a container)
                    if len(div.find_all('div')) > 3:
                        continue
                    
                    # Skip if div contains h2 (it's a section header)
                    if div.find('h2'):
                        continue
                    
                    # Skip navigation, card, or menu divs
                    div_classes = ' '.join(div.get('class', [])).lower()
                    skip_patterns = ['nav', 'menu', 'card', 'header', 'footer', 'sidebar']
                    if any(pattern in div_classes for pattern in skip_patterns):
                        continue
                    
                    # Get text content
                    text = div.get_text(strip=True)
                    
                    # Skip if it looks like navigation (lots of bullets or short items)
                    bullet_count = text.count('•')
                    if bullet_count > 3:
                        continue
                    
                    # Skip if it has contact info pattern (Tel., Email, Address mixed together)
                    has_tel = 'tel.' in text.lower() or 'tel:' in text.lower()
                    has_email = 'e-mail' in text.lower() or '@' in text
                    has_room = 'room' in text.lower() or 'raum' in text.lower()
                    if (has_tel and has_email) or (has_tel and has_room):
                        continue
                    
                    # Only add if substantial and not already in paragraphs
                    if text and len(text) > 100:  # Increased minimum length to filter noise
                        # Check for duplication
                        normalized = ' '.join(text.lower().split())
                        is_duplicate = any(
                            normalized == ' '.join(p.lower().split())
                            for p in section['paragraphs']
                        )
                        if not is_duplicate:
                            section['paragraphs'].append(text)
            except:
                pass
        
        # Lists before heading
        for ul in container.find_all(['ul', 'ol']):
            try:
                if all_elements.index(ul) < heading_index:
                    items = [li.get_text(strip=True) for li in ul.find_all('li', recursive=False)]
                    items = [item for item in items if item and len(item) > 1]
                    if items:
                        section['lists'].append(items)
            except:
                pass
        
        return section if (section['paragraphs'] or section['lists']) else None
    
    def _extract_section_between_headings(self, heading: Tag, next_heading: Optional[Tag]) -> Optional[Dict[str, Any]]:
        """Extract content between two h2 headings."""
        section = {
            'title': heading.get_text(strip=True),
            'paragraphs': [],
            'lists': [],
            'tables': []
        }
        
        # Walk siblings
        current = heading.next_sibling
        while current:
            if current == next_heading:
                break
            
            if hasattr(current, 'name'):
                if current.name == 'h2':
                    break
                elif current.name == 'p':
                    text = current.get_text(strip=True)
                    if text and len(text) > 1:
                        section['paragraphs'].append(text)
                elif current.name in ['ul', 'ol']:
                    items = [li.get_text(strip=True) for li in current.find_all('li', recursive=False)]
                    items = [item for item in items if item and len(item) > 1]
                    if items:
                        section['lists'].append(items)
            
            current = current.next_sibling
        
        # Also check inside parent div (common pattern)
        # IMPORTANT: Use recursive=True to find nested <p> tags in complex structures
        parent = heading.parent
        if parent and parent.name == 'div':
            for p in parent.find_all('p', recursive=True):
                if p not in [heading.next_sibling]:
                    text = p.get_text(strip=True)
                    if text and len(text) > 1 and text not in section['paragraphs']:
                        section['paragraphs'].append(text)
            
            for ul in parent.find_all(['ul', 'ol'], recursive=True):
                items = [li.get_text(strip=True) for li in ul.find_all('li', recursive=False)]
                items = [item for item in items if item and len(item) > 1]
                if items and items not in section['lists']:
                    section['lists'].append(items)
        
        return section if (section['paragraphs'] or section['lists']) else None
    
    def _extract_everything(self, container: Tag) -> Dict[str, Any]:
        """Extract all content as one section."""
        section = {
            'title': 'Content',
            'paragraphs': [],
            'lists': [],
            'tables': []
        }
        
        for p in container.find_all('p'):
            text = p.get_text(strip=True)
            if text and len(text) > 1:
                section['paragraphs'].append(text)
        
        for ul in container.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in ul.find_all('li', recursive=False)]
            items = [item for item in items if item and len(item) > 1]
            if items:
                section['lists'].append(items)
        
        return section
    
    def _extract_semantic_sections(self, main: Tag) -> List[Dict[str, Any]]:
        """Extract explicit semantic sections (using <section> tags or semantic divs)."""
        sections = []
        
        # Strategy: Look for high-value, specific content divs FIRST
        # Uses configured patterns to support different website structures
        content_divs = main.find_all('div', class_=lambda x: x and any(
            pattern in str(x).lower() 
            for pattern in self.config.content_div_patterns[:2]  # Use top patterns from config
        ))
        
        if content_divs:
            for div in content_divs:
                # Skip if empty
                text = div.get_text(strip=True)
                if not text:
                    continue
                
                section_data = self._extract_section_content(div)
                if section_data:
                    sections.append(section_data)
            
            # If we got good sections from these specific divs, return them
            if sections:
                return sections
        
        # Fallback: Look for <section> tags if no specific content divs found
        section_tags = main.find_all('section', recursive=False)
        if section_tags:
            for section_elem in section_tags:
                section_data = self._extract_section_content(section_elem)
                if section_data:
                    sections.append(section_data)
        
        return sections
    
    def _extract_heading_based_sections(self, main: Tag) -> List[Dict[str, Any]]:
        """Extract sections based on heading tags (h2, h3) as natural dividers."""
        sections = []
        
        # Find all h2/h3 headings (these are universal section markers)
        headings = main.find_all(['h2', 'h3'])
        
        if not headings:
            return []
        
        for heading in headings:
            # Skip navigation/footer headings (using configured keywords)
            heading_text = heading.get_text(strip=True).lower()
            if any(keyword in heading_text for keyword in self.config.skip_heading_keywords):
                continue
            
            # Find content after this heading until next heading or end
            section_content = []
            current = heading.next_sibling
            
            # Collect content until we hit another heading at same/higher level
            while current:
                if hasattr(current, 'name'):
                    # Stop if we hit another h2/h3
                    if current.name in ['h2', 'h3']:
                        break
                    section_content.append(current)
                current = current.next_sibling
            
            # If no direct siblings, check parent's next siblings (common pattern)
            if not section_content and heading.parent:
                parent = heading.parent
                current = parent.next_sibling
                while current:
                    if hasattr(current, 'name'):
                        if current.name in ['h2', 'h3']:
                            break
                        section_content.append(current)
                    current = current.next_sibling
            
            # Extract from the collected content
            if section_content:
                section_data = self._extract_from_elements(
                    heading.get_text(strip=True),
                    section_content
                )
                if section_data:
                    sections.append(section_data)
        
        return sections
    
    def _extract_from_elements(self, title: Optional[str], elements: List[Tag]) -> Optional[Dict[str, Any]]:
        """Extract content from a list of HTML elements."""
        # Create a temporary container
        from bs4 import BeautifulSoup
        temp_soup = BeautifulSoup('<div class="temp"></div>', 'html.parser')
        container = temp_soup.find('div')
        
        for elem in elements:
            if hasattr(elem, 'name'):
                container.append(elem)
        
        # Create fresh extractors for THIS section (pass config to maintain consistency)
        paragraph_extractor = ParagraphExtractor(self.config)
        list_extractor = ListExtractor(self.config)
        table_extractor = TableExtractor()
        
        paragraphs = paragraph_extractor.extract(container)
        lists = list_extractor.extract(container)
        tables = table_extractor.extract(container)
        
        if paragraphs or lists or tables:
            # Determine semantic title
            semantic_title = self._determine_semantic_title(title)
            return {
                "title": semantic_title,
                "paragraphs": paragraphs,
                "lists": lists,
                "tables": tables
            }
        
        return None
    
    def _extract_section_content(self, element: Tag) -> Optional[Dict[str, Any]]:
        """Extract content from a single section element."""
        # Get section title - look in multiple places
        title = None
        
        # Strategy 1: Look for heading as direct child
        for heading in element.find_all(['h1', 'h2', 'h3', 'h4'], recursive=False, limit=1):
            title = heading.get_text(strip=True)
            break
        
        # Strategy 2: If no direct child heading, look in parent and grandparent
        # (common pattern: TextImage -> TextImage--inner -> TextImage--content)
        if not title:
            # Check parent
            parent = element.parent
            if parent:
                for sibling in parent.find_all(['h1', 'h2', 'h3', 'h4'], recursive=False):
                    if sibling != element:
                        title = sibling.get_text(strip=True)
                        break
            
            # Check grandparent if still no title
            if not title and parent and parent.parent:
                grandparent = parent.parent
                for heading in grandparent.find_all(['h1', 'h2', 'h3', 'h4'], recursive=False):
                    title = heading.get_text(strip=True)
                    break
        
        # Strategy 3: Look for any heading inside element (deeper search)
        if not title:
            heading = element.find(['h1', 'h2', 'h3', 'h4'])
            if heading:
                title = heading.get_text(strip=True)
        
        # Create fresh extractors for THIS section (no shared deduplication state)
        paragraph_extractor = ParagraphExtractor(self.config)
        list_extractor = ListExtractor(self.config)
        table_extractor = TableExtractor()
        
        # Extract different content types
        paragraphs = paragraph_extractor.extract(element)
        lists = list_extractor.extract(element)
        tables = table_extractor.extract(element)
        
        # Only return if we found some content
        if paragraphs or lists or tables:
            semantic_title = self._determine_semantic_title(title)
            return {
                "title": semantic_title,
                "paragraphs": paragraphs,
                "lists": lists,
                "tables": tables
            }
        
        return None
    
    def _determine_semantic_title(self, title: Optional[str]) -> str:
        """Determine semantic title for a section based on content/keywords."""
        if not title:
            return "Content"
        
        title_lower = title.lower()
        
        # Check against known patterns
        for semantic_name, patterns in self.SECTION_PATTERNS.items():
            if any(pattern in title_lower for pattern in patterns):
                return semantic_name.title() + " Information" if semantic_name == 'contact' else semantic_name.title()
        
        return title



