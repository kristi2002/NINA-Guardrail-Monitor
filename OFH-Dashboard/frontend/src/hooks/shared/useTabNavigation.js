/**
 * Shared tab navigation hook
 */
import { useState, useRef, useEffect } from 'react'

export function useTabNavigation(initialTab, onTabChange = null) {
  const [activeTab, setActiveTab] = useState(initialTab)
  const prevActiveTab = useRef(initialTab)

  const handleTabClick = (tabId) => {
    if (tabId === activeTab) return
    setActiveTab(tabId)
  }

  useEffect(() => {
    if (prevActiveTab.current !== activeTab && onTabChange) {
      onTabChange(activeTab, prevActiveTab.current)
    }
    prevActiveTab.current = activeTab
  }, [activeTab, onTabChange])

  return { activeTab, handleTabClick, setActiveTab }
}

