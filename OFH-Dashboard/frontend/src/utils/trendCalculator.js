/**
 * Utility functions for calculating trends
 */

/**
 * Calculate trend percentage between current and previous value
 * Returns undefined if no meaningful comparison can be made (to hide the trend indicator)
 */
export function calculateTrend(current, previous) {
  // If no previous data, don't show trend
  if (previous === null || previous === undefined) return undefined
  // If previous was 0 and current is also 0, don't show trend
  if (previous === 0 && current === 0) return undefined
  // If values are the same, return 0 (no change)
  if (current === previous) return 0
  // If previous was 0 but current has value, can't calculate meaningful percentage
  if (previous === 0 && current > 0) return undefined
  // Calculate percentage change
  const change = ((current - previous) / previous) * 100
  return Math.round(change * 10) / 10 // Round to 1 decimal place
}

