<template>
  <div class="settings-wrapper">
    
    <!-- 核心：完全统一的毛玻璃大容器 -->
    <main class="feed-section glass-container">
      <h2 class="feed-main-title"> 系统设置</h2>

      <!-- 内部滚动区域，确保内容不会超出毛玻璃边框 -->
      <div class="settings-scroll-area">
        
        <!-- ================= 个人资料设置区块 ================= -->
        <section class="setting-group">
          <h3 class="group-title">个人资料</h3>
          
          <div class="form-item">
            <label class="form-label">用户名称</label>
            <input 
              type="text" 
              v-model="config.username" 
              class="custom-input" 
              placeholder="输入你的昵称"
            />
          </div>

          <div class="form-item">
            <label class="form-label">个性签名</label>
            <input 
              type="text" 
              v-model="config.signature" 
              class="custom-input" 
              placeholder="输入个性签名"
            />
          </div>

          <!-- 【修改】：彻底移除了 input type="file"，直接触发 Python API -->
          <div class="form-item">
            <label class="form-label">自定义头像</label>
            <div class="file-upload-wrapper">
              <button class="btn-outline" @click="handleNativeFileSelect('avatar')">浏览文件...</button>
              <span class="file-name">{{ displayNames.avatar || '未选择任何文件' }}</span>
            </div>
          </div>
        </section>

        <!-- ================= 系统外观与行为区块 ================= -->
        <section class="setting-group">
          <h3 class="group-title">系统选项</h3>
          
          <!-- 【修改】：彻底移除了 input type="file"，直接触发 Python API -->
          <div class="form-item">
            <label class="form-label">应用背景图</label>
            <div class="file-upload-wrapper">
              <button class="btn-outline" @click="handleNativeFileSelect('background')">浏览文件...</button>
              <span class="file-name">{{ displayNames.background || '未选择任何文件' }}</span>
            </div>
          </div>

          <div class="form-item checkbox-item">
            <label class="checkbox-container">
              <input type="checkbox" v-model="config.autoStart" />
              <span class="checkmark"></span>
              <span class="checkbox-text">开机自动启动 Galgame 记录器</span>
            </label>
          </div>
        </section>

      </div> <!-- 滚动区域结束 -->

      <!-- 底部保存按钮，固定在毛玻璃容器底部 -->
      <div class="footer-actions">
        <button class="btn-primary" @click="saveSettings">保存并应用</button>
      </div>

    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const config = ref({
  username: '',
  signature: '',
  autoStart: false
})

// 【新增】：仅用于前端展示刚刚选了什么文件
const displayNames = ref({
  avatar: null,
  background: null
})

onMounted(async () => {
  const waitForWebView = () => {
    return new Promise((resolve) => {
      if (window.pywebview && window.pywebview.api) resolve();
      else window.addEventListener('pywebviewready', resolve);
    });
  };
  
  await waitForWebView(); // 必须先等待！
  try {
    // 通过 Python 接口获取初始配置
    const configData = await window.pywebview.api.get_config()
    config.value.username = configData.username || ''
    config.value.signature = configData.signature || ''
    config.value.autoStart = configData.autoStart || false 
  } catch (e) {
    console.log("初始化读取配置失败")
  }
})

// === 【核心修改】：呼叫 Python 弹出原生选择器 ===
const handleNativeFileSelect = async (type) => {
  try {
    // 调用我们在 Python 中写的 select_and_save_image 接口
    const result = await window.pywebview.api.select_and_save_image(type)
    
    if (result.success) {
      // Python 已经默默地把文件复制好了，我们只需要在前端显示一下文件名即可
      displayNames.value[type] = result.filename
      alert(`图片已成功保存！\n(若是修改了背景，请重启应用以查看最新效果)`)
    } else if (result.msg !== "用户取消了选择。") {
      alert("图片保存失败: " + result.msg)
    }
  } catch (error) {
    console.error("调用原生文件选择器失败:", error)
    alert("请确保当前处于桌面应用环境。")
  }
}

// === 保存文本设置 ===
const saveSettings = async () => {
  try {
    await window.pywebview.api.save_config(
      config.value.username,
      config.value.signature,
      config.value.autoStart
    )
    alert("文本配置已成功保存！")
  } catch (error) {
    alert("保存设置失败，请检查 Python 终端报错。")
    console.error(error)
  }

}
</script>

<style scoped>
/* 限定在该组件内的样式，防止污染全局 */
.settings-wrapper { 
  max-width: 750px; 
  display: flex; 
  flex-direction: column; 
  height: 100%; /* 撑满父级可用高度 */
}

/* 核心：完全一致的毛玻璃容器样式 */
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
  overflow: hidden; /* 关键：绝对禁止内容溢出破坏边框 */
}

/* 标题样式 */
.feed-main-title { 
  margin: 0 0 20px 0; 
  font-size: 20px; 
  color: #111; 
  border-bottom: 1px solid rgba(0,0,0,0.1); 
  padding-bottom: 12px; 
  flex-shrink: 0; /* 防止标题被挤压 */
}

/* 内部滚动区域，这是防止内容溢出的关键设计 */
.settings-scroll-area {
  flex: 1; /* 占据剩余的所有可用空间 */
  overflow-y: auto; /* 内容超出时出现纵向滚动条 */
  padding-right: 15px; /* 给滚动条留出空间 */
  display: flex;
  flex-direction: column;
  gap: 25px; /* 区块之间的间距 */
}

/* 滚动条美化 */
.settings-scroll-area::-webkit-scrollbar { width: 6px; }
.settings-scroll-area::-webkit-scrollbar-thumb { background-color: rgba(0,0,0,0.2); border-radius: 3px; }

/* ================= 表单与控件样式 ================= */

.setting-group {
  background: rgba(255, 255, 255, 0.3);
  padding: 20px 25px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.6);
}

.group-title { margin: 0 0 20px 0; font-size: 16px; color: #333; font-weight: bold; }

.form-item { margin-bottom: 20px; display: flex; flex-direction: column; gap: 8px; }
.form-item:last-child { margin-bottom: 0; }

.form-label { font-size: 14px; color: #555; font-weight: 500; }

.custom-input {
  width: 100%; max-width: 400px; padding: 10px 14px; border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 10px; background: rgba(255, 255, 255, 0.7); font-size: 14px; color: #333;
  outline: none; transition: all 0.3s ease;
}
.custom-input:focus { background: rgba(255, 255, 255, 0.95); border-color: #1890ff; box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.1); }

/* 文件选择器 */
.file-upload-wrapper { display: flex; align-items: center; gap: 15px; }
.hidden-file-input { display: none; }
.file-name { font-size: 13px; color: #777; font-style: italic; }
.btn-outline {
  background: transparent; border: 1px solid #555; color: #555;
  padding: 8px 16px; border-radius: 8px; cursor: pointer; font-size: 13px; transition: all 0.2s ease;
}
.btn-outline:hover { background: #555; color: white; }

/* 自定义复选框 */
.checkbox-item { flex-direction: row; align-items: center; margin-top: 10px; }
.checkbox-container { display: flex; align-items: center; position: relative; cursor: pointer; user-select: none; }
.checkbox-container input { position: absolute; opacity: 0; cursor: pointer; height: 0; width: 0; }
.checkmark {
  height: 20px; width: 20px; background-color: rgba(255,255,255,0.7);
  border: 1px solid #ccc; border-radius: 6px; margin-right: 12px; transition: all 0.2s;
  display: flex; justify-content: center; align-items: center;
}
.checkbox-container:hover input ~ .checkmark { background-color: rgba(255,255,255,0.9); }
.checkbox-container input:checked ~ .checkmark { background-color: #1890ff; border-color: #1890ff; }
.checkmark:after {
  content: ""; display: none; width: 5px; height: 10px;
  border: solid white; border-width: 0 2px 2px 0; transform: rotate(45deg); margin-bottom: 2px;
}
.checkbox-container input:checked ~ .checkmark:after { display: block; }
.checkbox-text { font-size: 14px; color: #444; }

/* 底部操作区 */
.footer-actions {
  margin-top: 20px; 
  padding-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  display: flex; 
  justify-content: flex-end;
  flex-shrink: 0; /* 防止底部按钮区被挤压 */
}
.btn-primary {
  background: #1890ff; border: none; color: white; font-weight: bold;
  padding: 10px 24px; border-radius: 10px; cursor: pointer; font-size: 15px; transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}
.btn-primary:hover { background: #007aff; transform: translateY(-2px); box-shadow: 0 6px 16px rgba(24, 144, 255, 0.4); }
</style>