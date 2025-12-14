<template>
  <!-- Drawer -->
  <div
    v-if="open"
    class="fixed top-0 right-0 bottom-0 left-[16rem] bg-black/50 z-50 flex items-center justify-center p-6"
    @click.self="close"
  >
    <div
      class="bg-white w-[90%] max-w-4xl max-h-[81vh] rounded-2xl shadow-modal flex flex-col"
    >
      <!-- Header -->
      <div class="p-6 border-b border-neutral-200 flex justify-between items-center">
        <h3 class="text-xl font-bold text-neutral-700">上架新商品</h3>
        <button @click="close" class="text-neutral-500 hover:text-neutral-700">
          <i class="fas fa-times text-xl"></i>
        </button>
      </div>

      <!-- Steps -->
      <div class="px-6 pt-6 pb-2">
        <div class="flex justify-between items-center relative">
          <div class="absolute left-0 right-0 top-1/2 h-1 bg-neutral-200 -translate-y-1/2"></div>
          <div
            class="absolute left-0 top-1/2 h-1 bg-primary -translate-y-1/2 transition-all"
            :style="{ width: progressWidth }"
          ></div>

          <StepDot :active="currentStep>=1" :done="currentStep>1" label="上传图片" />
          <StepDot :active="currentStep>=2" :done="currentStep>2" label="识别确认" />
          <StepDot :active="currentStep>=3" label="填写信息" />
        </div>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-6">

        <!-- STEP 1 -->
        <div v-show="currentStep===1">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Left -->
            <div>
              <div v-if="previews.length" class="mb-4 grid grid-cols-4 gap-3">
                <div v-for="(src,i) in previews" :key="i" class="relative">
                  <img :src="src" class="rounded-lg border" />
                  <span v-if="i===0" class="absolute top-1 left-1 text-xs bg-primary text-white px-1 rounded">主图</span>
                </div>
              </div>

              <div
                class="border-2 border-dashed border-neutral-300 rounded-xl p-6 text-center cursor-pointer"
                @click="pickFiles"
              >
                <i class="fas fa-cloud-upload-alt text-4xl text-primary mb-3"></i>
                <p class="text-neutral-600">点击选择图片（最多4张）</p>
                <input
                  ref="fileInput"
                  type="file"
                  multiple
                  accept="image/jpeg,image/png"
                  class="hidden"
                  @change="onFileChange"
                />
              </div>

              <div v-if="stepError" class="text-danger mt-3 text-sm">{{ stepError }}</div>
            </div>

            <!-- Right -->
            <div class="border rounded-xl p-5">
              <FormRow label="产品类别">
                <select v-model="draftMeta.category_id" class="form-input">
                  <option value="">请选择</option>
                  <option v-for="c in categories" :key="c.id" :value="c.id">{{c.name}}</option>
                </select>
              </FormRow>

              <FormRow label="产品型号">
                <select v-model="draftMeta.device_model_id" class="form-input">
                  <option value="">请选择</option>
                  <option v-for="m in models" :key="m.id" :value="m.id">{{m.name}}</option>
                </select>
              </FormRow>

              <FormRow label="使用年限">
                <input v-model="draftMeta.years_used" type="number" step="0.5" class="form-input" />
              </FormRow>

              <FormRow label="原始价格">
                <input v-model="draftMeta.original_price" type="number" class="form-input" />
              </FormRow>
            </div>
          </div>
        </div>

        <!-- STEP 2 -->
        <div v-show="currentStep===2" class="text-center py-10">
          <div v-if="loading">
            <div class="loader mb-3"></div>
            正在识别商品图片...
          </div>

          <div v-else>
            <div class="text-lg font-semibold mb-4">{{ analyze.grade_label }}</div>
            <div class="mb-3 text-neutral-700">成色评分：{{ analyze.grade_score }}</div>

            <div class="text-danger space-y-1">
              <div v-for="(d,i) in analyze.defects" :key="i">{{d}}</div>
            </div>
          </div>
        </div>

        <!-- STEP 3 -->
        <div v-show="currentStep===3">
          <FormRow label="商品标题">
            <input v-model="form.title" class="form-input" />
          </FormRow>

          <FormRow label="商品描述">
            <textarea v-model="form.description" rows="4" class="form-input"></textarea>
          </FormRow>

          <FormRow label="售卖价格">
            <input v-model="form.price" type="number" class="form-input" />
          </FormRow>

          <div v-if="submitError" class="text-danger mt-2">{{submitError}}</div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-6 border-t flex justify-between">
        <button @click="prev" :disabled="currentStep===1" class="btn">上一步</button>

        <button v-if="currentStep<3" @click="next" class="btn-primary">下一步</button>
        <button v-else @click="publish" class="btn-success">确认上架</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from "vue";
import { initDraft, uploadDraftImage, analyzeDraft, publishDraft } from "@/api/market";

const props = defineProps<{ open:boolean }>();
const emit = defineEmits(["close","success"]);

const currentStep = ref(1);
const loading = ref(false);
const stepError = ref("");
const submitError = ref("");

const fileInput = ref<HTMLInputElement|null>(null);
const files = ref<File[]>([]);
const previews = ref<string[]>([]);

const draftKey = ref("");

const draftMeta = reactive({
  category_id: "",
  device_model_id: "",
  years_used: "",
  original_price: ""
});

const analyze = reactive({
  grade_label: "",
  grade_score: 0,
  defects: [] as string[]
});

const form = reactive({
  title: "",
  description: "",
  price: ""
});

const categories = [
  {id:1,name:"手机"},{id:2,name:"电脑"},{id:3,name:"平板"},
  {id:4,name:"智能手表"},{id:5,name:"耳机"},
  {id:6,name:"无人机"},{id:7,name:"相机"},
  {id:8,name:"游戏机"},{id:9,name:"其他"}
];

const models = [
  {id:1,name:"iPhone 16"},{id:2,name:"iPhone 15"},
  {id:3,name:"MacBook Pro 14"},{id:4,name:"Switch"}
];

const progressWidth = computed(()=>`${(currentStep.value-1)*50}%`);

function pickFiles(){ fileInput.value?.click(); }

function onFileChange(e:any){
  const list = Array.from(e.target.files).slice(0,4) as File[];
  files.value = list;
  previews.value = list.map(f=>URL.createObjectURL(f));
}

async function next(){
  stepError.value="";

  if(currentStep.value===1){
    if(!files.value.length) return stepError.value="请上传图片";
    const { draft_key } = await initDraft({
      category_id:Number(draftMeta.category_id),
      device_model_id:Number(draftMeta.device_model_id),
      years_used:Number(draftMeta.years_used),
      original_price:Number(draftMeta.original_price)
    });
    draftKey.value = draft_key;
    for(const f of files.value){
      await uploadDraftImage(draft_key,f);
    }
    loading.value=true;
    currentStep.value=2;
    const res = await analyzeDraft(draft_key);
    Object.assign(analyze,res);
    loading.value=false;
    return;
  }

  if(currentStep.value===2){
    currentStep.value=3;
  }
}

function prev(){ currentStep.value--; }

async function publish(){
  if(!form.title || !form.price){
    submitError.value="请填写完整信息"; return;
  }
  await publishDraft(draftKey.value,{
    title:form.title,
    description:form.description,
    selling_price:Number(form.price)
  });
  emit("success");
  emit("close");
}

function close(){ emit("close"); }
</script>

<style scoped>
.form-input{ @apply w-full border rounded px-3 py-2; }
.btn{ @apply border px-4 py-2 rounded; }
.btn-primary{ @apply bg-primary text-white px-4 py-2 rounded; }
.btn-success{ @apply bg-success text-white px-4 py-2 rounded; }
.loader{ width:40px;height:40px;border:4px solid #eee;border-top-color:#3b82f6;border-radius:50%;animation:spin 1s linear infinite;}
@keyframes spin{to{transform:rotate(360deg)}}
</style>