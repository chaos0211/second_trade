<template>
  <div class="p-6 md:p-8">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-6">
        <div>
          <h1 class="text-2xl md:text-3xl font-bold text-slate-800">系统管理</h1>
          <p class="text-slate-500 mt-1">用户列表管理（仅管理员可见）</p>
        </div>

        <div class="flex items-center gap-3">
          <div class="relative">
            <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"></i>
            <input
              v-model.trim="q"
              class="pl-9 pr-3 py-2 w-64 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
              placeholder="搜索用户名/邮箱/手机号"
              type="text"
            />
          </div>

          <button
            class="px-4 py-2 rounded-xl bg-[#165DFF] text-white font-semibold hover:opacity-95 transition inline-flex items-center gap-2"
            type="button"
            @click="openCreate"
          >
            <i class="fas fa-user-plus"></i>
            新增用户
          </button>
        </div>
      </div>

      <!-- Card -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <!-- Table header -->
        <div class="hidden md:grid grid-cols-12 px-6 py-3 bg-slate-50 border-b border-slate-200 text-sm text-slate-500 font-semibold">
          <div class="col-span-3">用户</div>
          <div class="col-span-2">角色</div>
          <div class="col-span-2">余额</div>
          <div class="col-span-2">信用分</div>
          <div class="col-span-3 text-right">操作</div>
        </div>

        <!-- Rows -->
        <div v-if="loading" class="p-10 flex items-center justify-center text-slate-500">
          <div class="w-10 h-10 border-4 border-slate-200 border-t-[#165DFF] rounded-full animate-spin"></div>
          <span class="ml-3">加载中...</span>
        </div>

        <div v-else class="divide-y divide-slate-200">
          <div
            v-for="u in paged"
            :key="u.id"
            class="px-6 py-4 hover:bg-slate-50 transition"
          >
            <div class="grid grid-cols-1 md:grid-cols-12 gap-3 md:gap-0 md:items-center">
              <!-- User -->
              <div class="md:col-span-3 flex items-center gap-3 min-w-0">
                <img
                  :src="u.avatar || fallbackAvatar"
                  class="w-10 h-10 rounded-xl border border-slate-200 object-cover"
                  alt="avatar"
                />
                <div class="min-w-0">
                  <div class="font-semibold text-slate-800 truncate">
                    {{ u.username }}
                    <span v-if="u.nickname" class="text-slate-500 font-medium">· {{ u.nickname }}</span>
                  </div>
                  <div class="text-sm text-slate-500 truncate">
                    {{ u.email || '-' }} · {{ u.phone || '-' }}
                  </div>
                </div>
              </div>

              <!-- Role -->
              <div class="md:col-span-2">
                <span
                  class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold"
                  :class="u.role === 'admin' ? 'bg-[#165DFF]/10 text-[#165DFF]' : 'bg-slate-100 text-slate-600'"
                >
                  {{ u.role === 'admin' ? '管理员' : '普通用户' }}
                </span>
              </div>

              <!-- Balance -->
              <div class="md:col-span-2 font-semibold text-slate-800">
                ¥{{ fmtMoney(u.balance) }}
              </div>

              <!-- Credit -->
              <div class="md:col-span-2">
                <div class="flex items-center gap-2">
                  <div class="w-24 h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      class="h-2"
                      :style="{ width: creditPercent(u.credit_score) + '%', backgroundColor: creditColor(u.credit_score) }"
                    ></div>
                  </div>
                  <div class="text-sm font-semibold text-slate-700">{{ u.credit_score }}</div>
                </div>
              </div>

              <!-- Actions -->
              <div class="md:col-span-3 flex md:justify-end gap-2">
                <button
                  class="px-3 py-2 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 transition text-sm font-semibold inline-flex items-center gap-2"
                  type="button"
                  @click="openEdit(u)"
                >
                  <i class="fas fa-pen"></i> 编辑
                </button>
                <button
                  class="px-3 py-2 rounded-xl bg-[#F53F3F] text-white hover:opacity-95 transition text-sm font-semibold inline-flex items-center gap-2"
                  type="button"
                  @click="confirmDelete(u)"
                >
                  <i class="fas fa-trash"></i> 删除
                </button>
              </div>
            </div>
          </div>

          <div v-if="filtered.length === 0" class="p-10 text-center text-slate-500">
            暂无匹配用户
          </div>
        </div>

        <!-- Pagination -->
        <div class="px-6 py-4 border-t border-slate-200 bg-white flex items-center justify-between">
          <div class="text-sm text-slate-500">
            共 {{ filtered.length }} 条 · 第 {{ page }} / {{ totalPages }} 页
          </div>

          <div class="flex items-center gap-2">
            <button
              class="px-3 py-2 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="page <= 1"
              @click="page--"
            >
              上一页
            </button>
            <button
              class="px-3 py-2 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="page >= totalPages"
              @click="page++"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>

    <AdminUserModal
      :open="modalOpen"
      :mode="modalMode"
      :user="editingUser"
      @close="closeModal"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import AdminUserModal from "@/components/admin/AdminUserModal.vue";

type Role = "user" | "admin";
type UserRow = {
  id: number | string;
  username: string;
  nickname?: string;
  email?: string;
  phone?: string;
  role: Role;
  balance: number;
  credit_score: number;
  avatar?: string;
};

const fallbackAvatar =
  "https://design.gemcoder.com/staticResource/echoAiSystemImages/877eae20b4cd21fa5cfbb0e03eedd327.png";

const loading = ref(true);
const q = ref("");
const page = ref(1);
const pageSize = 10;

const modalOpen = ref(false);
const modalMode = ref<"create" | "edit">("edit");
const editingUser = ref<UserRow | null>(null);

// mock 数据（接真实接口后替换 loadUsers / CRUD）
const users = reactive<UserRow[]>([
  { id: 1, username: "admin", nickname: "系统管理员", email: "admin@test.com", phone: "13800000001", role: "admin", balance: 10000, credit_score: 100 },
  { id: 2, username: "user123", nickname: "小明", email: "u1@test.com", phone: "13800000000", role: "user", balance: 12000, credit_score: 92 },
  { id: 3, username: "user456", nickname: "小红", email: "u2@test.com", phone: "13900000000", role: "user", balance: 8600, credit_score: 75 },
]);

async function loadUsers() {
  loading.value = true;
  try {
    // TODO: GET /api/admin/users/?q=...&page=...&page_size=10
    // 这里先模拟
    await new Promise((r) => setTimeout(r, 300));
  } finally {
    loading.value = false;
  }
}

onMounted(loadUsers);

const filtered = computed(() => {
  const s = q.value.toLowerCase();
  if (!s) return users;
  return users.filter((u) => {
    return (
      (u.username || "").toLowerCase().includes(s) ||
      (u.email || "").toLowerCase().includes(s) ||
      (u.phone || "").toLowerCase().includes(s) ||
      (u.nickname || "").toLowerCase().includes(s)
    );
  });
});

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)));
watch([q], () => (page.value = 1));

const paged = computed(() => {
  const start = (page.value - 1) * pageSize;
  return filtered.value.slice(start, start + pageSize);
});

// ===== actions =====
function openEdit(u: UserRow) {
  modalMode.value = "edit";
  editingUser.value = { ...u };
  modalOpen.value = true;
}
function openCreate() {
  modalMode.value = "create";
  editingUser.value = {
    id: "",
    username: "",
    nickname: "",
    email: "",
    phone: "",
    role: "user",
    balance: 10000,
    credit_score: 100,
    avatar: "",
  };
  modalOpen.value = true;
}
function closeModal() {
  modalOpen.value = false;
  editingUser.value = null;
}

function confirmDelete(u: UserRow) {
  if (!confirm(`确定要删除用户 ${u.username} 吗？`)) return;
  const idx = users.findIndex((x) => x.id === u.id);
  if (idx >= 0) users.splice(idx, 1);

  // TODO: DELETE /api/admin/users/{id}/
}

// modal submit
function handleSubmit(payload: UserRow & { password?: string }) {
  if (modalMode.value === "create") {
    // TODO: POST /api/admin/users/
    payload.id = Date.now();
    users.unshift({ ...payload });
  } else {
    // TODO: PATCH /api/admin/users/{id}/
    const idx = users.findIndex((x) => x.id === payload.id);
    if (idx >= 0) users[idx] = { ...payload };
  }
  closeModal();
}

// ===== ui helpers =====
function fmtMoney(v: any) {
  const n = typeof v === "string" ? Number(v) : v;
  if (Number.isNaN(n)) return String(v ?? "-");
  return n.toFixed(2).replace(/\.00$/, "");
}
function creditPercent(score: number) {
  const s = Math.max(0, Math.min(100, score));
  return s;
}
function creditColor(score: number) {
  if (score >= 85) return "#00B42A";
  if (score >= 60) return "#FF7D00";
  return "#F53F3F";
}
</script>