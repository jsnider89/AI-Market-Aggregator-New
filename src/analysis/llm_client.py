# src/analysis/llm_client.py
import os
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("market_aggregator.ai")

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def generate_analysis(self, prompt: str) -> Optional[str]:
        """Generate analysis from the given prompt"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider"""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        # Don't log the actual API key - just confirm it exists
        logger.info("OpenAI provider initialized")

    def generate_analysis(self, prompt: str) -> Optional[str]:
        """Generate analysis using OpenAI API"""
        try:
            logger.info("Sending request to OpenAI...")
            
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional financial market analyst. Provide comprehensive analysis with deep reasoning."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                # Updated parameters for better cost control and reliability
                "max_completion_tokens": 4000,  # More explicit than max_tokens
                "temperature": 0.7,  # Slight randomness for more natural output
                "top_p": 0.9  # Focus on most likely tokens
            }
            
            response = self.session.post(
                'https://api.openai.com/v1/chat/completions',
                json=data,
                timeout=120  # Longer timeout for complex analysis
            )
            
            logger.info(f"OpenAI response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                if not content or not content.strip():
                    logger.warning("Received empty response from OpenAI")
                    return None
                
                # Log token usage for cost monitoring (but don't log content)
                usage = result.get('usage', {})
                logger.info(f"OpenAI usage - prompt: {usage.get('prompt_tokens', 0)}, "
                          f"completion: {usage.get('completion_tokens', 0)}, "
                          f"total: {usage.get('total_tokens', 0)}")
                
                return content
            else:
                logger.error(f"OpenAI API error: {response.status_code}")
                try:
                    error_details = response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Raw error response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("OpenAI API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API network error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with OpenAI API: {e}")
            return None

    def get_provider_name(self) -> str:
        return "OpenAI GPT-4o Mini"

class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider implementation"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        })
        
        logger.info("Anthropic provider initialized")

    def generate_analysis(self, prompt: str) -> Optional[str]:
        """Generate analysis using Anthropic API"""
        try:
            logger.info("Sending request to Anthropic...")
            
            data = {
                'model': 'claude-3-5-haiku-20241022',
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 4000,
                'temperature': 0.7
            }
            
            response = self.session.post(
                'https://api.anthropic.com/v1/messages',
                json=data,
                timeout=120
            )
            
            logger.info(f"Anthropic response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                
                if not content or not content.strip():
                    logger.warning("Received empty response from Anthropic")
                    return None
                
                # Log usage for monitoring
                usage = result.get('usage', {})
                logger.info(f"Anthropic usage - input: {usage.get('input_tokens', 0)}, "
                          f"output: {usage.get('output_tokens', 0)}")
                
                return content
            else:
                logger.error(f"Anthropic API error: {response.status_code}")
                try:
                    error_details = response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Raw error response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Anthropic API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Anthropic API network error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Anthropic API: {e}")
            return None

    def get_provider_name(self) -> str:
        return "Anthropic Claude 3.5 Haiku"

class GeminiProvider(AIProvider):
    """Google Gemini API provider implementation"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # Gemini 2.0 Flash model endpoint
        self.model = "gemini-2.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        logger.info("Gemini provider initialized")

    def generate_analysis(self, prompt: str) -> Optional[str]:
        """Generate analysis using Google Gemini API"""
        try:
            logger.info("Sending request to Google Gemini...")
            
            # Gemini API request structure
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"You are a professional financial market analyst. Provide comprehensive analysis with deep reasoning.\n\n{prompt}"
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 8000,
                    "candidateCount": 1
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH", 
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            # Make the API request
            url = f"{self.base_url}/models/{self.model}:generateContent"
            params = {"key": self.api_key}
            
            response = self.session.post(
                url,
                params=params,
                json=data,
                timeout=120
            )
            
            logger.info(f"Gemini response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract content from Gemini response structure
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        content = candidate['content']['parts'][0].get('text', '')
                        
                        if not content or not content.strip():
                            logger.warning("Received empty response from Gemini")
                            return None
                        
                        # Log usage metadata if available
                        if 'usageMetadata' in result:
                            usage = result['usageMetadata']
                            logger.info(f"Gemini usage - prompt: {usage.get('promptTokenCount', 0)}, "
                                      f"response: {usage.get('candidatesTokenCount', 0)}, "
                                      f"total: {usage.get('totalTokenCount', 0)}")
                        
                        return content
                    else:
                        logger.error("Unexpected Gemini response structure - no content found")
                        return None
                else:
                    logger.error("Unexpected Gemini response structure - no candidates found")
                    return None
            else:
                logger.error(f"Gemini API error: {response.status_code}")
                try:
                    error_details = response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Raw error response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Gemini API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API network error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Gemini API: {e}")
            return None

    def get_provider_name(self) -> str:
        return "Google Gemini 2.0 Flash"

class AIClient:
    """
    Main AI client that manages multiple providers and handles fallback
    """
    
    def __init__(self):
        self.providers = []
        
        # Try to initialize providers based on available API keys
        # Prioritize Gemini 2.0 Flash if available (faster and potentially cheaper)
        if os.getenv('GEMINI_API_KEY'):
            try:
                self.providers.append(GeminiProvider())
                logger.info("Gemini provider added (prioritized)")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini provider: {e}")
        
        if os.getenv('OPENAI_API_KEY'):
            try:
                self.providers.append(OpenAIProvider())
                logger.info("OpenAI provider added")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")
        
        if os.getenv('ANTHROPIC_API_KEY'):
            try:
                self.providers.append(AnthropicProvider())
                logger.info("Anthropic provider added")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic provider: {e}")
        
        if not self.providers:
            logger.warning("No AI providers available - analysis will be basic")

    def generate_analysis(self, prompt: str) -> tuple[str, str]:
        """
        Generate analysis using available AI providers with fallback
        
        Returns:
            Tuple of (analysis_text, provider_name)
        """
        for provider in self.providers:
            try:
                logger.info(f"Attempting analysis with {provider.get_provider_name()}")
                analysis = provider.generate_analysis(prompt)
                
                if analysis:
                    logger.info(f"Successfully generated analysis using {provider.get_provider_name()}")
                    return analysis, provider.get_provider_name()
                else:
                    logger.warning(f"{provider.get_provider_name()} returned empty analysis")
                    
            except Exception as e:
                logger.error(f"Error with {provider.get_provider_name()}: {e}")
                continue
        
        # Fallback to basic analysis if all AI providers fail
        logger.warning("All AI providers failed - generating basic analysis")
        return self._create_basic_analysis(), "Basic Analysis (No AI)"

    def _create_basic_analysis(self) -> str:
        """Create a basic analysis when AI is not available"""
        from datetime import datetime
        
        return f"""**MARKET PERFORMANCE**
{datetime.now().strftime('%B %d, %Y')}

**Note:** AI analysis unavailable. Please check API configuration.

**TOP MARKET & ECONOMY STORIES**
Unable to generate AI-powered analysis. Key market and economic themes 
require AI integration for comprehensive coverage.

**GENERAL NEWS**
AI analysis required for detailed news categorization and sentiment analysis.

**Looking Ahead:** 
Monitor for economic data releases and corporate earnings reports."""

    def __del__(self):
        """Clean up sessions when object is destroyed"""
        for provider in self.providers:
            if hasattr(provider, 'session'):
                provider.session.close()
