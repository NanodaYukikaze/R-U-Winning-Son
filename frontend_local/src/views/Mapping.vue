<template>
  <div class="mapping-wrapper">
    
    <!-- 底部动态玻璃容器 -->
    <main class="feed-section glass-container">
      <h2 class="feed-main-title">Galgame 路径管理</h2>
      
      <div v-if="loading" class="status-msg">正在加载映射数据...</div>
      <div v-else-if="Object.keys(mappings).length === 0" class="status-msg">暂无路径映射记录</div>
      
      <!-- 映射列表区 -->
      <div v-else class="mapping-list">
        <div v-for="(info, exePath) in mappings" :key="exePath" class="mapping-item">
          
          <!-- 左侧：游戏标题和路径 -->
          <div class="game-info">
            <h3 class="game-title">{{ info.title || '未知名称' }}</h3>
            <p class="exe-path" :title="exePath">{{ exePath }}</p>
          </div>

          <!-- 右侧：VNID 交互编辑区 -->
          <div class="vnid-section">
            <span class="vnid-label">VNID:</span>
            
            <!-- 状态 A：默认文本显示状态 (点击触发 startEdit) -->
            <div 
              v-if="editingPath !== exePath" 
              class="vnid-display" 
              title="点击修改 VNID"
              @click="startEdit(exePath, info.vndb_id)"
            >
              {{ info.vndb_id || '未绑定' }}
            </div>

            <!-- 状态 B：编辑输入框状态 (失焦或回车触发 saveEdit) -->
            <input 
              v-else
              type="text" 
              v-model="editValue" 
              class="vnid-input"
              :ref="el => { if(el) inputRefs[exePath] = el }"
              @blur="saveEdit(exePath)"
              @keyup.enter="saveEdit(exePath)"
              placeholder="输入 ID"
            />
          </div>

        </div>
      </div>
    </main>

  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'

const loading = ref(true)
const mappings = ref({})

// 控制交互编辑状态的变量
const editingPath = ref(null) // 当前正在编辑的进程路径
const editValue = ref('')     // 输入框中暂存的 VNID 值
const inputRefs = ref({})     // 用于存储输入框 DOM 元素的引用，以便自动聚焦

onMounted(async () => {
  const waitForWebView = () => {
    return new Promise((resolve) => {
      if (window.pywebview && window.pywebview.api) resolve();
      else window.addEventListener('pywebviewready', resolve);
    });
  };
  
  await waitForWebView(); // 必须先等待！
  
  try {
    // 通过 Python 接口直接获取映射数据
    mappings.value = await window.pywebview.api.get_mappings()
  } catch (error) {
    console.error("加载映射文件失败", error)
  } finally {
    loading.value = false
  }
})

// === 交互：开始编辑 ===
const startEdit = async (path, currentVnid) => {
  editingPath.value = path
  editValue.value = currentVnid || ''
  
  // 等待 Vue DOM 更新渲染出 <input> 后，自动让输入框获取焦点
  await nextTick()
  if (inputRefs.value[path]) {
    inputRefs.value[path].focus()
  }
}

// === 交互：保存编辑 ===
const saveEdit = async (path) => {
  if (editingPath.value !== path) return 
  
  const newVnid = editValue.value.trim() || null

  try {
    // 1. 调用 Python API 写入 JSON
    await window.pywebview.api.update_mapping(path, newVnid)
    
    // 2. 写入成功后，更新前端显示状态
    if (mappings.value[path]) {
      mappings.value[path].vndb_id = newVnid
    }
  } catch (error) {
    alert("更新映射失败，请检查 Python 后端状态。")
    console.error(error)
  } finally {
    // 3. 退出编辑状态
    editingPath.value = null
  }
}
</script>

<style scoped>
/* 继承你提供的外部容器样式 */
.mapping-wrapper { 
  max-width: 750px; 
  display: flex; 
  flex-direction: column; 
  gap: 35px; 
  height: 100%; /* 让列表有空间滚动 */
}

.glass-container {
  background: rgba(255, 255, 255, 0.45); 
  backdrop-filter: blur(25px); 
  -webkit-backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.5); 
  border-radius: 28px; 
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  padding: 35px;
  display: flex;
  flex-direction: column;
}

.feed-main-title { margin: 0 0 25px 0; font-size: 20px; color: #111; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 12px; }
.status-msg { text-align: center; padding: 50px; color: #444; font-size: 14px; }

/* ================= 新增列表与交互样式 ================= */

.mapping-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px; /* 给滚动条留点空间 */
  display: flex;
  flex-direction: column;
  gap: 15px;
}

/* 滚动条美化 */
.mapping-list::-webkit-scrollbar { width: 6px; }
.mapping-list::-webkit-scrollbar-thumb { background-color: rgba(0,0,0,0.2); border-radius: 3px; }

/* 每一行的卡片样式 */
.mapping-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  padding: 16px 20px;
  transition: background 0.2s ease;
}

.mapping-item:hover {
  background: rgba(255, 255, 255, 0.5);
}

.game-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 70%;
}

.game-title {
  margin: 0;
  font-size: 16px;
  color: #2c3e50;
}

.exe-path {
  margin: 0;
  font-size: 12px;
  color: #7f8c8d;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* --- 右侧 VNID 编辑区样式 --- */
.vnid-section {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 120px;
  justify-content: flex-end;
}

.vnid-label {
  font-size: 13px;
  color: #555;
  font-weight: bold;
}

/* 文本展示态：增加悬浮反馈，暗示可点击 */
.vnid-display {
  font-size: 14px;
  color: #0366d6;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  background: transparent;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.vnid-display:hover {
  background: rgba(3, 102, 214, 0.1);
  border-color: rgba(3, 102, 214, 0.3);
}

/* 输入框编辑态 */
.vnid-input {
  width: 80px;
  font-size: 14px;
  padding: 4px 8px;
  color: #333;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #1890ff;
  border-radius: 6px;
  outline: none;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  transition: all 0.2s ease;
  text-align: center;
}
</style>