import { ref, reactive } from 'vue';

export interface Message {
  id: string;
  type: 'human' | 'ai' | 'tool';
  content: string;
  reasoning_content?: string;
  status?: 'thinking' | 'writing' | 'completed' | 'error';
  toolCalls?: any[];
  createdAt: string;
}

interface UseChatOptions {
  initialMessages?: Message[];
  sessionId?: string;
}

export function useChat(options: UseChatOptions = {}) {
  const messages = ref<Message[]>(options.initialMessages || []);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const sessionId = ref(options.sessionId || `session_${Date.now()}`);
  const deepThinking = ref(false);

  const loadHistory = async () => {
    try {
      loading.value = true;
      const res = await fetch(`/api/v1/conversations/${sessionId.value}/messages`);
      const data = await res.json();
      if (data.code === 200) {
        messages.value = data.data.map((msg: any) => ({
          id: msg.id.toString(),
          type: msg.type,
          content: msg.content,
          reasoning_content: msg.reasoning_content,
          status: 'completed',
          createdAt: msg.created_at
        }));
      }
    } catch (e) {
      console.error('Failed to load history', e);
    } finally {
      loading.value = false;
    }
  };

  const sendMessage = async (content: string, fileUrls?: string[]) => {
    if (!content.trim()) return;

    // 1. Add user message
    const userMsg: Message = {
      id: Date.now().toString(),
      type: 'human',
      content,
      createdAt: new Date().toISOString()
    };
    messages.value.push(userMsg);
    loading.value = true;
    error.value = null;

    // 2. Add placeholder AI message
    const aiMsgId = (Date.now() + 1).toString();
    const aiMsg = reactive<Message>({
      id: aiMsgId,
      type: 'ai',
      content: '',
      // 如果开启深度思考，初始状态为 thinking，否则为 writing (直接显示光标)
      status: deepThinking.value ? 'thinking' : 'writing',
      createdAt: new Date().toISOString()
    });
    messages.value.push(aiMsg);

    try {
      // 3. Call Backend API
      const response = await fetch('/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'smart-flow-agent-v1',
          messages: messages.value
            .filter(m => m.status === 'completed' || m.type === 'human') // Only send completed history
            .map(m => ({
              role: m.type === 'human' ? 'user' : 'assistant',
              content: m.content
            })),
          stream: true,
          session_id: sessionId.value,
          deep_thinking: deepThinking.value,
          urls: fileUrls || []
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      // 移除这里的强制切换，让状态流转更自然
      // aiMsg.status = 'writing';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.trim() === '') continue;
          if (line.trim() === 'data: [DONE]') {
            aiMsg.status = 'completed';
            continue;
          }
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              // Handle OpenAI chunk format
              if (data.choices && data.choices[0].delta) {
                const delta = data.choices[0].delta;
                if (delta.content) {
                  // 收到正文内容时，切换到 writing 状态
                  if (aiMsg.status === 'thinking') {
                    aiMsg.status = 'writing';
                  }
                  aiMsg.content += delta.content;
                }
                if (delta.reasoning_content) {
                  if (!aiMsg.reasoning_content) {
                    aiMsg.reasoning_content = '';
                  }
                  aiMsg.reasoning_content += delta.reasoning_content;
                }
              }
            } catch (e) {
              console.error('Error parsing SSE data', e);
            }
          }
        }
      }
    } catch (err: any) {
      console.error('Chat error:', err);
      error.value = err.message || 'Failed to send message';
      aiMsg.status = 'error';
      aiMsg.content += `\n[Error: ${error.value}]`;
    } finally {
      loading.value = false;
      if (aiMsg.status !== 'error' && aiMsg.status !== 'completed') {
        aiMsg.status = 'completed';
      }
    }
  };

  return {
    messages,
    loading,
    error,
    sessionId,
    deepThinking,
    sendMessage,
    loadHistory
  };
}
