<template>
  <div class="voice-mic-page">
    <h2>实时语音输入组件 Demo</h2>
    <VoiceMic @partial="onPartial" @final="onFinal" @error="onError" />
    <div style="margin-top:12px">
      <p>实时文本：</p>
      <pre>{{ live }}</pre>
    </div>
  </div>
</template>

<script>
import VoiceMic from '@/components/interview/VoiceMic.vue'
export default {
  name: 'VoiceMicDemo',
  components: { VoiceMic },
  data(){ return { live: '' } },
  methods:{
    onPartial(d){ this.live = d.text },
    onFinal(d){ this.live = d.text },
    onError(e){ console.error('mic error', e) }
  }
}
</script>

<style scoped>
pre{ background:#fafafa; padding:12px; border-radius:6px }
</style>
