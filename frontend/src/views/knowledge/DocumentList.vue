<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { 
  IconUpload, 
  IconFilePdf, 
  IconFile, 
  IconDelete,
  IconCheckCircle,
  IconSync
} from '@arco-design/web-vue/es/icon';
import type { FileItem } from '@arco-design/web-vue';
import { getDocuments, uploadDocument, deleteDocument, type DocumentInfo } from '@/api/document';
import { Message } from '@arco-design/web-vue';

const loading = ref(false);
const documents = ref<DocumentInfo[]>([]);

const columns = [
  {
    title: '文件名',
    dataIndex: 'filename',
    slotName: 'name'
  },
  {
    title: '大小',
    dataIndex: 'size',
    slotName: 'size'
  },
  {
    title: '状态',
    dataIndex: 'status',
    slotName: 'status'
  },
  {
    title: '上传时间',
    dataIndex: 'uploaded_at',
    slotName: 'uploaded_at'
  },
  {
    title: '操作',
    slotName: 'action'
  }
];

const fetchDocs = async () => {
  try {
    loading.value = true;
    const res = await getDocuments();
    if (res.code === 200) {
      documents.value = res.data;
    }
  } catch (e) {
    console.error('Fetch docs error', e);
    Message.error('获取文档列表失败');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchDocs();
});

const handleUpload = async (fileList: FileItem[]) => {
  const fileItem = fileList[fileList.length - 1];
  if (!fileItem || !fileItem.file) return;

  try {
    const res = await uploadDocument(fileItem.file);
    if (res.code === 200) {
      Message.success('上传成功');
      fetchDocs(); // Refresh list
    } else {
      Message.error(res.message || '上传失败');
    }
  } catch (e) {
    console.error('Upload error', e);
    Message.error('上传过程中发生错误');
  }
};

const handleDelete = async (record: DocumentInfo) => {
  try {
    const res = await deleteDocument(record.id);
    if (res.code === 200) {
      Message.success('删除成功');
      fetchDocs();
    } else {
      Message.error(res.message || '删除失败');
    }
  } catch (e) {
    console.error('Delete error', e);
    Message.error('删除过程中发生错误');
  }
};

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString();
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
        accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg"
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
      <a-table :columns="columns" :data="documents" :loading="loading" :pagination="false">
        <template #name="{ record }">
          <div class="file-name">
            <icon-file-pdf v-if="record.filename.endsWith('.pdf')" class="file-icon pdf" />
            <icon-file v-else class="file-icon" />
            <span>{{ record.filename }}</span>
          </div>
        </template>
        
        <template #size="{ record }">
          {{ formatSize(record.size) }}
        </template>

        <template #status="{ record }">
          <a-tag v-if="record.status === 'indexed'" color="green">
            <template #icon><icon-check-circle /></template>
            已索引
          </a-tag>
          <a-tag v-else-if="record.status === 'indexing' || record.status === 'pending'" color="blue" loading>
            <template #icon><icon-sync spin /></template>
            {{ record.status === 'indexing' ? '索引中' : '等待中' }}
          </a-tag>
          <a-tag v-else color="red">失败</a-tag>
        </template>

        <template #uploaded_at="{ record }">
          {{ formatDate(record.uploaded_at) }}
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
