const API_BASE = 'http://localhost:8002';

export interface StructuredQuestion {
  field: string;
  question: string;
  input_type: 'text' | 'number' | 'url' | 'address' | 'email' | 'interval' | 'select';
  field_type: string;
  required: boolean;
  options?: string[];
}

export interface AgentResponse {
  session_id: string;
  stage: 'idle' | 'needs_input' | 'planning' | 'awaiting_approval' | 'complete' | 'error';
  status: string;
  agent_status: string;
  agent_message: string;
  selected_trigger?: string;
  selected_actions?: string[];
  planning?: any;
  validation?: any;
  structured_questions?: StructuredQuestion[];
  plan_md?: string;
  automation_spec?: any;
  files?: Record<string, string>;
}

export const agentService = {
  async getModels(): Promise<any[]> {
    console.log('[AgentService] Fetching models...');
    const response = await fetch(`${API_BASE}/models`);
    if (!response.ok) throw new Error('Failed to fetch models');
    return await response.json();
  },

  async chat(
    userMessage: string,
    sessionId?: string,
    knownFields?: Record<string, any>,
    planningModelId?: string,
    codegenModelId?: string
  ): Promise<AgentResponse> {
    console.log(`[AgentService] Chat: ${userMessage}`);
    
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_message: userMessage,
        session_id: sessionId || undefined,
        known_fields: knownFields || {},
        planning_model_id: planningModelId || undefined,
        codegen_model_id: codegenModelId || undefined,
      })
    });
    
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || 'Chat failed');
    }
    
    return await response.json();
  },

  async continueChat(
    sessionId: string,
    fields: Record<string, any>,
    planningModelId?: string
  ): Promise<AgentResponse> {
    console.log(`[AgentService] Continue session: ${sessionId}`);
    
    const response = await fetch(`${API_BASE}/continue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        fields: fields,
        planning_model_id: planningModelId || undefined,
      })
    });
    
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || 'Continue failed');
    }
    
    return await response.json();
  },

  async approvePlan(
    sessionId: string,
    approved: boolean,
    changes?: string,
    codegenModelId?: string
  ): Promise<AgentResponse> {
    console.log(`[AgentService] Approve plan: ${approved}`);
    
    const response = await fetch(`${API_BASE}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        approved: approved,
        changes: changes || undefined,
        codegen_model_id: codegenModelId || undefined,
      })
    });
    
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || 'Approve failed');
    }
    
    return await response.json();
  },

  // Legacy endpoints (kept for compatibility)
  async plan(prompt: string, planningModel: string, knownFields: Record<string, any> = {}) {
    console.log(`[AgentService] Legacy plan: ${prompt}`);
    
    const response = await fetch(`${API_BASE}/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_prompt: prompt,
        known_fields: knownFields,
        planning_model_id: planningModel
      })
    });
    
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Plan failed');
    }
    
    return await response.json();
  },

  // =========================================================
  // Runtime API — Deploy & Manage Automations
  // =========================================================

  async deploy(
    name: string,
    specJson: Record<string, any>,
    sessionId?: string,
    description?: string,
    files?: Record<string, string>
  ): Promise<any> {
    console.log(`[AgentService] Deploying automation: ${name}`);
    
    const response = await fetch(`${API_BASE}/automations/deploy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        description: description || '',
        session_id: sessionId || '',
        spec_json: specJson,
        files: files || {},
      })
    });
    
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Deploy failed' }));
      throw new Error(err.detail || 'Deploy failed');
    }
    
    return await response.json();
  },

  async listAutomations(status?: string): Promise<any> {
    const url = status
      ? `${API_BASE}/automations/?status=${status}`
      : `${API_BASE}/automations/`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to list automations');
    return await response.json();
  },

  async getAutomation(automationId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/automations/${automationId}`);
    if (!response.ok) throw new Error('Failed to get automation');
    return await response.json();
  },

  async pauseAutomation(automationId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/automations/${automationId}/pause`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to pause automation');
    return await response.json();
  },

  async resumeAutomation(automationId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/automations/${automationId}/resume`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to resume automation');
    return await response.json();
  },

  async deleteAutomation(automationId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/automations/${automationId}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete automation');
    return await response.json();
  },

  async getAutomationLogs(automationId: string, limit: number = 50): Promise<any> {
    const response = await fetch(`${API_BASE}/automations/${automationId}/logs?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to get automation logs');
    return await response.json();
  },
};
