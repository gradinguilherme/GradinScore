const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function tratar(resposta) {
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}))
    throw new Error(corpo.detail || `Erro ${resposta.status} ao falar com o servidor.`)
  }
  return resposta.json()
}

export async function getLigas() {
  return tratar(await fetch(`${API_URL}/ligas`))
}

export async function getTimes(idLiga, busca) {
  const params = busca ? `?q=${encodeURIComponent(busca)}` : ''
  return tratar(await fetch(`${API_URL}/ligas/${idLiga}/times${params}`))
}

export async function gerarAnalise(pedido) {
  return tratar(
    await fetch(`${API_URL}/analise`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pedido),
    })
  )
}

export async function getHistorico() {
  return tratar(await fetch(`${API_URL}/analises`))
}
