<template>
  <aside
    class="bg-white shadow-lg z-20 flex flex-col transition-all duration-300 ease-in-out"
    :class="collapsed ? 'w-20' : 'w-64'"
  >
    <!-- Logo -->
    <div class="flex items-center justify-center h-16 border-b border-light-2">
      <div class="flex items-center space-x-2">
        <span class="text-xl font-bold text-dark" :class="collapsed ? 'hidden' : ''">二手电子产品交易中心</span>
      </div>
    </div>

    <!-- User -->
    <div class="p-4 border-b border-light-2">
      <div class="flex items-center space-x-3">
        <img
          src="https://design.gemcoder.com/staticResource/echoAiSystemImages/4db1f4e22c08cab67f2bb5c522cad076.png"
          class="w-10 h-10 rounded-full object-cover border-2 border-light-2"
          alt="用户头像"
        />
        <div :class="collapsed ? 'hidden' : ''">
          <h3 class="font-medium text-dark">张小明</h3>
          <div class="flex items-center text-xs text-dark-2">
            <span class="inline-block w-2 h-2 rounded-full bg-success mr-1"></span>
            <span>信用良好</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 overflow-y-auto scrollbar-hide py-4">
      <ul class="px-2">
        <li class="mb-1">
          <RouterLink
            to="/"
            class="flex items-center space-x-3 py-3 rounded-lg group transition-all duration-200"
            :class="[
              collapsed ? 'justify-center px-2' : 'px-4',
              isMarket ? 'bg-light-3 text-primary' : 'text-dark-2 hover:bg-light-3'
            ]"
          >
            <i class="fas fa-th-large w-5 text-center"></i>
            <span :class="collapsed ? 'hidden' : ''">市场大厅</span>
          </RouterLink>
        </li>

        <li class="mb-1" v-for="item in menus" :key="item.text">
          <RouterLink
            :to="item.to"
            class="flex items-center space-x-3 py-3 rounded-lg group transition-all duration-200"
            :class="[
              collapsed ? 'justify-center px-2' : 'px-4',
              isActive(item.to) ? 'bg-light-3 text-primary' : 'text-dark-2 hover:bg-light-3'
            ]"
          >
            <i :class="item.icon + ' w-5 text-center'"></i>
            <span :class="collapsed ? 'hidden' : ''">{{ item.text }}</span>
          </RouterLink>
        </li>
      </ul>
    </nav>

    <!-- Bottom -->
    <div class="p-4 border-t border-light-2">
      <a
        href="javascript:void(0);"
        class="flex items-center space-x-3 py-3 rounded-lg text-dark-2 group transition-all duration-200 hover:bg-light-3"
        :class="collapsed ? 'justify-center px-2' : 'px-4'"
      >
        <i class="fas fa-question-circle w-5 text-center"></i>
        <span :class="collapsed ? 'hidden' : ''">帮助中心</span>
      </a>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

defineProps<{ collapsed: boolean }>();
defineEmits<{ (e: "toggle"): void }>();

const rawMenus = [
  { icon: "fas fa-tag", text: "我要卖机", to: "/seller" },
  { icon: "fas fa-shopping-cart", text: "订单中心", to: "/orders" },
  { icon: "fas fa-user-circle", text: "个人中心", to: "/profile" },
  { icon: "fas fa-cog", text: "系统管理", to: "/admin", adminOnly: true },
] as const;

function parseMaybeJson(raw: string | null): any {
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function getStorageItem(key: string): string | null {
  return localStorage.getItem(key) ?? sessionStorage.getItem(key);
}

function truthySuperuser(v: any): boolean {
  return v === 1 || v === "1" || v === true || v === "true";
}

function decodeJwtPayload(token: string): any {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "===".slice((base64.length + 3) % 4);
    const json = decodeURIComponent(
      atob(padded)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(json);
  } catch {
    return null;
  }
}

const isSuperuser = computed(() => {
  try {
    const u1 = parseMaybeJson(getStorageItem("user"));
    if (u1 && truthySuperuser(u1?.is_superuser)) return true;

    const u2 = parseMaybeJson(getStorageItem("profile"));
    if (u2 && truthySuperuser(u2?.is_superuser)) return true;

    const u3 = parseMaybeJson(getStorageItem("me"));
    if (u3 && truthySuperuser(u3?.is_superuser)) return true;

    const auth = parseMaybeJson(getStorageItem("auth"));
    const au = auth?.user ?? auth?.data?.user ?? null;
    if (au && truthySuperuser(au?.is_superuser)) return true;

    // fallback: decode access token and check role
    const access =
      (parseMaybeJson(getStorageItem("access")) as any) ||
      getStorageItem("access") ||
      getStorageItem("access_token") ||
      "";
    const token = typeof access === "string" ? access : "";
    if (token) {
      const payload = decodeJwtPayload(token);
      if (payload?.is_superuser && truthySuperuser(payload?.is_superuser)) return true;
      if (payload?.role === "admin") return true;
    }

    return false;
  } catch {
    return false;
  }
});

const menus = computed(() => {
  return rawMenus.filter((m: any) => {
    if (m.adminOnly) return isSuperuser.value;
    return true;
  });
});

const route = useRoute();

const isMarket = computed(() => route.path === "/");

function isActive(prefix: string) {
  return route.path === prefix || route.path.startsWith(prefix + "/");
}
</script>