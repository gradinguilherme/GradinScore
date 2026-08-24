import { useState, useEffect, useRef } from 'react'
import { getTimes } from '../api.js'

export default function TeamSearch({ idLiga, label, ajuda, selecionado, onSelecionar, disabled }) {
  const [termo, setTermo] = useState('')
  const [resultados, setResultados] = useState([])
  const [aberto, setAberto] = useState(false)
  const timeoutRef = useRef(null)

  useEffect(() => {
    setTermo('')
    setResultados([])
  }, [idLiga])

  function onChangeTexto(valor) {
    setTermo(valor)
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    if (!valor || valor.length < 2) {
      setResultados([])
      return
    }
    timeoutRef.current = setTimeout(async () => {
      try {
        const dados = await getTimes(idLiga, valor)
        setResultados(dados)
        setAberto(true)
      } catch {
        setResultados([])
      }
    }, 300)
  }

  if (selecionado) {
    return (
      <div className="campo">
        <label>{label}</label>
        <div className="time-selecionado">
          <span>{selecionado.nome}</span>
          <button
            type="button"
            onClick={() => onSelecionar(null)}
            aria-label={`Remover ${selecionado.nome}`}
            disabled={disabled}
          >
            ×
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="campo">
      <label htmlFor={`busca-${label}`}>{label}</label>
      <div className="busca-time">
        <input
          id={`busca-${label}`}
          type="text"
          value={termo}
          disabled={disabled}
          placeholder="Digite ao menos 2 letras…"
          onChange={(e) => onChangeTexto(e.target.value)}
          onFocus={() => resultados.length > 0 && setAberto(true)}
          onBlur={() => setTimeout(() => setAberto(false), 150)}
          autoComplete="off"
        />
        {aberto && resultados.length > 0 && (
          <div className="busca-resultados">
            {resultados.map((t) => (
              <div
                key={t.id_api}
                className="busca-resultado-item"
                onMouseDown={() => {
                  onSelecionar(t)
                  setAberto(false)
                }}
              >
                <span>{t.nome}</span>
                <span style={{ color: 'var(--chalk-dim)' }}>{t.pais}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      {ajuda && <p className="campo-ajuda">{ajuda}</p>}
    </div>
  )
}
