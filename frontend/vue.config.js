// const { defineConfig } = require("@vue/cli-service");
// module.exports = defineConfig({
//   transpileDependencies: true,
// });
const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 8080,
    proxy: {
      // 后端API代理配置 - 对接后端时只需修改target即可
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        // 若后端路由包含/api前缀则不需要rewrite，否则开启
        // pathRewrite: { '^/api': '' }
      }
    }
  },
  css: {
    loaderOptions: {
      sass: {
        // 全局注入SCSS变量，所有组件均可直接使用
        additionalData: `@import "@/assets/styles/variables.scss";`
      }
    }
  },
   lintOnSave: false
})