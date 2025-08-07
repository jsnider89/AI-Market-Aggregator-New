# src/analysis/llm_client.py
import os
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("market_aggregator.ai")

# ═══════════════════════════════════════════════════════════════
# 🎛️  MODEL CONFIGURATION - CHANGE THIS LINE TO SWITCH MODELS
# ═══════════════════════════════════════════════════════════════

def get_ai_config():
    """
    Simple model configuration - just uncomment the model you want to use!
    """
    
    # 🟢 ACTIVE MODEL - Change this line to switch models
    return {
        "provider": "openai",
        "model": "gpt-5-mini",
        "reasoning_effort": "medium",  # minimal, low, medium, high (OpenAI only)
        "verbosity": "medium"          # low, medium, high (OpenAI only)
    }
    
    # 📋 ALL AVAILABLE OPTIONS (uncomment one to use):
    
    # OpenAI GPT-5 Options:
    # return {"provider": "openai", "model": "gpt-5", "reasoning_effort": "high", "verbosity": "medium"}
    # return {"provider": "openai", "model": "gpt-5-mini", "reasoning_effort": "medium", "verbosity": "medium"}
    # return {"provider": "openai", "model": "gpt-5-nano", "reasoning_effort": "low", "verbosity": "low"}
    
    # Anthropic Claude Options:
    # return {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"}
    
    # Google Gemini Options:
    # return {"provider": "gemini", "model": "gemini-2.5-flash"}
    
    # For faster responses (speed priority):
    # return {"provider": "openai", "model": "gpt-5-nano", "reasoning_effort": "minimal", "verbosity": "low"}
    
    # For highest quality (quality priority):
    # return {"provider": "openai", "model": "gpt-5", "reasoning_effort": "high", "verbosity": "high"}

# ═══════════════════════════════════════════════════════════════
# 🔧 PROVIDER CLASSES (No need to change anything below this line)
# ═══════════════════════════════════════════════════════════════

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
    """OpenAI API provider implementation with GPT-5 support"""
    
    def __init__(self, model="gpt-5-mini", reasoning_effort="medium", verbosity="medium"):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.verbosity = verbosity
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        logger.info(f"OpenAI provider initialized: {self.model} (reasoning: {self.reasoning_effort}, verbosity: {self.verbosity})")

    def generate_analysis(self, prompt: str) -> Optional[str]:
        """Generate analysis using OpenAI API"""
        try:
            logger.info(f"Sending request to OpenAI {self.model}...")
            
            data = {
                "model": self.model,
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
                "max_completion_tokens": 4000,
                "temperature": 0.7,
                "top_p": 0.9,
                "verbosity": self.verbosity,
                "reasoning_effort": self.reasoning_effort
            }
            
            response = self.session.post(
                'https://api.openai.com/v1/chat/completions',
                json=data,
                timeout=120
            )
            
            logger.info(f"OpenAI {self.model} response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                if not content or not content.strip():
                    logger.warning(f"Received empty response from OpenAI {self.model}")
                    return None
                
                usage = result.get('usage', {})
                logger.info(f"OpenAI {self.model} usage - prompt: {usage.get('prompt_tokens', 0)}, "
                          f"completion: {usage.get('completion_tokens', 0)}, "
                          f"total: {usage.get('total_tokens', 0)}")
                
                return content
            else:
                logger.error(f"OpenAI {self.model} API error: {response.status_code}")
                try:
                    error_details = response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Raw error response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"OpenAI {self.model} API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI {self.model} API network error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with OpenAI {self.model} API: {e}")
            return None

    def get_provider_name(self) -> str:
        return f"OpenAI {self.model.upper()} ({self.reasoning_effort} reasoning, {self.verbosity} verbosity)"

class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider implementation"""
    
    def __init__(self, model="claude-3-5-haiku-20241022"):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.model = model
        
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        })
        
        logger.info(f"Anthropic provider initialized: {self.model}")

    def generate_analysis(self, prompt: str) -> Optional[str]:
        """Generate analysis using Anthropic API"""
        try:
            logger.info(f"Sending request to Anthropic {self.model}...")
            
            data = {
                'model': self.model,
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
            
            logger.info(f"Anthropic {self.model} response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                
                if not content or not content.strip():
                    logger.warning(f"Received empty response from Anthropic {self.model}")
                    return None
                
                usage = result.get('usage', {})
                logger.info(f"Anthropic {self.model} usage - input: {usage.get('input_tokens', 0)}, "
                          f"output: {usage.get('output_tokens', 0)}")
                
                return content
            else:
                logger.error(f"Anthropic {self.model} API error: {response.status_code}")
                try:
                    error_details = response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Raw error response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Anthropic {self.model} API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Anthropic {self.model} API network error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Anthropic {self.model} API: {e}")
            return None

    def get_provider_name(self) -> str:
        return f"Anthropic {self.model}"

class GeminiProvider(AIProvider):
    """Google Gemini API provider implementation"""
    
    def __init__(self, model="gemini-2.5-flash"):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        self.model = model
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        logger.info(f"Gemini provider initialized: {self.model}")

    def generate_analysis(self, prompt: str) -> Optional[str]:
        """Generate analysis using Google Gemini API"""
        try:
            logger.info(f"Sending request to Google {self.model}...")
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"You are a professional financial market analyst. Provide comprehensive analysis with deep reasoning. Make sure to take into account the current time of day for your analysis.\n\n{prompt}"
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 12000,
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
            
            url = f"{self.base_url}/models/{self.model}:generateContent"
            params = {"key": self.api_key}
            
            response = self.session.post(
                url,
                params=params,
                json=data,
                timeout=120
            )
            
            logger.info(f"Gemini {self.model} response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        content = candidate['content']['parts'][0].get('text', '')
                        
                        if not content or not content.strip():
                            logger.warning(f"Received empty response from Gemini {self.model}")
                            return None
                        
                        if 'usageMetadata' in result:
                            usage = result['usageMetadata']
                            logger.info(f"Gemini {self.model} usage - prompt: {usage.get('promptTokenCount', 0)}, "
                                      f"response: {usage.get('candidatesTokenCount', 0)}, "
                                      f"total: {usage.get('totalTokenCount', 0)}")
                        
                        return content
                    else:
                        logger.error(f"Unexpected Gemini {self.model} response structure - no content found")
                        return None
                else:
                    logger.error(f"Unexpected Gemini {self.model} response structure - no candidates found")
                    return None
            else:
                logger.error(f"Gemini {self.model} API error: {response.status_code}")
                try:
                    error_details = response.json()
                    logger.error(f"Error details: {error_details}")
                except:
                    logger.error(f"Raw error response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Gemini {self.model} API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini {self.model} API network error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Gemini {self.model} API: {e}")
            return None

    def get_provider_name(self) -> str:
        return f"Google {self.model}"

class AIClient:
    """
    Main AI client that uses the configured provider
    """
    
    def __init__(self):
        self.provider = None
        config = get_ai_config()
        
        try:
            if config["provider"] == "openai":
                if not os.getenv('OPENAI_API_KEY'):
                    raise ValueError("OPENAI_API_KEY not found in environment")
                
                self.provider = OpenAIProvider(
                    model=config["model"],
                    reasoning_effort=config.get("reasoning_effort", "medium"),
                    verbosity=config.get("verbosity", "medium")
                )
                
            elif config["provider"] == "anthropic":
                if not os.getenv('ANTHROPIC_API_KEY'):
                    raise ValueError("ANTHROPIC_API_KEY not found in environment")
                    
                self.provider = AnthropicProvider(model=config["model"])
                
            elif config["provider"] == "gemini":
                if not os.getenv('GEMINI_API_KEY'):
                    raise ValueError("GEMINI_API_KEY not found in environment")
                    
                self.provider = GeminiProvider(model=config["model"])
                
            else:
                raise ValueError(f"Unknown provider: {config['provider']}")
                
            logger.info(f"AI Client initialized with: {self.provider.get_provider_name()}")
            
        except Exception as e:
            logger.error(f"Failed to initialize configured AI provider: {e}")
            logger.warning("No AI provider available - analysis will be basic")
            self.provider = None

    def generate_analysis(self, prompt: str) -> tuple[str, str]:
        """
        Generate analysis using the configured AI provider
        
        Returns:
            Tuple of (analysis_text, provider_name)
        """
        if self.provider:
            try:
                analysis = self.provider.generate_analysis(prompt)
                if analysis:
                    return analysis, self.provider.get_provider_name()
                else:
                    logger.warning(f"{self.provider.get_provider_name()} returned empty analysis")
            except Exception as e:
                logger.error(f"Error with {self.provider.get_provider_name()}: {e}")
        
        # Fallback to basic analysis if AI provider fails
        logger.warning("AI provider failed - generating basic analysis")
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
        if self.provider and hasattr(self.provider, 'session'):
            self.provider.session.close()
