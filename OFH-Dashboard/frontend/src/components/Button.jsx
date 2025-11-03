/**
 * Modern Button Component with utility classes
 */

import React, { memo, forwardRef } from 'react';
import './Button.css';

const Button = memo(forwardRef(({
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
  ...props
}, ref) => {
  const baseClasses = 'btn';
  const variantClasses = `btn-${variant}`;
  const sizeClasses = `btn-${size}`;
  const widthClasses = fullWidth ? 'w-full' : '';
  const disabledClasses = disabled || loading ? 'btn-disabled' : '';
  const loadingClasses = loading ? 'btn-loading' : '';

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

  const renderIcon = () => {
    if (!icon) return null;
    
    const iconElement = typeof icon === 'string' ? (
      <span className="btn-icon-text">{icon}</span>
    ) : (
      icon
    );

    return (
      <span className={`btn-icon ${iconPosition === 'right' ? 'btn-icon-right' : 'btn-icon-left'}`}>
        {iconElement}
      </span>
    );
  };

  const renderLoadingSpinner = () => {
    if (!loading) return null;
    
    return (
      <span className="btn-loading-spinner">
        <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25" />
          <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" className="opacity-75" />
        </svg>
      </span>
    );
  };

  return (
    <button
      ref={ref}
      type={type}
      className={buttonClasses}
      onClick={handleClick}
      disabled={disabled || loading}
      {...props}
    >
      {renderLoadingSpinner()}
      {icon && iconPosition === 'left' && renderIcon()}
      {children && (
        <span className="btn-content">
          {children}
        </span>
      )}
      {icon && iconPosition === 'right' && renderIcon()}
    </button>
  );
}));

Button.displayName = 'Button';

export default Button;

