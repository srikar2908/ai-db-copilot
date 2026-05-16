import Card from './ui/Card'

type MetricCardProps = {
  label: string
  value: string | number
  helper: string
}

function MetricCard({ label, value, helper }: MetricCardProps) {
  return (
    <Card>
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">{label}</p>
      <p className="mt-3 text-2xl font-semibold text-white">{value}</p>
      <p className="mt-2 text-sm text-slate-400">{helper}</p>
    </Card>
  )
}

export default MetricCard
