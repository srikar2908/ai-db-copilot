type LoadingSpinnerProps = {
  label?: string
}

function LoadingSpinner({ label = 'Loading...' }: LoadingSpinnerProps) {
  return (
    <div className="flex items-center justify-center gap-3 rounded-md border border-slate-800 bg-slate-950 px-4 py-8 text-sm text-slate-400">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-700 border-t-cyan-300" />
      {label}
    </div>
  )
}

export default LoadingSpinner
