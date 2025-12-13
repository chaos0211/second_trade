<template>
  <div class="min-h-[calc(100vh-64px)] flex items-center justify-center bg-gray-50 p-4">
    <div class="card p-8 max-w-md w-full shadow-lg bg-white rounded-xl">
      <h1 class="text-2xl font-bold mb-6 text-center text-dark">用户注册</h1>

      <form class="space-y-5" @submit.prevent="onSubmit">
        <div class="flex flex-col">
          <label class="mb-1 font-medium text-dark-2">用户名</label>
          <input v-model="username" type="text" class="border border-light-1 rounded px-3 py-2 focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
        </div>

        <div class="flex flex-col">
          <label class="mb-1 font-medium text-dark-2">邮箱</label>
          <input v-model="email" type="email" class="border border-light-1 rounded px-3 py-2 focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
        </div>

        <div class="flex flex-col">
          <label class="mb-1 font-medium text-dark-2">手机号</label>
          <input v-model="mobile" type="text" class="border border-light-1 rounded px-3 py-2 focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
        </div>

        <div class="flex flex-col">
          <label class="mb-1 font-medium text-dark-2">密码</label>
          <input v-model="pwd" type="password" class="border border-light-1 rounded px-3 py-2 focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
        </div>

        <div class="flex flex-col">
          <label class="mb-1 font-medium text-dark-2">确认密码</label>
          <input v-model="confirm" type="password" class="border border-light-1 rounded px-3 py-2 focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
        </div>

        <button class="w-full bg-primary text-white py-2 rounded-lg font-medium hover:bg-primary/90 transition-colors shadow">
          注册
        </button>
      </form>

      <p class="text-sm text-dark-2 mt-5 text-center">
        已有账户？
        <router-link to="/login" class="text-primary font-medium hover:underline">立即登录</router-link>
      </p>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import http from "@/api/http";

const router = useRouter();
const username = ref("");
const email = ref("");
const mobile = ref("");
const pwd = ref("");
const confirm = ref("");

async function onSubmit() {
  if (!username.value || !email.value || !mobile.value || !pwd.value || !confirm.value) {
    alert("请完整填写必填项");
    return;
  }
  if (pwd.value !== confirm.value) {
    alert("两次输入的密码不一致");
    return;
  }
  try {
    await http.post("/api/auth/register", {
      username: username.value,
      email: email.value,
      phone: mobile.value,
      password: pwd.value,
    });
    alert("注册成功，前往登录");
    router.push("/login");
  } catch (e: any) {
    const data = e?.response?.data;
    const msg =
      (typeof data?.detail === "string" && data.detail) ||
      (data && typeof data === "object" && JSON.stringify(data)) ||
      "注册失败";
    alert(msg);
  }
}
</script>
