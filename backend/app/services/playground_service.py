"""
Direct provider API service for playground - bypasses unified API complexity.
"""
import asyncio
import json
from typing import List, Dict, Optional, AsyncGenerator
from uuid import UUID
import json
import httpx
from datetime import datetime
from ..utils.supabase_client import supabase_service
from ..core.encryption import encryption_service
from ..models.organization import Organization
from ..core.deps import CurrentUser


class PlaygroundProviderService:
    """Direct API calls to providers using user's configured API keys."""
    
    @staticmethod
    async def generate_session_name(provider: str, model: str, first_message: str, api_key: str) -> str:
        """Generate a contextual session name using a simple, reliable LLM call."""
        try:
            # Use a simple, reliable model for name generation (gpt-3.5-turbo for OpenAI, claude-3-haiku for Anthropic)
            name_model = "gpt-3.5-turbo" if provider.lower() == "openai" else "claude-3-haiku-20240307"
            
            # Simple, direct prompt that should always get a response
            name_prompt = f"""Based on this user message, create a short 2-4 word title for the conversation:

User message: "{first_message[:100]}"

Respond with ONLY the title, nothing else. Examples:
- "Python Code Help"
- "Travel Planning"
- "Recipe Ideas"
- "Math Problem"

Title:"""
            
            messages = [
                {"role": "user", "content": name_prompt}
            ]
            
            if provider.lower() == "openai":
                response = await PlaygroundProviderService.openai_chat_completion(
                    api_key, name_model, messages, temperature=0.1, max_tokens=20
                )
                
                if response.get("choices") and len(response["choices"]) > 0:
                    generated_name = response["choices"][0]["message"]["content"].strip()
                    # Clean up the response
                    generated_name = generated_name.replace("Title:", "").strip().strip('"').strip("'")
                    
                    if generated_name and len(generated_name.strip()) > 0:
                        return generated_name
                
            elif provider.lower() == "anthropic":
                response = await PlaygroundProviderService.anthropic_chat_completion(
                    api_key, name_model, messages, temperature=0.1, max_tokens=20
                )
                
                if response.get("choices") and len(response["choices"]) > 0:
                    generated_name = response["choices"][0]["message"]["content"].strip()
                    # Clean up the response
                    generated_name = generated_name.replace("Title:", "").strip().strip('"').strip("'")
                    
                    if generated_name and len(generated_name.strip()) > 0:
                        return generated_name
            
            # If we get here, something went wrong - use a descriptive fallback
            print("LLM call failed or returned empty, using descriptive fallback")
            words = first_message.split()[:2]  # Take first 2 words
            if len(words) > 0:
                return " ".join(words).title() + " Discussion"
            else:
                return "New Discussion"
                
        except Exception as e:
            print(f"Error generating session name: {e}")
            import traceback
            traceback.print_exc()
            # Even in error case, try to create something meaningful
            try:
                words = first_message.split()[:2]
                if len(words) > 0:
                    return " ".join(words).title() + " Chat"
            except:
                pass
            return "New Chat"
    
    @staticmethod
    async def save_message_with_tokens(
        session_id: str,
        role: str,
        content: str,
        provider: str,
        model: str,
        token_count: int,
        token_type: str
    ) -> str:
        """Save message and its token usage to database."""
        supabase = supabase_service
        
        try:
            # Insert message
            message_result = supabase.table("chat_messages").insert({
                "session_id": session_id,
                "role": role,
                "content": content
            }).execute()
            
            if not message_result.data:
                raise Exception("Failed to save message")
            
            message_id = message_result.data[0]["id"]
            
            # Insert token usage
            supabase.table("token_usage").insert({
                "message_id": message_id,
                "provider": provider,
                "model": model,
                "token_count": token_count,
                "token_type": token_type
            }).execute()
            
            # Update session timestamp
            supabase.table("chat_sessions").update({
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", session_id).execute()
            
            return message_id
            
        except Exception as e:
            print(f"Error saving message: {e}")
            raise
    
    @staticmethod
    async def update_message_token_count(message_id: str, token_count: int):
        """Update token count for an existing message."""
        supabase = supabase_service
        
        try:
            # Update token usage record
            supabase.table("token_usage").update({
                "token_count": token_count
            }).eq("message_id", message_id).execute()
            
        except Exception as e:
            print(f"Error updating token count: {e}")
            raise
    
    @staticmethod
    async def update_session_name_if_needed(
        session_id: str, 
        provider: str, 
        model: str, 
        first_message: str, 
        api_key: str
    ):
        """Update session name if it's still 'New Chat' and this is the first message."""
        supabase = supabase_service
        
        try:
            # Check if session name is still "New Chat" and if there's only one message
            session_result = supabase.table("chat_sessions").select(
                "session_name"
            ).eq("id", session_id).execute()
            
            if session_result.data and session_result.data[0]["session_name"] == "New Chat":
                # Count messages in this session
                message_count = supabase.table("chat_messages").select(
                    "id", count="exact"
                ).eq("session_id", session_id).execute()
                
                # If this is the first conversation (2 messages: user + assistant)
                if message_count.count and message_count.count <= 2:
                    print(f"Generating session name for new conversation...")
                    session_name = await PlaygroundProviderService.generate_session_name(
                        provider, model, first_message, api_key
                    )
                    
                    print(f"Generated session name: '{session_name}'")
                    
                    # Update session name
                    supabase.table("chat_sessions").update({
                        "session_name": session_name
                    }).eq("id", session_id).execute()
                    
        except Exception as e:
            print(f"Error updating session name: {e}")
            # Don't raise - this is not critical
    
    @staticmethod
    async def create_or_get_session(
        user_id: str,
        provider: str,
        model: str,
        current_session_id: Optional[str] = None
    ) -> str:
        """Create new session or return existing one based on provider compatibility."""
        supabase = supabase_service
        
        try:
            # If we have a current session, check if provider matches
            if current_session_id:
                session_result = supabase.table("chat_sessions").select(
                    "provider"
                ).eq("id", current_session_id).eq("user_id", user_id).execute()
                
                if session_result.data:
                    current_provider = session_result.data[0]["provider"]
                    # If provider matches, use existing session
                    if current_provider == provider:
                        return current_session_id
            
            # Create new session (provider changed or no current session)
            session_result = supabase.table("chat_sessions").insert({
                "user_id": user_id,
                "provider": provider,
                "model": model,
                "session_name": "New Chat"
            }).execute()
            
            if not session_result.data:
                raise Exception("Failed to create session")
            
            return session_result.data[0]["id"]
            
        except Exception as e:
            print(f"Error managing session: {e}")
            raise
    
    @staticmethod
    async def get_decrypted_api_key(
        organization_id: UUID, 
        provider_name: str
    ) -> Optional[str]:
        """Get and decrypt user's API key for a provider."""
        try:
            # First get the provider ID
            provider_result = supabase_service.table("ai_providers").select(
                "id"
            ).eq("name", provider_name.lower()).execute()
            
            if not provider_result.data:
                return None
            
            provider_id = provider_result.data[0]['id']
            
            # Then get the API key for this organization and provider
            result = supabase_service.table("api_keys").select(
                "encrypted_key_value"
            ).eq("organization_id", str(organization_id)).eq(
                "provider_id", provider_id
            ).eq("is_active", True).execute()
            
            if not result.data:
                return None
            
            encrypted_key = result.data[0]['encrypted_key_value']
            # Decrypt the API key using the encryption service
            decrypted_key = encryption_service.decrypt_api_key(encrypted_key)
            return decrypted_key
            
        except Exception as e:
            print(f"Error retrieving API key: {e}")
            return None
    
    @staticmethod
    async def openai_chat_completion(
        api_key: str,
        model: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2500,
        stream: bool = False
    ) -> Dict:
        """Direct OpenAI API call."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Use max_completion_tokens for newer models (gpt-4o, gpt-5, etc.)
        # and max_tokens for older models
        token_param = "max_completion_tokens" if model.startswith(("gpt-4o", "gpt-5", "o1")) else "max_tokens"
        
        payload = {
            "model": model,
            "messages": messages,
            token_param: max_tokens,
            "stream": stream
        }
        
        # Only add temperature for models that support it (gpt-5 and o1 models only support default temperature)
        if not model.startswith(("gpt-5", "o1")):
            payload["temperature"] = temperature
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                print(f"OpenAI API timeout after 120 seconds for model {model}")
                raise ValueError(f"Request timeout - OpenAI API took too long to respond for model {model}")
            except httpx.HTTPStatusError as e:
                error_response = await e.response.aread() if hasattr(e.response, 'aread') else str(e.response.text)
                error_text = error_response.decode() if isinstance(error_response, bytes) else error_response
                print(f"OpenAI HTTP Error {e.response.status_code}: {error_text}")
                raise ValueError(f"OpenAI API Error: {error_text}")
    
    @staticmethod
    async def openai_chat_completion_stream(
        api_key: str,
        model: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2500
    ) -> AsyncGenerator[str, None]:
        """Direct OpenAI streaming API call."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Use max_completion_tokens for newer models (gpt-4o, gpt-5, etc.)
        # and max_tokens for older models
        token_param = "max_completion_tokens" if model.startswith(("gpt-4o", "gpt-5", "o1")) else "max_tokens"
        
        payload = {
            "model": model,
            "messages": messages,
            token_param: max_tokens,
            "stream": True
        }
        
        # Only add temperature for models that support it (gpt-5 and o1 models only support default temperature)
        if not model.startswith(("gpt-5", "o1")):
            payload["temperature"] = temperature
        
        # Debug logging (remove in production)
        print(f"OpenAI Request payload: {json.dumps(payload, indent=2)}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        print(f"OpenAI API Error {response.status_code}: {error_text.decode()}")
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data.strip() == "[DONE]":
                                yield "data: [DONE]\n\n"
                                break
                            try:
                                chunk = json.loads(data)
                                # Validate chunk structure according to OpenAI API docs
                                if (chunk.get("object") == "chat.completion.chunk" and 
                                    chunk.get("choices") and 
                                    isinstance(chunk["choices"], list)):
                                    yield f"data: {data}\n\n"
                            except json.JSONDecodeError:
                                continue
            except httpx.TimeoutException:
                print(f"OpenAI streaming API timeout after 120 seconds for model {model}")
                raise ValueError(f"Streaming request timeout - OpenAI API took too long to respond for model {model}")
            except httpx.HTTPStatusError as e:
                error_response = await e.response.aread() if hasattr(e.response, 'aread') else str(e.response.text)
                error_text = error_response.decode() if isinstance(error_response, bytes) else error_response
                print(f"OpenAI HTTP Error {e.response.status_code}: {error_text}")
                
                # Handle specific streaming verification error
                if "organization must be verified" in error_text.lower():
                    raise ValueError("Organization verification required for streaming with this model. Please verify your OpenAI organization or disable streaming.")
                raise ValueError(f"OpenAI API Error: {error_text}")
    
    @staticmethod
    async def anthropic_chat_completion(
        api_key: str,
        model: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2500,
        stream: bool = False
    ) -> Dict:
        """Direct Anthropic API call."""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert OpenAI format to Anthropic format
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        if system_message:
            payload["system"] = system_message
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
            except httpx.TimeoutException:
                print(f"Anthropic API timeout after 120 seconds for model {model}")
                raise ValueError(f"Request timeout - Anthropic API took too long to respond for model {model}")
            except httpx.HTTPStatusError as e:
                error_response = await e.response.aread() if hasattr(e.response, 'aread') else str(e.response.text)
                error_text = error_response.decode() if isinstance(error_response, bytes) else error_response
                print(f"Anthropic HTTP Error {e.response.status_code}: {error_text}")
                raise ValueError(f"Anthropic API Error: {error_text}")
            
            # Convert Anthropic response to OpenAI format
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": result["content"][0]["text"]
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": result.get("usage", {}).get("input_tokens", 0),
                    "completion_tokens": result.get("usage", {}).get("output_tokens", 0),
                    "total_tokens": result.get("usage", {}).get("input_tokens", 0) + result.get("usage", {}).get("output_tokens", 0)
                }
            }
    
    @staticmethod
    async def anthropic_chat_completion_stream(
        api_key: str,
        model: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2500
    ) -> AsyncGenerator[str, None]:
        """Direct Anthropic streaming API call."""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert OpenAI format to Anthropic format
        system_message = None
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data.strip() == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if chunk.get("delta", {}).get("text"):
                                # Convert Anthropic format to OpenAI format
                                openai_chunk = {
                                    "id": chunk.get("id", ""),
                                    "object": "chat.completion.chunk",
                                    "created": chunk.get("created", 0),
                                    "model": chunk.get("model", model),
                                    "choices": [{
                                        "index": 0,
                                        "delta": {
                                            "content": chunk.get("delta", {}).get("text", "")
                                        }
                                    }]
                                }
                                yield f"data: {json.dumps(openai_chunk)}\n\n"
                        except json.JSONDecodeError:
                            continue
    
    @classmethod
    async def chat_completion_stream(
        cls,
        organization_id: UUID,
        provider: str,
        model: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2500
    ):
        """Route to appropriate provider for streaming chat completion."""
        api_key = await cls.get_decrypted_api_key(organization_id, provider)
        if not api_key:
            raise ValueError(f"No API key found for provider: {provider}")
        
        if provider.lower() == "openai":
            async for chunk in cls.openai_chat_completion_stream(
                api_key, model, messages, temperature, max_tokens
            ):
                yield chunk
        elif provider.lower() == "anthropic":
            async for chunk in cls.anthropic_chat_completion_stream(
                api_key, model, messages, temperature, max_tokens
            ):
                yield chunk
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    @classmethod
    async def chat_completion(
        cls,
        organization_id: UUID,
        provider: str,
        model: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2500,
        stream: bool = False
    ):
        """Route to appropriate provider for chat completion."""
        if stream:
            return cls.chat_completion_stream(
                organization_id, provider, model, messages, temperature, max_tokens
            )
        
        api_key = await cls.get_decrypted_api_key(organization_id, provider)
        if not api_key:
            raise ValueError(f"No API key found for provider: {provider}")
        
        if provider.lower() == "openai":
            return await cls.openai_chat_completion(
                api_key, model, messages, temperature, max_tokens, stream
            )
        elif provider.lower() == "anthropic":
            return await cls.anthropic_chat_completion(
                api_key, model, messages, temperature, max_tokens, stream
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
