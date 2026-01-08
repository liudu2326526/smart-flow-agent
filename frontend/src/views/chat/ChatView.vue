<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { 
  IconSend, 
  IconAttachment, 
  IconRobot, 
  IconUser,
  IconLoading,
  IconCheckCircle,
  IconCloseCircle,
  IconBulb,
  IconFile
} from '@arco-design/web-vue/es/icon';
import type { FileItem } from '@arco-design/web-vue';
import { useChat } from '@/hooks/useChat';
import { useConversationStore } from '@/store/conversation';
import { uploadDocument } from '@/api/document';
import { Message as MessageNotify } from '@arco-design/web-vue';

const route = useRoute();
const router = useRouter();
const inputVal = ref('');
const scrollRef = ref<HTMLElement | null>(null);
const conversationStore = useConversationStore();

// Uploaded files for the current session
const uploadedFiles = ref<any[]>([]);
const isUploading = ref(false);

// Initialize chat hook
const { messages, loading, sendMessage, sessionId, deepThinking, loadHistory } = useChat({
  sessionId: route.params.id as string
});

const currentTitle = computed(() => {
  if (!route.params.id) return '新对话';
  const conv = conversationStore.conversations.find(c => c.id === route.params.id);
  return conv ? conv.title : '会话 ' + route.params.id;
});

// Watch route to update session
watch(() => route.params.id, async (newId) => {
  if (newId) {
    sessionId.value = newId as string;
    await loadHistory();
    uploadedFiles.value = []; // Clear files on session change
  } else {
    sessionId.value = `session_${Date.now()}`;
    messages.value = [];
    uploadedFiles.value = [];
  }
});

onMounted(async () => {
  // Ensure conversation list is loaded
  if (conversationStore.conversations.length === 0) {
    await conversationStore.fetchConversations();
  }
  
  if (route.params.id) {
    sessionId.value = route.params.id as string;
    await loadHistory();
  }
});

const scrollToBottom = async () => {
  await nextTick();
  if (scrollRef.value) {
    scrollRef.value.scrollTop = scrollRef.value.scrollHeight;
  }
};

// Auto scroll when messages change
watch(() => messages.value.length, () => {
  scrollToBottom();
});

// Also scroll when last message content updates (streaming)
watch(() => messages.value[messages.value.length - 1]?.content, () => {
  scrollToBottom();
}, { deep: true });

const handleSend = async () => {
  if (!inputVal.value.trim() && uploadedFiles.value.length === 0 || loading.value) return;
  
  const content = inputVal.value;
  const urls = uploadedFiles.value
    .filter(f => f.url)
    .map(f => f.url as string);

  inputVal.value = ''; // Clear input immediately
  
  await sendMessage(content, urls);
  
  // Clear uploaded files after sending (they are now part of the conversation)
  uploadedFiles.value = [];
  
  // Refresh conversation list after sending message (to update title if generated)
  // Add a small delay to ensure backend has processed it
  setTimeout(() => {
    conversationStore.fetchConversations();
  }, 2000);
};

const handleUpload = async (fileList: FileItem[]) => {
  const fileItem = fileList[fileList.length - 1];
  if (!fileItem || !fileItem.file) return;

  try {
    isUploading.value = true;
    const res = await uploadDocument(fileItem.file, sessionId.value);
    if (res.code === 200) {
      uploadedFiles.value.push({
        id: res.data.id,
        name: res.data.filename,
        url: res.data.url,
        status: 'success'
      });
      MessageNotify.success('文件上传成功');
    } else {
      MessageNotify.error(res.message || '上传失败');
    }
  } catch (e) {
    console.error('Upload error', e);
    MessageNotify.error('上传过程中发生错误');
  } finally {
    isUploading.value = false;
  }
};

const removeFile = (index: number) => {
  uploadedFiles.value.splice(index, 1);
};

const getFileName = (url: string) => {
  if (!url) return 'Unknown File';
  const parts = url.split('/');
  const filename = parts[parts.length - 1] || 'Unknown File';
  // Remove the timestamp prefix if it exists (e.g., 1234567890_filename.txt)
  return filename.replace(/^\d+_/, '');
};
</script>

<template>
  <div class="chat-container">
    <!-- Header -->
    <div class="chat-header">
      <div class="title">{{ currentTitle }}</div>
    </div>

    <!-- Message List -->
    <div class="message-list" ref="scrollRef">
      <div 
        v-for="msg in messages" 
        :key="msg.id" 
        class="message-item"
        :class="{ 'message-human': msg.type === 'human', 'message-ai': msg.type === 'ai' }"
      >
        <div class="avatar">
          <a-avatar :size="32" :style="{ backgroundColor: msg.type === 'human' ? '#165DFF' : 'transparent' }">
            <icon-user v-if="msg.type === 'human'" />
            <img v-else src="/logo.svg" style="width: 100%; height: 100%" />
          </a-avatar>
        </div>
        
        <div class="content-wrapper">
          <div class="name">{{ msg.type === 'human' ? 'User' : 'SmartFlow Agent' }}</div>
          
          <!-- Thinking State -->
          <div v-if="msg.status === 'thinking' && !msg.reasoning_content" class="thinking-bubble">
            <icon-loading spin /> 正在思考中...
          </div>

          <!-- Deep Thinking Content -->
          <div v-if="msg.reasoning_content" class="reasoning-card">
            <details :open="msg.status !== 'completed'">
              <summary>
                <icon-bulb /> 深度思考过程
                <span class="thinking-status" v-if="msg.status !== 'completed'"><icon-loading spin /></span>
              </summary>
              <div class="reasoning-body markdown-body">{{ msg.reasoning_content }}</div>
            </details>
          </div>
          
          <!-- Message Content -->
          <div class="bubble" v-if="msg.content || (msg.status !== 'thinking' && !msg.reasoning_content)">
            <div class="markdown-body">{{ msg.content }}</div>
            <span v-if="msg.status === 'writing'" class="cursor">|</span>
          </div>

          <!-- File Attachments -->
          <div v-if="msg.fileUrls && msg.fileUrls.length > 0" class="message-attachments">
            <a 
              v-for="(url, index) in msg.fileUrls" 
              :key="index" 
              :href="url" 
              target="_blank" 
              class="attachment-link"
              @click.stop
            >
              <icon-file />
              <span class="file-name">{{ getFileName(url) }}</span>
            </a>
          </div>
          
          <!-- Tools/Citations (Placeholder) -->
          <div v-if="msg.toolCalls && msg.toolCalls.length" class="tool-calls">
            <div class="tool-card">
              <div class="tool-header">调用工具: Google Search</div>
              <div class="tool-body">Query: SmartFlow Agent</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="input-area">
      <div class="input-options">
        <a-space>
          <a-switch v-model="deepThinking" size="small">
            <template #checked-icon><icon-bulb /></template>
            <template #unchecked-icon><icon-bulb /></template>
          </a-switch>
          <span class="option-label" :class="{ active: deepThinking }">深度思考</span>
        </a-space>
      </div>
      <div class="input-wrapper">
        <div v-if="uploadedFiles.length > 0" class="uploaded-files-preview">
          <div v-for="(file, index) in uploadedFiles" :key="file.id" class="file-tag">
            <icon-file />
            <span class="file-name">{{ file.name }}</span>
            <icon-close-circle @click="removeFile(index)" class="remove-icon" />
          </div>
        </div>
        <a-upload 
          action="/" 
          :auto-upload="false"
          @change="handleUpload"
          :show-file-list="false"
          :disabled="isUploading"
          accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg"
        >
          <template #upload-button>
            <a-button type="text" shape="circle" :loading="isUploading">
              <icon-attachment />
            </a-button>
          </template>
        </a-upload>
        
        <a-textarea 
          v-model="inputVal"
          placeholder="输入您的问题... (Shift + Enter 换行)" 
          :auto-size="{ minRows: 1, maxRows: 5 }"
          @keydown.enter.prevent="handleSend"
          class="chat-input"
        />
        
        <a-button type="primary" shape="circle" @click="handleSend" :loading="loading">
          <icon-send />
        </a-button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

.chat-header {
  height: 60px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 20px;
  background: var(--color-bg-2);
  
  .title {
    font-size: 16px;
    font-weight: bold;
  }
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-item {
  display: flex;
  gap: 12px;
  max-width: 80%;
  
  &.message-human {
    align-self: flex-end;
    flex-direction: row-reverse;
    
    .content-wrapper {
      align-items: flex-end;
      
      .bubble {
        background: rgb(var(--primary-6));
        color: white;
        border-radius: 12px 0 12px 12px;
      }
    }
  }
  
  &.message-ai {
    align-self: flex-start;
    
    .content-wrapper {
      align-items: flex-start;
      
      .bubble {
        background: var(--color-fill-2);
        color: var(--color-text-1);
        border-radius: 0 12px 12px 12px;
      }
    }
  }
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
  
  .name {
    font-size: 12px;
    color: var(--color-text-3);
  }
  
  .bubble {
    padding: 12px 16px;
    font-size: 14px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .message-attachments {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 8px;

    .attachment-link {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      background: var(--color-fill-2);
      border-radius: 6px;
      font-size: 13px;
      color: rgb(var(--primary-6));
      text-decoration: none;
      transition: all 0.2s;
      border: 1px solid var(--color-border);

      &:hover {
        background: var(--color-fill-3);
        border-color: rgb(var(--primary-6));
      }

      .file-name {
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }
  
  .thinking-bubble {
    padding: 8px 12px;
    background: var(--color-fill-1);
    border-radius: 8px;
    font-size: 12px;
    color: var(--color-text-3);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .reasoning-card {
    background: var(--color-fill-1);
    border-radius: 8px;
    margin-bottom: 8px;
    overflow: hidden;
    max-width: 100%;
    
    details {
      &[open] summary {
        border-bottom: 1px solid var(--color-border);
      }
    }

    summary {
      padding: 8px 12px;
      cursor: pointer;
      font-size: 12px;
      color: var(--color-text-3);
      display: flex;
      align-items: center;
      gap: 6px;
      user-select: none;
      
      &:hover {
        background: var(--color-fill-2);
      }
      
      &::marker {
        color: var(--color-text-4);
      }
      
      .thinking-status {
        margin-left: auto;
      }
    }

    .reasoning-body {
      padding: 12px;
      font-size: 13px;
      color: var(--color-text-2);
      white-space: pre-wrap;
      line-height: 1.6;
      border-top: 1px solid var(--color-fill-2); /* Fallback */
    }
  }
}

.input-area {
  padding: 20px;
  background: var(--color-bg-2);
  border-top: 1px solid var(--color-border);
  
  .input-options {
    margin-bottom: 8px;
    padding-left: 4px;
    
    .option-label {
      font-size: 12px;
      color: var(--color-text-3);
      transition: all 0.3s;
      
      &.active {
        color: rgb(var(--primary-6));
        font-weight: 500;
      }
    }
  }

  .input-wrapper {
    background: var(--color-bg-2);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 8px;
    display: flex;
    align-items: flex-end;
    gap: 8px;
    transition: all 0.3s;
    position: relative;
    flex-wrap: wrap;

    &:focus-within {
      border-color: rgb(var(--primary-6));
      box-shadow: 0 0 0 2px rgba(var(--primary-6), 0.1);
    }

    .uploaded-files-preview {
      width: 100%;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 4px 8px 8px;
      border-bottom: 1px solid var(--color-border);
      margin-bottom: 4px;

      .file-tag {
        display: flex;
        align-items: center;
        gap: 6px;
        background: var(--color-fill-2);
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 12px;
        color: var(--color-text-2);

        .file-name {
          max-width: 150px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .remove-icon {
          cursor: pointer;
          color: var(--color-text-4);
          &:hover {
            color: rgb(var(--danger-6));
          }
        }
      }
    }
    
    .chat-input {
      background: transparent;
      border: none;
      padding: 0;
      flex: 1;
      
      :deep(.arco-textarea) {
        background: transparent;
      }
      
      :deep(.arco-textarea-wrapper) {
        background: transparent;
        border: none;
        padding: 4px 0;
      }
    }
  }
}

.cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background-color: currentColor;
  animation: blink 1s step-end infinite;
  vertical-align: text-bottom;
  margin-left: 2px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
