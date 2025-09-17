import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
  {
    variants: {
      variant: {
        default: 'bg-gray-100 text-gray-800',
        success: 'bg-green-100 text-green-800',
        warning: 'bg-yellow-100 text-yellow-800',
        error: 'bg-red-100 text-red-800',
        info: 'bg-blue-100 text-blue-800',
        purple: 'bg-purple-100 text-purple-800',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  showDot?: boolean
}

const StatusBadge = React.forwardRef<HTMLSpanElement, StatusBadgeProps>(
  ({ className, variant, showDot = false, children, ...props }, ref) => {
    const dotColor = {
      default: 'bg-gray-400',
      success: 'bg-green-500',
      warning: 'bg-yellow-500',
      error: 'bg-red-500',
      info: 'bg-blue-500',
      purple: 'bg-purple-500',
    }

    return (
      <span className={badgeVariants({ variant, className })} ref={ref} {...props}>
        {showDot && (
          <div className={`w-1.5 h-1.5 rounded-full mr-1.5 ${dotColor[variant || 'default']}`} />
        )}
        {children}
      </span>
    )
  }
)
StatusBadge.displayName = 'StatusBadge'

export { StatusBadge, badgeVariants }