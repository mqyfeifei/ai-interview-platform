<template>
  <div class="voice-mic-demo">
    <div class="controls">
      <button @click="startRecording" :disabled="recording">开始</button>
      <button @click="stopRecording" :disabled="!recording">结束</button>
      <span class="status">{{ statusText }}</span>
    </div>
    <textarea v-model="liveText" placeholder="识别文本会实时显示在这里..." rows="6"></textarea>
    <div class="log">{{ logText }}</div>
  </div>
</template>

<script>
export default {
  name: 'VoiceMic',
  emits: ['partial','final','error'],
  data() {
    return {
      socket: null,
      recording: false,
      audioContext: null,
      input: null,
      processor: null,
      globalStream: null,
      sampleRate: 16000,
      sendSeq: 0,
      voiceId: null,
      lastSendTs: 0,
      MIN_SEND_INTERVAL_MS: 80,
      ENABLE_VAD: true,
      VAD_THRESHOLD: 0.0015,
      liveText: '',
      logText: ''
    }
  },
  computed: {
    statusText(){
      return this.recording ? '录音中...' : '空闲'
    }
  },
  mounted(){
    this.loadSocketIO()
  },
  beforeUnmount(){
    this.disconnectSocket()
    this.stopRecording()
  },
  methods: {
    log(msg){
      this.logText = new Date().toLocaleTimeString() + ' ' + msg + '\n' + this.logText
    },
    ensureSocket(){
      if(window.io){
        const SERVER_URL = (location.hostname === 'localhost') ? 'http://localhost:5000' : (location.origin || 'http://localhost:5000')
        this.socket = window.io(SERVER_URL, { transports: ['websocket'] })
        this.socket.on('connect', ()=>{ this.log('socket connected') })
        this.socket.on('disconnect', ()=>{ this.log('socket disconnected') })
        this.socket.on('asr_partial', (d)=>{ this.liveText = d.text; this.$emit('partial', d) })
        this.socket.on('asr_final', (d)=>{ this.liveText = d.text; this.$emit('final', d) })
        this.socket.on('asr_error', (d)=>{ this.log('server error: '+JSON.stringify(d)); this.$emit('error', d) })
      }
    },
    loadSocketIO(){
      if(window.io) { this.ensureSocket(); return }
      // dynamically load CDN
      const s = document.createElement('script')
      s.src = 'https://cdn.socket.io/4.7.2/socket.io.min.js'
      s.onload = ()=>{ this.ensureSocket(); this.log('loaded socket.io client') }
      s.onerror = ()=>{ this.log('failed to load socket.io client') }
      document.head.appendChild(s)
    },
    disconnectSocket(){
      try{ this.socket && this.socket.disconnect(); }catch(e){}
      this.socket = null
    },
    downsampleBuffer(buffer, inputSampleRate, outSampleRate){
      if(outSampleRate === inputSampleRate) return buffer
      const sampleRateRatio = inputSampleRate / outSampleRate
      const newLength = Math.round(buffer.length / sampleRateRatio)
      const result = new Float32Array(newLength)
      let offsetResult = 0, offsetBuffer = 0
      while(offsetResult < result.length){
        const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio)
        let accum = 0, count = 0
        for(let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++){ accum += buffer[i]; count++ }
        result[offsetResult] = count ? accum / count : 0
        offsetResult++
        offsetBuffer = nextOffsetBuffer
      }
      return result
    },
    floatTo16BitPCM(float32Array){
      const l = float32Array.length
      const buf = new ArrayBuffer(l * 2)
      const view = new DataView(buf)
      let offset = 0
      for(let i=0;i<l;i++, offset+=2){
        let s = Math.max(-1, Math.min(1, float32Array[i]))
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
      }
      return buf
    },
    arrayBufferToBase64(buffer){
      let binary = ''
      const bytes = new Uint8Array(buffer)
      const chunkSize = 0x8000
      for(let i=0;i<bytes.length;i+=chunkSize){
        const chunk = bytes.subarray(i, i+chunkSize)
        binary += String.fromCharCode.apply(null, chunk)
      }
      return btoa(binary)
    },
    sendChunkImmediate(float32Chunk){
      const now = Date.now()
      if(now - this.lastSendTs < this.MIN_SEND_INTERVAL_MS) return
      this.lastSendTs = now
      if(this.ENABLE_VAD){
        let sum = 0; for(let i=0;i<float32Chunk.length;i++) sum += float32Chunk[i]*float32Chunk[i]
        const rms = Math.sqrt(sum/float32Chunk.length)
        if(rms < this.VAD_THRESHOLD) return
      }
      const inputSampleRate = this.audioContext.sampleRate
      const out = this.downsampleBuffer(float32Chunk, inputSampleRate, this.sampleRate)
      const pcm16Buffer = this.floatTo16BitPCM(out)
      const b64 = this.arrayBufferToBase64(pcm16Buffer)
      const payload = { voice_id: this.voiceId, seq: this.sendSeq++, chunk_b64: b64, is_end: 0 }
      try{ this.socket && this.socket.emit('audio_chunk', payload); this.log('sent seq='+ (this.sendSeq-1)) }catch(e){ this.log('socket emit err '+e) }
    },
    async startRecording(){
      if(this.recording) return
      try{
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
        this.globalStream = stream
        this.input = this.audioContext.createMediaStreamSource(stream)
        const bufferSize = 2048
        this.processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1)
        this.processor.onaudioprocess = (e)=>{
          const floatData = e.inputBuffer.getChannelData(0)
          this.sendChunkImmediate(new Float32Array(floatData))
        }
        this.input.connect(this.processor)
        this.processor.connect(this.audioContext.destination)
        this.voiceId = 'v_' + Date.now()
        this.sendSeq = 0
        this.lastSendTs = 0
        this.recording = true
        this.log('recording started voiceId='+this.voiceId)
      }catch(err){ this.log('startRecording error '+err); this.$emit('error', err) }
    },
    stopRecording(){
      if(!this.recording) return
      try{ if(this.processor){ this.processor.disconnect(); this.processor.onaudioprocess=null; this.processor=null } }catch(e){}
      try{ if(this.input){ this.input.disconnect(); this.input=null } }catch(e){}
      try{ if(this.audioContext){ this.audioContext.close(); this.audioContext=null } }catch(e){}
      try{ this.globalStream && this.globalStream.getTracks().forEach(t=>t.stop()) }catch(e){}
      this.recording = false
      const payload = { voice_id: this.voiceId, seq: this.sendSeq++, chunk_b64: '', is_end: 1 }
      try{ this.socket && this.socket.emit('audio_chunk', payload); this.log('sent final packet') }catch(e){ this.log('final emit error '+e) }
    }
  }
}
</script>

<style scoped>
.voice-mic-demo { border: 1px solid #eee; padding: 12px; border-radius: 6px }
.controls { margin-bottom: 8px }
.controls button { margin-right: 6px }
textarea { width: 100%; font-size: 14px }
.log { margin-top: 8px; white-space: pre-wrap; color: #666 }
</style>
