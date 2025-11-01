#!/usr/bin/env python3
"""
Guardrail Validators
Contains validation logic using Guardrails-AI and OpenAI
"""

import os
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available. Some features may be limited.")

logger = logging.getLogger(__name__)


class GuardrailValidator:
    """Validates messages against guardrails"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.openai_temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
        
        # Initialize OpenAI client if API key is available
        self.openai_client = None
        if self.openai_api_key and OPENAI_AVAILABLE:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Guardrail settings
        self.enable_pii_detection = os.getenv('GUARDRAIL_ENABLE_PII_DETECTION', 'True').lower() == 'true'
        self.enable_toxicity_check = os.getenv('GUARDRAIL_ENABLE_TOXICITY_CHECK', 'True').lower() == 'true'
        self.enable_compliance_check = os.getenv('GUARDRAIL_ENABLE_COMPLIANCE_CHECK', 'True').lower() == 'true'
        
        # PII patterns for basic detection
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b|\b\+\d{1,3}[-.]?\d{1,4}[-.]?\d{1,4}[-.]?\d{1,9}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b',
            'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        }
    
    def validate(self, message: str, conversation_id: str) -> Dict[str, Any]:
        """
        Validate a message against all configured guardrails
        
        Args:
            message: The message to validate
            conversation_id: The conversation ID
            
        Returns:
            Dictionary with validation results
        """
        start_time = datetime.now()
        results = {
            'valid': True,
            'violations': [],
            'checks': {},
            'response_time_ms': 0,
            'validation_timestamp': start_time.isoformat()
        }
        
        logger.info(f"Validating message for conversation {conversation_id}")
        
        # Run all enabled checks
        if self.enable_pii_detection:
            pii_result = self.check_pii(message)
            results['checks']['pii'] = pii_result
            if pii_result['detected']:
                results['valid'] = False
                results['violations'].append({
                    'type': 'pii_detection',
                    'severity': 'high',
                    'details': pii_result
                })
        
        if self.enable_toxicity_check:
            toxicity_result = self.check_toxicity(message)
            results['checks']['toxicity'] = toxicity_result
            if toxicity_result['is_toxic']:
                results['valid'] = False
                results['violations'].append({
                    'type': 'toxicity',
                    'severity': 'medium' if toxicity_result['score'] < 0.7 else 'high',
                    'details': toxicity_result
                })
        
        if self.enable_compliance_check:
            compliance_result = self.check_compliance(message)
            results['checks']['compliance'] = compliance_result
            if not compliance_result['compliant']:
                results['valid'] = False
                results['violations'].extend([
                    {
                        'type': 'compliance',
                        'severity': 'medium',
                        'details': violation
                    }
                    for violation in compliance_result['violations']
                ])
        
        # Calculate response time
        end_time = datetime.now()
        results['response_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info(f"Validation complete for conversation {conversation_id}: {'PASS' if results['valid'] else 'FAIL'}")
        
        return results
    
    def check_pii(self, message: str) -> Dict[str, Any]:
        """Check for PII (Personally Identifiable Information)"""
        detected_types = []
        
        # Pattern-based detection
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                detected_types.append({
                    'type': pii_type,
                    'count': len(matches),
                    'matches': matches[:3]  # Limit to first 3 matches
                })
        
        # OpenAI-based detection if available
        if self.openai_client and len(message) > 20:  # Only use OpenAI for longer messages
            try:
                ai_result = self._check_pii_with_openai(message)
                if ai_result['detected']:
                    # Merge with pattern-based results
                    for ai_type in ai_result['types']:
                        # Avoid duplicates
                        if not any(d['type'] == ai_type['type'] for d in detected_types):
                            detected_types.append(ai_type)
            except Exception as e:
                logger.warning(f"OpenAI PII check failed: {e}")
        
        return {
            'detected': len(detected_types) > 0,
            'types': detected_types,
            'method': 'pattern+ai' if self.openai_client else 'pattern'
        }
    
    def _check_pii_with_openai(self, message: str) -> Dict[str, Any]:
        """Use OpenAI to detect PII"""
        if not self.openai_client:
            return {'detected': False, 'types': []}
        
        try:
            prompt = f"""Analyze the following text and identify any Personally Identifiable Information (PII) present.

Text: "{message}"

Respond with a JSON object containing:
- "detected": true/false
- "types": array of objects with "type" (e.g., "name", "address", "phone", "email", "ssn") and "count"

Text to analyze:"""

            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a PII detection expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.openai_temperature,
                max_tokens=200
            )
            
            # Parse response (simple approach - in production, use proper JSON parsing)
            content = response.choices[0].message.content.lower()
            
            # Simple heuristic: check if response indicates PII detection
            detected = 'true' in content or '"detected": true' in content
            
            return {
                'detected': detected,
                'types': []  # Could parse more details from response
            }
        except Exception as e:
            logger.error(f"OpenAI PII check error: {e}")
            return {'detected': False, 'types': []}
    
    def check_toxicity(self, message: str) -> Dict[str, Any]:
        """Check for toxic content"""
        # Basic keyword-based toxicity check
        toxic_keywords = [
            'hate', 'violence', 'abuse', 'threat', 'harassment',
            'discrimination', 'offensive', 'inappropriate'
        ]
        
        message_lower = message.lower()
        toxicity_score = 0.0
        found_keywords = []
        
        for keyword in toxic_keywords:
            if keyword in message_lower:
                toxicity_score += 0.2
                found_keywords.append(keyword)
        
        # Cap at 1.0
        toxicity_score = min(toxicity_score, 1.0)
        
        # OpenAI-based toxicity check if available
        if self.openai_client and len(message) > 10:
            try:
                ai_result = self._check_toxicity_with_openai(message)
                # Combine scores (average or max)
                toxicity_score = max(toxicity_score, ai_result.get('score', 0.0))
            except Exception as e:
                logger.warning(f"OpenAI toxicity check failed: {e}")
        
        return {
            'is_toxic': toxicity_score > 0.5,
            'score': round(toxicity_score, 2),
            'keywords_found': found_keywords,
            'method': 'keyword+ai' if self.openai_client else 'keyword'
        }
    
    def _check_toxicity_with_openai(self, message: str) -> Dict[str, Any]:
        """Use OpenAI to check for toxic content"""
        if not self.openai_client:
            return {'is_toxic': False, 'score': 0.0}
        
        try:
            prompt = f"""Analyze the following text for toxicity, hate speech, harassment, or inappropriate content.

Text: "{message}"

Respond with a JSON object containing:
- "is_toxic": true/false
- "score": number between 0.0 (not toxic) and 1.0 (highly toxic)

Text to analyze:"""

            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a content moderation expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.openai_temperature,
                max_tokens=100
            )
            
            content = response.choices[0].message.content.lower()
            
            # Parse score (simple heuristic)
            score = 0.0
            if 'true' in content or '"is_toxic": true' in content:
                # Try to extract score
                score_match = re.search(r'"score":\s*([0-9.]+)', content)
                if score_match:
                    score = float(score_match.group(1))
                else:
                    score = 0.7  # Default if toxic but no score found
            
            return {
                'is_toxic': score > 0.5,
                'score': score
            }
        except Exception as e:
            logger.error(f"OpenAI toxicity check error: {e}")
            return {'is_toxic': False, 'score': 0.0}
    
    def check_compliance(self, message: str) -> Dict[str, Any]:
        """Check compliance with rules"""
        violations = []
        
        # Check for medical advice without disclaimers (healthcare compliance)
        medical_keywords = ['prescribe', 'diagnosis', 'treatment', 'medication', 'dosage', 'should take']
        has_medical_content = any(keyword in message.lower() for keyword in medical_keywords)
        
        if has_medical_content:
            # Check if disclaimer is present
            disclaimer_keywords = ['not a doctor', 'consult', 'professional', 'advice', 'disclaimer']
            has_disclaimer = any(keyword in message.lower() for keyword in disclaimer_keywords)
            
            if not has_disclaimer:
                violations.append({
                    'rule': 'medical_advice_disclaimer',
                    'description': 'Medical advice provided without proper disclaimer',
                    'severity': 'medium'
                })
        
        # Check for inappropriate length (could indicate spam or abuse)
        if len(message) > 5000:
            violations.append({
                'rule': 'message_length',
                'description': 'Message exceeds maximum recommended length',
                'severity': 'low'
            })
        
        # OpenAI-based compliance check if available
        if self.openai_client and len(message) > 20:
            try:
                ai_violations = self._check_compliance_with_openai(message)
                violations.extend(ai_violations)
            except Exception as e:
                logger.warning(f"OpenAI compliance check failed: {e}")
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations,
            'method': 'rule+ai' if self.openai_client else 'rule'
        }
    
    def _check_compliance_with_openai(self, message: str) -> List[Dict[str, Any]]:
        """Use OpenAI to check compliance"""
        if not self.openai_client:
            return []
        
        try:
            prompt = f"""Analyze the following text for compliance issues, especially:
1. Medical advice without proper disclaimers
2. Privacy violations
3. Safety concerns
4. Regulatory compliance issues

Text: "{message}"

Respond with a JSON array of violations, each with:
- "rule": rule name
- "description": violation description
- "severity": "low", "medium", or "high"

If no violations, return empty array [].

Text to analyze:"""

            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a compliance expert. Respond only with valid JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.openai_temperature,
                max_tokens=300
            )
            
            # For now, return empty - in production, parse JSON response
            # This is a simplified version
            return []
        except Exception as e:
            logger.error(f"OpenAI compliance check error: {e}")
            return []

