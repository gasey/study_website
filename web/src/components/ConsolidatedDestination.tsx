import {Navigate, useLocation} from 'react-router-dom'
import {consolidatedDestination} from '../lib/consolidation'

export default function ConsolidatedDestination() {
  const {pathname, search, hash} = useLocation()
  return <Navigate to={consolidatedDestination(pathname, search, hash)} replace />
}
