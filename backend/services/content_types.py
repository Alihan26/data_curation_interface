"""
Content type detection and configuration.

Automatically detects what kind of content is being scraped
and applies appropriate extraction strategies.
"""

from typing import Dict, Any, List
from bs4 import BeautifulSoup
from dataclasses import dataclass
from enum import Enum


class ContentType(Enum):
    """Types of content we can extract."""
    RESEARCHER_PROFILE = "researcher_profile"
    DIGITAL_EDITION = "digital_edition"
    INSTITUTIONAL_PAGE = "institutional_page"
    GENERIC = "generic"


@dataclass
class ContentConfig:
    """Configuration for content extraction based on type."""
    
    # Content type
    content_type: ContentType
    
    # CSS patterns to look for content divs
    content_div_patterns: List[str]
    
    # Section detection strategy
    section_strategy: str  # "headings", "divs", "both"
    
    # Enable paragraph deduplication
    deduplicate: bool
    
    # Minimum paragraph length
    min_paragraph_length: int
    
    # Keywords to skip in headings
    skip_heading_keywords: List[str]


# Configuration for researcher profiles (UZH, UniBE, etc.)
RESEARCHER_PROFILE_CONFIG = ContentConfig(
    content_type=ContentType.RESEARCHER_PROFILE,
    content_div_patterns=[
        'personcard--content',
        'textimage--content', 
        'richtext',
        'person-bio',
        'biography',
        'team-detail',
        'staff-profile',
        'content',  # Generic content
        'text',     # Generic text
        'main',     # Main content
        'body',     # Body content
        'article',  # Article content
        'section',  # Section content
        'info',     # Information
        'about',    # About sections
        'detail'    # Detail sections
    ],
    section_strategy="both",  # Try headings first, then divs
    deduplicate=False,  # Disable deduplication to preserve all content
    min_paragraph_length=5,  # Further reduced to capture even shorter important content like emails
    skip_heading_keywords=[
        'navigation', 'footer', 'sprachwahl', 'wichtige seiten',
        'rechtliches', 'impressum', 'adresse', 'partner', 'hier',
        'quicklinks', 'hauptnavigation', 'weiterführende',
        'menu', 'sidebar', 'widget'  # Only skip obvious navigation elements
    ]
)


# Configuration for digital editions and scholarly texts
DIGITAL_EDITION_CONFIG = ContentConfig(
    content_type=ContentType.DIGITAL_EDITION,
    content_div_patterns=[
        'edition-content',
        'text-body',
        'manuscript-text',
        'critical-text',
        'apparatus',
        'commentary',
        'annotation',
        'transcription',
        'diplomatic',
        'normalized',
        'content',  # Generic content
        'text',     # Generic text
        'main',     # Main content
        'body',     # Body content
        'article',  # Article content
        'section'   # Section content
    ],
    section_strategy="headings",  # Scholarly texts use semantic headings
    deduplicate=False,  # Don't dedupe - variants are intentional!
    min_paragraph_length=5,  # Even shorter for scholarly annotations
    skip_heading_keywords=[
        'navigation', 'menu', 'footer', 'copyright'
    ]
)


# Configuration for institutional/organization pages
INSTITUTIONAL_CONFIG = ContentConfig(
    content_type=ContentType.INSTITUTIONAL_PAGE,
    content_div_patterns=[
        'main-content',
        'page-content',
        'article-body',
        'content-area',
        'content',  # Generic content
        'text',     # Generic text
        'main',     # Main content
        'body',     # Body content
        'article',  # Article content
        'section'   # Section content
    ],
    section_strategy="headings",
    deduplicate=False,  # Disable deduplication to preserve all content
    min_paragraph_length=5,  # Further reduced to capture even shorter important content like emails
    skip_heading_keywords=[
        'navigation', 'menu', 'footer', 'sidebar'
    ]
)


# Generic fallback configuration
GENERIC_CONFIG = ContentConfig(
    content_type=ContentType.GENERIC,
    content_div_patterns=[
        'content',
        'article',
        'main',
        'body-content',
        'text',     # Generic text
        'body',     # Body content
        'section',  # Section content
        'info',     # Information
        'about'     # About sections
    ],
    section_strategy="headings",
    deduplicate=False,  # Disable deduplication to preserve all content
    min_paragraph_length=5,  # Further reduced to capture even shorter important content like emails
    skip_heading_keywords=[
        'navigation', 'menu', 'footer'
    ]
)


def detect_content_type(url: str, soup: BeautifulSoup) -> ContentConfig:
    """
    Automatically detect what type of content we're scraping.
    
    Args:
        url: The URL being scraped
        soup: Parsed HTML
        
    Returns:
        Appropriate ContentConfig for this content
    """
    url_lower = url.lower()
    html_text = str(soup).lower()
    
    # Check for digital edition indicators
    edition_keywords = [
        'edition', 'manuscript', 'diplomatic', 'apparatus',
        'transcription', 'critical edition', 'textual witness',
        'variant', 'lemma', 'manuscript description'
    ]
    if any(keyword in url_lower for keyword in ['edition', 'manuscript', 'archive', 'corpus']):
        return DIGITAL_EDITION_CONFIG
    if any(keyword in html_text for keyword in edition_keywords):
        return DIGITAL_EDITION_CONFIG
    
    # Check for researcher profile indicators
    profile_keywords = [
        'personcard', 'staff', 'team', 'researcher', 'professor',
        'publikationen', 'publications', 'forschung', 'research',
        'cv', 'curriculum vitae', 'biography'
    ]
    profile_classes = ['personcard', 'team-detail', 'staff-profile', 'researcher-profile']
    
    if any(keyword in url_lower for keyword in ['team', 'people', 'personen', 'staff']):
        return RESEARCHER_PROFILE_CONFIG
    if any(cls in html_text for cls in profile_classes):
        return RESEARCHER_PROFILE_CONFIG
    if sum(keyword in html_text for keyword in profile_keywords) >= 3:
        return RESEARCHER_PROFILE_CONFIG
    
    # Check for institutional page indicators
    if any(keyword in url_lower for keyword in ['about', 'ueber', 'institut', 'department']):
        return INSTITUTIONAL_CONFIG
    
    # Default to generic
    return GENERIC_CONFIG


def get_config(url: str, soup: BeautifulSoup) -> ContentConfig:
    """
    Get the appropriate configuration for this content.
    
    This is the main entry point for content type detection.
    """
    config = detect_content_type(url, soup)
    return config

