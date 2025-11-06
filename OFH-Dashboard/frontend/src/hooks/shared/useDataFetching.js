/**
 * Shared data fetching hook with abort controller support
 */
import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

export function useDataFetching(fetchFunction, dependencies = [], options = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const abortControllerRef = useRef(null)

  useEffect(() => {
    const controller = new AbortController()
    abortControllerRef.current = controller
    const signal = controller.signal

    const loadData = async () => {
      try {
        setLoading(true)
        setError(null)
        const result = await fetchFunction(signal)
        setData(result)
      } catch (err) {
        if (err.name !== 'CanceledError' && !axios.isCancel(err)) {
          setError(err)
          console.error('Data fetching error:', err)
        }
      } finally {
        setLoading(false)
      }
    }

    loadData()

    return () => {
      controller.abort()
    }
  }, dependencies)

  return { data, loading, error, refetch: () => fetchFunction(abortControllerRef.current?.signal) }
}

