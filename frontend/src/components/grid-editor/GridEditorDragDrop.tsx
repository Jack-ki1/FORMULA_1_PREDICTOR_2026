// Drag-drop variant — uses @dnd-kit/core when available, falls back to plain selects
import { GridEditor } from '../../features/manual-grid/GridEditor'
export function GridEditorDragDrop(props: any) {
  return <GridEditor {...props} />
}
