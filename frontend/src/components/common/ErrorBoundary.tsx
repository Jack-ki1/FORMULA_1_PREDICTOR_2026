import { Component } from 'react'
import type { ReactNode, ErrorInfo } from 'react'

interface Props {
  children: ReactNode
  /** Label shown in the fallback UI, e.g. "Dashboard" or "Standings". */
  label?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * Without this, a single chart/widget throwing during render (undefined field,
 * empty array, an API response shape the component didn't expect) unmounts the
 * ENTIRE React tree — the whole app goes blank, not just the broken panel.
 * Wrap each route/page (and any particularly data-fragile widget) in this so a
 * failure is contained, visible, and recoverable instead of a silent white screen.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error(`[ErrorBoundary${this.props.label ? ` — ${this.props.label}` : ''}]`, error, info.componentStack)
  }

  private reset = () => this.setState({ hasError: false, error: null })

  render() {
    if (this.state.hasError) {
      return (
        <div className="card p-6 m-4" role="alert">
          <div className="f1-display font-bold mb-2">
            {this.props.label ? `${this.props.label} hit a problem` : 'Something went wrong'}
          </div>
          <div className="fs-11 text-sub mb-4">
            {this.state.error?.message || 'An unexpected error occurred while rendering this section.'}
          </div>
          <button className="btn btn-sm" onClick={this.reset}>Try again</button>
        </div>
      )
    }
    return this.props.children
  }
}
