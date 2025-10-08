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
        # Optional model overrides for two-pass mode
        self.reasoner_model = os.getenv('AI_REASONER_MODEL', self.model)
        self.interpreter_model = os.getenv('AI_INTERPRETER_MODEL', self.model)
        self.temperature = float(os.getenv('AI_TEMPERATURE', '0.3'))
        self.max_tokens = int(os.getenv('AI_MAX_TOKENS', '2000'))
        # Confidence mode: 'single' (default) or 'two_pass'
        self.confidence_mode = os.getenv('AI_CONFIDENCE_MODE', 'single').lower()
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI client with explicit configuration
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=60.0
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
            
            # Prepare the prompt for the AI (single-pass default)
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
                    max_tokens=min(self.max_tokens, 800),
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

    # ----------------------------- Two-pass mode APIs -----------------------------
    def generate_reasoned_suggestions(
        self,
        html_content: str,
        url: str,
        properties: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Agent A (Reasoner): Generate suggestions WITHOUT confidence but WITH longer reasoning and concrete evidence.
        Returns a list of dicts with keys: property_id, property_technical_name, suggested_value, evidence, reasoning.
        """
        try:
            if not hasattr(self, 'client') or self.client is None:
                logger.error("OpenAI client not properly initialized")
                return []

            prompt = self._build_reasoner_prompt(html_content, url, properties)

            response = self.client.chat.completions.create(
                model=self.reasoner_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert metadata reasoner. Your reasoning will be analyzed by a strict confidence system. "
                            "BE HONEST about uncertainty - use appropriate hedging language when you're not 100% certain. "
                            "ALWAYS mention alternative interpretations you considered and why you rejected them. "
                            "Provide EXACT verbatim quotes as evidence whenever possible. "
                            "Use CLEAR language signals: "
                            "- CERTAIN: 'explicitly states', 'clearly shows', 'directly mentions' "
                            "- LIKELY: 'indicates', 'suggests', 'appears to be' "
                            "- UNCERTAIN: 'might', 'possibly', 'could be', 'seems to imply' "
                            "Return ONLY valid JSON with detailed, honest reasoning."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,  # Slightly higher for more nuanced reasoning
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            ai_response = response.choices[0].message.content
            parsed = json.loads(ai_response)
            suggestions = parsed.get('suggestions', [])
            logger.info(f"Reasoner produced {len(suggestions)} suggestions (no confidence)")
            # Ensure confidence is absent
            for s in suggestions:
                if 'confidence' in s:
                    s.pop('confidence', None)
            return suggestions
        except Exception as e:
            logger.error(f"Reasoner error: {e}")
            return []

    def interpret_confidence(
        self,
        reasoned_suggestions: List[Dict[str, Any]],
        properties: List[Dict[str, Any]],
        url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Agent B (Interpreter): Given the suggestions with reasoning/evidence, return calibrated confidences.
        Returns list of {property_id, confidence, rationale, tags}.
        """
        if not reasoned_suggestions:
            return []

        try:
            if not hasattr(self, 'client') or self.client is None:
                logger.error("OpenAI client not properly initialized")
                return []

            # Build interpreter prompt with compact property schema and the reasoned items
            prompt = self._build_interpreter_prompt(reasoned_suggestions, properties, url)

            response = self.client.chat.completions.create(
                model=self.interpreter_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a CONSERVATIVE confidence scorer for metadata curation. "
                            "Your job is to prevent overconfidence - be STRICT and CRITICAL. "
                            "Follow the algorithm exactly, applying ALL penalties. "
                            "High confidence (>0.80) should be RARE - reserve for explicit, unambiguous statements only. "
                            "Most scores should fall in 0.30-0.70 range. "
                            "Look for hedging language, ambiguity, missing evidence, and alternative interpretations. "
                            "When in doubt, score lower. Return ONLY valid JSON with calculations shown in rationale."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,  # Lower temperature for more consistent, conservative scoring
                max_tokens=min(self.max_tokens, 1200),
                response_format={"type": "json_object"},
            )

            ai_response = response.choices[0].message.content
            logger.debug(f"Agent B raw response: {ai_response}")
            
            try:
                parsed = json.loads(ai_response)
            except json.JSONDecodeError as e:
                logger.error(f"Agent B JSON parsing failed: {e}")
                logger.error(f"Raw response: {ai_response}")
                
                # Try to fix common JSON issues
                try:
                    # Remove trailing comma before closing bracket
                    fixed_response = ai_response.rstrip().rstrip(',')
                    if not fixed_response.endswith(']'):
                        fixed_response += ']'
                    if not fixed_response.endswith('}'):
                        fixed_response += '}'
                    
                    parsed = json.loads(fixed_response)
                    logger.info("Successfully fixed JSON parsing issue")
                except json.JSONDecodeError as e2:
                    logger.error(f"JSON fix attempt failed: {e2}")
                    return []
                
            items = parsed.get('confidences', [])
            # Normalize
            normalized = []
            for item in items:
                try:
                    pid = int(item.get('property_id'))
                    c = float(item.get('confidence', 0.0))
                    if c < 0.0:
                        c = 0.0
                    if c > 1.0:
                        c = 1.0
                    normalized.append({
                        'property_id': pid,
                        'confidence': c,
                        'rationale': item.get('rationale', ''),
                        'tags': item.get('tags', {}),
                        'confidence_source': 'interpreter_v1'
                    })
                except Exception:
                    continue
            logger.info(f"Interpreter produced confidences for {len(normalized)} properties")
            return normalized
        except Exception as e:
            logger.error(f"Interpreter error: {e}")
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

    def _build_reasoner_prompt(self, html_content: str, url: str, properties: List[Dict[str, Any]]) -> str:
        """Prompt for Agent A (Reasoner) without confidence, with longer reasoning and direct evidence."""
        cleaned_content = ' '.join(html_content.split())[:8000]

        property_descriptions = []
        for prop in properties:
            prop_id = prop.get('id', 'UNKNOWN')
            prop_type = prop.get('type', 'UNKNOWN')
            prop_name = prop.get('name', 'Unknown')
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
Analyze the following HTML content from {url} and propose metadata suggestions.

AVAILABLE METADATA PROPERTIES:
{chr(10).join(property_descriptions)}

HTML CONTENT:
{cleaned_content}

INSTRUCTIONS:
1. For each property, suggest a value if supported by content.
2. EVIDENCE: Provide DIRECT verbatim quotes when possible. Be specific about location/context.
3. REASONING: Write 3-6 sentences using CLEAR language patterns:
   - Use DEFINITIVE language when certain: "clearly states", "explicitly mentions", "definitively shows"
   - Use HEDGING language when uncertain: "might indicate", "possibly suggests", "seems to imply"
   - MENTION ALTERNATIVES: "Other options like X were rejected because..."
   - BE SPECIFIC: Include exact locations, context, and detailed analysis
4. DO NOT output confidence scores - a separate system will analyze your reasoning.
5. Use EXACT property ID numbers.

RETURN FORMAT (JSON):
{{
  "suggestions": [
    {{
      "property_id": <exact_property_id_number>,
      "property_technical_name": "<technical_name>",
      "suggested_value": "<value>",
      "evidence": "<direct quote or very specific snippet>",
      "reasoning": "<long reasoning, 3-6 sentences>"
    }}
  ]
}}
"""
        return prompt.strip()

    def _build_interpreter_prompt(
        self,
        reasoned_suggestions: List[Dict[str, Any]],
        properties: List[Dict[str, Any]],
        url: Optional[str] = None
    ) -> str:
        """Prompt for Agent B to assign calibrated confidences to reasoned suggestions."""
        # Build a compact property schema map for constraints/context
        prop_lines = []
        prop_map = {}
        for p in properties:
            pid = p.get('id')
            if pid is None:
                continue
            prop_map[int(pid)] = p
            ptype = p.get('type', 'FREE_TEXT')
            name = p.get('name', '')
            opts = ', '.join([o.get('name', '') for o in p.get('property_options', [])]) if ptype in ['MULTIPLE_CHOICE', 'SINGLE_CHOICE', 'BINARY'] else ''
            prop_lines.append(f"- {pid}: {name} [{ptype}] {opts}")

        items_lines = []
        for s in reasoned_suggestions:
            pid = s.get('property_id')
            val = s.get('suggested_value')
            ev = s.get('evidence', '')
            rs = s.get('reasoning', '')
            items_lines.append(
                f"- property_id={pid}\n  value={val}\n  evidence={ev}\n  reasoning={rs}"
            )

        context_url = url or ""

        prompt = f"""You are a STRICT confidence scorer. Rate each suggestion [0.0-1.0] using this CONSERVATIVE algorithm:

CONFIDENCE CALIBRATION GUIDE:
• 0.90-1.00 = CERTAIN: Explicit statement with exact quote, zero ambiguity
• 0.70-0.89 = HIGH: Strong evidence, definitive reasoning, minimal alternatives
• 0.50-0.69 = MODERATE: Good evidence but some interpretation needed
• 0.30-0.49 = LOW: Weak evidence, significant uncertainty, multiple alternatives
• 0.00-0.29 = VERY LOW: Speculation, minimal evidence, highly uncertain

SCORING ALGORITHM:
1. START: Base = 0.40 (conservative baseline)

2. EVIDENCE QUALITY (+/-):
   - Exact verbatim quote from source: +0.30
   - Paraphrased but specific reference: +0.15
   - Vague/general reference: +0.05
   - No concrete evidence: -0.20
   - Evidence contradicts value: -0.50

3. REASONING STRENGTH (+/-):
   - Uses "clearly states", "explicitly shows": +0.20
   - Uses "indicates", "suggests": +0.10
   - Uses "might", "possibly", "seems": -0.15
   - Uses "uncertain", "unclear", "ambiguous": -0.25
   - Mentions multiple viable alternatives: -0.15
   - No alternatives discussed: -0.10
   - Detailed step-by-step logic: +0.10

4. PROPERTY MATCH (+/-):
   - Perfect match (e.g., exact option in list): +0.15
   - Close match, minor interpretation: +0.05
   - Requires assumption/inference: -0.10
   - Questionable fit: -0.20

5. METADATA TYPE PENALTIES:
   - FREE_TEXT without direct quote: -0.10
   - CHOICE not explicitly stated: -0.15
   - NUMERICAL without exact number: -0.20

BE CONSERVATIVE: High confidence (>0.80) should be RARE and only for explicit, unambiguous cases.
FINAL = Base + Evidence + Reasoning + Match + Type penalties
CLAMP to [0.0, 1.0]

PROPERTIES:
{chr(10).join(prop_lines)}

CALIBRATION EXAMPLES:

Example 1 - CONFIDENCE 0.95 (VERY HIGH):
• Evidence: "The page states: 'Dr. Schmidt is Professor of History at ETH Zurich'"
• Reasoning: "The content explicitly mentions the department name in the page header. No ambiguity."
• Score: 0.40 + 0.30(exact quote) + 0.20(definitive) + 0.15(perfect match) = 1.05 → clamped to 0.95

Example 2 - CONFIDENCE 0.65 (MODERATE):
• Evidence: "The researcher focuses on machine learning applications"
• Reasoning: "The content indicates research in ML. Could also fit Computer Science or AI departments."
• Score: 0.40 + 0.15(paraphrased) + 0.10(indicates) - 0.15(alternatives) + 0.05(close match) = 0.55

Example 3 - CONFIDENCE 0.35 (LOW):
• Evidence: "Works with data visualization tools"
• Reasoning: "The page might suggest Informatics, but could also be Computer Science or Statistics."
• Score: 0.40 + 0.05(vague) - 0.15(might) - 0.15(alternatives) - 0.10(assumption) = 0.05

Example 4 - CONFIDENCE 0.20 (VERY LOW):
• Evidence: "No clear department mentioned"
• Reasoning: "The field seems unclear from the content. Multiple departments are possible."
• Score: 0.40 - 0.20(no evidence) - 0.25(uncertain) - 0.15(hedging) = -0.20 → clamped to 0.20

ITEMS TO SCORE:
{chr(10).join(items_lines)}

Apply the algorithm STRICTLY to each item. Be CONSERVATIVE - most scores should be 0.30-0.70 range. Return JSON:
{{
  "confidences": [
    {{
      "property_id": <id>,
      "confidence": <score>,
      "rationale": "<show calculation: base + evidence + reasoning + match + penalties>",
      "tags": {{"evidence": "direct|indirect|none", "reasoning": "definitive|moderate|hedged|uncertain"}}
    }}
  ]
}}"""
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
