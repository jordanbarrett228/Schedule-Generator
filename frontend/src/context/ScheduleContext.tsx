import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'

interface ScheduleProgress {
  count: number
  elapsed: number
}

interface ScheduleContextType {
  isGenerating: boolean
  progress: ScheduleProgress
  setIsGenerating: (value: boolean) => void
  setProgress: (value: ScheduleProgress) => void
}

const ScheduleContext = createContext<ScheduleContextType | undefined>(undefined)

export function ScheduleProvider({ children }: { children: ReactNode }) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [progress, setProgress] = useState<ScheduleProgress>({ count: 0, elapsed: 0 })

  // Subscribe to solver progress events globally
  useEffect(() => {
    const handleProgress = (data: any) => {
      if (data.type === 'solution_found') {
        setProgress({ count: data.count, elapsed: data.elapsed })
      }
    }

    if (window.electron?.onSolverProgress) {
      window.electron.onSolverProgress(handleProgress)
    }

    return () => {
      if (window.electron?.offSolverProgress) {
        window.electron.offSolverProgress(handleProgress)
      }
    }
  }, [])

  return (
    <ScheduleContext.Provider value={{ isGenerating, progress, setIsGenerating, setProgress }}>
      {children}
    </ScheduleContext.Provider>
  )
}

export function useSchedule() {
  const context = useContext(ScheduleContext)
  if (context === undefined) {
    throw new Error('useSchedule must be used within a ScheduleProvider')
  }
  return context
}
