export const getQueryParam = (key: string) =>
  new URLSearchParams(window.location.search).get(key)

export const removeQueryParam = (key: string) => {
  const url = new URL(window.location.href)
  url.searchParams.delete(key)
  window.history.replaceState({}, '', url.toString())
}
