<template>
  <div class="p-6 md:p-8">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-6">
        <div>
          <h1 class="text-2xl md:text-3xl font-bold text-slate-800">系统管理</h1>
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
            暂无用户
          </div>
        </div>

        <!-- Pagination -->
        <div class="px-6 py-4 border-t border-slate-200 bg-white flex items-center justify-between">
          <div class="text-sm text-slate-500">
            共 {{ totalCount || filtered.length }} 条 · 第 {{ page }} / {{ totalPages }} 页
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
import http from "@/api/http";

type Role = "user" | "admin";
type UserRow = {
  id: number | string;
  username: string;
  nickname?: string;
  email?: string;
  phone?: string;
  role: Role;
  balance: number | string;
  credit_score: number;
  avatar?: string;
  address?: string;
  is_superuser?: number | boolean | string;
  is_staff?: number | boolean | string;
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

const users = ref<UserRow[]>([]);
const totalCount = ref(0);

async function loadUsers() {
  loading.value = true;
  try {
    const params: any = { page: page.value, page_size: pageSize };
    if (q.value) params.q = q.value;

    const resp: any = await http.get("/api/auth/admin/users/", { params });
    const data: any = resp?.data ?? resp;

    // 支持两种返回：分页 {count, results} 或数组 []
    if (Array.isArray(data)) {
      users.value = data as UserRow[];
      totalCount.value = data.length;
    } else {
      const results = Array.isArray(data?.results) ? data.results : Array.isArray(data?.data) ? data.data : [];
      users.value = results as UserRow[];
      totalCount.value = Number(data?.count ?? results.length ?? 0);
    }
  } catch (e: any) {
    const d = e?.response?.data;
    const msg = d?.detail || d?.error || (typeof d === "string" ? d : "加载用户列表失败");
    alert(msg);
    users.value = [];
    totalCount.value = 0;
  } finally {
    loading.value = false;
  }
}

onMounted(loadUsers);

const filtered = computed(() => users.value);

const totalPages = computed(() => {
  const n = totalCount.value || filtered.value.length;
  return Math.max(1, Math.ceil(n / pageSize));
});

watch([q], () => {
  page.value = 1;
  loadUsers();
});

watch([page], () => {
  loadUsers();
});

const paged = computed(() => filtered.value);

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
    address: "",
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

async function confirmDelete(u: UserRow) {
  if (!confirm(`确定要删除用户 ${u.username} 吗？`)) return;
  try {
    await http.delete(`/api/auth/admin/users/${u.id}/`);
    await loadUsers();
  } catch (e: any) {
    const d = e?.response?.data;
    const msg = d?.detail || d?.error || (typeof d === "string" ? d : "删除失败");
    alert(msg);
  }
}

// modal submit
async function handleSubmit(payload: UserRow & { password?: string }) {
  try {
    if (modalMode.value === "create") {
      const body: any = {
        username: payload.username,
        nickname: payload.nickname,
        email: payload.email,
        phone: payload.phone,
        address: payload.address,
        role: payload.role,
        balance: payload.balance,
        credit_score: payload.credit_score,
        avatar: payload.avatar,
      };
      if (payload.password) body.password = payload.password;

      await http.post("/api/auth/admin/users/", body);
    } else {
      const body: any = {
        username: payload.username,
        nickname: payload.nickname,
        email: payload.email,
        phone: payload.phone,
        address: payload.address,
        role: payload.role,
        balance: payload.balance,
        credit_score: payload.credit_score,
        avatar: payload.avatar,
      };
      if (payload.password) body.password = payload.password;

      await http.put(`/api/auth/admin/users/${payload.id}/`, body);
    }

    closeModal();
    await loadUsers();
  } catch (e: any) {
    const d = e?.response?.data;
    const msg = d?.detail || d?.error || (typeof d === "string" ? d : "保存失败");
    alert(msg);
  }
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