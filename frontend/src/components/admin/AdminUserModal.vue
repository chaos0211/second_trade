<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-6"
    @click.self="emit('close')"
  >
    <div class="w-full max-w-2xl bg-white rounded-2xl shadow-lg overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
        <div class="text-lg font-bold text-slate-800">
          {{ mode === 'create' ? '新增用户' : '编辑用户' }}
        </div>
        <button class="text-slate-400 hover:text-slate-700" type="button" @click="emit('close')">
          <i class="fas fa-times text-lg"></i>
        </button>
      </div>

      <div class="p-6 space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="用户名">
            <input
              v-model.trim="form.username"
              :disabled="mode === 'edit'"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 disabled:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
              placeholder="username"
            />
          </Field>

          <Field label="角色">
            <select
              v-model="form.role"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
            >
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
            </select>
          </Field>

          <Field label="昵称">
            <input
              v-model.trim="form.nickname"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
              placeholder="nickname"
            />
          </Field>

          <Field label="邮箱">
            <input
              v-model.trim="form.email"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
              placeholder="email"
            />
          </Field>

          <Field label="手机号">
            <input
              v-model.trim="form.phone"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
              placeholder="phone"
            />
          </Field>

          <Field label="信用分">
            <input
              v-model.number="form.credit_score"
              type="number"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
              placeholder="credit_score"
            />
          </Field>

          <Field label="钱包余额">
            <input
              v-model.number="form.balance"
              type="number"
              class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
              placeholder="balance"
            />
          </Field>

          <div class="md:col-span-2 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div class="text-sm text-slate-600 mb-3">
              密码（可选）：留空表示不修改
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label="新密码">
                <input
                  v-model="form.password"
                  type="password"
                  class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
                  placeholder="password"
                />
              </Field>
              <Field label="确认密码">
                <input
                  v-model="form.password2"
                  type="password"
                  class="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#165DFF]/30"
                  placeholder="password again"
                />
              </Field>
            </div>

            <div v-if="passwordError" class="mt-2 text-sm text-red-600">
              {{ passwordError }}
            </div>
          </div>
        </div>
      </div>

      <div class="px-6 py-4 border-t border-slate-200 bg-white flex items-center justify-end gap-3">
        <button
          type="button"
          class="px-4 py-2 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 transition"
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
          确认保存
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, reactive, watch } from "vue";

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

const props = defineProps<{
  open: boolean;
  mode: "create" | "edit";
  user: UserRow | null;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "submit", payload: UserRow & { password?: string }): void;
}>();

const original = reactive<any>({});
const form = reactive<any>({
  id: "",
  username: "",
  nickname: "",
  email: "",
  phone: "",
  role: "user",
  balance: 10000,
  credit_score: 100,
  avatar: "",
  password: "",
  password2: "",
});

watch(
  () => props.open,
  (v) => {
    if (!v) return;
    const u = props.user || ({} as any);

    Object.assign(form, {
      id: u.id ?? "",
      username: u.username ?? "",
      nickname: u.nickname ?? "",
      email: u.email ?? "",
      phone: u.phone ?? "",
      role: u.role ?? "user",
      balance: u.balance ?? 10000,
      credit_score: u.credit_score ?? 100,
      avatar: u.avatar ?? "",
      password: "",
      password2: "",
    });

    Object.assign(original, JSON.parse(JSON.stringify(form)));
  },
  { immediate: true }
);

const dirty = computed(() => {
  if (!props.open) return false;
  return (
    form.nickname !== original.nickname ||
    form.email !== original.email ||
    form.phone !== original.phone ||
    form.role !== original.role ||
    Number(form.balance) !== Number(original.balance) ||
    Number(form.credit_score) !== Number(original.credit_score) ||
    form.username !== original.username ||
    !!form.password ||
    !!form.password2
  );
});

const passwordError = computed(() => {
  if (!form.password && !form.password2) return "";
  if (form.password !== form.password2) return "两次输入的密码不一致";
  return "";
});

const canSubmit = computed(() => dirty.value && !passwordError.value);

function submit() {
  if (!canSubmit.value) return;
  emit("submit", {
    id: form.id,
    username: form.username,
    nickname: form.nickname,
    email: form.email,
    phone: form.phone,
    role: form.role,
    balance: Number(form.balance),
    credit_score: Number(form.credit_score),
    avatar: form.avatar,
    password: form.password ? form.password : undefined,
  });
}

/** Field：左侧 label，右侧 input */
const Field = defineComponent({
  name: "Field",
  props: { label: { type: String, required: true } },
  setup(props, { slots }) {
    return () =>
      h("div", { class: "grid grid-cols-12 items-center gap-3" }, [
        h("div", { class: "col-span-4 text-sm text-slate-600 font-semibold" }, props.label),
        h("div", { class: "col-span-8" }, slots.default?.()),
      ]);
  },
});
</script>