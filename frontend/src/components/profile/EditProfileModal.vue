<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-6"
    @click.self="emit('close')"
  >
    <div class="w-full max-w-xl bg-white rounded-2xl shadow-lg overflow-hidden">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
        <div class="text-lg font-bold text-slate-800">修改资料</div>
        <button class="text-slate-400 hover:text-slate-700" type="button" @click="emit('close')">
          <i class="fas fa-times text-lg"></i>
        </button>
      </div>

      <!-- Body -->
      <div class="p-6 space-y-4">
        <div class="grid grid-cols-1 gap-4">
          <!-- 显示原始内容 + 可编辑 -->
          <FieldRow label="昵称">
            <input
              v-model.trim="form.nickname"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
              type="text"
              placeholder="请输入昵称"
            />
          </FieldRow>

          <FieldRow label="邮箱">
            <input
              v-model.trim="form.email"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
              type="email"
              placeholder="请输入邮箱"
            />
          </FieldRow>

          <FieldRow label="手机号">
            <input
              v-model.trim="form.phone"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
              type="text"
              placeholder="请输入手机号"
            />
          </FieldRow>

          <FieldRow label="地址">
            <input
              v-model.trim="form.address"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
              type="text"
              placeholder="请输入收货地址"
            />
          </FieldRow>

          <div class="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div class="text-sm text-slate-600 mb-3">
              密码修改为可选项：留空表示不修改
            </div>

            <FieldRow label="新密码">
              <input
                v-model="form.password"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
                type="password"
              />
            </FieldRow>

            <FieldRow label="确认密码">
              <input
                v-model="form.password2"
                class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
                type="password"
                placeholder="再次输入新密码（可选）"
              />
            </FieldRow>

            <div v-if="passwordError" class="mt-2 text-sm text-red-600">
              {{ passwordError }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="apiError" class="px-6 pb-2">
        <div class="rounded-xl border border-red-200 bg-red-50 text-red-700 text-sm px-4 py-3">
          {{ apiError }}
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-slate-200 bg-white flex items-center justify-end gap-3">
        <button
          type="button"
          class="px-4 py-2 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="submitting"
          @click="emit('close')"
        >
          取消
        </button>

        <button
          type="button"
          class="px-4 py-2 rounded-xl font-semibold transition"
          :class="canSubmit
            ? 'bg-[#165DFF] text-white hover:opacity-95'
            : 'bg-slate-200 text-slate-500 cursor-not-allowed'"
          :disabled="!canSubmit"
          @click="submit"
        >
          {{ submitting ? '提交中…' : '确认修改' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, reactive, ref, watch } from "vue";
import http from "@/api/http";

type Profile = {
  username: string;
  nickname: string;
  email: string;
  phone: string;
  address: string;
};

const props = defineProps<{
  open: boolean;
  profile: Profile;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "submit", payload: { nickname: string; email: string; phone: string; address: string; password?: string }): void;
}>();

const original = reactive({
  nickname: "",
  email: "",
  phone: "",
  address: "",
});

const form = reactive({
  nickname: "",
  email: "",
  phone: "",
  address: "",
  password: "",
  password2: "",
});

const submitting = ref(false);
const apiError = ref("");

watch(
  () => props.open,
  (v) => {
    if (!v) return;
    // 打开弹窗时，把原始值灌进去，并记录一份 original 用于 dirty 检测
    original.nickname = props.profile.nickname || "";
    original.email = props.profile.email || "";
    original.phone = props.profile.phone || "";
    original.address = props.profile.address || "";

    form.nickname = original.nickname;
    form.email = original.email;
    form.phone = original.phone;
    form.address = original.address;
    form.password = "";
    form.password2 = "";

    apiError.value = "";
  },
  { immediate: true }
);

const dirty = computed(() => {
  return (
    form.nickname !== original.nickname ||
    form.email !== original.email ||
    form.phone !== original.phone ||
    form.address !== original.address ||
    !!form.password ||
    !!form.password2
  );
});

const passwordError = computed(() => {
  if (!form.password && !form.password2) return "";
  if (form.password !== form.password2) return "两次输入的密码不一致";
  return "";
});

const canSubmit = computed(() => {
  if (submitting.value) return false;
  if (!dirty.value) return false;
  if (passwordError.value) return false;
  return true;
});

async function submit() {
  if (!canSubmit.value) return;
  apiError.value = "";
  submitting.value = true;

  try {
    const body: any = {
      nickname: form.nickname,
      email: form.email,
      phone: form.phone,
      address: form.address,
    };
    if (form.password) body.password = form.password;

    // 后端：PUT /api/auth/me （无斜杠）
    const resp: any = await http.put("/api/auth/me", body);
    const data: any = resp?.data ?? resp;

    // 让父组件可选择刷新
    emit("submit", {
      nickname: data?.nickname ?? form.nickname,
      email: data?.email ?? form.email,
      phone: data?.phone ?? form.phone,
      address: data?.address ?? form.address,
      password: undefined,
    });

    emit("close");
  } catch (e: any) {
    const d = e?.response?.data;
    apiError.value =
      (typeof d === "string" && d) ||
      d?.detail ||
      d?.error ||
      (d && JSON.stringify(d)) ||
      e?.message ||
      "更新失败";
  } finally {
    submitting.value = false;
  }
}

/** FieldRow：左侧 label，右侧输入框（你要求字段不放在框里） */
const FieldRow = defineComponent({
  name: "FieldRow",
  props: { label: { type: String, required: true } },
  setup(props, { slots }) {
    return () =>
      h("div", { class: "grid grid-cols-12 items-center gap-3" }, [
        h("div", { class: "col-span-4 sm:col-span-3 text-sm text-slate-600 font-medium" }, props.label),
        h("div", { class: "col-span-8 sm:col-span-9" }, slots.default?.()),
      ]);
  },
});
</script>