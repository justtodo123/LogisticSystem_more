import { ref } from 'vue'

/** 登录页密码框焦点状态（Owl 遮眼动画） */
export function useFocus() {
  const isFocus = ref(false)

  function handleBlur() {
    isFocus.value = false
  }

  function handleFocus() {
    isFocus.value = true
  }

  return { isFocus, handleBlur, handleFocus }
}
