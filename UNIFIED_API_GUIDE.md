# StrataAI Unified API Gateway

The StrataAI Unified API Gateway provides a single, OpenAI-compatible endpoint that works with multiple AI providers (OpenAI, Anthropic). Users only need their Strata Personal Access Token (PAT) and can switch between providers by simply changing the model field.

## 🚀 Quick Start

### 1. Get Your Strata PAT Token
- Log into your StrataAI dashboard
- Navigate to **User Management** → **API Tokens**
- Click **"Create New Token"** to generate a PAT
- Copy the token (starts with `pat_`) - **this is shown only once**
- Token includes organization context and scopes

### 2. Configure Provider API Keys
Before using the unified API, add your provider API keys in the StrataAI dashboard:
- Navigate to **API Keys** section in your organization
- **OpenAI**: Add your OpenAI API key (starts with `sk-`)
- **Anthropic**: Add your Anthropic API key (starts with `sk-ant-`)
- Keys are encrypted with Fernet encryption and stored securely

### 3. Make Your First Request

```python
import requests

headers = {"Authorization": "Bearer YOUR_STRATA_PAT"}
data = {
    "model": "openai/gpt-4o-mini",  # or "anthropic/claude-3-5-sonnet-20241022"
    "messages": [
        {"role": "user", "content": "Hello, world!"}
    ]
}

response = requests.post(
    "https://your-strataai-domain.com/v1/chat/completions",
    headers=headers,
    json=data
)

print(response.json())
```

## 📚 API Reference

### Base URL
```
https://your-strataai-domain.com/v1
```

### Authentication
All requests require a Bearer token with your Strata PAT:
```
Authorization: Bearer YOUR_STRATA_PAT
```

### Organization Context (Optional)
Override the default organization using the `X-Organization-ID` header:
```
X-Organization-ID: your-organization-uuid
```
- Must be a valid UUID
- User must have active membership in the organization
- Falls back to PAT's default organization if not provided

### Core Endpoints

#### POST `/v1/chat/completions`
Create a chat completion using any supported provider with OpenAI-compatible interface.

**Request Body:**
```json
{
  "model": "openai/gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 150,
  "stream": false
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1704067200,
  "model": "openai/gpt-4o-mini",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 12,
    "total_tokens": 21
  }
}
```

**Streaming Request:**
```json
{
  "model": "anthropic/claude-3-5-sonnet-20241022",
  "messages": [
    {"role": "user", "content": "Tell me a story"}
  ],
  "stream": true
}
```

**Streaming Response:** Server-Sent Events (SSE) stream in OpenAI format:
```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1704067200,"model":"anthropic/claude-3-5-sonnet-20241022","choices":[{"index":0,"delta":{"role":"assistant","content":"Once"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1704067200,"model":"anthropic/claude-3-5-sonnet-20241022","choices":[{"index":0,"delta":{"content":" upon"},"finish_reason":null}]}

data: [DONE]
```

#### Read-Only Playground Endpoints (PAT Required)

#### GET `/v1/playground/sessions/{session_id}`
Get session metadata and message count.

**Response:**
```json
{
  "id": "session-uuid",
  "title": "Chat about AI",
  "created_at": "2025-09-07T07:20:00Z",
  "updated_at": "2025-09-07T07:25:00Z",
  "message_count": 4,
  "metadata": {}
}
```

#### GET `/v1/playground/sessions/{session_id}/messages`
Get paginated messages with token usage data.

**Query Parameters:**
- `after_index` (optional): Start after this message index
- `limit` (optional): Number of messages (1-200, default 50)

**Response:**
```json
{
  "messages": [
    {
      "id": "msg-uuid",
      "message_index": 0,
      "role": "user",
      "content": "Hello!",
      "created_at": "2025-09-07T07:20:00Z"
    },
    {
      "id": "msg-uuid-2",
      "message_index": 1,
      "role": "assistant",
      "content": "Hello! How can I help?",
      "created_at": "2025-09-07T07:20:05Z",
      "usage": {
        "prompt_tokens": 9,
        "completion_tokens": 12,
        "total_tokens": 21
      },
      "cost": {
        "currency": "USD",
        "total_cost": "0.000042"
      }
    }
  ],
  "next_after_index": 1
}
```

## 🔧 Supported Providers & Models

### OpenAI
**Prefix:** `openai/`

**Available Models:**
- `openai/gpt-4o` - Latest GPT-4 Omni model
- `openai/gpt-4o-mini` - Faster, cost-effective GPT-4 Omni
- `openai/gpt-4-turbo` - GPT-4 Turbo with 128k context
- `openai/gpt-4` - Original GPT-4 model
- `openai/gpt-3.5-turbo` - Fast and efficient model

### Anthropic
**Prefix:** `anthropic/`

**Available Models:**
- `anthropic/claude-3-5-sonnet-20241022` - Latest Claude 3.5 Sonnet
- `anthropic/claude-3-5-haiku-20241022` - Latest Claude 3.5 Haiku
- `anthropic/claude-3-opus-20240229` - Most capable Claude 3 model
- `anthropic/claude-3-sonnet-20240229` - Balanced Claude 3 model
- `anthropic/claude-3-haiku-20240307` - Fast Claude 3 model

### Model Selection
Simply change the `model` field to switch providers:
```python
# Use OpenAI GPT-4o Mini
{"model": "openai/gpt-4o-mini", "messages": [...]}

# Use Anthropic Claude 3.5 Sonnet
{"model": "anthropic/claude-3-5-sonnet-20241022", "messages": [...]}
```

### Model Capabilities
- **Context Windows**: Varies by model (4k to 200k tokens)
- **Streaming**: Supported for all models
- **Function Calling**: Available for OpenAI models (not in MVP)
- **Vision**: Available for GPT-4o models (not in MVP)

## 💡 Usage Examples

### Python with requests
```python
import requests

def chat_with_strata(message, model="openai/gpt-4o-mini"):
    headers = {"Authorization": f"Bearer {STRATA_PAT}"}
    data = {
        "model": model,
        "messages": [{"role": "user", "content": message}]
    }
    
    response = requests.post(
        "https://your-strataai-domain.com/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    return response.json()["choices"][0]["message"]["content"]

# Use OpenAI GPT-4o Mini
print(chat_with_strata("Hello!", "openai/gpt-4o-mini"))

# Use Anthropic Claude 3.5 Sonnet
print(chat_with_strata("Hello!", "anthropic/claude-3-5-sonnet-20241022"))
```

### Python with OpenAI SDK
```python
from openai import OpenAI

# Initialize with StrataAI endpoint
client = OpenAI(
    api_key="YOUR_STRATA_PAT",
    base_url="https://your-strataai-domain.com/v1"
)

# Use any provider by changing the model
response = client.chat.completions.create(
    model="anthropic/claude-3-5-sonnet-20241022",  # Anthropic via StrataAI
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### JavaScript/Node.js
```javascript
const STRATA_PAT = "your_strata_pat_here";

async function chatWithStrata(message, model = "openai/gpt-4o-mini") {
    const response = await fetch("https://your-strataai-domain.com/v1/chat/completions", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${STRATA_PAT}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            model: model,
            messages: [{ role: "user", content: message }]
        })
    });
    
    const data = await response.json();
    return data.choices[0].message.content;
}

// Use different providers
chatWithStrata("Hello!", "openai/gpt-4o-mini").then(console.log);
chatWithStrata("Hello!", "anthropic/claude-3-5-sonnet-20241022").then(console.log);
```

### cURL
```bash
curl -X POST "https://your-strataai-domain.com/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_STRATA_PAT" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## 🔒 Security & Best Practices

### API Key Management
- **Never expose your Strata PAT** in client-side code
- Store PATs securely as environment variables
- Rotate PATs regularly through the StrataAI dashboard
- Use different PATs for different environments (dev/staging/prod)

### Rate Limiting
- Requests are subject to your provider's rate limits
- StrataAI adds minimal overhead to requests
- Monitor usage through the StrataAI dashboard

### Error Handling
StrataAI returns OpenAI-compatible error responses for consistent client handling:

```python
import requests

def safe_chat_request(message, model):
    try:
        response = requests.post(
            "https://your-strataai-domain.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {STRATA_PAT}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": message}]
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            # All errors follow OpenAI format
            error = response.json()
            print(f"Error {response.status_code}: {error['error']['message']}")
            print(f"Error code: {error['error']['code']}")
            return None
            
    except requests.RequestException as e:
        print(f"Network error: {e}")
        return None
```

**Common Error Codes:**
- `401` - `authentication_error`: Invalid or missing PAT token
- `400` - `invalid_request_error`: Malformed request or invalid model format
- `403` - `permission_denied_error`: No access to organization or missing API key
- `429` - `rate_limit_exceeded_error`: Provider rate limits exceeded
- `500` - `api_error`: Internal server error
- `502` - `service_unavailable_error`: Provider API unavailable

## 🚨 Migration from Direct Provider APIs

### From OpenAI SDK
**Before:**
```python
from openai import OpenAI
client = OpenAI(api_key="sk-...")

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

**After:**
```python
from openai import OpenAI
client = OpenAI(
    api_key="YOUR_STRATA_PAT",  # Your Strata PAT
    base_url="https://your-strataai-domain.com/v1"  # StrataAI endpoint
)

response = client.chat.completions.create(
    model="openai/gpt-4o-mini",  # Add provider prefix
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### From Anthropic SDK
**Before:**
```python
import anthropic
client = anthropic.Anthropic(api_key="sk-ant-...")

message = client.messages.create(
    model="claude-3-haiku-20240307",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

**After:**
```python
from openai import OpenAI  # Use OpenAI SDK for all providers
client = OpenAI(
    api_key="YOUR_STRATA_PAT",
    base_url="https://your-strataai-domain.com/v1"
)

response = client.chat.completions.create(
    model="anthropic/claude-3-5-sonnet-20241022",  # Anthropic via StrataAI
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## 🔍 Monitoring & Analytics

All requests through the unified API are automatically tracked in your StrataAI dashboard:

### Real-time Metrics
- **Token Usage**: Prompt, completion, and total tokens per request
- **Cost Tracking**: Real-time cost calculation across all providers
- **Request Volume**: API calls per provider, model, and organization
- **Response Times**: Latency metrics and performance monitoring

### Analytics Dashboard
- **Usage Trends**: Historical usage patterns and growth metrics
- **Cost Analysis**: Spending breakdown by provider, model, and time period
- **Error Rates**: Success/failure rates and error categorization
- **Model Performance**: Response quality and user satisfaction metrics

### Playground Integration
- **Session Analytics**: Chat session metrics and user engagement
- **Message Tracking**: Individual message costs and token usage
- **Provider Comparison**: Performance comparison across different models

### API Monitoring
Access detailed logs and metrics via read-only playground endpoints:
- `GET /v1/playground/sessions/{id}` - Session metadata and message counts
- `GET /v1/playground/sessions/{id}/messages` - Message history with usage data

## 🆘 Troubleshooting

### Common Issues

**401 Unauthorized**
- Check your Strata PAT token is correct
- Ensure the token hasn't expired
- Verify you're using the correct Authorization header format

**400 Bad Request - Invalid model format**
- Model must include provider prefix: `openai/gpt-4o-mini` not `gpt-4o-mini`
- Use forward slash format: `anthropic/claude-3-5-sonnet-20241022`
- Check model availability in your organization

**403 Forbidden - Missing API key**
- Add your provider API keys in the StrataAI dashboard under **API Keys**
- Ensure API keys are active and properly encrypted
- Verify organization membership and permissions

**403 Forbidden - Organization access denied**
- Check `X-Organization-ID` header is valid UUID
- Ensure you have active membership in the specified organization
- Verify organization exists and is active

**429 Rate Limited**
- Provider rate limits exceeded (OpenAI/Anthropic limits apply)
- Implement exponential backoff in your client
- Monitor usage in StrataAI dashboard

**502 Bad Gateway - Provider unavailable**
- Provider API is temporarily unavailable
- Check provider status pages (status.openai.com, status.anthropic.com)
- Retry with exponential backoff

### Advanced Troubleshooting

**Token Usage Tracking Issues**
- Token counts may vary slightly between providers
- Usage data available in playground endpoints
- Cost calculations based on current provider pricing

**Streaming Connection Problems**
- Ensure your client supports Server-Sent Events (SSE)
- Check firewall/proxy settings for streaming connections
- Verify `stream: true` parameter in request

**Organization Context Issues**
- PAT tokens include default organization context
- Use `X-Organization-ID` header to override organization
- Verify membership via StrataAI dashboard

### Getting Help
- **Dashboard Logs**: Check detailed error logs in StrataAI dashboard
- **Support**: Contact support through the StrataAI dashboard
- **Documentation**: Review provider docs for model-specific requirements
- **Status**: Monitor system status at status.strataai.com

---

## 🎯 Why Use StrataAI Unified API?

✅ **Single Integration** - One API for all providers  
✅ **OpenAI Compatible** - Drop-in replacement for existing code  
✅ **Secure** - Your provider keys never leave StrataAI  
✅ **Observable** - Built-in monitoring and analytics  
✅ **Cost Effective** - Track spending across all providers  
✅ **Future Proof** - Easy to add new providers without code changes
