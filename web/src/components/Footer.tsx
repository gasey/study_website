import { Link } from 'react-router-dom'
import { destinationPath } from '../lib/siteMap'

export default function Footer() {
  return (
    <footer className="finna-footer">
      <div>
        <span>
          <strong>Finna.</strong> · India Study Map · Aizawl
        </span>
        <span className="flex flex-wrap items-center gap-4">
          <Link to={destinationPath('index')} className="font-semibold text-link hover:underline">
            Index
          </Link>
          <Link to={destinationPath('guides')} className="font-semibold text-link hover:underline">
            Guides
          </Link>
          <span>Past MPSC questions · Clear source provenance</span>
        </span>
      </div>
    </footer>
  )
}
