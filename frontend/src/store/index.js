// import { createStore } from "vuex";

// export default createStore({
//   state: {},
//   getters: {},
//   mutations: {},
//   actions: {},
//   modules: {},
// });


import { createStore } from 'vuex'
import user from './modules/user'
import interview from './modules/interview'
import learning from './modules/learning'
import getters from './getters'

export default createStore({
  getters,
  modules: {
    user,
    interview,
    learning
  },
  // 开发模式下开启严格模式
  strict: process.env.NODE_ENV !== 'production'
})
