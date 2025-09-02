#!/usr/bin/env python3
"""
AI-powered metadata curation service using OpenAI GPT models.
Generates metadata suggestions based on HTML content analysis.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AICurationService:
    """Service for AI-powered metadata curation using OpenAI."""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.temperature = float(os.getenv('AI_TEMPERATURE', '0.3'))
        self.max_tokens = int(os.getenv('AI_MAX_TOKENS', '2000'))
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI client with explicit configuration
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=30.0
            )
            logger.info(f"AI Curation Service initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if the AI service is available and working."""
        try:
            if not hasattr(self, 'client') or self.client is None:
                return False
            # Try a simple API call to test connectivity
            self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"AI service availability check failed: {e}")
            return False
    
    def generate_metadata_suggestions(
        self, 
        html_content: str, 
        url: str,
        existing_properties: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate metadata suggestions using AI based on HTML content.
        
        Args:
            html_content: Raw HTML content from the webpage
            url: Source URL for context
            existing_properties: List of available metadata properties
            
        Returns:
            List of metadata suggestions with confidence scores
        """
        try:
            # Check if client is properly initialized
            if not hasattr(self, 'client') or self.client is None:
                logger.error("OpenAI client not properly initialized")
                return []
            
            # Prepare the prompt for the AI
            prompt = self._build_prompt(html_content, url, existing_properties)
            
            # Call OpenAI API with error handling
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert metadata curator for digital libraries. Analyze the provided HTML content and generate metadata suggestions based on the available property types. Return only valid JSON."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
                
                # Parse the AI response
                ai_response = response.choices[0].message.content
                suggestions = json.loads(ai_response)
                
                logger.info(f"AI generated {len(suggestions.get('suggestions', []))} metadata suggestions")
                return suggestions.get('suggestions', [])
                
            except Exception as api_error:
                logger.error(f"OpenAI API error: {str(api_error)}")
                return []
            
        except Exception as e:
            logger.error(f"Error generating AI suggestions: {str(e)}")
            return []
    
    def _build_prompt(self, html_content: str, url: str, properties: List[Dict[str, Any]]) -> str:
        """Build the prompt for the AI model."""
        
        # Clean HTML content (remove excessive whitespace, limit length)
        cleaned_content = ' '.join(html_content.split())[:8000]  # Limit to 8000 chars
        
        # Build property descriptions with IDs
        property_descriptions = []
        for prop in properties:
            prop_id = prop.get('id', 'UNKNOWN')
            prop_type = prop.get('type', 'UNKNOWN')
            prop_name = prop.get('name', 'Unknown')
            prop_tech = prop.get('technical_name', 'unknown')
            
            if prop_type in ['MULTIPLE_CHOICE', 'SINGLE_CHOICE']:
                options = [opt['name'] for opt in prop.get('property_options', [])]
                prop_desc = f"ID {prop_id}: {prop_name} ({prop_type}): {', '.join(options)}"
            elif prop_type == 'BINARY':
                prop_desc = f"ID {prop_id}: {prop_name} (BINARY): true/false"
            elif prop_type == 'NUMERICAL':
                prop_desc = f"ID {prop_id}: {prop_name} (NUMERICAL): numeric value"
            elif prop_type == 'FREE_TEXT':
                prop_desc = f"ID {prop_id}: {prop_name} (FREE_TEXT): descriptive text"
            else:
                prop_desc = f"ID {prop_id}: {prop_name} ({prop_type})"
            
            property_descriptions.append(f"- {prop_desc}")
        
        prompt = f"""
Analyze the following HTML content from {url} and generate metadata suggestions.

AVAILABLE METADATA PROPERTIES:
{chr(10).join(property_descriptions)}

HTML CONTENT:
{cleaned_content}

INSTRUCTIONS:
1. Analyze the HTML content to understand the webpage's topic, purpose, and key information
2. For each metadata property, provide a suggestion based on the content analysis
3. For CHOICE properties, select the most appropriate option from the available choices
4. For BINARY properties, determine true/false based on content evidence
5. For NUMERICAL properties, extract relevant numbers (years, quantities, etc.)
6. For FREE_TEXT properties, provide concise, descriptive text
7. Assign a confidence score (0.0 to 1.0) for each suggestion
8. Include evidence (specific text snippets) that supports each suggestion
9. Use the EXACT property ID numbers shown above

RETURN FORMAT (JSON):
{{
    "suggestions": [
        {{
            "property_id": <exact_property_id_number>,
            "property_technical_name": "<technical_name>",
            "suggested_value": "<value>",
            "confidence": <0.0-1.0>,
            "evidence": "<supporting text snippet>",
            "reasoning": "<brief explanation>"
        }}
    ]
}}

Generate suggestions based on what you can confidently determine from the content. Only suggest values when you have clear evidence. If you cannot determine a value for a property, set confidence to 0.0 and provide reasoning.
"""
        
        return prompt.strip()
    
    def validate_suggestions(
        self, 
        suggestions: List[Dict[str, Any]], 
        properties: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate and format AI suggestions to match our data model.
        
        Args:
            suggestions: Raw AI suggestions
            properties: Available metadata properties
            
        Returns:
            Validated suggestions ready for database insertion
        """
        validated_suggestions = []
        
        for suggestion in suggestions:
            try:
                # Find the corresponding property by ID
                prop_id = suggestion.get('property_id')
                if prop_id is None:
                    logger.warning("Suggestion missing property_id, skipping")
                    continue
                
                # Convert to int if it's a string
                try:
                    prop_id = int(prop_id)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid property_id format: {prop_id}, skipping")
                    continue
                
                prop = next((p for p in properties if p['id'] == prop_id), None)
                
                if not prop:
                    logger.warning(f"Property ID {prop_id} not found in available properties, skipping suggestion")
                    continue
                
                # Validate the suggestion based on property type
                validated_suggestion = self._validate_single_suggestion(suggestion, prop)
                if validated_suggestion:
                    validated_suggestions.append(validated_suggestion)
                    
            except Exception as e:
                logger.error(f"Error validating suggestion: {str(e)}")
                continue
        
        logger.info(f"Validated {len(validated_suggestions)} suggestions from AI")
        return validated_suggestions
    
    def _validate_single_suggestion(
        self, 
        suggestion: Dict[str, Any], 
        property_def: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Validate a single suggestion against its property definition."""
        
        prop_type = property_def.get('type')
        suggested_value = suggestion.get('suggested_value')
        confidence = suggestion.get('confidence', 0.0)
        
        # Validate confidence score
        if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
            confidence = 0.0
        
        # Validate value based on property type
        if prop_type == 'BINARY':
            if suggested_value in ['true', '1', True, 1]:
                property_option_id = next((opt['id'] for opt in property_def.get('property_options', []) if opt['name'] == '1'), None)
                custom_value = None
            elif suggested_value in ['false', '0', False, 0]:
                property_option_id = next((opt['id'] for opt in property_def.get('property_options', []) if opt['name'] == '0'), None)
                custom_value = None
            else:
                logger.warning(f"Invalid binary value: {suggested_value}")
                return None
                
        elif prop_type in ['MULTIPLE_CHOICE', 'SINGLE_CHOICE']:
            # Find matching option
            property_option_id = None
            custom_value = None
            for opt in property_def.get('property_options', []):
                if opt['name'].lower() == str(suggested_value).lower():
                    property_option_id = opt['id']
                    break
            
            if not property_option_id:
                logger.warning(f"No matching option found for {suggested_value} in {property_def['name']}")
                return None
                
        elif prop_type in ['NUMERICAL', 'FREE_TEXT']:
            property_option_id = None
            custom_value = str(suggested_value) if suggested_value else None
            
            if not custom_value:
                logger.warning(f"Empty value for {prop_type} property")
                return None
        
        else:
            logger.warning(f"Unknown property type: {prop_type}")
            return None
        
        # Return validated suggestion
        return {
            'property_id': property_def['id'],
            'property_option_id': property_option_id,
            'custom_value': custom_value,
            'confidence': confidence,
            'evidence': suggestion.get('evidence', ''),
            'reasoning': suggestion.get('reasoning', ''),
            'ai_generated': True
        }
