<script setup lang="ts">
import { ref, reactive } from 'vue';
import { 
  IconUpload, 
  IconFilePdf, 
  IconFile, 
  IconDelete,
  IconCheckCircle,
  IconSync
} from '@arco-design/web-vue/es/icon';
import type { FileItem } from '@arco-design/web-vue';

interface Document {
  id: string;
  name: string;
  size: string;
  status: 'indexing' | 'indexed' | 'failed';
  uploadedAt: string;
}

const loading = ref(false);
const documents = ref<Document[]>([
  {
    id: '1',
    name: '2024广告审核规范.pdf',
    size: '2.5 MB',
    status: 'indexed',
    uploadedAt: '2024-05-20 10:00:00'
  },
  {
    id: '2',
    name: 'Q1产品手册.docx',
    size: '1.2 MB',
    status: 'indexing',
    uploadedAt: '2024-05-20 11:30:00'
  }
]);

const columns = [
  {
    title: '文件名',
    dataIndex: 'name',
    slotName: 'name'
  },
  {
    title: '大小',
    dataIndex: 'size',
  },
  {
    title: '状态',
    dataIndex: 'status',
    slotName: 'status'
  },
  {
    title: '上传时间',
    dataIndex: 'uploadedAt',
  },
  {
    title: '操作',
    slotName: 'action'
  }
];

const handleUpload = (files: FileItem[]) => {
  // Mock upload logic
  files.forEach(file => {
    documents.value.unshift({
      id: Date.now().toString(),
      name: file.name,
      size: (file.file?.size ? (file.file.size / 1024 / 1024).toFixed(2) : '0') + ' MB',
      status: 'indexing',
      uploadedAt: new Date().toLocaleString()
    });
    
    // Simulate indexing completion
    setTimeout(() => {
      const doc = documents.value.find(d => d.name === file.name);
      if (doc) doc.status = 'indexed';
    }, 3000);
  });
  return true;
};

const handleDelete = (record: Document) => {
  documents.value = documents.value.filter(d => d.id !== record.id);
};
</script>

<template>
  <div class="knowledge-container">
    <div class="header">
      <div class="title-section">
        <h2>知识库管理</h2>
        <p class="subtitle">上传文档以构建 Agent 的专属知识库，支持 PDF, Word, Markdown 等格式。</p>
      </div>
      
      <a-upload
        multiple
        :auto-upload="false"
        @change="handleUpload"
        :show-file-list="false"
      >
        <template #upload-button>
          <a-button type="primary">
            <template #icon><icon-upload /></template>
            上传文档
          </a-button>
        </template>
      </a-upload>
    </div>

    <div class="table-container">
      <a-table :columns="columns" :data="documents" :pagination="false">
        <template #name="{ record }">
          <div class="file-name">
            <icon-file-pdf v-if="record.name.endsWith('.pdf')" class="file-icon pdf" />
            <icon-file v-else class="file-icon" />
            <span>{{ record.name }}</span>
          </div>
        </template>
        
        <template #status="{ record }">
          <a-tag v-if="record.status === 'indexed'" color="green">
            <template #icon><icon-check-circle /></template>
            已索引
          </a-tag>
          <a-tag v-else-if="record.status === 'indexing'" color="blue" loading>
            <template #icon><icon-sync spin /></template>
            索引中
          </a-tag>
          <a-tag v-else color="red">失败</a-tag>
        </template>
        
        <template #action="{ record }">
          <a-button type="text" status="danger" @click="handleDelete(record)">
            <template #icon><icon-delete /></template>
            删除
          </a-button>
        </template>
      </a-table>
    </div>
  </div>
</template>

<style scoped lang="less">
.knowledge-container {
  padding: 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  h2 {
    margin: 0 0 8px 0;
  }
  
  .subtitle {
    margin: 0;
    color: var(--color-text-3);
  }
}

.table-container {
  background: var(--color-bg-2);
  padding: 20px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .file-icon {
    font-size: 20px;
    &.pdf { color: rgb(var(--danger-6)); }
  }
}
</style>
