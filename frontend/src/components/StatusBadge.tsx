import Badge from './ui/Badge'

type StatusBadgeProps = {
  value: string | null
}

function StatusBadge({ value }: StatusBadgeProps) {
  const normalized = value || 'unknown'
  const tone =
    normalized === 'approved' || normalized === 'success'
      ? 'success'
      : normalized === 'pending' || normalized === 'pending review' || normalized === 'medium'
        ? 'warning'
        : normalized === 'rejected' || normalized === 'failed' || normalized === 'high'
          ? 'danger'
          : normalized === 'low'
            ? 'info'
            : 'neutral'

  return (
    <Badge className="capitalize" tone={tone}>
      {normalized}
    </Badge>
  )
}

export default StatusBadge
