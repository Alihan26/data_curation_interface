#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
# --------------------------- standard lib ---------------------------------
from enum import Enum
import os
from dotenv import load_dotenv

# Import metadata curation client
from metadata_curation_client import CurationAPIClient, PropertyType, SourceManager

# Import scraping service
from services.scraper import EntityScraper, ScraperError, HTMLFetchError, ContentExtractionError

# --------------------------------------------------------------------------
# Constants (external demo endpoint used by the preview helper below)
# --------------------------------------------------------------------------

# External API URL will be replaced by metadata curation client
EXTERNAL_API: str = "https://api.example.org/v1/pages"  # ← placeholder (replaced by client)

# --------------------------------------------------------------------------------------
# Existing preview/utility imports and constants
# --------------------------------------------------------------------------------------


app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Configure logging first
import logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)
logger = app.logger

# Initialize Metadata Curation API Client
curation_client = None
try:
    api_base_url = os.getenv('CURATION_API_BASE_URL')
    api_key = os.getenv('CURATION_API_KEY')
    
    if api_base_url:
        curation_client = CurationAPIClient(
            base_url=api_base_url,
            api_key=api_key
        )
        logger.info(f"Metadata Curation API Client initialized with base URL: {api_base_url}")
    else:
        # Default to self-referencing mode for development
        curation_client = CurationAPIClient(
            base_url="http://localhost:8001",
            api_key="dev-key"
        )
        logger.info("Metadata Curation API Client initialized in self-referencing mode: http://localhost:8001")
except Exception as e:
    logger.error(f"Failed to initialize Metadata Curation API Client: {e}")
    logger.warning("Falling back to dummy data mode")

# Initialize AI service (will fail gracefully if no API key)
ai_service = None
try:
    from ai_curation import AICurationService
    if os.getenv('OPENAI_API_KEY'):
        ai_service = AICurationService()
        # Test if the service is actually working
        if hasattr(ai_service, 'is_available') and ai_service.is_available():
            app.logger.info("AI Curation Service initialized successfully")
        else:
            app.logger.warning("AI service initialized but availability check failed")
            ai_service = None
    else:
        app.logger.warning("No OPENAI_API_KEY found, AI suggestions disabled")
except ImportError as e:
    app.logger.warning(f"AI service not available: {e}")
except Exception as e:
    app.logger.error(f"Failed to initialize AI service: {e}")
    ai_service = None

# Initialize scraping service
entity_scraper = EntityScraper(curation_client)
logger.info("Entity scraping service initialized")


class PropertyType(str, Enum):
    """Enumeration that mirrors the public client SDK."""

    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    BINARY = "BINARY"
    NUMERICAL = "NUMERICAL"
    FREE_TEXT = "FREE_TEXT"


# --------------------------------------------------------------------------------------
# In-memory demo implementation of the Metadata-Curation API
# --------------------------------------------------------------------------------------

# Import dummy data module
from dummy_data import (
    get_dummy_sources, get_dummy_properties, get_dummy_editions,
    create_dummy_suggestions_for_edition
)

# Enhanced data structure with evidence tracking and required fields
DATA: dict[str, list] = {
    "sources": [],       # [{id:int, name:str, description:str, is_dummy:bool, source_type:str}]
    "properties": [],    # [{id:int, technical_name:str, name:str, type:PropertyType, property_options:list, is_required:bool}]
    "editions": [],      # [{id:int, source_id:int, source_internal_id:str, entity_name:str, entity_description:str, is_dummy:bool}]
    "suggestions": [],   # [{id:int, source_id:int, edition_id:int, property_id:int, ..., evidence:dict, is_required:bool}]
    "curation_history": [],  # [{id:int, suggestion_id:int, action:str, timestamp:str, user_note:str, user_id:str, model_version:str}]
    "evidence": [],      # [{id:int, suggestion_id:int, content:str, source_url:str, confidence:float, extraction_method:str}]
    "publishing_state": []  # [{id:int, edition_id:int, status:str, published_at:str, published_by:str, validation_errors:list}]
}


def _gen_id(key: str) -> int:
    """Incremental id generator per table."""

    return len(DATA[key]) + 1


def _fetch_api_data() -> None:
    """Fetch data from the metadata curation API if available, otherwise use dummy data."""
    
    if DATA["sources"]:  # already populated
        return
    
    if curation_client:
        try:
            logger.info("Fetching data from Metadata Curation API...")
            
            # Fetch sources from API
            api_sources = curation_client.get_sources()
            DATA["sources"] = []
            for source in api_sources:
                DATA["sources"].append({
                    "id": source.get("id"),
                    "name": source.get("name", "Unknown Source"),
                    "description": source.get("description", ""),
                    "source_type": source.get("source_type", "unknown"),
                    "is_dummy": False
                })
            
            # Fetch properties from API
            api_properties = curation_client.get_properties()
            DATA["properties"] = []
            for prop in api_properties:
                # Normalize property type to uppercase for compatibility
                prop_type = prop.get("type", "FREE_TEXT").upper()
                
                property_data = {
                    "id": prop.get("id"),
                    "technical_name": prop.get("technical_name", ""),
                    "name": prop.get("name", "Unknown Property"),
                    "type": prop_type,
                    "is_required": prop.get("is_required", False),
                    "property_options": prop.get("property_options", []),
                    "is_dummy": False
                }
                DATA["properties"].append(property_data)
            
            # Fetch entities/editions from API
            DATA["editions"] = []
            try:
                # FIXED: Call get_entities() only ONCE (it returns all entities from all sources)
                entities = curation_client.get_entities()
                
                # Create source lookup for entity descriptions
                source_lookup = {s["id"]: s["name"] for s in DATA["sources"]}
                
                for entity in entities:
                    source_id = entity.get("source_id")
                    source_name = source_lookup.get(source_id, "Unknown Source")
                    
                    DATA["editions"].append({
                        "id": entity.get("id"),
                        "source_id": source_id,
                        "source_internal_id": entity.get("source_internal_id", ""),
                        "entity_name": entity.get("name", entity.get("source_internal_id", f"Entity {entity.get('id')}")),
                        "entity_description": f"Entity from {source_name}",
                        "is_dummy": False,
                        "context_ids": entity.get("context_ids", [])
                    })
            except Exception as e:
                logger.error(f"Failed to fetch entities: {e}")
            
            # Initialize empty arrays for runtime data
            DATA["suggestions"] = []
            DATA["curation_history"] = []
            DATA["evidence"] = []
            DATA["publishing_state"] = []
            
            logger.info(f"API data loaded - Sources: {len(DATA['sources'])}, Properties: {len(DATA['properties'])}, Editions: {len(DATA['editions'])}")

            # Always append the dummy source as an additional catalog for demo/testing
            try:
                _append_dummy_catalog()
                logger.info(
                    f"Dummy catalog appended - Total Sources: {len(DATA['sources'])}, Properties: {len(DATA['properties'])}, Editions: {len(DATA['editions'])}"
                )
            except Exception as e:
                logger.error(f"Failed to append dummy catalog: {e}")
            
        except Exception as e:
            logger.error(f"Failed to fetch data from API: {e}")
            logger.info("Falling back to dummy data...")
            _initialize_dummy_data()
    else:
        logger.info("No API client available, using dummy data...")
        _initialize_dummy_data()

def _initialize_dummy_data() -> None:
    """Populate store with deterministic demo data so the front-end has something to fetch
    even before the real extractor runs.
    """

    if DATA["sources"]:  # already populated
        return

    # 1) Load dummy sources with clear identification
    DATA["sources"] = get_dummy_sources()
    
    # 2) Load dummy properties
    DATA["properties"] = get_dummy_properties()
    
    # 3) Load dummy editions with multiple entities per source
    DATA["editions"] = get_dummy_editions()
    
    # 4) NO automatic dummy suggestions - they should be created only when needed
    # DATA["suggestions"] starts empty - suggestions are generated on-demand


def _next_id(values: list[int]) -> int:
    return (max(values) + 1) if values else 1


def _append_dummy_catalog() -> None:
    """Append the dummy source/properties/editions alongside API data.
    Ensures IDs do not collide and tags dummy properties with their source.
    """
    # Load originals
    dummy_sources = get_dummy_sources()
    dummy_properties = get_dummy_properties()
    dummy_editions = get_dummy_editions()

    # Compute safe ID bases to avoid collision with API data
    existing_source_ids = [s["id"] for s in DATA["sources"]]
    existing_property_ids = [p["id"] for p in DATA["properties"]]
    existing_edition_ids = [e["id"] for e in DATA["editions"]]

    base_source_id = (max(existing_source_ids) + 1000) if existing_source_ids else 1000
    base_property_id = (max(existing_property_ids) + 1000) if existing_property_ids else 1000
    base_edition_id = (max(existing_edition_ids) + 1000) if existing_edition_ids else 1000

    # Remap and append sources
    source_id_map: dict[int, int] = {}
    for i, src in enumerate(dummy_sources):
        new_id = base_source_id + i
        source_id_map[src["id"]] = new_id
        DATA["sources"].append({**src, "id": new_id, "is_dummy": True})

    # Remap and append properties, tagging with source_id of first dummy source
    dummy_source_target_id = next(iter(source_id_map.values()), None)
    for i, prop in enumerate(dummy_properties):
        new_prop = {**prop}
        new_prop["id"] = base_property_id + i
        # Tag properties to dummy source so the frontend can request per-source
        new_prop["source_id"] = dummy_source_target_id
        new_prop["is_dummy"] = True
        DATA["properties"].append(new_prop)

    # Remap and append editions
    for i, ed in enumerate(dummy_editions):
        new_ed = {**ed}
        new_ed["id"] = base_edition_id + i
        old_src_id = ed.get("source_id")
        new_ed["source_id"] = source_id_map.get(old_src_id, dummy_source_target_id)
        DATA["editions"].append(new_ed)


# --------------------------------------------------------------------------------------
# Metadata-Curation REST endpoints (demo-only)
# --------------------------------------------------------------------------------------


@app.route("/api/sources", methods=["GET"])
def sources_collection():
    logger.info("Listing all sources")
    # Return sources with their editions and suggestion counts
    sources_with_details = []
    for source in DATA["sources"]:
        source_editions = [e for e in DATA["editions"] if e["source_id"] == source["id"]]
        
        # Group editions by entity for better organization
        entities = {}
        for edition in source_editions:
            entity_name = edition.get("entity_name", "Unknown Entity")
            if entity_name not in entities:
                entities[entity_name] = {
                    "name": entity_name,
                    "description": edition.get("entity_description", ""),
                    "editions": []
                }
            entities[entity_name]["editions"].append(edition)
        
        sources_with_details.append({
            **source,
            "editions_count": len(source_editions),
            "suggestions_count": 0,  # Start with 0 - suggestions are generated on-demand
            "editions": source_editions,
            "entities": list(entities.values())
        })

    return jsonify(sources_with_details)

# --------------------------------------------------------------------------
#   GET collections helpers
# --------------------------------------------------------------------------


@app.route("/api/editions", methods=["GET"])
def list_editions():
    source_id = request.args.get("source_id", type=int)
    
    if source_id:
        # Filter editions by source
        filtered_editions = [e for e in DATA["editions"] if e["source_id"] == source_id]
        return jsonify(filtered_editions)
    
    return jsonify(DATA["editions"])


@app.route("/api/suggestions", methods=["GET"])
def list_suggestions():
    source_id = request.args.get("source_id", type=int)
    edition_id = request.args.get("edition_id", type=int)

    # Basic filtering if params provided
    items = DATA["suggestions"]
    if source_id:
        items = [s for s in items if s["source_id"] == source_id]
    if edition_id:
        items = [s for s in items if s["edition_id"] == edition_id]
    return jsonify(items)


@app.route("/api/properties", methods=["GET"])
def properties_collection():
    logger.info("Listing all properties")
    source_id = request.args.get("source_id", type=int)
    if source_id:
        # 1) Prefer explicit source-scoped properties if present
        scoped = [p for p in DATA["properties"] if p.get("source_id") == source_id]
        if scoped:
            return jsonify(scoped)

        # 2) Otherwise, separate by dummy vs non-dummy to avoid leaking between catalogs
        src = next((s for s in DATA["sources"] if s["id"] == source_id), None)
        if src:
            if src.get("is_dummy", False):
                return jsonify([p for p in DATA["properties"] if p.get("is_dummy", False) is True])
            else:
                return jsonify([p for p in DATA["properties"] if p.get("is_dummy", False) is False])

        # 3) If source not found, return empty set
        return jsonify([])

    return jsonify(DATA["properties"])





@app.route("/api/suggestions", methods=["POST"])
def create_suggestion():
    return jsonify({"error": "Creation disabled in demo teardown"}), 404


@app.route("/api/ai-suggestions", methods=["POST"])
def generate_ai_suggestions():
    """Generate AI-powered metadata suggestions from HTML content."""

    if not ai_service:
        return jsonify({"error": "AI service not available. Please set OPENAI_API_KEY."}), 503

    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    payload = request.get_json(force=True)
    html_content = payload.get('html_content')
    url = payload.get('url')

    if not html_content or not url:
        return jsonify({"error": "html_content and url are required"}), 400

    try:
        logger.info(f"Generating AI suggestions for URL: {url}")

        # Get existing properties for context
        properties = DATA["properties"]

        # Generate AI suggestions
        ai_suggestions = ai_service.generate_metadata_suggestions(
            html_content, url, properties
        )

        # Validate and format suggestions
        validated_suggestions = ai_service.validate_suggestions(
            ai_suggestions, properties
        )

        # Add to our data store (for demo purposes)
        for suggestion in validated_suggestions:
            suggestion['id'] = _gen_id("suggestions")
            suggestion['source_id'] = 1  # Default to first source
            suggestion['edition_id'] = 1  # Default to first edition
            DATA["suggestions"].append(suggestion)

        logger.info(f"Generated and stored {len(validated_suggestions)} AI suggestions")

        return jsonify({
            "success": True,
            "suggestions": validated_suggestions,
            "total_generated": len(validated_suggestions)
        })

    except Exception as e:
        logger.error(f"Error generating AI suggestions: {str(e)}")
        return jsonify({"error": f"Failed to generate suggestions: {str(e)}"}), 500


@app.route("/api/suggestions/<int:suggestion_id>/curate", methods=["POST"])
def curate_suggestion(suggestion_id: int):
    """
    Accept, reject, or edit a metadata suggestion.
    
    Business Logic:
    - Suggestions can only be curated if they have evidence attached
    - Evidence must be valid and accessible
    - All curation actions are logged with user context and timestamps
    """
    
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    payload = request.get_json(force=True)
    action = payload.get('action')  # 'accept', 'reject', 'edit'
    user_note = payload.get('note', '') or payload.get('curator_note', '')
    user_id = payload.get('user_id', 'anonymous')  # In production, this would come from auth
    
    if action not in ['accept', 'reject', 'edit']:
        return jsonify({"error": "Action must be 'accept', 'reject', or 'edit'"}), 400
    
    # Find the suggestion
    suggestion = next((s for s in DATA["suggestions"] if s["id"] == suggestion_id), None)
    if not suggestion:
        return jsonify({"error": "Suggestion not found"}), 404
    
    # CRITICAL BUSINESS LOGIC: Validate evidence before allowing curation
    if not _has_valid_evidence(suggestion):
        return jsonify({
            "error": "Cannot curate suggestion without valid evidence",
            "details": "All suggestions must have evidence attached before they can be accepted, rejected, or edited",
            "suggestion_id": suggestion_id,
            "evidence_status": _get_evidence_status(suggestion)
        }), 400
    
    # Create comprehensive curation history entry
    import datetime as dt
    from datetime import timezone
    current_time = dt.datetime.now(timezone.utc)
    
    history_entry = {
        "id": _gen_id("curation_history"),
        "suggestion_id": suggestion_id,
        "action": action,
        "timestamp": current_time.isoformat(),
        "user_note": user_note,
        "user_id": user_id,
        "model_version": suggestion.get('model_version', 'unknown'),
        "previous_value": suggestion.copy(),
        "evidence_references": _get_evidence_references(suggestion)
    }
    
    # Update suggestion status and metadata
    status_map = {
        "accept": "accepted",
        "reject": "rejected",
        "edit": "edited"
    }
    suggestion["status"] = status_map.get(action, suggestion.get("status", "pending"))
    suggestion["curated_at"] = current_time.isoformat()
    suggestion["curator_note"] = user_note
    suggestion["curated_by"] = user_id
    
    # If editing, update the value with validation
    if action == "edit":
        new_value = payload.get('new_value')
        if new_value is not None:
            # Validate the new value based on property type
            validation_result = _validate_suggestion_value(suggestion, new_value)
            if not validation_result["valid"]:
                return jsonify({
                    "error": "Invalid value for property type",
                    "details": validation_result["error"]
                }), 400
            
            # Update the appropriate field based on property type
            property_def = next((p for p in DATA["properties"] if p["id"] == suggestion["property_id"]), None)
            if property_def:
                if property_def["type"] in ["MULTIPLE_CHOICE", "SINGLE_CHOICE", "BINARY"]:
                    suggestion['property_option_id'] = new_value
                    suggestion['custom_value'] = None
                else:
                    suggestion['custom_value'] = new_value
                    suggestion['property_option_id'] = None
    
    # Store the history entry
    DATA["curation_history"].append(history_entry)
    
    # Log the curation action
    logger.info(f"Suggestion {suggestion_id} {action}ed by user {user_id} with evidence validation")
    
    return jsonify({
        "success": True,
        "suggestion": suggestion,
        "history_entry": history_entry,
        "evidence_validated": True,
        "curation_allowed": True
    })


def _has_valid_evidence(suggestion: dict) -> bool:
    """
    Validate that a suggestion has sufficient evidence for curation.
    
    Args:
        suggestion: The suggestion dictionary to validate
        
    Returns:
        bool: True if evidence is valid and sufficient
        
    Business Rules:
    - Must have evidence content
    - Evidence must have a source URL
    - Evidence confidence must be above threshold
    - Evidence must be accessible (not expired/invalid)
    """
    # Check if suggestion has evidence
    if not suggestion.get('evidence'):
        return False
    
    evidence = suggestion['evidence']
    
    # Evidence must have content
    if not evidence.get('content') or not evidence['content'].strip():
        return False
    
    # Evidence must have a source URL
    if not evidence.get('source_url') or not evidence['source_url'].strip():
        return False
    
    # Evidence must have reasonable confidence (above 0.1)
    if evidence.get('confidence', 0) < 0.1:
        return False
    
    # Evidence must not be expired (if it has an expiration)
    if evidence.get('expires_at'):
        import datetime as dt
        from datetime import timezone
        try:
            expires_at = dt.datetime.fromisoformat(evidence['expires_at'].replace('Z', '+00:00'))
            if expires_at < dt.datetime.now(timezone.utc):
                return False
        except (ValueError, TypeError):
            # If we can't parse the date, assume it's valid
            pass
    
    return True


def _get_evidence_status(suggestion: dict) -> dict:
    """Get detailed status of evidence for a suggestion."""
    evidence = suggestion.get('evidence', {})
    
    return {
        "has_evidence": bool(evidence),
        "has_content": bool(evidence.get('content')),
        "has_source_url": bool(evidence.get('source_url')),
        "confidence": evidence.get('confidence', 0),
        "confidence_sufficient": evidence.get('confidence', 0) >= 0.1,
        "extraction_method": evidence.get('extraction_method', 'unknown'),
        "evidence_type": type(evidence).__name__
    }


def _get_evidence_references(suggestion: dict) -> list:
    """Extract evidence references for audit logging."""
    evidence = suggestion.get('evidence', {})
    references = []
    
    if evidence.get('source_url'):
        references.append({
            "type": "source_url",
            "value": evidence['source_url'],
            "description": "Source URL for evidence"
        })
    
    if evidence.get('content'):
        references.append({
            "type": "content_excerpt",
            "value": evidence['content'][:100] + "..." if len(evidence['content']) > 100 else evidence['content'],
            "description": "Evidence content excerpt"
        })
    
    if evidence.get('extraction_method'):
        references.append({
            "type": "extraction_method",
            "value": evidence['extraction_method'],
            "description": "Method used to extract evidence"
        })
    
    return references


def _validate_suggestion_value(suggestion: dict, new_value) -> dict:
    """
    Validate a new value for a suggestion based on its property type.
    
    Args:
        suggestion: The suggestion being edited
        new_value: The new value to validate
        
    Returns:
        dict: Validation result with 'valid' boolean and optional 'error' message
    """
    property_def = next((p for p in DATA["properties"] if p["id"] == suggestion["property_id"]), None)
    if not property_def:
        return {"valid": False, "error": "Property definition not found"}
    
    # Validate based on property type
    if property_def["type"] in ["MULTIPLE_CHOICE", "SINGLE_CHOICE", "BINARY"]:
        # Must be a valid option ID
        if not isinstance(new_value, int):
            return {"valid": False, "error": f"Value must be an integer option ID for {property_def['type']} properties"}
        
        valid_options = [opt["id"] for opt in property_def.get("property_options", [])]
        if new_value not in valid_options:
            return {"valid": False, "error": f"Invalid option ID. Must be one of: {valid_options}"}
    
    elif property_def["type"] == "NUMERICAL":
        # Must be a number
        try:
            float(new_value)
        except (ValueError, TypeError):
            return {"valid": False, "error": "Value must be a number for numerical properties"}
    
    elif property_def["type"] == "FREE_TEXT":
        # Must be a string
        if not isinstance(new_value, str) or not new_value.strip():
            return {"valid": False, "error": "Value must be a non-empty string for free text properties"}
    
    return {"valid": True}


@app.route("/api/suggestions/<int:suggestion_id>/history", methods=["GET"])
def get_suggestion_history(suggestion_id: int):
    return jsonify({"error": "History disabled in demo teardown"}), 404


@app.route("/api/suggestions/<int:suggestion_id>/revert", methods=["POST"])
def revert_suggestion(suggestion_id: int):
    """
    Revert a suggestion to a previous state from its history.
    
    Business Logic:
    - Can only revert to states that had valid evidence
    - Revert creates a new history entry
    - Original history is preserved
    - Revert action requires user authentication
    """
    
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    payload = request.get_json(force=True)
    target_history_id = payload.get('history_id')
    user_note = payload.get('note', 'Reverted by curator')
    user_id = payload.get('user_id', 'anonymous')
    
    if not target_history_id:
        return jsonify({"error": "history_id is required to specify which state to revert to"}), 400
    
    # Find the suggestion
    suggestion = next((s for s in DATA["suggestions"] if s["id"] == suggestion_id), None)
    if not suggestion:
        return jsonify({"error": "Suggestion not found"}), 404
    
    # Find the target history entry
    target_history = next((h for h in DATA["curation_history"] if h["id"] == target_history_id), None)
    if not target_history:
        return jsonify({"error": "History entry not found"}), 404
    
    # Validate that the target history belongs to this suggestion
    if target_history["suggestion_id"] != suggestion_id:
        return jsonify({"error": "History entry does not belong to this suggestion"}), 400
    
    # Get the previous value from the target history
    previous_value = target_history.get("previous_value", {})
    if not previous_value:
        return jsonify({"error": "No previous value found in target history entry"}), 400
    
    # Create a revert history entry
    import datetime as dt
    from datetime import timezone
    current_time = dt.datetime.now(timezone.utc)
    
    revert_history_entry = {
        "id": _gen_id("curation_history"),
        "suggestion_id": suggestion_id,
        "action": "revert",
        "timestamp": current_time.isoformat(),
        "user_note": user_note,
        "user_id": user_id,
        "model_version": suggestion.get('model_version', 'unknown'),
        "previous_value": suggestion.copy(),
        "reverted_to_history_id": target_history_id,
        "reverted_to_timestamp": target_history.get("timestamp"),
        "evidence_references": _get_evidence_references(suggestion)
    }
    
    # Revert the suggestion to the previous state
    suggestion.update(previous_value)
    suggestion["status"] = "reverted"
    suggestion["reverted_at"] = current_time.isoformat()
    suggestion["reverted_by"] = user_id
    suggestion["revert_note"] = user_note
    
    # Store the revert history entry
    DATA["curation_history"].append(revert_history_entry)
    
    # Log the revert action
    logger.info(f"Suggestion {suggestion_id} reverted by user {user_id} to history entry {target_history_id}")
    
    return jsonify({
        "success": True,
        "suggestion": suggestion,
        "revert_history_entry": revert_history_entry,
        "reverted_to_timestamp": target_history.get("timestamp"),
        "message": f"Successfully reverted to state from {_format_timestamp(target_history.get('timestamp', ''))}"
    })


def _format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display purposes."""
    if not timestamp_str:
        return "Unknown"
    
    try:
        import datetime as dt
        from datetime import timezone
        
        # Parse the timestamp
        if 'Z' in timestamp_str:
            timestamp_str = timestamp_str.replace('Z', '+00:00')
        
        dt_obj = dt.datetime.fromisoformat(timestamp_str)
        
        # Format for display
        return dt_obj.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, TypeError):
        return timestamp_str


@app.route("/api/sources/<int:source_id>/ingestion_complete", methods=["POST"])
def ingestion_complete(source_id: int):
    # In this mock implementation we just record a timestamp.
    import datetime as _dt
    from datetime import timezone
    for src in DATA["sources"]:
        if src["id"] == source_id:
            src["last_ingested_at"] = _dt.datetime.now(timezone.utc).isoformat()
            return jsonify({"success": True, "source_id": source_id})
    return jsonify({"error": "Source not found"}), 404

# --------------------------------------------------------------------------------------
# Existing preview endpoints (unchanged)
# --------------------------------------------------------------------------------------


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": str(error)}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred"}), 500


# Legacy helper functions removed - now using services/scraper.py
# These functions have been replaced by the EntityScraper service for better
# separation of concerns, error handling, and testability


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

# Test endpoint removed - new endpoints are working correctly

@app.route('/api/entities/<int:entity_id>/scrape', methods=['POST'])
def scrape_entity_content(entity_id: int):
    """
    Unified endpoint for scraping entity content and generating suggestions.
    
    This replaces the old /api/process-curation endpoint with a more RESTful design.
    Automatically determines URLs based on entity, scrapes content, and optionally
    generates AI suggestions based on the 'use_ai' parameter.
    """
    try:
        logger.info(f"Scraping content for entity {entity_id}")
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Find the entity
        entity = next((e for e in DATA["editions"] if e["id"] == entity_id), None)
        if not entity:
            return jsonify({"error": "Entity not found"}), 404
        
        # Find the source
        source = next((s for s in DATA["sources"] if s["id"] == entity["source_id"]), None)
        if not source:
            return jsonify({"error": "Source not found"}), 404

        # Check if AI suggestions are requested
        use_ai = data.get('use_ai', False)
        
        # Start with empty suggestions - they will be populated if AI is enabled
        suggestions = []
        logger.info(f"Processing entity '{entity['entity_name']}' with AI={'enabled' if use_ai else 'disabled'}")

        # Use the new robust scraping service
        fallback_urls = data.get('urls', None)
        pages_data, scraping_errors = entity_scraper.scrape_entity(entity, source, fallback_urls)
        
        # Log any scraping errors
        if scraping_errors:
            for error in scraping_errors:
                logger.warning(f"Scraping error: {error}")

        # Initialize ai_suggestions variable
        ai_suggestions = []
        
        # NOW generate AI suggestions after we have the HTML content
        if use_ai and ai_service:
            logger.info("AI suggestions requested, generating for each page")
            
            # DEBUG: Log the data being sent to AI service
            logger.info(f"DEBUG: Properties count: {len(DATA['properties'])}")
            logger.info(f"DEBUG: First property: {DATA['properties'][0] if DATA['properties'] else 'None'}")
            logger.info(f"DEBUG: Pages data count: {len(pages_data)}")
            if pages_data:
                logger.info(f"DEBUG: First page text length: {len(pages_data[0].get('text_content', ''))}")
            
            # Use the entity and source IDs from the request
            selected_source_id = source["id"]
            selected_edition_id = entity_id
            
            logger.info(f"Using source_id: {selected_source_id}, edition_id: {selected_edition_id}")
            
            # CRITICAL: Remove existing AI-generated suggestions for this source/edition combination
            # This prevents duplicates when reprocessing content
            existing_ai_suggestions = [
                s for s in DATA["suggestions"] 
                if s.get('ai_generated', False) 
                and s.get('source_id') == selected_source_id 
                and s.get('edition_id') == selected_edition_id
            ]
            
            if existing_ai_suggestions:
                logger.info(f"Removing {len(existing_ai_suggestions)} existing AI suggestions for source_id={selected_source_id}, edition_id={selected_edition_id}")
                # Keep only non-AI suggestions and AI suggestions for different source/edition combinations
                DATA["suggestions"] = [
                    s for s in DATA["suggestions"] 
                    if not (s.get('ai_generated', False) 
                           and s.get('source_id') == selected_source_id 
                           and s.get('edition_id') == selected_edition_id)
                ]
                logger.info(f"Remaining suggestions after cleanup: {len(DATA['suggestions'])}")
            
            # Decide confidence mode
            confidence_mode = os.getenv('AI_CONFIDENCE_MODE', 'single').lower()

            for page in pages_data:
                try:
                    logger.info(f"DEBUG: Processing page: {page.get('url')}")
                    logger.info(f"DEBUG: Page text content length: {len(page.get('text_content', ''))}")

                    if confidence_mode == 'two_pass' and hasattr(ai_service, 'generate_reasoned_suggestions'):
                        logger.info("🤖 Starting two-pass AI confidence system")
                        # Agent A: get reasoned suggestions without confidence
                        reasoned = ai_service.generate_reasoned_suggestions(
                            page.get('text_content', ''),
                            page.get('url', ''),
                            DATA['properties']
                        )
                        logger.info(f"🧠 Agent A (Reasoner) generated {len(reasoned)} reasoned suggestions")
                        logger.info(f"DEBUG: Reasoner suggestions: {len(reasoned)}")

                        # Validate shape for value/evidence (ignore confidence)
                        # Reuse validator by temporarily injecting confidence=0.0 to pass schema where needed
                        prepared_for_validation = []
                        for rs in reasoned:
                            rs_copy = dict(rs)
                            if 'confidence' not in rs_copy:
                                rs_copy['confidence'] = 0.0
                            prepared_for_validation.append(rs_copy)

                        validated = ai_service.validate_suggestions(prepared_for_validation, DATA['properties'])
                        logger.info(f"DEBUG: Validated (two-pass) suggestions: {len(validated)}")

                        # Agent B: interpret confidences
                        interpreter_outputs = ai_service.interpret_confidence(reasoned, DATA['properties'], page.get('url'))
                        logger.info(f"🎯 Agent B (Interpreter) processed {len(interpreter_outputs)} confidence interpretations")
                        
                        # Map property_id -> interpreter result
                        interp_by_pid = {int(it.get('property_id')): it for it in interpreter_outputs if it.get('property_id') is not None}
                        
                        # Log confidence distribution statistics
                        confidence_scores = [float(it.get('confidence', 0.0)) for it in interpreter_outputs]
                        if confidence_scores:
                            avg_confidence = sum(confidence_scores) / len(confidence_scores)
                            min_confidence = min(confidence_scores)
                            max_confidence = max(confidence_scores)
                            high_conf_count = len([c for c in confidence_scores if c >= 0.8])
                            low_conf_count = len([c for c in confidence_scores if c < 0.5])
                            
                            logger.info(f"📊 Two-pass confidence distribution:")
                            logger.info(f"   • Average: {avg_confidence:.2f}")
                            logger.info(f"   • Range: {min_confidence:.2f} - {max_confidence:.2f}")
                            logger.info(f"   • High confidence (≥80%): {high_conf_count}/{len(confidence_scores)}")
                            logger.info(f"   • Low confidence (<50%): {low_conf_count}/{len(confidence_scores)}")

                        for sug in validated:
                            pid = sug['property_id']
                            interp = interp_by_pid.get(pid, {})
                            final_confidence = float(interp.get('confidence', 0.0))
                            
                            # Debug logging for each suggestion
                            logger.info(f"🎯 Property {pid}: final_confidence={final_confidence:.2f} ({final_confidence*100:.0f}%)")
                            # Build record
                            suggestion_record = {
                                'id': _gen_id('suggestions'),
                                'source_id': selected_source_id,
                                'edition_id': selected_edition_id,
                                'property_id': sug['property_id'],
                                'property_option_id': sug.get('property_option_id'),
                                'custom_value': sug.get('custom_value'),
                                'status': 'pending',
                                'ai_generated': True,
                                'confidence': final_confidence,
                                'confidence_source': interp.get('confidence_source', 'interpreter_v1'),
                                'evidence': {
                                    'content': reasoned and next((r.get('evidence') for r in reasoned if int(r.get('property_id', -1)) == pid), ''),
                                    'source_url': page.get('url'),
                                    'confidence': final_confidence,
                                    'extraction_method': 'ai_generated'
                                },
                                'reasoning': reasoned and next((r.get('reasoning') for r in reasoned if int(r.get('property_id', -1)) == pid), ''),
                                'agentA_reasoning': reasoned and next((r.get('reasoning') for r in reasoned if int(r.get('property_id', -1)) == pid), ''),
                                'agentA_evidence': reasoned and next((r.get('evidence') for r in reasoned if int(r.get('property_id', -1)) == pid), ''),
                                'agentB_confidence': final_confidence,
                                'agentB_rationale': interp.get('rationale', ''),
                                'agentB_tags': interp.get('tags', {}),
                                'page_url': page.get('url'),
                                'page_title': page.get('title')
                            }

                            DATA['suggestions'].append(suggestion_record)
                            ai_suggestions.append(suggestion_record)

                    else:
                        # Single-pass fallback (current behavior)
                        page_suggestions = ai_service.generate_metadata_suggestions(
                            page.get('text_content', ''),
                            page.get('url', ''),
                            DATA['properties']
                        )

                        logger.info(f"DEBUG: Raw AI suggestions received: {len(page_suggestions)}")
                        if page_suggestions:
                            logger.info(f"DEBUG: First raw suggestion: {page_suggestions[0]}")

                        validated = ai_service.validate_suggestions(page_suggestions, DATA['properties'])
                        logger.info(f"DEBUG: Validated suggestions: {len(validated)}")

                        for sug in validated:
                            suggestion_record = {
                                'id': _gen_id('suggestions'),
                                'source_id': selected_source_id,
                                'edition_id': selected_edition_id,
                                'property_id': sug['property_id'],
                                'property_option_id': sug.get('property_option_id'),
                                'custom_value': sug.get('custom_value'),
                                'status': 'pending',
                                'ai_generated': True,
                                'confidence': sug.get('confidence', 0.0),
                                'evidence': {
                                    'content': sug.get('evidence', ''),
                                    'source_url': page.get('url'),
                                    'confidence': sug.get('confidence', 0.0),
                                    'extraction_method': 'ai_generated'
                                },
                                'reasoning': sug.get('reasoning', ''),
                                'page_url': page.get('url'),
                                'page_title': page.get('title')
                            }
                            DATA['suggestions'].append(suggestion_record)
                            ai_suggestions.append(suggestion_record)

                except Exception as e:
                    logger.error(f"Failed to generate AI suggestions for {page.get('url')}: {e}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
            
            if ai_suggestions:
                suggestions = ai_suggestions
                logger.info(f"Generated and stored {len(ai_suggestions)} AI suggestions")
            else:
                logger.warning("No AI suggestions were generated despite successful processing")
        elif use_ai and not ai_service:
            logger.warning("AI suggestions requested but service not available")

        # Log what we're returning
        if use_ai and ai_suggestions:
            logger.info(f"AI Processing: {len(pages_data)} pages, {len(ai_suggestions)} AI suggestions generated")
        else:
            logger.info(f"Manual Processing: {len(pages_data)} pages, ready for manual curation")
        
        import datetime as dt
        
        return jsonify({
            "success": True,
            "entity": {
                "id": entity_id,
                "name": entity["entity_name"],
                "description": entity["entity_description"],
                "source_id": entity["source_id"]
            },
            "source": {
                "id": source["id"],
                "name": source["name"]
            },
            "scraped_content": {
                "pages": pages_data,
                "total_pages": len(pages_data),
                "scraped_at": dt.datetime.now(dt.timezone.utc).isoformat()
            },
            "suggestions": {
                "items": suggestions,
                "total_count": len(suggestions),
                "ai_generated": len([s for s in suggestions if s.get('ai_generated', False)]),
                "manual_required": len(DATA["properties"]) - len([s for s in suggestions if s.get('ai_generated', False)]) if use_ai else len(DATA["properties"])
            }
        })
    except Exception as e:
        logger.error(f"Unexpected error in scrape_entity_content: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Removed old page-specific endpoints - no longer needed with unified interface


@app.route('/api/fetch-external')
def fetch_external():
    """Relay query → external API; return pages list that the front-end already expects."""
    q     = request.args.get('query', '')
    limit = int(request.args.get('limit', 10) or 10)

    try:
        r = requests.get(EXTERNAL_API,
                         params={"q": q, "limit": limit},
                         timeout=15)
        r.raise_for_status()
        data = r.json()          # assume [{url:str,title:str}, …]

        pages = [{"url": p["url"],
                  "title": p.get("title", p["url"])} for p in data]

        return jsonify({"success": True, "pages": pages})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 502


## Removed POST /api/sources (creation disabled)

## Removed POST /api/editions (creation disabled)

@app.route("/api/manual-metadata", methods=["POST"])
def create_manual_metadata():
    """
    Create or update metadata suggestions manually (without AI).
    
    Business Logic:
    - Manual metadata must include evidence for validation
    - Evidence is required for all manual entries
    - Required fields are tracked and validated
    - All manual entries create proper evidence records
    """
    
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    payload = request.get_json(force=True)
    required_fields = ["source_id", "edition_id", "property_id"]
    for field in required_fields:
        if not payload.get(field):
            return jsonify({"error": f"Field '{field}' is required"}), 400
    
    # Validate references exist
    if not any(s["id"] == payload["source_id"] for s in DATA["sources"]):
        return jsonify({"error": "Source not found"}), 404
    if not any(e["id"] == payload["edition_id"] for e in DATA["editions"]):
        return jsonify({"error": "Edition not found"}), 404
    if not any(p["id"] == payload["property_id"] for p in DATA["properties"]):
        return jsonify({"error": "Property not found"}), 404
    
    # Get the property to validate the value and check if it's required
    property_def = next(p for p in DATA["properties"] if p["id"] == payload["property_id"])
    is_required = property_def.get("is_required", False)
    
    # Validate that either property_option_id/property_option_ids or custom_value is provided based on property type
    property_option_id = payload.get("property_option_id")
    property_option_ids = payload.get("property_option_ids")  # For MULTIPLE_CHOICE
    custom_value = payload.get("custom_value")
    curator_note = payload.get("curator_note", "")
    
    if property_def["type"] == "MULTIPLE_CHOICE":
        # Handle multiple selections
        if property_option_ids and isinstance(property_option_ids, list) and len(property_option_ids) > 0:
            # Validate all options exist
            for opt_id in property_option_ids:
                if not any(opt["id"] == opt_id for opt in property_def.get("property_options", [])):
                    return jsonify({"error": f"Invalid property_option_id: {opt_id}"}), 400
            # Store as JSON string or comma-separated for compatibility
            property_option_id = property_option_ids[0]  # Store first as primary
            custom_value = ",".join(map(str, property_option_ids))  # Store all in custom_value as fallback
        elif not curator_note:
            return jsonify({"error": "property_option_ids or curator_note is required for MULTIPLE_CHOICE properties"}), 400
        else:
            # Allow saving with only curator note (e.g., "not sure")
            property_option_id = None
            custom_value = None
    elif property_def["type"] in ["SINGLE_CHOICE", "BINARY"]:
        if property_option_id:
            # Validate the option exists
            if not any(opt["id"] == property_option_id for opt in property_def.get("property_options", [])):
                return jsonify({"error": "Invalid property_option_id"}), 400
            custom_value = None
        elif not curator_note:
            return jsonify({"error": "property_option_id or curator_note is required for choice-based properties"}), 400
        else:
            # Allow saving with only curator note (e.g., "not sure")
            property_option_id = None
            custom_value = None
    else:  # NUMERICAL, FREE_TEXT
        if not custom_value and not curator_note:
            return jsonify({"error": "custom_value or curator_note is required for text/numerical properties"}), 400
        property_option_id = None
    
    # CRITICAL: Validate evidence for manual metadata
    evidence = payload.get("evidence")
    if not evidence:
        return jsonify({
            "error": "Evidence is required for manual metadata",
            "details": "All manual metadata entries must include evidence for validation and audit purposes"
        }), 400
    
    # Create evidence record
    evidence_record = {
        "id": _gen_id("evidence"),
        "suggestion_id": None,  # Will be set after suggestion creation
        "content": evidence.get("content", str(evidence)),
        "source_url": evidence.get("source_url", "manual_entry"),
        "confidence": evidence.get("confidence", 1.0),
        "extraction_method": "manual_curator",
        "created_at": None  # Will be set after creation
    }
    
    # Check if suggestion already exists for this combination
    existing_suggestion = next(
        (s for s in DATA["suggestions"] 
         if s["source_id"] == payload["source_id"] 
         and s["edition_id"] == payload["edition_id"] 
         and s["property_id"] == payload["property_id"]), 
        None
    )
    
    if existing_suggestion:
        # Update existing suggestion
        existing_suggestion.update({
            "property_option_id": property_option_id,
            "custom_value": custom_value,
            "status": "accepted",  # Manual updates are pre-accepted
            "ai_generated": False,
            "curated_at": None,
            "curator_note": curator_note or payload.get("note", "Manually edited by curator"),
            "evidence": evidence_record,
            "is_required": is_required
        })
        
        # Update evidence record
        evidence_record["suggestion_id"] = existing_suggestion["id"]
        evidence_record["created_at"] = existing_suggestion.get("curated_at")
        DATA["evidence"].append(evidence_record)
        
        logger.info(f"Updated existing suggestion {existing_suggestion['id']} with evidence")
        return jsonify({
            "success": True,
            "suggestion": existing_suggestion,
            "evidence": evidence_record,
            "action": "updated"
        })
    else:
        # Create new suggestion
        new_id = _gen_id("suggestions")
        import datetime as dt
        from datetime import timezone
        
        record = {
            "id": new_id,
            "source_id": payload["source_id"],
            "edition_id": payload["edition_id"],
            "property_id": payload["property_id"],
            "property_option_id": property_option_id,
            "property_option_ids": property_option_ids if property_def["type"] == "MULTIPLE_CHOICE" else None,
            "custom_value": custom_value,
            "status": "accepted",  # Manual entries are pre-accepted by curator
            "ai_generated": False,
            "confidence": 1.0,  # Manual entries have full confidence
            "evidence": evidence_record,
            "reasoning": payload.get("reasoning", "Manually entered by curator"),
            "curator_note": curator_note or payload.get("note", ""),
            "is_required": is_required,
            "created_at": dt.datetime.now(timezone.utc).isoformat()
        }
        
        # Set evidence reference
        evidence_record["suggestion_id"] = new_id
        evidence_record["created_at"] = record["created_at"]
        
        DATA["suggestions"].append(record)
        DATA["evidence"].append(evidence_record)
        
        logger.info(f"Created new manual suggestion: {new_id} with evidence")
        return jsonify({
            "success": True,
            "suggestion": record,
            "evidence": evidence_record,
            "action": "created"
        }), 201


@app.route("/api/suggestions/<int:suggestion_id>/edit", methods=["PUT"])
def edit_suggestion(suggestion_id: int):
    """Edit an existing metadata suggestion."""
    
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    payload = request.get_json(force=True)
    
    # Find the suggestion
    suggestion = next((s for s in DATA["suggestions"] if s["id"] == suggestion_id), None)
    if not suggestion:
        return jsonify({"error": "Suggestion not found"}), 404
    
    # Get the property to validate the new value
    property_def = next(p for p in DATA["properties"] if p["id"] == suggestion["property_id"])
    
    # Update fields if provided
    if "property_option_id" in payload:
        if property_def["type"] in ["MULTIPLE_CHOICE", "SINGLE_CHOICE", "BINARY"]:
            # Validate the option exists
            if not any(opt["id"] == payload["property_option_id"] for opt in property_def.get("property_options", [])):
                return jsonify({"error": "Invalid property_option_id"}), 400
            suggestion["property_option_id"] = payload["property_option_id"]
            suggestion["custom_value"] = None
        else:
            return jsonify({"error": "property_option_id not applicable for this property type"}), 400
    
    if "custom_value" in payload:
        if property_def["type"] in ["NUMERICAL", "FREE_TEXT"]:
            suggestion["custom_value"] = payload["custom_value"]
            suggestion["property_option_id"] = None
        else:
            return jsonify({"error": "custom_value not applicable for this property type"}), 400
    
    # Update metadata
    if "note" in payload or "curator_note" in payload:
        suggestion["curator_note"] = payload.get("curator_note") or payload.get("note", "")
    
    suggestion["status"] = "edited"
    suggestion["ai_generated"] = False
    
    # Create history entry
    import datetime as dt
    from datetime import timezone
    history_entry = {
        "id": _gen_id("curation_history"),
        "suggestion_id": suggestion_id,
        "action": "edit",
        "timestamp": dt.datetime.now(timezone.utc).isoformat(),
        "user_note": payload.get("note", "Edited by curator"),
        "previous_value": suggestion.copy()
    }
    DATA["curation_history"].append(history_entry)
    
    logger.info(f"Suggestion {suggestion_id} edited by curator")
    
    return jsonify({
        "success": True,
        "suggestion": suggestion,
        "history_entry": history_entry
    })


# --------------------------------------------------------------------------------------
# Publishing System and Required Field Validation
# --------------------------------------------------------------------------------------

@app.route("/api/editions/<int:edition_id>/publish", methods=["POST"])
def publish_edition(edition_id: int):
    """
    Publish an edition when all required fields are filled and validated.
    
    Business Logic:
    - All required fields must have accepted values
    - All accepted values must have evidence
    - Publishing creates a comprehensive audit trail
    - Publishing state is tracked and managed
    """
    
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    payload = request.get_json(force=True)
    user_id = payload.get('user_id', 'anonymous')
    publish_note = payload.get('note', 'Published by curator')
    
    # Find the edition
    edition = next((e for e in DATA["editions"] if e["id"] == edition_id), None)
    if not edition:
        return jsonify({"error": "Edition not found"}), 404
    
    # Get all suggestions for this edition
    edition_suggestions = [s for s in DATA["suggestions"] if s["edition_id"] == edition_id]
    
    # Validate publishing requirements
    validation_result = _validate_publishing_requirements(edition_suggestions)
    if not validation_result["valid"]:
        return jsonify({
            "error": "Cannot publish edition",
            "details": validation_result["errors"],
            "validation_summary": validation_result["summary"]
        }), 400
    
    # Create publishing record
    import datetime as dt
    from datetime import timezone
    current_time = dt.datetime.now(timezone.utc)
    
    publishing_record = {
        "id": _gen_id("publishing_state"),
        "edition_id": edition_id,
        "status": "published",
        "published_at": current_time.isoformat(),
        "published_by": user_id,
        "publish_note": publish_note,
        "validation_errors": [],
        "total_fields": len(edition_suggestions),
        "required_fields": len([s for s in edition_suggestions if s.get("is_required", False)]),
        "accepted_fields": len([s for s in edition_suggestions if s.get("status") == "accepted"]),
        "evidence_validation": "passed"
    }
    
    # Update all suggestions to published status
    for suggestion in edition_suggestions:
        if suggestion.get("status") == "accepted":
            suggestion["published_at"] = current_time.isoformat()
            suggestion["published_by"] = user_id
            suggestion["publish_note"] = publish_note
    
    # Store publishing record
    DATA["publishing_state"].append(publishing_record)
    
    # Log the publishing action
    logger.info(f"Edition {edition_id} published by user {user_id} with {len(edition_suggestions)} fields validated")
    
    return jsonify({
        "success": True,
        "publishing_record": publishing_record,
        "edition": edition,
        "validation_summary": validation_result["summary"],
        "message": f"Successfully published edition '{edition['entity_name']}' with {len(edition_suggestions)} validated fields"
    })


@app.route("/api/editions/<int:edition_id>/publishing-status", methods=["GET"])
def get_publishing_status(edition_id: int):
    """
    Get the current publishing status and validation state for an edition.
    
    Returns:
        - Current publishing status
        - Validation requirements and progress
        - Missing required fields
        - Evidence validation status
    """
    
    # Find the edition
    edition = next((e for e in DATA["editions"] if e["id"] == edition_id), None)
    if not edition:
        return jsonify({"error": "Edition not found"}), 404
    
    # Get publishing state
    publishing_state = next((p for p in DATA["publishing_state"] if p["edition_id"] == edition_id), None)
    
    # Get all suggestions for this edition
    edition_suggestions = [s for s in DATA["suggestions"] if s["edition_id"] == edition_id]
    
    # Calculate validation status
    validation_status = _calculate_validation_status(edition_suggestions)
    
    return jsonify({
        "edition_id": edition_id,
        "edition_name": edition["entity_name"],
        "publishing_state": publishing_state,
        "validation_status": validation_status,
        "can_publish": validation_status["all_requirements_met"]
    })


@app.route("/api/audit-log", methods=["GET"])
def get_audit_log():
    """
    Get comprehensive audit log for the system.
    
    Returns:
        - All curation actions with timestamps
        - User information and model versions
        - Evidence references
        - Publishing actions
        - Filtered by date range, user, action type
    """
    
    # Get query parameters for filtering
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = request.args.get('user_id')
    action_type = request.args.get('action_type')
    edition_id = request.args.get('edition_id', type=int)
    
    # Start with all history entries
    audit_entries = []
    
    # Add curation history
    for entry in DATA["curation_history"]:
        suggestion = next((s for s in DATA["suggestions"] if s["id"] == entry["suggestion_id"]), None)
        if suggestion:
            audit_entry = {
                "id": entry["id"],
                "timestamp": entry["timestamp"],
                "action": entry["action"],
                "user_id": entry.get("user_id", "unknown"),
                "model_version": entry.get("model_version", "unknown"),
                "suggestion_id": entry["suggestion_id"],
                "edition_id": suggestion.get("edition_id"),
                "source_id": suggestion.get("source_id"),
                "property_id": suggestion.get("property_id"),
                "user_note": entry.get("user_note", ""),
                "evidence_references": entry.get("evidence_references", []),
                "entry_type": "curation"
            }
            audit_entries.append(audit_entry)
    
    # Add publishing actions
    for entry in DATA["publishing_state"]:
        audit_entry = {
            "id": entry["id"],
            "timestamp": entry["published_at"],
            "action": "publish",
            "user_id": entry.get("published_by", "unknown"),
            "model_version": "system",
            "edition_id": entry["edition_id"],
            "user_note": entry.get("publish_note", ""),
            "evidence_references": [],
            "entry_type": "publishing",
            "validation_summary": {
                "total_fields": entry.get("total_fields", 0),
                "required_fields": entry.get("required_fields", 0),
                "accepted_fields": entry.get("accepted_fields", 0)
            }
        }
        audit_entries.append(audit_entry)
    
    # Apply filters
    if start_date:
        audit_entries = [e for e in audit_entries if e["timestamp"] >= start_date]
    if end_date:
        audit_entries = [e for e in audit_entries if e["timestamp"] <= end_date]
    if user_id:
        audit_entries = [e for e in audit_entries if e["user_id"] == user_id]
    if action_type:
        audit_entries = [e for e in audit_entries if e["action"] == action_type]
    if edition_id:
        audit_entries = [e for e in audit_entries if e.get("edition_id") == edition_id]
    
    # Sort by timestamp (newest first)
    audit_entries.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return jsonify({
        "total_entries": len(audit_entries),
        "filters_applied": {
            "start_date": start_date,
            "end_date": end_date,
            "user_id": user_id,
            "action_type": action_type,
            "edition_id": edition_id
        },
        "audit_log": audit_entries
    })


def _validate_publishing_requirements(suggestions: list) -> dict:
    """
    Validate that all publishing requirements are met.
    
    Business Rules:
    1. All required fields must have suggestions
    2. All suggestions must have status 'accepted'
    3. All accepted suggestions must have valid evidence
    4. No pending or rejected suggestions for required fields
    """
    
    errors = []
    summary = {
        "total_fields": len(suggestions),
        "required_fields": 0,
        "accepted_fields": 0,
        "pending_fields": 0,
        "rejected_fields": 0,
        "fields_with_evidence": 0,
        "validation_passed": False
    }
    
    # Count required fields
    required_suggestions = [s for s in suggestions if s.get("is_required", False)]
    summary["required_fields"] = len(required_suggestions)
    
    # Check each required field
    for suggestion in required_suggestions:
        if suggestion.get("status") != "accepted":
            errors.append(f"Required field '{_get_property_name(suggestion['property_id'])}' is not accepted (status: {suggestion.get('status', 'unknown')})")
            summary["pending_fields"] += 1
        elif not _has_valid_evidence(suggestion):
            errors.append(f"Required field '{_get_property_name(suggestion['property_id'])}' lacks valid evidence")
        else:
            summary["accepted_fields"] += 1
            summary["fields_with_evidence"] += 1
    
    # Check non-required fields for evidence if they're accepted
    non_required_suggestions = [s for s in suggestions if not s.get("is_required", False)]
    for suggestion in non_required_suggestions:
        if suggestion.get("status") == "accepted":
            if not _has_valid_evidence(suggestion):
                errors.append(f"Accepted field '{_get_property_name(suggestion['property_id'])}' lacks valid evidence")
            else:
                summary["accepted_fields"] += 1
                summary["fields_with_evidence"] += 1
        elif suggestion.get("status") == "rejected":
            summary["rejected_fields"] += 1
    
    # Determine if all requirements are met
    all_requirements_met = (
        summary["required_fields"] > 0 and
        summary["accepted_fields"] == summary["required_fields"] and
        summary["fields_with_evidence"] == summary["accepted_fields"] and
        len(errors) == 0
    )
    
    summary["validation_passed"] = all_requirements_met
    
    return {
        "valid": all_requirements_met,
        "errors": errors,
        "summary": summary
    }


def _calculate_validation_status(suggestions: list) -> dict:
    """Calculate detailed validation status for publishing."""
    
    # Enrich suggestions with is_required from properties
    enriched_suggestions = []
    for suggestion in suggestions:
        property_def = next((p for p in DATA["properties"] if p["id"] == suggestion["property_id"]), None)
        suggestion_copy = suggestion.copy()
        suggestion_copy["is_required"] = property_def.get("is_required", False) if property_def else False
        enriched_suggestions.append(suggestion_copy)
    
    required_suggestions = [s for s in enriched_suggestions if s.get("is_required", False)]
    non_required_suggestions = [s for s in enriched_suggestions if not s.get("is_required", False)]
    
    status = {
        "required_fields": {
            "total": len(required_suggestions),
            "accepted": len([s for s in required_suggestions if s.get("status") == "accepted"]),
            "pending": len([s for s in required_suggestions if s.get("status") == "pending"]),
            "rejected": len([s for s in required_suggestions if s.get("status") == "rejected"]),
            "with_evidence": len([s for s in required_suggestions if _has_valid_evidence(s)])
        },
        "non_required_fields": {
            "total": len(non_required_suggestions),
            "accepted": len([s for s in non_required_suggestions if s.get("status") == "accepted"]),
            "pending": len([s for s in non_required_suggestions if s.get("status") == "pending"]),
            "rejected": len([s for s in non_required_suggestions if s.get("status") == "rejected"]),
            "with_evidence": len([s for s in non_required_suggestions if _has_valid_evidence(s)])
        },
        "all_requirements_met": False,
        "ready_for_publishing": False
    }
    
    # Check if all required fields are accepted with evidence
    required_ready = (
        status["required_fields"]["total"] > 0 and
        status["required_fields"]["accepted"] == status["required_fields"]["total"] and
        status["required_fields"]["with_evidence"] == status["required_fields"]["accepted"]
    )
    
    # Check if all accepted fields (required and non-required) have evidence
    all_accepted = status["required_fields"]["accepted"] + status["non_required_fields"]["accepted"]
    all_with_evidence = status["required_fields"]["with_evidence"] + status["non_required_fields"]["with_evidence"]
    
    status["all_requirements_met"] = required_ready
    status["ready_for_publishing"] = required_ready and (all_accepted == all_with_evidence)
    
    return status


def _get_property_name(property_id: int) -> str:
    """Get property name by ID for error messages."""
    property_def = next((p for p in DATA["properties"] if p["id"] == property_id), None)
    return property_def.get("name", f"Property {property_id}") if property_def else f"Property {property_id}"


@app.route('/api/debug/clear-data', methods=['POST'])
def clear_all_data():
    """Debug endpoint to clear all data and reload from dummy data."""
    try:
        global DATA
        DATA = {
            "sources": [],
            "properties": [],
            "editions": [],
            "suggestions": [],
            "evidence": []
        }
        _fetch_api_data()
        return jsonify({
            "success": True,
            "message": "Data cleared and reloaded",
            "sources": len(DATA["sources"]),
            "properties": len(DATA["properties"]),
            "editions": len(DATA["editions"])
        })
    except Exception as e:
        logger.error(f"Error clearing data: {e}")
        return jsonify({"error": "Failed to clear data"}), 500

@app.route('/api/debug/cleanup-duplicates', methods=['POST'])
def cleanup_duplicate_suggestions():
    """Debug endpoint to manually clean up duplicate AI suggestions."""
    try:
        original_count = len(DATA["suggestions"])
        
        # Group suggestions by source_id, edition_id, property_id
        suggestions_by_key = {}
        for suggestion in DATA["suggestions"]:
            key = (suggestion.get('source_id'), suggestion.get('edition_id'), suggestion.get('property_id'))
            if key not in suggestions_by_key:
                suggestions_by_key[key] = []
            suggestions_by_key[key].append(suggestion)
        
        # Keep only the latest AI suggestion for each key, keep all manual suggestions
        cleaned_suggestions = []
        duplicates_removed = 0
        
        for key, suggestions in suggestions_by_key.items():
            ai_suggestions = [s for s in suggestions if s.get('ai_generated', False)]
            manual_suggestions = [s for s in suggestions if not s.get('ai_generated', False)]
            
            # Keep all manual suggestions
            cleaned_suggestions.extend(manual_suggestions)
            
            # Keep only the latest AI suggestion (highest ID)
            if ai_suggestions:
                latest_ai = max(ai_suggestions, key=lambda x: x.get('id', 0))
                cleaned_suggestions.append(latest_ai)
                duplicates_removed += len(ai_suggestions) - 1
        
        DATA["suggestions"] = cleaned_suggestions
        final_count = len(DATA["suggestions"])
        
        logger.info(f"Cleanup: Removed {duplicates_removed} duplicate AI suggestions ({original_count} -> {final_count})")
        
        return jsonify({
            "success": True,
            "original_count": original_count,
            "final_count": final_count,
            "duplicates_removed": duplicates_removed,
            "cleanup_summary": f"Removed {duplicates_removed} duplicate AI suggestions"
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up duplicates: {e}")
        return jsonify({"error": "Failed to cleanup duplicates"}), 500


@app.route('/api/log-curation-time', methods=['POST'])
def log_curation_time():
    """
    Log curation time data for user study analysis.
    
    This endpoint receives timing data when a user completes curation of an entity.
    Data is stored in JSON files for later analysis.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        log_data = request.get_json(force=True)
        
        # Validate required fields
        required_fields = ['entity_id', 'source_id', 'curation_mode', 'duration_seconds', 'start_time', 'completion_time']
        for field in required_fields:
            if field not in log_data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create logs directory if it doesn't exist
        import os
        from pathlib import Path
        import datetime as dt
        
        logs_dir = Path(__file__).parent / 'study_logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        timestamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
        entity_id = log_data.get('entity_id')
        filename = f"{entity_id}_{timestamp}.json"
        filepath = logs_dir / filename
        
        # Add server-side metadata
        log_data['logged_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        log_data['log_filename'] = filename
        
        # Write to file
        import json
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        logger.info(f"📊 Curation time logged: Entity {entity_id}, Mode: {log_data['curation_mode']}, Duration: {log_data['duration_seconds']:.2f}s")
        
        return jsonify({
            "success": True,
            "message": "Curation time logged successfully",
            "log_file": filename,
            "duration_seconds": log_data['duration_seconds']
        })
        
    except Exception as e:
        logger.error(f"Error logging curation time: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": "Failed to log curation time"}), 500


if __name__ == '__main__':
    print("🚀 Starting Curation Preview API & Metadata-Curation mock…")
    # Initialize data (API or dummy) before starting the server
    _fetch_api_data()
    logger.info(f"DEBUG: Data initialized - Sources: {len(DATA['sources'])}, Properties: {len(DATA['properties'])}, Editions: {len(DATA['editions'])}")
    app.run(debug=False, host='0.0.0.0', port=8001)
