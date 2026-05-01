<template>
  <div id="bg-layer" :style="bgStyle"></div>

  <!-- 主体弹性布局，设置为水平居中 -->
  <div class="app-layout">
    
    <!-- 左侧悬浮：紧凑型毛玻璃导航 -->
    <aside class="sidebar-glass glass-panel">
      <!-- 删除了原本的标题区域，仅保留按钮导航 -->
      <nav class="nav-menu">
        <button 
          :class="['nav-btn', { active: currentTab === 'Dashboard' }]" 
          @click="currentTab = 'Dashboard'"
        >
          🎮 游玩动态
        </button>
        
        <button 
          :class="['nav-btn', { active: currentTab === 'Mapping' }]" 
          @click="currentTab = 'Mapping'"
        >
          📁 路径管理
        </button>
        
        <button 
          :class="['nav-btn', { active: currentTab === 'Settings' }]" 
          @click="currentTab = 'Settings'"
        >
          ⚙️ 系统设置
        </button>
      </nav>
    </aside>

    <!-- 屏幕正中：动态内容区 -->
    <main class="main-content">
      <component :is="tabs[currentTab]"></component>
    </main>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Dashboard from './views/Dashboard.vue'
import Mapping from './views/Mapping.vue'
import Settings from './views/Settings.vue'

// 简单的占位页面


const tabs = { Dashboard, Mapping, Settings }
const currentTab = ref('Dashboard')

const backgroundUrl = ref("")

const bgStyle = computed(() => {
  if (backgroundUrl.value) {
    return { backgroundImage: `url(${backgroundUrl.value})` }
  }
  return { background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)' }
})

onMounted(async () => {
  const waitForWebView = () => {
    return new Promise((resolve) => {
      if (window.pywebview && window.pywebview.api) resolve();
      else window.addEventListener('pywebviewready', resolve);
    });
  };

  await waitForWebView(); // 等待 API 就绪

  try {
    // 从 Python 获取背景的 Base64 数据
    const bgBase64 = await window.pywebview.api.get_image('background')
    if (bgBase64) {
      backgroundUrl.value = bgBase64
    }
  } catch (e) {
    console.error("加载背景图片失败", e)
  }
})
</script>

<style>
/* 全局基础设置 */
body, html {
  margin: 0;
  padding: 0;
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  overflow: hidden; 
}

#app {
  height: 100%;
}

/* 全局固定背景 */
#bg-layer {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-size: cover;
  background-position: center;
  z-index: -1; 
}

/* 核心布局：全屏宽，使内部主体绝对居中 */
.app-layout {
  position: relative; /* 为左侧的绝对定位提供参考系 */
  display: flex;
  justify-content: center; /* 核心魔法：让内部的 main-content 绝对水平居中 */
  width: 100vw;
  height: 100vh;
  box-sizing: border-box;
}

/* 公共毛玻璃类 */
.glass-panel {
  background: rgba(255, 255, 255, 0.55); 
  backdrop-filter: blur(20px);           
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.6); 
  border-radius: 24px;                   
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1); 
}

/* 左侧悬浮导航栏 */
.sidebar-glass {
  position: absolute; /* 脱离文档流，不挤压中间内容 */
  left: 40px;         /* 距离屏幕左边缘的距离 */
  top: 50%;           
  transform: translateY(-50%); /* 核心魔法：绝对垂直居中 */
  padding: 15px 12px; /* 紧凑的内边距，仅容纳按钮 */
  z-index: 50;        /* 确保其浮在背景之上 */
  /* 移除了宽度的设定，让按钮文本自己撑开盒子的宽度 */
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 8px; /* 按钮之间的垂直间距 */
}

.nav-btn {
  background: transparent;
  border: none;
  padding: 12px 18px;
  text-align: left;
  font-size: 15px;
  color: #444;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
  white-space: nowrap; /* 确保按钮文字不会意外换行 */
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.6);
  transform: translateX(4px); 
}

.nav-btn.active {
  background: rgba(255, 255, 255, 0.9);
  color: #0066cc;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

/* 居中的主体内容区 */
.main-content {
  width: 100%;
  max-width: 800px; /* 限制最大宽度，配合外层的 justify-content: center 完美居中 */
  height: 100vh;
  padding: 40px 15px; /* 上下预留滚动空间 */
  overflow-y: auto;   /* 允许内容在区域内滚动 */
  box-sizing: border-box;
}

/* 美化中间的滚动条 */
.main-content::-webkit-scrollbar {
  width: 8px;
}
.main-content::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}
</style>