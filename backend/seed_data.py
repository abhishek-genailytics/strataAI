#!/usr/bin/env python3
"""
Script to populate the database with initial providers and models data.
This script creates sample AI providers and their models for testing.
"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import AsyncSessionLocal
from app.models.ai_provider import AIProvider
from app.models.ai_model import AIModel
from app.models.model_pricing import ModelPricing
from sqlalchemy import select


async def create_providers_and_models():
    """Create initial providers and models in the database."""
    
    async with AsyncSessionLocal() as db:
        # Check if providers already exist
        result = await db.execute(select(AIProvider))
        existing_providers = result.scalars().all()
        
        if existing_providers:
            print("Providers already exist in database. Skipping seed data creation.")
            return
        
        print("Creating initial providers and models...")
        
        # Create OpenAI provider
        openai_provider = AIProvider(
            id=uuid4(),
            name="openai",
            display_name="OpenAI",
            base_url="https://api.openai.com/v1",
            logo_url="https://upload.wikimedia.org/wikipedia/commons/0/04/ChatGPT_logo.svg",
            website_url="https://openai.com",
            description="OpenAI is an AI research company that develops advanced language models including GPT-4, GPT-3.5, and other AI technologies.",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(openai_provider)
        
        # Create Anthropic provider
        anthropic_provider = AIProvider(
            id=uuid4(),
            name="anthropic",
            display_name="Anthropic",
            base_url="https://api.anthropic.com/v1",
            logo_url="https://www.anthropic.com/favicon.ico",
            website_url="https://www.anthropic.com",
            description="Anthropic develops state-of-the-art language models with a strong focus on safety, reliability, and powerful AI capabilities designed for diverse applications.",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(anthropic_provider)
        
        # Create Google provider
        google_provider = AIProvider(
            id=uuid4(),
            name="google",
            display_name="Google",
            base_url="https://generativelanguage.googleapis.com/v1",
            logo_url="https://www.google.com/favicon.ico",
            website_url="https://ai.google.dev",
            description="Google's AI platform offering advanced language models including Gemini and PaLM for various AI applications.",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(google_provider)
        
        await db.commit()
        await db.refresh(openai_provider)
        await db.refresh(anthropic_provider)
        await db.refresh(google_provider)
        
        print(f"Created provider: {openai_provider.display_name}")
        print(f"Created provider: {anthropic_provider.display_name}")
        print(f"Created provider: {google_provider.display_name}")
        
        # Create OpenAI models
        openai_models = [
            {
                "model_name": "gpt-4",
                "display_name": "GPT-4",
                "description": "Most capable GPT-4 model, great for complex tasks",
                "model_type": "chat",
                "max_tokens": 8192,
                "max_input_tokens": 128000,
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_vision": False,
                "supports_audio": False,
                "capabilities": {"reasoning": "advanced", "creativity": "high"},
                "pricing": [
                    {"type": "input", "price": 0.03, "unit": "1K tokens"},
                    {"type": "output", "price": 0.06, "unit": "1K tokens"}
                ]
            },
            {
                "model_name": "gpt-4-turbo",
                "display_name": "GPT-4 Turbo",
                "description": "Faster and more cost-effective GPT-4 model",
                "model_type": "chat",
                "max_tokens": 4096,
                "max_input_tokens": 128000,
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_vision": True,
                "supports_audio": False,
                "capabilities": {"reasoning": "advanced", "creativity": "high", "vision": True},
                "pricing": [
                    {"type": "input", "price": 0.01, "unit": "1K tokens"},
                    {"type": "output", "price": 0.03, "unit": "1K tokens"}
                ]
            },
            {
                "model_name": "gpt-3.5-turbo",
                "display_name": "GPT-3.5 Turbo",
                "description": "Fast and efficient model for most tasks",
                "model_type": "chat",
                "max_tokens": 4096,
                "max_input_tokens": 16385,
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_vision": False,
                "supports_audio": False,
                "capabilities": {"reasoning": "good", "creativity": "medium"},
                "pricing": [
                    {"type": "input", "price": 0.001, "unit": "1K tokens"},
                    {"type": "output", "price": 0.002, "unit": "1K tokens"}
                ]
            }
        ]
        
        # Create Anthropic models
        anthropic_models = [
            {
                "model_name": "claude-3-opus-20240229",
                "display_name": "Claude 3 Opus",
                "description": "Most powerful Claude model for complex tasks",
                "model_type": "chat",
                "max_tokens": 4096,
                "max_input_tokens": 200000,
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_vision": True,
                "supports_audio": False,
                "capabilities": {"reasoning": "excellent", "creativity": "high", "vision": True},
                "pricing": [
                    {"type": "input", "price": 0.015, "unit": "1K tokens"},
                    {"type": "output", "price": 0.075, "unit": "1K tokens"}
                ]
            },
            {
                "model_name": "claude-3-sonnet-20240229",
                "display_name": "Claude 3 Sonnet",
                "description": "Balanced performance and cost model",
                "model_type": "chat",
                "max_tokens": 4096,
                "max_input_tokens": 200000,
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_vision": True,
                "supports_audio": False,
                "capabilities": {"reasoning": "excellent", "creativity": "high", "vision": True},
                "pricing": [
                    {"type": "input", "price": 0.003, "unit": "1K tokens"},
                    {"type": "output", "price": 0.015, "unit": "1K tokens"}
                ]
            },
            {
                "model_name": "claude-3-haiku-20240307",
                "display_name": "Claude 3 Haiku",
                "description": "Fast and efficient model for simple tasks",
                "model_type": "chat",
                "max_tokens": 4096,
                "max_input_tokens": 200000,
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_vision": True,
                "supports_audio": False,
                "capabilities": {"reasoning": "good", "creativity": "medium", "vision": True},
                "pricing": [
                    {"type": "input", "price": 0.00025, "unit": "1K tokens"},
                    {"type": "output", "price": 0.00125, "unit": "1K tokens"}
                ]
            }
        ]
        
        # Create Google models
        google_models = [
            {
                "model_name": "gemini-pro",
                "display_name": "Gemini Pro",
                "description": "Google's most capable text generation model",
                "model_type": "chat",
                "max_tokens": 2048,
                "max_input_tokens": 30720,
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_vision": False,
                "supports_audio": False,
                "capabilities": {"reasoning": "excellent", "creativity": "high"},
                "pricing": [
                    {"type": "input", "price": 0.0005, "unit": "1K tokens"},
                    {"type": "output", "price": 0.0015, "unit": "1K tokens"}
                ]
            },
            {
                "model_name": "gemini-pro-vision",
                "display_name": "Gemini Pro Vision",
                "description": "Multimodal model with vision capabilities",
                "model_type": "chat",
                "max_tokens": 2048,
                "max_input_tokens": 30720,
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_vision": True,
                "supports_audio": False,
                "capabilities": {"reasoning": "excellent", "creativity": "high", "vision": True},
                "pricing": [
                    {"type": "input", "price": 0.0005, "unit": "1K tokens"},
                    {"type": "output", "price": 0.0015, "unit": "1K tokens"}
                ]
            }
        ]
        
        # Create models for each provider
        all_models = [
            (openai_provider, openai_models),
            (anthropic_provider, anthropic_models),
            (google_provider, google_models)
        ]
        
        for provider, models_data in all_models:
            for model_data in models_data:
                model = AIModel(
                    id=uuid4(),
                    provider_id=provider.id,
                    model_name=model_data["model_name"],
                    display_name=model_data["display_name"],
                    description=model_data["description"],
                    model_type=model_data["model_type"],
                    max_tokens=model_data["max_tokens"],
                    max_input_tokens=model_data["max_input_tokens"],
                    supports_streaming=model_data["supports_streaming"],
                    supports_function_calling=model_data["supports_function_calling"],
                    supports_vision=model_data["supports_vision"],
                    supports_audio=model_data["supports_audio"],
                    capabilities=model_data["capabilities"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(model)
                await db.flush()  # Flush to get the model ID
                
                # Create pricing for the model
                for pricing_data in model_data["pricing"]:
                    pricing = ModelPricing(
                        id=uuid4(),
                        model_id=model.id,
                        pricing_type=pricing_data["type"],
                        price_per_unit=pricing_data["price"],
                        unit=pricing_data["unit"],
                        currency="USD",
                        region="us-east-1",
                        effective_from=datetime.utcnow(),
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(pricing)
                
                print(f"  Created model: {model.display_name}")
        
        await db.commit()
        print("\n✅ Successfully created initial providers and models!")
        print(f"Created {len(openai_models)} OpenAI models")
        print(f"Created {len(anthropic_models)} Anthropic models")
        print(f"Created {len(google_models)} Google models")


async def main():
    """Main function to run the seed data script."""
    try:
        await create_providers_and_models()
    except Exception as e:
        print(f"❌ Error creating seed data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
