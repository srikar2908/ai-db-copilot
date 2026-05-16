type EmptyStateProps = {
  description: string
  title: string
}

function EmptyState({ description, title }: EmptyStateProps) {
  return (
    <div className="rounded-md border border-dashed border-slate-700 bg-slate-950 px-4 py-8 text-center">
      <p className="text-sm font-semibold text-slate-200">{title}</p>
      <p className="mt-2 text-sm text-slate-500">{description}</p>
    </div>
  )
}

export default EmptyState

