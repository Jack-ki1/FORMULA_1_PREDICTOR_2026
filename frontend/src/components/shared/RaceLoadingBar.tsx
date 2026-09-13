import { useIsFetching } from '@tanstack/react-query'

export function RaceLoadingBar() {
  const isFetching = useIsFetching()
  return (
    <div className="race-loading-bar-track" aria-hidden="true">
      <div className={`race-loading-bar-fill ${isFetching ? 'is-active' : ''}`} />
    </div>
  )
}
