// Basic smoke test for OpenAI service
// Note: This is a minimal test - in production, you would mock axios and test actual functionality

import { useOpenAIService } from '../../services/openai';

// Simple function check test
export function testOpenAIService() {
  const svc = useOpenAIService('test-token');
  
  if (typeof svc.createChatCompletion !== 'function') {
    throw new Error('createChatCompletion method not found');
  }
  
  console.log('✓ OpenAI service smoke test passed');
}

// Run test if this file is executed directly
if (typeof window !== 'undefined') {
  testOpenAIService();
}
