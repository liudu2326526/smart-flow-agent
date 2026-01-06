import { ref } from 'vue';
import { defineStore } from 'pinia';

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export const useConversationStore = defineStore('conversation', () => {
  const conversations = ref<Conversation[]>([]);
  const loading = ref(false);
  const total = ref(0);

  const fetchConversations = async (page = 1, size = 20) => {
    try {
      loading.value = true;
      const res = await fetch(`/api/v1/conversations?page=${page}&size=${size}`);
      const data = await res.json();
      if (data.code === 200) {
        conversations.value = data.data.items;
        total.value = data.data.total;
      }
    } catch (e) {
      console.error('Failed to fetch conversations', e);
    } finally {
      loading.value = false;
    }
  };

  const createConversation = async (title?: string) => {
    try {
      const res = await fetch('/api/v1/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title })
      });
      const data = await res.json();
      if (data.code === 200) {
        conversations.value.unshift(data.data);
        return data.data;
      }
    } catch (e) {
      console.error('Failed to create conversation', e);
    }
    return null;
  };

  const deleteConversation = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/conversations/${id}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (data.code === 200) {
        conversations.value = conversations.value.filter(c => c.id !== id);
        return true;
      }
    } catch (e) {
      console.error('Failed to delete conversation', e);
    }
    return false;
  };

  return {
    conversations,
    loading,
    total,
    fetchConversations,
    createConversation,
    deleteConversation
  };
});
