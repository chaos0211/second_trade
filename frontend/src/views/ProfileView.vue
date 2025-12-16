<template>
  <div class="p-6 md:p-8">
    <div class="max-w-4xl mx-auto">
      <div class="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 class="text-2xl md:text-3xl font-bold text-slate-800">个人中心</h1>
          <p class="text-slate-500 mt-1">管理你的头像与个人资料</p>
        </div>
      </div>

      <!-- Card -->
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div class="p-6 md:p-8 grid grid-cols-1 md:grid-cols-12 gap-6">
          <!-- Avatar -->
          <div class="md:col-span-4">
            <div class="flex items-center gap-4">
              <div class="relative">
                <img
                  :src="profile.avatar || fallbackAvatar"
                  class="w-20 h-20 rounded-2xl object-cover border border-slate-200"
                  alt="avatar"
                />
                <span class="absolute -bottom-2 -right-2 inline-flex items-center justify-center w-8 h-8 rounded-full bg-white border border-slate-200 shadow-sm">
                  <i class="fas fa-user text-slate-500 text-sm"></i>
                </span>
              </div>

              <div class="min-w-0">
                <div class="text-lg font-semibold text-slate-800 truncate">
                  {{ profile.nickname || profile.username || "未设置昵称" }}
                </div>
                <div class="text-sm text-slate-500 truncate">
                  ID：{{ profile.id ?? "-" }}
                </div>
              </div>
            </div>

            <div class="mt-4 text-sm text-slate-500 leading-relaxed">
              你可以在右下角点击“修改资料”，更新昵称、邮箱、手机号与密码。
            </div>
          </div>

          <!-- Info -->
          <div class="md:col-span-8">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <InfoItem label="用户名" :value="profile.username || '-'" />
              <InfoItem label="昵称" :value="profile.nickname || '-'" />
              <InfoItem label="邮箱" :value="profile.email || '-'" />
              <InfoItem label="手机号" :value="profile.phone || '-'" />
              <InfoItem label="地址" :value="profile.address || '-'" />
              <InfoItem label="信用分" :value="(profile.credit_score ?? '-').toString()" />
            </div>

            <div class="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div class="text-sm text-slate-600">
                <span class="font-semibold text-slate-700">提示：</span>
                密码修改为可选项，留空表示不修改。
              </div>
            </div>
          </div>
        </div>

        <!-- Footer / Edit button bottom-right -->
        <div class="px-6 md:px-8 py-4 border-t border-slate-200 bg-white flex items-center justify-end">
          <button
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#165DFF] text-white font-medium hover:opacity-95 transition"
            @click="openEdit"
          >
            <i class="fas fa-pen"></i>
            修改资料
          </button>
        </div>
      </div>
    </div>

    <EditProfileModal
      :open="editOpen"
      :profile="profile"
      @close="closeEdit"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { defineComponent, h, onMounted, reactive, ref } from "vue";
import EditProfileModal from "@/components/profile/EditProfileModal.vue";
import http from "@/api/http";

/** 你后端登录返回 user 里目前有：id/username/nickname/email/role
 * 这里扩展 phone/avatar 以便前端展示
 */
type Profile = {
  id: number | null;
  username: string;
  nickname: string;
  email: string;
  phone: string;
  avatar: string;
  address: string;
  credit_score: number | null;
};

const fallbackAvatar =
  "https://design.gemcoder.com/staticResource/echoAiSystemImages/877eae20b4cd21fa5cfbb0e03eedd327.png";

const profile = reactive<Profile>({
  id: null,
  username: "",
  nickname: "",
  email: "",
  phone: "",
  avatar: "",
  address: "",
  credit_score: null,
});

const editOpen = ref(false);

function openEdit() {
  editOpen.value = true;
}
function closeEdit() {
  editOpen.value = false;
}

/** 这里先做 mock：你接真实接口时，把 loadProfile / updateProfile 换成 http 请求即可 */
async function loadProfile() {
  try {
    const resp: any = await http.get("/api/auth/me");
    const data: any = resp?.data ?? resp;
    profile.id = data?.id ?? null;
    profile.username = data?.username ?? "";
    profile.nickname = data?.nickname ?? "";
    profile.email = data?.email ?? "";
    profile.phone = data?.phone ?? "";
    profile.avatar = data?.avatar ?? "";
    profile.address = data?.address ?? "";
    profile.credit_score = data?.credit_score ?? null;

    // keep local cache in sync
    const cache = {
      id: profile.id,
      username: profile.username,
      nickname: profile.nickname,
      email: profile.email,
      phone: profile.phone,
      avatar: profile.avatar,
      address: profile.address,
      credit_score: profile.credit_score,
    };
    localStorage.setItem("user", JSON.stringify(cache));
  } catch (e: any) {
    const msg =
      e?.response?.data?.detail ||
      e?.response?.data?.error ||
      e?.message ||
      "获取个人信息失败";
    alert(msg);
  }
}

async function handleSubmit(payload: {
  nickname: string;
  email: string;
  phone: string;
  address: string;
  password?: string; // 为空表示不修改
}) {
  try {
    const body: any = {
      nickname: payload.nickname,
      email: payload.email,
      phone: payload.phone,
      address: payload.address,
    };
    if (payload.password) body.password = payload.password;
    await http.put("/api/auth/me", body);
    editOpen.value = false;
    await loadProfile();
  } catch (e: any) {
    const data = e?.response?.data;
    const msg =
      (typeof data === "string" && data) ||
      data?.detail ||
      data?.error ||
      e?.message ||
      "更新失败";
    alert(msg);
  }
}

onMounted(loadProfile);

/** 小组件：信息展示块 */
const InfoItem = defineComponent({
  name: "InfoItem",
  props: {
    label: { type: String, required: true },
    value: { type: String, required: true },
  },
  setup(props) {
    return () =>
      h("div", { class: "rounded-xl border border-slate-200 p-4 bg-white" }, [
        h("div", { class: "text-xs text-slate-500" }, props.label),
        h("div", { class: "mt-1 text-slate-800 font-semibold break-all" }, props.value),
      ]);
  },
});
</script>