<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useConversationStore } from '@/store/conversation';
import { 
  IconMessage, 
  IconBook, 
  IconSettings, 
  IconPlus,
  IconMenuFold,
  IconMenuUnfold,
  IconHistory,
  IconDelete
} from '@arco-design/web-vue/es/icon';
import { Modal } from '@arco-design/web-vue';

const router = useRouter();
const route = useRoute();
const collapsed = ref(false);
const conversationStore = useConversationStore();

const menuItems = [
  {
    key: 'chat',
    title: '对话',
    icon: IconMessage,
    path: '/chat'
  },
  {
    key: 'knowledge',
    title: '知识库',
    icon: IconBook,
    path: '/knowledge'
  },
  {
    key: 'settings',
    title: '设置',
    icon: IconSettings,
    path: '/settings'
  }
];

const handleMenuItemClick = (key: string) => {
  const item = menuItems.find(i => i.key === key);
  if (item) {
    router.push(item.path);
  }
};

const createNewChat = async () => {
  const newConv = await conversationStore.createConversation('新的对话');
  if (newConv) {
    router.push(`/chat/${newConv.id}`);
  } else {
    // Fallback if API fails (or offline mode)
    router.push('/chat/new');
  }
};

const navigateToHistory = (id: string) => {
  router.push(`/chat/${id}`);
};

const handleDeleteConversation = async (e: Event, id: string) => {
  e.stopPropagation(); // 阻止冒泡，避免触发跳转
  
  Modal.warning({
    title: '确认删除',
    content: '确定要删除这个会话吗？删除后将无法恢复。',
    hideCancel: false,
    okText: '删除',
    cancelText: '取消',
    okButtonProps: {
      type: 'primary',
      status: 'danger'
    },
    cancelButtonProps: {
      type: 'outline'
    },
    onOk: async () => {
      const success = await conversationStore.deleteConversation(id);
      if (success && route.params.id === id) {
        // 如果删除的是当前会话，跳转到新会话页
        router.push('/chat/new');
      }
    }
  });
};

const onCollapse = (val: boolean) => {
  collapsed.value = val;
};

onMounted(() => {
  conversationStore.fetchConversations();
});
</script>

<template>
  <a-layout class="layout-demo">
    <a-layout-sider
      breakpoint="lg"
      :width="240"
      collapsible
      :collapsed="collapsed"
      @collapse="onCollapse"
    >
      <div class="sider-inner">
        <div class="logo">
          <img src="/logo.svg" alt="SmartFlow Logo" class="logo-img" />
          <div class="logo-text" v-if="!collapsed">SmartFlow Agent</div>
        </div>
        
        <div class="new-chat-btn">
          <a-button type="primary" long @click="createNewChat">
            <template #icon><icon-plus /></template>
            <span v-if="!collapsed">新建对话</span>
          </a-button>
        </div>

        <a-menu
          :selected-keys="[route.path.split('/')[1] || 'chat']"
          @menu-item-click="handleMenuItemClick"
        >
          <a-menu-item v-for="item in menuItems" :key="item.key">
            <template #icon>
              <component :is="item.icon" />
            </template>
            {{ item.title }}
          </a-menu-item>
        </a-menu>

        <div class="menu-divider"></div>
        
        <div class="history-section" v-if="!collapsed">
          <div class="history-title">历史记录</div>
          <div class="history-list">
            <div 
              v-for="session in conversationStore.conversations" 
              :key="session.id"
              class="history-item"
              :class="{ active: route.params.id === session.id }"
              @click="navigateToHistory(session.id)"
            >
              <icon-message class="history-icon" />
              <span class="history-text">{{ session.title }}</span>
              <div class="delete-btn" @click="(e) => handleDeleteConversation(e, session.id)">
                <icon-delete />
              </div>
            </div>
          </div>
        </div>
      </div>
    </a-layout-sider>
    
    <a-layout>
      <a-layout-content class="layout-content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<style scoped lang="less">
.layout-demo {
  height: 100vh;
  background: var(--color-fill-2);
  border: 1px solid var(--color-border);
}

.sider-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.layout-demo :deep(.arco-layout-sider) .logo {
  height: 64px;
  background: var(--color-bg-2);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  
  .logo-img {
    width: 32px;
    height: 32px;
    margin-right: 8px;
  }
  
  .logo-text {
    font-size: 18px;
    font-weight: bold;
    color: rgb(var(--primary-6));
    white-space: nowrap;
  }
}

.new-chat-btn {
  padding: 16px;
  border-bottom: 1px solid var(--color-border);
}

.layout-content {
  background: var(--color-bg-1);
  display: flex;
  flex-direction: column;
}

.menu-divider {
  margin: 10px 16px;
  height: 1px;
  background-color: var(--color-border);
}

.history-section {
  padding: 0 16px;
  flex: 1;
  overflow-y: auto;
}

.history-title {
  font-size: 12px;
  color: var(--color-text-3);
  margin-bottom: 8px;
  padding-left: 12px;
}

.history-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 4px;
  color: var(--color-text-2);
  transition: all 0.2s;
  margin-bottom: 4px;
  position: relative;
  
  &:hover {
    background-color: var(--color-fill-2);
    
    .delete-btn {
      opacity: 1;
    }
  }
  
  &.active {
    background-color: var(--color-fill-2);
    color: rgb(var(--primary-6));
    
    .history-icon {
      color: rgb(var(--primary-6));
    }
  }
}

.history-icon {
  margin-right: 8px;
  font-size: 16px;
  flex-shrink: 0;
}

.history-text {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 24px; /* 为删除按钮留出空间 */
}

.delete-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.2s;
  color: var(--color-text-3);
  padding: 4px;
  border-radius: 4px;
  
  &:hover {
    color: rgb(var(--danger-6));
    background-color: var(--color-fill-3);
  }
}
</style>
