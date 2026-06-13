import request from './request'

export async function getHealth() {
  const { data } = await request.get('/health')
  return data
}
