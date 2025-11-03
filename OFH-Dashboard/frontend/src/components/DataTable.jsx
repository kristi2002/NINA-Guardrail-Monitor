/**
 * Performance-optimized Data Table Component
 */

import React, { memo, useMemo, useCallback, useState, useRef, useEffect } from 'react';
import './DataTable.css';

const DataTable = memo(({
  data = [],
  columns = [],
  onRowClick,
  onSort,
  onFilter,
  loading = false,
  emptyMessage = 'No data available',
  pageSize = 10,
  enablePagination = true,
  enableSorting = true,
  enableFiltering = true,
  enableSelection = false,
  selectedRows = [],
  onSelectionChange,
  className = '',
  ...props
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [filterConfig, setFilterConfig] = useState({});
  const [selectedRowsInternal, setSelectedRowsInternal] = useState(selectedRows);
  const tableRef = useRef(null);

  // Memoize filtered and sorted data
  const processedData = useMemo(() => {
    let result = [...data];

    // Apply filters
    if (enableFiltering && Object.keys(filterConfig).length > 0) {
      result = result.filter(row => {
        return Object.entries(filterConfig).every(([key, value]) => {
          if (!value) return true;
          const cellValue = row[key];
          if (typeof cellValue === 'string') {
            return cellValue.toLowerCase().includes(value.toLowerCase());
          }
          return cellValue === value;
        });
      });
    }

    // Apply sorting
    if (enableSorting && sortConfig.key) {
      result.sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];
        
        if (aValue < bValue) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }

    return result;
  }, [data, filterConfig, sortConfig, enableFiltering, enableSorting]);

  // Memoize paginated data
  const paginatedData = useMemo(() => {
    if (!enablePagination) return processedData;
    
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return processedData.slice(startIndex, endIndex);
  }, [processedData, currentPage, pageSize, enablePagination]);

  // Memoize pagination info
  const paginationInfo = useMemo(() => {
    const totalPages = Math.ceil(processedData.length / pageSize);
    return {
      currentPage,
      totalPages,
      totalItems: processedData.length,
      startItem: (currentPage - 1) * pageSize + 1,
      endItem: Math.min(currentPage * pageSize, processedData.length)
    };
  }, [processedData.length, currentPage, pageSize]);

  // Memoized event handlers
  const handleSort = useCallback((key) => {
    if (!enableSorting) return;
    
    const newDirection = sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc';
    const newSortConfig = { key, direction: newDirection };
    
    setSortConfig(newSortConfig);
    onSort?.(newSortConfig);
  }, [enableSorting, sortConfig, onSort]);

  const handleFilter = useCallback((key, value) => {
    if (!enableFiltering) return;
    
    const newFilterConfig = { ...filterConfig, [key]: value };
    setFilterConfig(newFilterConfig);
    onFilter?.(newFilterConfig);
  }, [enableFiltering, filterConfig, onFilter]);

  const handleRowClick = useCallback((row, index) => {
    onRowClick?.(row, index);
  }, [onRowClick]);

  const handleRowSelect = useCallback((row, checked) => {
    if (!enableSelection) return;
    
    let newSelection;
    if (checked) {
      newSelection = [...selectedRowsInternal, row];
    } else {
      newSelection = selectedRowsInternal.filter(selectedRow => selectedRow !== row);
    }
    
    setSelectedRowsInternal(newSelection);
    onSelectionChange?.(newSelection);
  }, [enableSelection, selectedRowsInternal, onSelectionChange]);

  const handleSelectAll = useCallback((checked) => {
    if (!enableSelection) return;
    
    const newSelection = checked ? [...paginatedData] : [];
    setSelectedRowsInternal(newSelection);
    onSelectionChange?.(newSelection);
  }, [enableSelection, paginatedData, onSelectionChange]);

  const handlePageChange = useCallback((page) => {
    setCurrentPage(page);
  }, []);

  // Reset pagination when data changes
  useEffect(() => {
    setCurrentPage(1);
  }, [data.length]);

  // Sync external selected rows
  useEffect(() => {
    setSelectedRowsInternal(selectedRows);
  }, [selectedRows]);

  // Memoized column headers
  const columnHeaders = useMemo(() => {
    return columns.map(column => (
      <th
        key={column.key}
        className={`data-table-header ${column.sortable ? 'sortable' : ''} ${sortConfig.key === column.key ? `sorted-${sortConfig.direction}` : ''}`}
        onClick={() => column.sortable && handleSort(column.key)}
        style={{ width: column.width }}
      >
        <div className="header-content">
          <span>{column.title}</span>
          {column.sortable && (
            <span className="sort-indicator">
              {sortConfig.key === column.key ? (
                sortConfig.direction === 'asc' ? '↑' : '↓'
              ) : '↕'}
            </span>
          )}
        </div>
        {enableFiltering && column.filterable !== false && (
          <div className="filter-input">
            <input
              type="text"
              placeholder={`Filter ${column.title.toLowerCase()}...`}
              value={filterConfig[column.key] || ''}
              onChange={(e) => handleFilter(column.key, e.target.value)}
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        )}
      </th>
    ));
  }, [columns, sortConfig, filterConfig, enableFiltering, handleSort, handleFilter]);

  // Memoized table rows
  const tableRows = useMemo(() => {
    return paginatedData.map((row, index) => (
      <tr
        key={row.id || index}
        className={`data-table-row ${selectedRowsInternal.includes(row) ? 'selected' : ''}`}
        onClick={() => handleRowClick(row, index)}
      >
        {enableSelection && (
          <td className="selection-cell">
            <input
              type="checkbox"
              checked={selectedRowsInternal.includes(row)}
              onChange={(e) => {
                e.stopPropagation();
                handleRowSelect(row, e.target.checked);
              }}
            />
          </td>
        )}
        {columns.map(column => (
          <td
            key={column.key}
            className="data-table-cell"
            style={{ width: column.width }}
          >
            {column.render ? column.render(row[column.key], row, index) : row[column.key]}
          </td>
        ))}
      </tr>
    ));
  }, [paginatedData, columns, selectedRowsInternal, enableSelection, handleRowClick, handleRowSelect]);

  // Memoized pagination controls
  const paginationControls = useMemo(() => {
    if (!enablePagination || paginationInfo.totalPages <= 1) return null;

    const pages = [];
    const { currentPage, totalPages } = paginationInfo;

    // Previous page
    pages.push(
      <button
        key="prev"
        className="pagination-btn"
        disabled={currentPage === 1}
        onClick={() => handlePageChange(currentPage - 1)}
      >
        ← Previous
      </button>
    );

    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          className={`pagination-btn ${i === currentPage ? 'active' : ''}`}
          onClick={() => handlePageChange(i)}
        >
          {i}
        </button>
      );
    }

    // Next page
    pages.push(
      <button
        key="next"
        className="pagination-btn"
        disabled={currentPage === totalPages}
        onClick={() => handlePageChange(currentPage + 1)}
      >
        Next →
      </button>
    );

    return (
      <div className="pagination-controls">
        <div className="pagination-info">
          Showing {paginationInfo.startItem}-{paginationInfo.endItem} of {paginationInfo.totalItems} items
        </div>
        <div className="pagination-buttons">
          {pages}
        </div>
      </div>
    );
  }, [enablePagination, paginationInfo, handlePageChange]);

  if (loading) {
    return (
      <div className={`data-table-container ${className}`} {...props}>
        <div className="data-table-loading">
          <div className="loading-spinner"></div>
          <p>Loading data...</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className={`data-table-container ${className}`} {...props}>
        <div className="data-table-empty">
          <p>{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`data-table-container ${className}`} {...props}>
      <div className="data-table-wrapper">
        <table ref={tableRef} className="data-table">
          <thead>
            <tr>
              {enableSelection && (
                <th className="selection-header">
                  <input
                    type="checkbox"
                    checked={selectedRowsInternal.length === paginatedData.length && paginatedData.length > 0}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                  />
                </th>
              )}
              {columnHeaders}
            </tr>
          </thead>
          <tbody>
            {tableRows}
          </tbody>
        </table>
      </div>
      {paginationControls}
    </div>
  );
});

DataTable.displayName = 'DataTable';

export default DataTable;

