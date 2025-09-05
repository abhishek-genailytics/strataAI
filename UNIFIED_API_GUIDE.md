# StrataAI Unified API Gateway

The StrataAI Unified API Gateway provides a single, OpenAI-compatible endpoint that works with multiple AI providers. Users only need their Strata Personal Access Token (PAT) and can switch between providers by simply changing the model field.

## 🚀 Quick Start

### 1. Get Your Strata PAT Token
- Log into your StrataAI dashboard
- Navigate to API Keys section
- Your Personal Access Token is automatically created
- Copy the token (starts with `pat_`)

### 2. Configure Provider API Keys
Before using the unified API, add your provider API keys in the StrataAI dashboard:
- **OpenAI**: Add your OpenAI API key
- **Anthropic**: Add your Anthropic API key

### 3. Make Your First Request

```python
import requests

headers = {"Authorization": "Bearer YOUR_STRATA_PAT"}
data = {
    "model": "openai/gpt-3.5-turbo",  # or "anthropic/claude-3-haiku"
    "messages": [
        {"role": "user", "content": "Hello, world!"}
    ]
}

response = requests.post(
    "https://your-strataai-domain.com/api/v1/chat/completions",
    headers=headers,
    json=data
)

print(response.json())
```

## 📚 API Reference

### Base URL
```
https://your-strataai-domain.com/api/v1
```

### Authentication
All requests require a Bearer token with your Strata PAT:
```
Authorization: Bearer YOUR_STRATA_PAT
```

### Endpoints

#### POST `/v1/chat/completions`
Create a chat completion using any supported provider.

**Request Body:**
```json
{
  "model": "openai/gpt-3.5-turbo",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 150,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "stop": null
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "openai/gpt-3.5-turbo",
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

#### POST `/v1/chat/completions/stream`
Create a streaming chat completion.

**Request Body:**
```json
{
  "model": "anthropic/claude-3-haiku-20240307",
  "messages": [
    {"role": "user", "content": "Tell me a story"}
  ],
  "stream": true
}
```

**Response:** Server-Sent Events (SSE) stream in OpenAI format.

#### GET `/v1/models`
List available models based on your configured API keys.

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "openai/gpt-3.5-turbo",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai"
    },
    {
      "id": "anthropic/claude-3-haiku-20240307",
      "object": "model", 
      "created": 1677610602,
      "owned_by": "anthropic"
    }
  ]
}
```

#### GET `/v1/providers`
List all supported providers (no authentication required).

## 🔧 Supported Providers & Models

### OpenAI
**Prefix:** `openai/`

**Models:**
- `openai/gpt-4`
- `openai/gpt-4-turbo`
- `openai/gpt-3.5-turbo`
- `openai/gpt-3.5-turbo-0125`

### Anthropic
**Prefix:** `anthropic/`

**Models:**
- `anthropic/claude-3-opus-20240229`
- `anthropic/claude-3-sonnet-20240229`
- `anthropic/claude-3-haiku-20240307`
- `anthropic/claude-3-5-sonnet-20241022`

## 💡 Usage Examples

### Python with requests
```python
import requests

def chat_with_strata(message, model="openai/gpt-3.5-turbo"):
    headers = {"Authorization": f"Bearer {STRATA_PAT}"}
    data = {
        "model": model,
        "messages": [{"role": "user", "content": message}]
    }
    
    response = requests.post(
        "https://api.strataai.com/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    return response.json()["choices"][0]["message"]["content"]

# Use OpenAI
print(chat_with_strata("Hello!", "openai/gpt-3.5-turbo"))

# Use Anthropic
print(chat_with_strata("Hello!", "anthropic/claude-3-haiku-20240307"))
```

### Python with OpenAI SDK
```python
from openai import OpenAI

# Initialize with StrataAI endpoint
client = OpenAI(
    api_key="YOUR_STRATA_PAT",
    base_url="https://api.strataai.com/v1"
)

# Use any provider by changing the model
response = client.chat.completions.create(
    model="anthropic/claude-3-haiku-20240307",  # Anthropic via StrataAI
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### JavaScript/Node.js
```javascript
const STRATA_PAT = "your_strata_pat_here";

async function chatWithStrata(message, model = "openai/gpt-3.5-turbo") {
    const response = await fetch("https://api.strataai.com/v1/chat/completions", {
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
chatWithStrata("Hello!", "openai/gpt-4").then(console.log);
chatWithStrata("Hello!", "anthropic/claude-3-sonnet-20240229").then(console.log);
```

### cURL
```bash
curl -X POST "https://api.strataai.com/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_STRATA_PAT" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-3.5-turbo",
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
```python
import requests

def safe_chat_request(message, model):
    try:
        response = requests.post(
            "https://api.strataai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {STRATA_PAT}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": message}]
            }
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            print("Invalid PAT token")
        elif response.status_code == 400:
            error = response.json()
            print(f"Bad request: {error['detail']}")
        elif response.status_code == 502:
            error = response.json()
            print(f"Provider error: {error['detail']['message']}")
        else:
            print(f"Unexpected error: {response.status_code}")
            
    except requests.RequestException as e:
        print(f"Network error: {e}")
```

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
    base_url="https://api.strataai.com/v1"  # StrataAI endpoint
)

response = client.chat.completions.create(
    model="openai/gpt-3.5-turbo",  # Add provider prefix
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
    base_url="https://api.strataai.com/v1"
)

response = client.chat.completions.create(
    model="anthropic/claude-3-haiku-20240307",  # Anthropic via StrataAI
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## 🔍 Monitoring & Analytics

All requests through the unified API are automatically tracked in your StrataAI dashboard:
- **Usage metrics** per provider and model
- **Cost tracking** across all providers
- **Performance analytics** and response times
- **Error monitoring** and debugging tools

## 🆘 Troubleshooting

### Common Issues

**401 Unauthorized**
- Check your Strata PAT token is correct
- Ensure the token hasn't expired
- Verify you're using the correct Authorization header format

**400 Bad Request - Missing provider prefix**
- Model must include provider prefix: `openai/gpt-4` not `gpt-4`
- Check supported models with `GET /v1/models`

**400 Bad Request - No API key for provider**
- Add your provider API keys in the StrataAI dashboard
- Ensure the API keys are active and valid

**502 Bad Gateway - Provider error**
- Check your provider API key is valid
- Verify you have sufficient credits with the provider
- Check provider status pages for outages

### Getting Help
- Check the StrataAI dashboard for detailed error logs
- Contact support through the StrataAI dashboard
- Review provider documentation for model-specific requirements

---

## 🎯 Why Use StrataAI Unified API?

✅ **Single Integration** - One API for all providers  
✅ **OpenAI Compatible** - Drop-in replacement for existing code  
✅ **Secure** - Your provider keys never leave StrataAI  
✅ **Observable** - Built-in monitoring and analytics  
✅ **Cost Effective** - Track spending across all providers  
✅ **Future Proof** - Easy to add new providers without code changes
