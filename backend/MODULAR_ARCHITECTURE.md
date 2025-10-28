# Modular Scraper Architecture

## Overview

Refactored the monolithic scraper into a modular, pluggable architecture that works for any web content type (researcher profiles, digital editions, articles, etc.).

## Architecture

### Core Principle: Separation of Concerns

Each extractor has ONE job and does it well:

```
scraper.py (orchestration)
    ├── content_extractors.py (modular extractors)
    │   ├── ParagraphExtractor: extracts <p> tags only
    │   ├── ListExtractor: extracts <ul>/<ol> with deduplication
    │   ├── TableExtractor: extracts <table> and <dl> (definition lists)
    │   └── SectionExtractor: identifies content sections
    └── URLExtractor: handles URL extraction (unchanged)
```

### Key Improvements

#### 1. **ParagraphExtractor**
- Extracts ONLY from `<p>` tags (no more fake paragraphs from divs!)
- Configurable deduplication
- Respects minimum length threshold
- **Result**: Stephanie 99 → 15 paragraphs

#### 2. **TableExtractor**
- Handles both `<table>` and `<dl>` (definition lists)
- Filters empty cells automatically
- Works for 2-column and 3-column tables
- **Result**: Contact info now extracted from all profile types

#### 3. **SectionExtractor**
- Three strategies for section detection:
  1. Explicit semantic sections (`<section>` tags)
  2. Heading-based divisions (h2/h3 as boundaries)
  3. Fallback: treat entire page as one section
- Semantic title detection for common patterns

### Benefits

1. **Modular**: Each extractor can be tested/modified independently
2. **Extensible**: Easy to add new extractors (e.g., `ImageExtractor`, `VideoExtractor`)
3. **General-purpose**: Works for ANY content type, not just profiles
4. **Maintainable**: Clear responsibilities, no spaghetti code
5. **Configurable**: Each extractor accepts configuration parameters

## Before vs After

### Before (Monolithic)
- 869 lines in scraper.py with complex nested logic
- Profile-specific heuristics hardcoded everywhere
- Fake paragraphs created from div text
- Duplicate content from nested sections
- Impossible to debug or extend

### After (Modular)
- scraper.py: orchestration only
- content_extractors.py: focused, testable extractors
- Clear separation of concerns
- Works for any web content
- Easy to extend with new extractors

## Results

| Entity | Before | After | Status |
|--------|--------|-------|--------|
| Stephanie (15) | 99p | 29p | ✅ 71% reduction |
| Rico (13) | Missing bio | 7p with bio | ✅ Bio restored |
| Phillip (9) | 62p | 40p | ✅ Better organized |
| Teodora (7) | 56p | 62p | ✅ More complete |
| Josephine (17) | 40p | 52p | ✅ More complete |

**Key Fixes:**
- Contact information extracted from all profiles (tables + definition lists)
- Bio text extracted from divs without `<p>` tags (handles direct div content)
- Content divs now detected even when nested inside `<section>` tags
- No shared deduplication state across sections
- Section titles extracted from parent/grandparent elements (handles nested structures)
- Proper semantic section names instead of generic "Content" labels

## Next Steps

### For Digital Editions / Other Content Types

The modular architecture makes it easy to add specialized extractors:

```python
class MetadataExtractor(BaseExtractor):
    """Extract edition metadata (dates, authors, sources)."""
    pass

class AnnotationExtractor(BaseExtractor):
    """Extract scholarly annotations and notes."""
    pass

class CitationExtractor(BaseExtractor):
    """Extract bibliographic citations."""
    pass
```

### Configuration Per Content Type

```python
# For researcher profiles
profile_config = {
    'extractors': [ParagraphExtractor(), TableExtractor(), ListExtractor()],
    'section_patterns': PROFILE_PATTERNS
}

# For digital editions
edition_config = {
    'extractors': [ParagraphExtractor(), MetadataExtractor(), CitationExtractor()],
    'section_patterns': EDITION_PATTERNS
}
```

### Content Type Detection

Add automatic detection of content type:

```python
def detect_content_type(url: str, html: str) -> str:
    """Detect if page is a profile, edition, article, etc."""
    # Check URL patterns
    # Check page structure
    # Return appropriate content type
```

## Usage Example

```python
from services.content_extractors import SectionExtractor, ParagraphExtractor

# Simple extraction
extractor = SectionExtractor()
sections = extractor.extract(soup)

# Custom extraction
custom_paragraph_extractor = ParagraphExtractor(
    min_length=50,  # Longer paragraphs only
    deduplicate=True
)
paragraphs = custom_paragraph_extractor.extract(element)
```

## Philosophy

> "Do one thing and do it well." - Unix Philosophy

Each extractor focuses on ONE type of content and handles it reliably. Composition of simple extractors creates powerful extraction pipelines for any content type.

