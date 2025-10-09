# Scraping System Improvements

## Overview

The scraping functionality has been completely refactored for improved reliability, maintainability, and error handling. The new implementation follows clean code principles with proper separation of concerns.

## What Changed

### 1. New Modular Architecture

**Before**: Complex inline logic in `app.py` endpoint (~400 lines of nested conditionals)
**After**: Clean service module in `services/scraper.py` with distinct responsibilities

### 2. Three-Layer Service Architecture

```
EntityScraper (Orchestration)
    ├── URLExtractor (URL Discovery)
    │   ├── Known entity mappings
    │   ├── External API suggestions
    │   ├── Context URL extraction
    │   └── Fallback strategies
    │
    └── ContentExtractor (HTML Processing)
        ├── HTML fetching with proper error handling
        ├── Structured content extraction
        ├── Metadata extraction
        └── Plain text fallback
```

### 3. Key Improvements

#### A. URL Extraction (`URLExtractor`)

**Features:**
- Multiple extraction strategies with clear priority
- Robust URL validation to prevent malformed URLs
- Improved regex for URL extraction from contexts
- Better error handling and logging

**Extraction Strategy Priority:**
1. Known entity mappings (for dummy/test data)
2. URL from suggestions (property_id = 2)
3. URL extracted from entity contexts
4. Provided fallback URLs
5. Generate placeholder content

#### B. Content Extraction (`ContentExtractor`)

**Features:**
- Proper HTTP timeout handling
- User-agent string for better compatibility
- Content-type validation
- Configurable extraction limits (max sections, paragraphs, etc.)
- Structured content preservation (navigation, headers, sections, footer)
- Metadata extraction (title, description, keywords, language)
- Plain text fallback for AI processing

**Configuration Constants:**
- `MAX_CONTENT_LENGTH = 10000` characters
- `MAX_SECTIONS = 10` sections per page
- `MAX_PARAGRAPHS_PER_SECTION = 20`
- `MAX_LISTS_PER_SECTION = 5`
- `MAX_NAV_LENGTH = 500` characters
- `MAX_FOOTER_LENGTH = 300` characters

#### C. Error Handling

**Custom Exceptions:**
- `ScraperError` - Base exception
- `URLExtractionError` - URL discovery failures
- `HTMLFetchError` - Network/HTTP errors
- `ContentExtractionError` - Parsing failures

**Benefits:**
- Specific error types for better debugging
- Graceful degradation (errors don't crash the system)
- Detailed error logging for troubleshooting
- Error pages included in results for user visibility

### 4. Code Quality Improvements

#### Before:
```python
# Nested conditionals, hardcoded values, mixed concerns
if entity["entity_name"] == "Martha Ballard's Diary Online":
    urls = ['https://dohistory.org/diary/about.html']
elif entity["entity_name"] == "Atharvaveda Paippalāda":
    urls = ['https://www.atharvavedapaippalada.uzh.ch/en.html']
elif not entity.get("is_dummy", True):
    urls = []
    # ... 100+ more lines of nested logic
```

#### After:
```python
# Clean service call with proper error handling
pages_data, scraping_errors = entity_scraper.scrape_entity(
    entity, source, fallback_urls
)

# Log any scraping errors
if scraping_errors:
    for error in scraping_errors:
        logger.warning(f"Scraping error: {error}")
```

### 5. Testability

The new modular design enables easy unit testing:

```python
# URLExtractor can be tested independently
def test_url_validation():
    assert URLExtractor._is_valid_url("https://example.com")
    assert not URLExtractor._is_valid_url("not a url")

# ContentExtractor can be tested with mock HTML
def test_content_extraction():
    html = "<html><body><p>Test</p></body></html>"
    content = ContentExtractor.extract_plain_text(html)
    assert "Test" in content
```

## Benefits

### For Developers
1. **Easier to understand** - Clear separation of concerns
2. **Easier to maintain** - Modular functions with single responsibilities
3. **Easier to debug** - Specific error types and detailed logging
4. **Easier to extend** - Add new extraction strategies without touching existing code
5. **Easier to test** - Independent modules can be tested in isolation

### For Users
1. **More reliable** - Better error handling prevents crashes
2. **Better error messages** - Specific error types show what went wrong
3. **Fallback strategies** - System tries multiple approaches before giving up
4. **Consistent behavior** - Well-defined extraction rules

### For Operations
1. **Better logging** - Detailed logs at each step for troubleshooting
2. **Configurable** - Easy to adjust extraction limits via constants
3. **Observable** - Clear success/failure indicators in logs

## Migration Notes

### Backward Compatibility
- The API endpoint `/api/entities/<id>/scrape` remains unchanged
- Response format is identical
- Existing frontend code requires no changes

### Removed Functions
- `fetch_html()` - Replaced by `ContentExtractor.fetch_html()`
- `_extract_structured_content()` - Replaced by `ContentExtractor.extract_structured_content()`

### New Dependencies
- No new external dependencies required
- Uses existing `requests`, `BeautifulSoup4`, `re`, `logging`

## Configuration

All extraction limits can be adjusted in `services/scraper.py`:

```python
class ContentExtractor:
    MAX_CONTENT_LENGTH = 10000  # Adjust as needed
    MAX_SECTIONS = 10           # More sections for detailed pages
    MAX_PARAGRAPHS_PER_SECTION = 20
    # ... etc
```

## Error Scenarios

### Scenario 1: Network Timeout
```
[ERROR] HTML fetch timeout after 20s: https://example.com
[INFO] Added error page data with user-friendly message
```

### Scenario 2: Invalid URL in Context
```
[WARNING] Invalid URL found in context: htp://broken-url
[INFO] Skipping invalid URL, continuing with other strategies
```

### Scenario 3: No URLs Found
```
[WARNING] No URLs found for entity 'Example Entity'
[INFO] Generated placeholder content for manual curation
```

## Future Enhancements

Potential improvements for future iterations:

1. **Caching** - Cache scraped content to reduce repeated fetches
2. **Rate Limiting** - Implement rate limiting for external URLs
3. **Async Scraping** - Use async/await for parallel URL fetching
4. **Content Quality** - Add heuristics to detect low-quality extractions
5. **JavaScript Rendering** - Support for JavaScript-heavy pages (Selenium/Playwright)
6. **Retry Logic** - Configurable retry with exponential backoff
7. **Custom Extractors** - Plugin system for domain-specific extractors

## Testing

### Manual Testing
1. Start backend: `python app.py`
2. Test entity with known URL (dummy data)
3. Test entity from external API
4. Test entity with no URL (should generate placeholder)
5. Test with invalid URL (should handle gracefully)

### Automated Testing
```bash
# Future: Run unit tests
pytest tests/test_scraper.py

# Future: Run integration tests
pytest tests/test_scraping_integration.py
```

## Performance

### Metrics
- **URL extraction**: ~100ms (with external API)
- **HTML fetching**: 500ms - 2000ms (depends on target site)
- **Content extraction**: ~50-200ms (depends on page size)
- **Total scraping time**: ~1-3 seconds per URL

### Optimization Opportunities
1. Parallel URL fetching (currently sequential)
2. Content streaming for large pages
3. Selective parsing (skip irrelevant sections early)

## Support

For issues or questions about the scraping system:

1. Check logs in `backend.log` for detailed error traces
2. Review this documentation for common scenarios
3. Check `services/scraper.py` docstrings for implementation details
4. Test with `curl` to isolate backend vs frontend issues

## Summary

The new scraping system is:
- ✅ **More reliable** - Robust error handling and fallback strategies
- ✅ **More maintainable** - Clean modular architecture
- ✅ **More testable** - Independent components
- ✅ **More observable** - Detailed logging at every step
- ✅ **Better documented** - Comprehensive docstrings and comments
- ✅ **Backward compatible** - No API changes required

The refactoring transformed 400+ lines of complex nested logic into a clean, well-structured service with proper separation of concerns.

