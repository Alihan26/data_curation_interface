#!/usr/bin/env python3
"""
Dummy data module for the Metadata Curation System.
Contains test data that simulates real-world scenarios.
"""

from typing import List, Dict, Any
from enum import Enum

class PropertyType(str, Enum):
    """Enumeration that mirrors the public client SDK."""
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    BINARY = "BINARY"
    NUMERICAL = "NUMERICAL"
    FREE_TEXT = "FREE_TEXT"

def get_dummy_sources() -> List[Dict[str, Any]]:
    """Get dummy sources with clear distinction from API data."""
    return [
        {
            "id": 1,
            "name": "Digital Edition Catalogue",
            "description": "Collection of digital scholarly editions from various academic institutions",
            "is_dummy": True,
            "source_type": "academic_digital_library"
        }
    ]

def get_dummy_properties() -> List[Dict[str, Any]]:
    """Get dummy metadata properties."""
    return [
        {
            "id": 1,
            "technical_name": "genre",
            "name": "Genre",
            "type": PropertyType.MULTIPLE_CHOICE.value,
            "is_required": True,
            "property_options": [
                {"id": 1, "name": "Poetry"},
                {"id": 2, "name": "Prose"},
                {"id": 3, "name": "Drama"},
                {"id": 4, "name": "Philosophy"},
                {"id": 5, "name": "Religious Text"},
                {"id": 6, "name": "Historical Document"}
            ]
        },
        {
            "id": 2,
            "technical_name": "language",
            "name": "Language",
            "type": PropertyType.SINGLE_CHOICE.value,
            "is_required": True,
            "property_options": [
                {"id": 1, "name": "Sanskrit"},
                {"id": 2, "name": "English"},
                {"id": 3, "name": "German"},
                {"id": 4, "name": "French"},
                {"id": 5, "name": "Latin"},
                {"id": 6, "name": "Arabic"},
                {"id": 7, "name": "Persian"}
            ]
        },
        {
            "id": 3,
            "technical_name": "has_annotations",
            "name": "Has Annotations",
            "type": PropertyType.BINARY.value,
            "is_required": False,
            "property_options": [
                {"id": 1, "name": "0", "description": "No annotations"},
                {"id": 2, "name": "1", "description": "Has annotations"}
            ]
        },
        {
            "id": 4,
            "technical_name": "publication_year",
            "name": "Publication Year",
            "type": PropertyType.NUMERICAL.value,
            "is_required": False,
            "property_options": []
        },
        {
            "id": 5,
            "technical_name": "description",
            "name": "Description",
            "type": PropertyType.FREE_TEXT.value,
            "is_required": True,
            "property_options": []
        },
        {
            "id": 6,
            "technical_name": "manuscript_age",
            "name": "Manuscript Age",
            "type": PropertyType.NUMERICAL.value,
            "is_required": False,
            "property_options": []
        },
        {
            "id": 7,
            "technical_name": "preservation_status",
            "name": "Preservation Status",
            "type": PropertyType.SINGLE_CHOICE.value,
            "is_required": False,
            "property_options": [
                {"id": 1, "name": "Excellent"},
                {"id": 2, "name": "Good"},
                {"id": 3, "name": "Fair"},
                {"id": 4, "name": "Poor"},
                {"id": 5, "name": "Critical"}
            ]
        },
        {
            "id": 8,
            "technical_name": "digitization_quality",
            "name": "Digitization Quality",
            "type": PropertyType.SINGLE_CHOICE.value,
            "is_required": False,
            "property_options": [
                {"id": 1, "name": "High Resolution"},
                {"id": 2, "name": "Medium Resolution"},
                {"id": 3, "name": "Low Resolution"},
                {"id": 4, "name": "Not Digitized"}
            ]
        }
    ]

def get_dummy_editions() -> List[Dict[str, Any]]:
    """Get dummy editions with multiple entities per source."""
    return [
        # Source 1: Digital Edition Catalogue
        {
            "id": 1,
            "source_id": 1,
            "source_internal_id": "paippalada_atharvaveda_001",
            "entity_name": "Paippalāda Recension of the Atharvaveda",
            "entity_description": "Primary recension of the Atharvaveda - digital critical edition",
            "is_dummy": True
        },
        {
            "id": 2,
            "source_id": 1,
            "source_internal_id": "martha_ballard_diary_159",
            "entity_name": "Martha Ballard's Diary Online",
            "entity_description": "Digital edition of Martha Ballard's diary (1785-1812) from Maine State Library",
            "is_dummy": True
        }
    ]

def get_dummy_suggestions() -> List[Dict[str, Any]]:
    """Get dummy suggestions with realistic data for each edition."""
    suggestions = []
    
    # This will be populated by the main app when needed
    # We'll create suggestions dynamically based on editions and properties
    
    return suggestions

def create_dummy_suggestions_for_edition(edition_id: int, source_id: int, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create realistic dummy suggestions for a specific edition."""
    suggestions = []
    
    for prop in properties:
        suggestion = {
            "edition_id": edition_id,
            "source_id": source_id,
            "property_id": prop["id"],
            "status": "pending",
            "ai_generated": False,
            "is_dummy": True
        }
        
        # Generate realistic dummy values based on property type
        if prop["type"] == PropertyType.MULTIPLE_CHOICE.value:
            if prop["technical_name"] == "genre":
                # Realistic genre for different types of texts
                if "veda" in get_edition_by_id(edition_id).get("source_internal_id", ""):
                    suggestion["property_option_id"] = 5  # Religious Text
                elif "manuscript" in get_edition_by_id(edition_id).get("source_internal_id", ""):
                    suggestion["property_option_id"] = 1  # Poetry
                else:
                    suggestion["property_option_id"] = 2  # Prose
            elif prop["technical_name"] == "preservation_status":
                suggestion["property_option_id"] = 2  # Good
            elif prop["technical_name"] == "digitization_quality":
                suggestion["property_option_id"] = 1  # High Resolution
            else:
                suggestion["property_option_id"] = prop["property_options"][0]["id"] if prop["property_options"] else None
            suggestion["custom_value"] = None
            
        elif prop["type"] == PropertyType.SINGLE_CHOICE.value:
            if prop["technical_name"] == "language":
                if "veda" in get_edition_by_id(edition_id).get("source_internal_id", ""):
                    suggestion["property_option_id"] = 1  # Sanskrit
                elif "european" in get_edition_by_id(edition_id).get("source_internal_id", ""):
                    suggestion["property_option_id"] = 2  # English
                else:
                    suggestion["property_option_id"] = 1  # Default
            else:
                suggestion["property_option_id"] = prop["property_options"][0]["id"] if prop["property_options"] else None
            suggestion["custom_value"] = None
            
        elif prop["type"] == PropertyType.BINARY.value:
            suggestion["property_option_id"] = 2  # 1 (true) for most cases
            suggestion["custom_value"] = None
            
        elif prop["type"] == PropertyType.NUMERICAL.value:
            suggestion["property_option_id"] = None
            if prop["technical_name"] == "publication_year":
                suggestion["custom_value"] = "2023"
            elif prop["technical_name"] == "manuscript_age":
                suggestion["custom_value"] = "1500"
            else:
                suggestion["custom_value"] = "2023"
                
        elif prop["type"] == PropertyType.FREE_TEXT.value:
            suggestion["property_option_id"] = None
            if prop["technical_name"] == "description":
                edition = get_edition_by_id(edition_id)
                suggestion["custom_value"] = f"Digital edition of {edition.get('entity_name', 'Unknown')}"
            else:
                suggestion["custom_value"] = "Sample description"
        
        suggestions.append(suggestion)
    
    return suggestions

def get_edition_by_id(edition_id: int) -> Dict[str, Any]:
    """Helper function to get edition by ID."""
    editions = get_dummy_editions()
    return next((e for e in editions if e["id"] == edition_id), {})
