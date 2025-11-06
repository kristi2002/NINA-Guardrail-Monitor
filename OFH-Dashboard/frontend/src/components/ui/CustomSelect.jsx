import { useState, useEffect, useRef } from 'react'
import './CustomSelect.css'

function CustomSelect({ options = [], value, onChange, placeholder = 'Seleziona...', className = '' }) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedLabel, setSelectedLabel] = useState('')
  const selectRef = useRef(null)

  // Find the selected option label and style
  const selectedOption = options.find(opt => opt.value === value)
  const selectedColor = selectedOption?.color || null
  const selectedClassName = selectedOption?.className || ''
  
  useEffect(() => {
    const option = options.find(opt => opt.value === value)
    setSelectedLabel(option ? option.label : placeholder)
  }, [value, options, placeholder])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (selectRef.current && !selectRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleSelect = (optionValue) => {
    onChange(optionValue)
    setIsOpen(false)
  }

  return (
    <div className={`custom-select ${className} ${isOpen ? 'open' : ''}`} ref={selectRef}>
      <div 
        className="custom-select-trigger"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className={`custom-select-value ${selectedClassName}`} style={selectedColor ? { color: selectedColor } : {}}>
          {selectedLabel}
        </span>
        <span className={`custom-select-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </div>
      
      <div className="custom-select-options">
        {options.map((option) => {
          const optionStyle = option.color ? { color: option.color } : {};
          const optionClass = option.className ? ` ${option.className}` : '';
          return (
            <div
              key={option.value}
              className={`custom-select-option ${value === option.value ? 'selected' : ''}${optionClass}`}
              style={optionStyle}
              onClick={() => handleSelect(option.value)}
            >
              {option.label}
            </div>
          );
        })}
      </div>
    </div>
  )
}

export default CustomSelect

