<template>
  <div id="bg-layer" :style="bgStyle"></div>

  <div class="dashboard-wrapper">
    
    <header class="profile-section">
      <img :src="userConfig.avatar" alt="Avatar" class="avatar" @error="handleAvatarError">
      <div class="profile-info">
        <h1 class="username auto-invert-text">{{userConfig.username}}</h1>
        <p class="signature auto-invert-text">{{userConfig.signature}}</p>
        <p class="total-time auto-invert-text">总计游玩: <span class="highlight">{{ formatTime(totalMinutes) }}</span></p>
      </div>
    </header>

    <main class="feed-section glass-container">
      <h2 class="feed-main-title">旮旯给木动态</h2>
      
      <div v-if="loading" class="status-msg">正在同步 VNDB 数据...</div>
      <div v-else-if="groupedTimeline.length === 0" class="status-msg">暂无游玩记录</div>
      
      <div v-else class="feed-list">
        <div v-for="day in groupedTimeline" :key="day.date" class="date-group">
          <h3 class="date-header">{{ day.date }}</h3>
          
          <div class="game-cards">
            <div v-for="(game, index) in day.games" :key="index" class="game-item">
              <img 
                :src="game.info.cover" 
                class="cover-img" 
                :style="game.info.isNsfw ? 'filter: blur(18px);' : ''" 
              >
              <div class="game-details">
                <h4 class="game-title"><a :href="`https://vndb.org/${game.id}`" target="_blank" class="vndb-link" title="在 VNDB 中查看">
                    {{ game.info.title }}
                  </a>
                </h4>
                <div class="playtime">游玩时长: {{ formatTime(game.minutes) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const loading = ref(true)
const totalMinutes = ref(0)
const groupedTimeline = ref([])
const gameCache = {}

// --- 用户配置状态 ---
const userConfig = ref({
  username: "@Loading",
  signature: "正在加载用户信息...",
  avatar: "",
  background: ""
})

// 计算背景样式
const bgStyle = computed(() => {
  if (userConfig.value.background) {
    return { backgroundImage: `url(${userConfig.value.background})` }
  }
  return { backgroundColor: '#f6f8fa' } // 默认背景色
})

// 头像加载失败的兜底
const handleAvatarError = (e) => {
  e.target.src = 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
}

const formatTime = (m) => m < 60 ? `${m} 分钟` : `${(m / 60).toFixed(1)} 小时`

// 核心功能：请求 VNDB API
const fetchGameInfo = async (id) => {
  if (gameCache[id]) return gameCache[id]
  try {
    const res = await fetch('https://api.vndb.org/kana/vn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        filters: ["id", "=", id], 
        fields: "id, title, image.url, image.sexual, image.violence" 
      })
    })
    const data = await res.json()
    const item = data.results[0]
    const info = {
      title: item.title,
      cover: item.image?.url || 'https://via.placeholder.com/120x160?text=No+Cover',
      isNsfw: (item.image?.sexual >= 2 || item.image?.violence >= 2)
    }
    gameCache[id] = info
    return info
  } catch (err) {
    return { title: "未知游戏", cover: "https://via.placeholder.com/120x160", isNsfw: false }
  }
}

onMounted(async () => {
  const baseUrl = import.meta.env.BASE_URL

  try {
    // 读取文字配置
    const configRes = await fetch(`${baseUrl}user_config/config.json`)
    if (configRes.ok) {
      const configData = await configRes.json()
      userConfig.value.username = configData.username
      userConfig.value.signature = configData.signature
    }

    // 设置图片路径 (加上时间戳防止浏览器缓存不更新)
    const timestamp = new Date().getTime()
    userConfig.value.avatar = `${baseUrl}user_config/avatar.jpg?t=${timestamp}`
    userConfig.value.background = `${baseUrl}user_config/background.jpg?t=${timestamp}`
  } catch (e) {
    console.error("无法加载用户配置，将使用默认值")
    userConfig.value.username = "@MyProfile"
    userConfig.value.signature = "在这里设置你的个性签名"
  }

  try {
    // 读取 public/data.json
    const response = await fetch(`${baseUrl}data.json`)
    const data = await response.json()
    
    let total = 0
    const dates = Object.keys(data).sort((a, b) => new Date(b) - new Date(a))
    const groups = []

    for (const date of dates) {
      const games = []
      for (const [id, min] of Object.entries(data[date])) {
        total += min
        games.push({ id, minutes: min, info: await fetchGameInfo(id) })
      }
      groups.push({ date, games })
    }
    totalMinutes.value = total
    groupedTimeline.value = groups
  } catch (error) {
    console.error("加载数据失败", error)
  } finally {
    loading.value = false
  }
})
</script>

<style>
/* 全局基础设置 */
body, html { 
  margin: 0; padding: 0; 
  background-color:transparent !important; 
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

#app {
  background: transparent !important;
}

#bg-layer { 
  position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
  background-size: cover; background-position: center; z-index: -1; 
}

.dashboard-wrapper { 
  position: relative;
  max-width: 750px; 
  margin: 50px auto; 
  padding: 0 20px; 
  display: flex; 
  flex-direction: column; 
  gap: 35px; 
}

/* ================= 核心：毛玻璃玻璃容器样式 ================= */
.glass-container {
  background: rgba(255, 255, 255, 0.45); /* 半透明底色 */
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(25px); /* 高斯模糊 */
  border: 1px solid rgba(255, 255, 255, 0.5); /* 边缘高光线 */
  border-radius: 28px; /* 大圆角 */
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  padding: 35px;
}

/* --- 1. 顶部个人资料 --- */
.profile-section { 
  display: flex; 
  align-items: center; 
  padding-left: 10px; /* 为了对齐下面的容器 */
}

.avatar { 
  width: 100px; 
  height: 100px; 
  border-radius: 50%; 
  margin-right: 25px; 
  border: 4px solid rgba(255,255,255,0.9);
  box-shadow: 0 5px 20px rgba(0,0,0,0.15);
}

.profile-info { display: flex; flex-direction: column; }
.username { margin: 0 0 4px; font-size: 28px; color: #24292f; }
.signature { margin: 0 0 12px; font-size: 14px; color: rgba(36, 41, 47, 0.9); }
.total-time { margin: 0; font-size: 15px; color: #24292f; font-weight: 500; }
.highlight { color: #5ef18b; font-weight: bold; } /* 稍微显眼的绿色数字 */

/* --- 2. 底部动态容器内容 --- */
.feed-main-title {
  margin: 0 0 25px 0;
  font-size: 20px;
  color: #111;
  border-bottom: 1px solid rgba(0,0,0,0.1);
  padding-bottom: 12px;
}

.status-msg { text-align: center; padding: 50px; color: #444; font-size: 14px; }

.date-group { margin-bottom: 35px; }
.date-header { 
  font-size: 14px; color: #555; 
  margin: 0 0 18px 0; text-transform: uppercase; letter-spacing: 1px;
}

.game-cards { display: flex; flex-direction: column; gap: 10px; }

/* 每一项的排版 (左图右文) */
.game-item { 
  display: flex; 
  padding: 18px 0; 
  gap: 22px; 
  border-bottom: 1px solid rgba(0,0,0,0.05); 
}
.game-item:last-child { border-bottom: none; }

.cover-img { 
  width: 120px; height: 168px; 
  border-radius: 10px; object-fit: cover; 
  box-shadow: 0 3px 10px rgba(0,0,0,0.1);
  background-color: #f6f8fa; /* 图片加载前的占位底色 */
}

.game-details { display: flex; flex-direction: column; justify-content: center; }
.game-title { margin: 0 0 10px; font-size: 18px; color: #111; line-height: 1.3; }

/* 【新增样式】VNDB 超链接的优雅交互 */
.vndb-link {
  color: #24292f;
  text-decoration: none; /* 去除默认下划线 */
  transition: color 0.2s ease; /* 颜色渐变过渡效果 */
}
.vndb-link:hover {
  color: #084993; /* 悬浮时变成 蓝色 */
}

.playtime { font-size: 14px; color: #666; font-weight: 500; }

.auto-invert-text {
  /* 必须先设置为纯白色，差值模式下的白色才能完美反转出黑白效果 */
  color: #ffffff; 
  
  /* 核心魔法：差值混合模式 */
  mix-blend-mode: difference;
  
  /* 提升渲染层级，确保它能正确与其下方的背景图进行混合计算 */
  position: relative;
  z-index: 10;
}
</style>