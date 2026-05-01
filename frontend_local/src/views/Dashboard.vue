<template>
  <div class="dashboard-wrapper">
    
    <!-- 顶部个人资料区域 -->
    <header class="profile-section">
      <img :src="userConfig.avatar" alt="Avatar" class="avatar" @error="handleAvatarError">
      <div class="profile-info">
        <h1 class="username auto-invert-text">{{userConfig.username}}</h1>
        <p class="signature auto-invert-text">{{userConfig.signature}}</p>
        <p class="total-time auto-invert-text">总计游玩: <span class="highlight">{{ formatTime(totalMinutes) }}</span></p>
      </div>
    </header>

    <!-- 底部动态列表 -->
    <main class="feed-section glass-panel">
      <h2 class="feed-main-title">💻 游玩动态</h2>
      
      <div v-if="loading" class="status-msg">正在读取本地数据...</div>
      <div v-else-if="groupedTimeline.length === 0" class="status-msg">暂无游玩记录</div>
      
      <div v-else class="feed-list">
        <!-- 遍历每一天 -->
        <div v-for="(day, dayIndex) in groupedTimeline" :key="day.date" class="date-group">
          <h3 class="date-header">{{ day.date }}</h3>
          
          <div class="game-cards">
            <!-- 遍历每一天里的每一个游戏记录 -->
            <div v-for="(game, gameIndex) in day.games" :key="game.id" class="game-item">
              
              <!-- 左侧：封面与信息 -->
              <div class="item-main">
                <img 
                  :src="game.info.cover" 
                  class="cover-img" 
                  :style="game.info.isNsfw ? 'filter: blur(18px);' : ''" 
                >
                <div class="game-details">
                  <h4 class="game-title">
                    <a :href="`https://vndb.org/${game.id}`" target="_blank" class="vndb-link" title="在 VNDB 中查看">
                      {{ game.info.title }}
                    </a>
                  </h4>
                  <div class="playtime">游玩时长: {{ formatTime(game.minutes) }}</div>
                </div>
              </div>

              <!-- 右侧：极简/低调的删除按钮 -->
              <button 
                class="btn-subtle-delete" 
                title="删除此记录"
                @click="handleDelete(dayIndex, gameIndex, day.date, game.id, game.info.title, game.minutes)"
              >
                ×
              </button>

            </div>
          </div>
        </div>
      </div>
    </main>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const loading = ref(true)
const totalMinutes = ref(0)
const groupedTimeline = ref([])
const gameCache = {}

const userConfig = ref({
  username: "@Loading",
  signature: "正在加载用户信息...",
  avatar: ""
})

const handleAvatarError = (e) => {
  e.target.src = 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
}

const formatTime = (m) => m < 60 ? `${m} 分钟` : `${(m / 60).toFixed(1)} 小时`

const fetchGameInfo = async (id) => {
  if (gameCache[id]) return gameCache[id]
  try {
    const res = await fetch('https://api.vndb.org/kana/vn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filters: ["id", "=", id], fields: "id, title, image.url, image.sexual, image.violence" })
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

// === 核心逻辑：处理删除事件 ===
const handleDelete = async (dayIndex, gameIndex, date, vnid, title, minutes) => {
  const confirmDelete = confirm(`确认要从 ${date} 的记录中删除 [${title}] 吗？`)
  
  if (confirmDelete) {
    try{
      await window.pywebview.api.delete_record(date, vnid)
    // 1. 从前端的显示数组中移除该项
    groupedTimeline.value[dayIndex].games.splice(gameIndex, 1)
    
    // 2. 扣除对应的总时长
    totalMinutes.value -= minutes

    // 3. 检查：如果这一天里没有任何游戏记录了，就把这天整个隐藏/删掉
    if (groupedTimeline.value[dayIndex].games.length === 0) {
      groupedTimeline.value.splice(dayIndex, 1)
    }

    } catch (error) {
      alert("删除失败，Python 端可能发生错误。")
      console.error(error)
    }
    
  }
}

const waitForWebView = () => {
  return new Promise((resolve) => {
    if (window.pywebview && window.pywebview.api) {
      resolve();
    } else {
      window.addEventListener('pywebviewready', () => {
        resolve();
      });
    }
  });
};

onMounted(async () => {
  await waitForWebView();
  const baseUrl = import.meta.env.BASE_URL

  try {
    // 读取文本配置
    const configData = await window.pywebview.api.get_config()
    userConfig.value.username = configData.username || '正在加载用户...'
    userConfig.value.signature = configData.signature || '正在加载个性签名...'
    
    // 【核心修改】：通过 Python API 获取 Base64 格式的头像
    const avatarBase64 = await window.pywebview.api.get_image('avatar')
    
    if (avatarBase64) {
      // 如果成功获取到 Base64 字符串，直接赋值
      userConfig.value.avatar = avatarBase64
    } else {
      // 如果后端没找到图片（返回空字符串），则使用默认头像
      userConfig.value.avatar = 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
    }
  } catch (e) {
    console.error("读取用户配置或头像失败", e)
    // 发生异常时的兜底 UI
    userConfig.value.username = "加载失败"
    userConfig.value.avatar = 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png'
  }

  try {
    // 2. 通过 Python 接口获取游玩数据
    const data = await window.pywebview.api.get_data()
    
    let total = 0
    const dates = Object.keys(data).sort((a, b) => new Date(b) - new Date(a))
    const groups = []

    for (const date of dates) {
      const games = []
      for (const [id, min] of Object.entries(data[date])) {
        total += min
        games.push({ id, minutes: min, info: await fetchGameInfo(id) }) // VNDB 是外部网络请求，不受影响
      }
      groups.push({ date, games })
    }
    totalMinutes.value = total
    groupedTimeline.value = groups
  } catch (error) {
    console.error("加载外层数据失败", error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard-wrapper { 
  display: flex; 
  flex-direction: column; 
  gap: 35px; 
}

.glass-panel {
  background: rgba(255, 255, 255, 0.55); 
  backdrop-filter: blur(20px); 
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.6); 
  border-radius: 24px; 
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  padding: 35px;
}

.profile-section { display: flex; align-items: center; padding-left: 10px; }
.avatar { width: 100px; height: 100px; border-radius: 50%; margin-right: 25px; border: 4px solid rgba(255,255,255,0.9); box-shadow: 0 5px 20px rgba(0,0,0,0.15); }
.profile-info { display: flex; flex-direction: column; }
.username { margin: 0 0 4px; font-size: 28px; color: #24292f; }
.signature { margin: 0 0 12px; font-size: 14px; color: rgba(36, 41, 47, 0.9); }
.total-time { margin: 0; font-size: 15px; color: #24292f; font-weight: 500; }
.highlight { color: #5ef18b; font-weight: bold; }

.feed-main-title { margin: 0 0 25px 0; font-size: 20px; color: #111; border-bottom: 1px solid rgba(0,0,0,0.1); padding-bottom: 12px; }
.status-msg { text-align: center; padding: 50px; color: #444; font-size: 14px; }
.date-group { margin-bottom: 35px; }
.date-header { font-size: 14px; color: #555; margin: 0 0 18px 0; text-transform: uppercase; letter-spacing: 1px; }

.game-cards { display: flex; flex-direction: column; gap: 10px; }

/* 单个记录条目的整体容器 */
.game-item { 
  display: flex; 
  justify-content: space-between; /* 让左右两端的内容靠边对齐 */
  align-items: center; /* 垂直居中对齐 */
  padding: 18px 10px; 
  border-bottom: 1px solid rgba(0,0,0,0.05);
  border-radius: 12px;
  transition: background-color 0.2s ease;
}

/* 当鼠标悬浮在这一条记录上时，给一点微妙的背景反馈 */
.game-item:hover {
  background-color: rgba(255, 255, 255, 0.4);
}
.game-item:last-child { border-bottom: none; }

/* 包含封面和文字的左侧主要内容区 */
.item-main {
  display: flex;
  gap: 22px;
}

.cover-img { width: 120px; height: 168px; border-radius: 10px; object-fit: cover; box-shadow: 0 3px 10px rgba(0,0,0,0.1); background-color: #f6f8fa; }
.game-details { display: flex; flex-direction: column; justify-content: center; }
.game-title { margin: 0 0 10px; font-size: 18px; color: #111; line-height: 1.3; }
.vndb-link { color: #24292f; text-decoration: none; transition: color 0.2s ease; }
.vndb-link:hover { color: #084993; }
.playtime { font-size: 14px; color: #666; font-weight: 500; }

/* ================= 极简删除按钮样式 ================= */
.btn-subtle-delete {
  background: transparent;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  opacity: 0.15; /* 默认极度透明，降低视觉干扰 */
  transition: all 0.2s ease;
}

/* 魔法逻辑：只有鼠标进入这一行记录时，按钮才显现一点 */
.game-item:hover .btn-subtle-delete {
  opacity: 0.6;
}

/* 鼠标直接放到按钮上时，变红警示 */
.btn-subtle-delete:hover {
  opacity: 1 !important;
  color: #d73a49;
  background-color: rgba(215, 58, 73, 0.1);
}

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