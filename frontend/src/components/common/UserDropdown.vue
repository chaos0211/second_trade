<template>
  <div class="relative group">
    <button class="flex items-center space-x-2 focus:outline-none">
      <img
        src="https://design.gemcoder.com/staticResource/echoAiSystemImages/4db1f4e22c08cab67f2bb5c522cad076.png"
        class="w-8 h-8 rounded-full object-cover border-2 border-light-2"
        alt="用户头像"
      />
      <span class="hidden md:inline text-sm font-medium">张小明</span>
      <i class="fas fa-chevron-down text-xs text-light-1 group-hover:text-primary transition-colors"></i>
    </button>

    <div
      class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-dropdown opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50"
    >
      <div class="py-2">
        <a href="javascript:void(0);" class="block px-4 py-2 text-sm text-dark-2 hover:bg-light-3 hover:text-primary">
          <i class="fas fa-user mr-2"></i>个人资料
        </a>
        <a href="javascript:void(0);" class="block px-4 py-2 text-sm text-dark-2 hover:bg-light-3 hover:text-primary">
          <i class="fas fa-cog mr-2"></i>设置
        </a>
        <div class="border-t border-light-2 my-1"></div>
        <a
          href="javascript:void(0);"
          class="block px-4 py-2 text-sm text-danger hover:bg-light-3"
          @click="handleLogout"
        >
          <i class="fas fa-sign-out-alt mr-2"></i>退出登录
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import http from '@/api/http'

const router = useRouter()

const handleLogout = async () => {
  try {
    const refresh = localStorage.getItem('refresh')
    if (refresh) {
      await http.post('/api/auth/logout/', { refresh })
    }
  } catch (e) {
    // ignore errors; logout should still proceed locally
  } finally {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    // optional: clear any cached user info
    localStorage.removeItem('user')
    router.replace('/login')
  }
}
</script>