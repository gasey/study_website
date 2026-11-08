export default function NavIcon({name}:{name:string}){
 const paths:Record<string,string>={home:'m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z',exam:'M8 4H5v17h14V4h-3M9 3h6v4H9ZM8 12h8M8 16h5',library:'M3 4h5v16H3ZM11 4h4v16h-4ZM18 4l3 15',create:'M12 5v14M5 12h14',more:'M4 6h16M4 12h16M4 18h16',search:'M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0'}
 return <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]||paths.more}/></svg>
}
