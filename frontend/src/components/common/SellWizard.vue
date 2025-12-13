<template>
  <!-- Drawer -->
  <div
    v-if="open"
    class="fixed top-0 right-0 bottom-0 left-[16rem] bg-black/50 z-50 flex items-center justify-center p-6"
    @click.self="close"
  >
    <div
      class="bg-white w-[90%] max-w-4xl max-h-[81vh] rounded-2xl shadow-modal flex flex-col transform transition-transform duration-300 translate-y-0"
    >
      <!-- 头部 -->
      <div class="p-6 border-b border-neutral-200 flex justify-between items-center">
        <h3 class="text-xl font-bold text-neutral-700">上架新商品</h3>
        <button class="text-neutral-500 hover:text-neutral-700 transition-colors" @click="close">
          <i class="fas fa-times text-xl"></i>
        </button>
      </div>

      <!-- 步骤指示器 -->
      <div class="px-6 pt-6 pb-2">
        <div class="flex items-center justify-between relative">
          <div class="absolute top-1/2 left-0 right-0 h-1 bg-neutral-200 -translate-y-1/2 z-0"></div>
          <div
            class="absolute top-1/2 left-0 h-1 bg-primary -translate-y-1/2 z-10 transition-all duration-500"
            :style="{ width: progressWidth }"
          ></div>

          <div class="flex flex-col items-center relative z-20">
            <div class="w-8 h-8 rounded-full border-2 flex items-center justify-center"
              :class="stepClass(1)">1</div>
            <span class="mt-2 text-sm font-medium" :class="stepTextClass(1)">上传图片</span>
          </div>

          <div class="flex flex-col items-center relative z-20">
            <div class="w-8 h-8 rounded-full border-2 flex items-center justify-center"
              :class="stepClass(2)">2</div>
            <span class="mt-2 text-sm font-medium" :class="stepTextClass(2)">识别与确认</span>
          </div>

          <div class="flex flex-col items-center relative z-20">
            <div class="w-8 h-8 rounded-full border-2 flex items-center justify-center"
              :class="stepClass(3)">3</div>
            <span class="mt-2 text-sm font-medium" :class="stepTextClass(3)">填写信息</span>
          </div>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="flex-1 overflow-y-auto p-6">
        <!-- Step 1 -->
        <div v-show="currentStep === 1" class="step-content">
          <div class="text-center mb-8">
            <h4 class="text-lg font-semibold text-neutral-700 mb-2">上传商品图片</h4>
            <p class="text-neutral-500 max-w-lg mx-auto">
              请上传清晰的商品图片，至少1张，最多5张。多角度拍摄可以提高商品的吸引力。
            </p>
          </div>

          <div
            class="border-2 border-dashed border-neutral-300 rounded-xl p-8 text-center hover:border-primary transition-colors cursor-pointer mb-8"
            :class="dragActive ? 'upload-area-active' : 'upload-area-active'"
            @click="pickFiles"
            @dragenter.prevent="dragActive = true"
            @dragover.prevent="dragActive = true"
            @dragleave.prevent="dragActive = false"
            @drop.prevent="onDrop"
          >
            <div class="max-w-md mx-auto">
              <i class="fas fa-cloud-upload-alt text-4xl text-primary mb-4"></i>
              <p class="text-neutral-700 font-medium mb-2">拖拽图片到此处或点击上传</p>
              <p class="text-neutral-500 text-sm mb-4">支持 JPG、PNG 格式，单张图片不超过5MB</p>
              <button
                type="button"
                class="bg-white border border-neutral-300 text-neutral-700 px-4 py-2 rounded-lg hover:bg-neutral-50 transition-colors"
              >
                选择图片
              </button>
              <input
                ref="fileInput"
                type="file"
                class="hidden"
                accept="image/*"
                multiple
                @change="onFileChange"
              />
            </div>
          </div>

          <div class="bg-neutral-50 border border-neutral-200 rounded-lg p-4 mb-6">
            <h5 class="font-medium text-neutral-700 flex items-center mb-3">
              <i class="fas fa-info-circle text-primary mr-2"></i>拍摄规范提示
            </h5>
            <ul class="text-neutral-500 space-y-2 text-sm">
              <li class="flex items-start">
                <i class="fas fa-check-circle text-success mt-1 mr-2"></i>
                <span>在光线充足的环境下拍摄，保证图片清晰</span>
              </li>
              <li class="flex items-start">
                <i class="fas fa-check-circle text-success mt-1 mr-2"></i>
                <span>拍摄商品正面、背面、侧面和细节部位</span>
              </li>
              <li class="flex items-start">
                <i class="fas fa-check-circle text-success mt-1 mr-2"></i>
                <span>展示商品的成色，如有划痕请拍摄清晰</span>
              </li>
              <li class="flex items-start">
                <i class="fas fa-check-circle text-success mt-1 mr-2"></i>
                <span>避免拍摄无关物品，保持背景简洁</span>
              </li>
            </ul>
          </div>

          <div v-if="previews.length">
            <h5 class="font-medium text-neutral-700 mb-3">已上传图片</h5>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
              <div v-for="(src, idx) in previews" :key="idx" class="relative group">
                <img
                  :src="src"
                  alt="预览图片"
                  class="w-full aspect-square object-cover rounded-lg border border-neutral-200"
                />
                <button
                  type="button"
                  class="absolute top-1 right-1 bg-black/50 text-white w-6 h-6 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  @click.stop="removePreview(idx)"
                >
                  <i class="fas fa-times text-xs"></i>
                </button>
              </div>
            </div>
          </div>

          <div v-if="stepError" class="mt-4 text-danger text-sm">{{ stepError }}</div>
        </div>

        <!-- Step 2 -->
        <div v-show="currentStep === 2" class="step-content">
          <div class="text-center mb-8">
            <h4 class="text-lg font-semibold text-neutral-700 mb-2">商品识别与确认</h4>
            <p class="text-neutral-500 max-w-lg mx-auto">
              系统正在识别您的商品信息，请稍候...
            </p>
          </div>

          <!-- 加载 -->
          <div v-if="recognizeState === 'loading'" class="flex flex-col items-center justify-center py-12">
            <div class="w-16 h-16 border-4 border-neutral-200 border-t-primary rounded-full animate-spin mb-4"></div>
            <p class="text-neutral-600">正在识别商品信息...</p>
            <p class="text-neutral-500 text-sm mt-1">这可能需要几秒钟时间</p>
          </div>

          <!-- 失败 -->
          <div v-else-if="recognizeState === 'error'" class="flex flex-col items-center justify-center py-12 text-center">
            <div class="w-16 h-16 rounded-full bg-danger/10 flex items-center justify-center mb-4">
              <i class="fas fa-exclamation-triangle text-danger text-2xl"></i>
            </div>
            <h5 class="text-lg font-medium text-neutral-700 mb-2">识别失败</h5>
            <p class="text-neutral-500 max-w-md mb-6">
              无法识别您上传的商品图片，请确保图片清晰且商品完整展示。
            </p>
            <div class="flex space-x-3">
              <button
                type="button"
                class="bg-white border border-neutral-300 text-neutral-700 px-4 py-2 rounded-lg hover:bg-neutral-50 transition-colors"
                @click="simulateRecognition"
              >
                重新识别
              </button>
              <button
                type="button"
                class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
                @click="goStep(1)"
              >
                返回重新上传
              </button>
            </div>
          </div>

          <!-- 成功 -->
          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h5 class="font-medium text-neutral-700 mb-3">已上传图片</h5>
              <div class="grid grid-cols-3 gap-3 mb-4">
                <img
                  v-for="(src, idx) in previews.slice(0, 3)"
                  :key="idx"
                  :src="src"
                  alt="商品图片预览"
                  class="w-full aspect-square object-cover rounded-lg border border-neutral-200"
                />
              </div>
              <button type="button" class="text-primary hover:text-primary/80 text-sm flex items-center" @click="goStep(1)">
                <i class="fas fa-edit mr-1"></i>重新选择图片
              </button>
            </div>

            <div class="bg-neutral-50 border border-neutral-200 rounded-xl p-5">
              <h5 class="font-medium text-neutral-700 mb-4">识别结果</h5>

              <div class="space-y-4">
                <div>
                  <label class="block text-neutral-500 text-sm mb-1">商品品类</label>
                  <select v-model="recognized.category"
                    class="w-full border border-neutral-300 rounded-lg px-3 py-2.5 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none">
                    <option value="phone">手机</option>
                    <option value="laptop">笔记本电脑</option>
                    <option value="tablet">平板电脑</option>
                    <option value="watch">智能手表</option>
                    <option value="headphones">耳机</option>
                  </select>
                </div>

                <div>
                  <label class="block text-neutral-500 text-sm mb-1">品牌</label>
                  <select v-model="recognized.brand"
                    class="w-full border border-neutral-300 rounded-lg px-3 py-2.5 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none">
                    <option value="apple">苹果</option>
                    <option value="huawei">华为</option>
                    <option value="xiaomi">小米</option>
                    <option value="samsung">三星</option>
                    <option value="oppo">OPPO</option>
                    <option value="vivo">vivo</option>
                  </select>
                </div>

                <div>
                  <label class="block text-neutral-500 text-sm mb-1">型号</label>
                  <input
                    v-model="recognized.model"
                    type="text"
                    class="w-full border border-neutral-300 rounded-lg px-3 py-2.5 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
                  />
                </div>

                <div>
                  <label class="block text-neutral-500 text-sm mb-1">存储容量</label>
                  <select v-model="recognized.storage"
                    class="w-full border border-neutral-300 rounded-lg px-3 py-2.5 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none">
                    <option value="64">64GB</option>
                    <option value="128">128GB</option>
                    <option value="256">256GB</option>
                    <option value="512">512GB</option>
                    <option value="1024">1TB</option>
                  </select>
                </div>

                <div>
                  <label class="block text-neutral-500 text-sm mb-1">大致成色</label>
                  <div class="flex space-x-3">
                    <label class="flex items-center space-x-1 cursor-pointer" v-for="c in [99,95,90,85,80]" :key="c">
                      <input
                        type="radio"
                        name="condition"
                        :value="c"
                        v-model="recognized.condition"
                        class="text-primary focus:ring-primary"
                      />
                      <span>{{ c }}新</span>
                    </label>
                  </div>
                </div>

                <div class="flex items-center text-sm text-neutral-500">
                  <i class="fas fa-check-circle text-primary mr-1"></i>
                  <span>识别置信度: {{ recognized.confidence }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 3 -->
        <div v-show="currentStep === 3" class="step-content">
          <div class="text-center mb-8">
            <h4 class="text-lg font-semibold text-neutral-700 mb-2">填写上架信息</h4>
            <p class="text-neutral-500 max-w-lg mx-auto">
              请完善商品信息，准确的描述可以提高商品的销售速度
            </p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- 左侧图片与摘要 -->
            <div class="md:col-span-1">
              <h5 class="font-medium text-neutral-700 mb-3">商品图片</h5>
              <div class="grid grid-cols-2 gap-2 mb-4">
                <img
                  v-for="(src, idx) in previews.slice(0, 4)"
                  :key="idx"
                  :src="src"
                  alt="商品图片预览"
                  class="w-full aspect-square object-cover rounded-lg border border-neutral-200"
                />
              </div>

              <div class="bg-neutral-50 border border-neutral-200 rounded-xl p-4 mt-6">
                <h5 class="font-medium text-neutral-700 mb-3">商品摘要</h5>
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between">
                    <span class="text-neutral-500">品类:</span>
                    <span class="text-neutral-700">{{ categoryText }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-neutral-500">品牌型号:</span>
                    <span class="text-neutral-700">{{ modelText }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-neutral-500">存储容量:</span>
                    <span class="text-neutral-700">{{ recognized.storage }}GB</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-neutral-500">成色:</span>
                    <span class="text-neutral-700">{{ recognized.condition }}新</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 右侧表单 -->
            <div class="md:col-span-2 space-y-5">
              <div>
                <label class="block text-neutral-500 text-sm mb-1">商品标题</label>
                <input
                  v-model="form.title"
                  type="text"
                  class="w-full border border-neutral-300 rounded-lg px-3 py-2.5 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
                />
                <p class="text-neutral-500 text-xs mt-1">请包含关键信息，如品牌、型号、配置、成色等</p>
              </div>

              <div>
                <label class="block text-neutral-500 text-sm mb-1">商品描述</label>
                <textarea
                  v-model="form.description"
                  rows="5"
                  class="w-full border border-neutral-300 rounded-lg px-3 py-2.5 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
                  placeholder="请详细描述商品情况，包括使用时长、有无维修史、功能是否正常、外观是否有划痕等..."
                ></textarea>
              </div>

              <div>
                <label class="block text-neutral-500 text-sm mb-1">售卖金额</label>
                <div class="flex items-center">
                  <span class="bg-neutral-100 text-neutral-700 px-3 py-2.5 rounded-l-lg border border-r-0 border-neutral-300">¥</span>
                  <input
                    v-model="form.price"
                    type="number"
                    class="flex-1 border border-neutral-300 px-3 py-2.5 focus:border-primary focus:ring-1 focus:ring-primary focus:outline-none"
                    placeholder="请输入价格"
                  />
                  <span class="bg-neutral-100 text-neutral-700 px-3 py-2.5 rounded-r-lg border border-l-0 border-neutral-300">元</span>
                </div>

                <div class="mt-2 flex items-center text-sm text-primary">
                  <i class="fas fa-lightbulb mr-1"></i>
                  <span>建议售价：¥5,000 - ¥5,500</span>
                </div>
              </div>

              <div v-if="submitError" class="text-danger text-sm">{{ submitError }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div class="p-6 border-t border-neutral-200 bg-white sticky bottom-0">
        <div class="flex justify-between items-center">
          <button
            class="bg-white border border-neutral-300 text-neutral-700 px-6 py-2.5 rounded-lg hover:bg-neutral-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="currentStep === 1 || submitting"
            @click="prev"
          >
            <i class="fas fa-arrow-left mr-2"></i>上一步
          </button>

          <button
            v-if="currentStep < 3"
            class="bg-primary text-white px-6 py-2.5 rounded-lg hover:bg-primary/90 transition-colors"
            :disabled="submitting"
            @click="next"
          >
            下一步<i class="fas fa-arrow-right ml-2"></i>
          </button>

          <button
            v-else
            class="bg-success text-white px-6 py-2.5 rounded-lg hover:bg-success/90 transition-colors"
            :disabled="submitting"
            @click="confirm"
          >
            <i :class="submitting ? 'fas fa-spinner fa-spin mr-2' : 'fas fa-check mr-2'"></i>
            {{ submitting ? "提交中..." : "确认上架" }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Toast -->
  <div
    class="fixed top-4 right-4 bg-success text-white px-4 py-3 rounded-lg shadow-lg flex items-center transform transition-transform duration-300 z-50"
    :class="toastVisible ? 'translate-x-0' : 'translate-x-full'"
  >
    <i class="fas fa-check-circle mr-2"></i>
    <span>商品上架成功！</span>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{
  (e: "close"): void;
  // 提交成功后通知父组件刷新列表
  (e: "success"): void;
}>();

const currentStep = ref<1 | 2 | 3>(1);
const submitting = ref(false);
const submitError = ref("");

const dragActive = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const previews = ref<string[]>([]);
const stepError = ref("");

type Recognized = {
  category: string;
  brand: string;
  model: string;
  storage: string;
  condition: number;
  confidence: number;
};

const recognizeState = ref<"loading" | "error" | "success">("loading");
const recognized = reactive<Recognized>({
  category: "phone",
  brand: "apple",
  model: "iPhone 13 Pro",
  storage: "256",
  condition: 95,
  confidence: 92,
});

const form = reactive({
  title: "iPhone 13 Pro 256GB 星光色 95新",
  description: "",
  price: "",
});

const toastVisible = ref(false);

const progressWidth = computed(() => `${(currentStep.value - 1) * 50}%`);

const categoryText = computed(() => {
  const map: any = { phone: "手机", laptop: "笔记本电脑", tablet: "平板电脑", watch: "智能手表", headphones: "耳机" };
  return map[recognized.category] || "未知";
});
const modelText = computed(() => {
  const brandMap: any = { apple: "Apple", huawei: "华为", xiaomi: "小米", samsung: "三星", oppo: "OPPO", vivo: "vivo" };
  return `${brandMap[recognized.brand] || recognized.brand} ${recognized.model}`.trim();
});

watch(
  () => props.open,
  (v) => {
    if (v) resetAll();
  }
);

function resetAll() {
  currentStep.value = 1;
  previews.value = [];
  stepError.value = "";
  submitError.value = "";
  submitting.value = false;
  recognizeState.value = "loading";
  toastVisible.value = false;
}

function close() {
  emit("close");
}

function stepClass(step: number) {
  if (currentStep.value === step) return "step-active";
  if (currentStep.value > step) return "step-completed";
  return "step-pending";
}
function stepTextClass(step: number) {
  if (currentStep.value >= step) return "text-primary";
  return "text-neutral-500";
}

function pickFiles() {
  fileInput.value?.click();
}

function onDrop(e: DragEvent) {
  dragActive.value = false;
  if (!e.dataTransfer?.files) return;
  handleFiles(e.dataTransfer.files);
}

function onFileChange(e: Event) {
  const files = (e.target as HTMLInputElement).files;
  if (!files) return;
  handleFiles(files);
  (e.target as HTMLInputElement).value = "";
}

function handleFiles(files: FileList) {
  const imgFiles = Array.from(files)
    .filter((f) => f.type.startsWith("image/"))
    .slice(0, 5);

  previews.value = [];
  imgFiles.forEach((file) => {
    previews.value.push(URL.createObjectURL(file));
  });
}

function removePreview(idx: number) {
  previews.value.splice(idx, 1);
}

function next() {
  stepError.value = "";
  submitError.value = "";

  if (currentStep.value === 1) {
    if (previews.value.length === 0) {
      stepError.value = "请先上传至少一张商品图片";
      return;
    }
    currentStep.value = 2;
    simulateRecognition();
    return;
  }

  if (currentStep.value === 2) {
    // 识别失败则不能进入第三步（你要求“识别不到提示回到第一步”）
    if (recognizeState.value !== "success") {
      recognizeState.value = "error";
      return;
    }
    // 进入 step3 时把标题按识别结果自动填一份（可改）
    if (!form.title) {
      form.title = `${recognized.model} ${recognized.storage}GB ${recognized.condition}新`;
    }
    currentStep.value = 3;
  }
}

function prev() {
  submitError.value = "";
  if (currentStep.value > 1) currentStep.value = (currentStep.value - 1) as any;
}

function goStep(step: 1 | 2 | 3) {
  currentStep.value = step;
}

function simulateRecognition() {
  recognizeState.value = "loading";

  setTimeout(() => {
    // 这里保持和原 HTML 一样：有概率失败；你接真实识别接口后换成真实逻辑
    const ok = Math.random() > 0.2;
    recognizeState.value = ok ? "success" : "error";
  }, 1200);
}

async function confirm() {
  submitError.value = "";

  if (!form.title.trim()) {
    submitError.value = "请填写商品标题";
    return;
  }
  if (!form.price || Number(form.price) <= 0) {
    submitError.value = "请输入有效价格";
    return;
  }

  submitting.value = true;
  try {
    // TODO: 替换为真实上架 API
    await new Promise((r) => setTimeout(r, 900));

    toastVisible.value = true;
    emit("success");

    // 让 toast 显示一下再关闭抽屉（保持 a.html 的体验）
    setTimeout(() => {
      close();
      setTimeout(() => (toastVisible.value = false), 1500);
    }, 700);
  } finally {
    submitting.value = false;
  }
}
</script>