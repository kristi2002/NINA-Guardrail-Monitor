/**
 * Accessible Button Component with ARIA support
 */

import React, { memo, forwardRef } from 'react';
import './AccessibleButton.css';

const AccessibleButton = memo(forwardRef(({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  className = '',
  onClick,
  type = 'button',
  // Accessibility props
  ariaLabel,
  ariaDescribedBy,
  ariaExpanded,
  ariaControls,
  ariaPressed,
  ariaCurrent,
  ariaLive,
  role,
  tabIndex,
  // Keyboard navigation
  onKeyDown,
  onKeyUp,
  onFocus,
  onBlur,
  // Screen reader support
  screenReaderText,
  ...props
}, ref) => {
  const baseClasses = 'accessible-btn';
  const variantClasses = `accessible-btn-${variant}`;
  const sizeClasses = `accessible-btn-${size}`;
  const widthClasses = fullWidth ? 'w-full' : '';
  const disabledClasses = disabled || loading ? 'accessible-btn-disabled' : '';
  const loadingClasses = loading ? 'accessible-btn-loading' : '';

  const buttonClasses = [
    baseClasses,
    variantClasses,
    sizeClasses,
    widthClasses,
    disabledClasses,
    loadingClasses,
    className
  ].filter(Boolean).join(' ');

  const handleClick = (e) => {
    if (disabled || loading) {
      e.preventDefault();
      return;
    }
    onClick?.(e);
  };

  const handleKeyDown = (e) => {
    // Handle Enter and Space key activation
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick(e);
    }
    onKeyDown?.(e);
  };

  const renderIcon = () => {
    if (!icon) return null;
    
    const iconElement = typeof icon === 'string' ? (
      <span className="accessible-btn-icon-text" aria-hidden="true">{icon}</span>
    ) : (
      React.cloneElement(icon, { 'aria-hidden': true })
    );

    return (
      <span className={`accessible-btn-icon ${iconPosition === 'right' ? 'accessible-btn-icon-right' : 'accessible-btn-icon-left'}`}>
        {iconElement}
      </span>
    );
  };

  const renderLoadingSpinner = () => {
    if (!loading) return null;
    
    return (
      <span className="accessible-btn-loading-spinner" aria-hidden="true">
        <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25" />
          <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" className="opacity-75" />
        </svg>
      </span>
    );
  };

  const renderScreenReaderText = () => {
    if (!screenReaderText) return null;
    
    return (
      <span className="sr-only">
        {screenReaderText}
      </span>
    );
  };

  return (
    <button
      ref={ref}
      type={type}
      className={buttonClasses}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onKeyUp={onKeyUp}
      onFocus={onFocus}
      onBlur={onBlur}
      disabled={disabled || loading}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      aria-expanded={ariaExpanded}
      aria-controls={ariaControls}
      aria-pressed={ariaPressed}
      aria-current={ariaCurrent}
      aria-live={ariaLive}
      role={role}
      tabIndex={tabIndex}
      {...props}
    >
      {renderLoadingSpinner()}
      {icon && iconPosition === 'left' && renderIcon()}
      {children && (
        <span className="accessible-btn-content">
          {children}
        </span>
      )}
      {icon && iconPosition === 'right' && renderIcon()}
      {renderScreenReaderText()}
    </button>
  );
}));

AccessibleButton.displayName = 'AccessibleButton';

export default AccessibleButton;

