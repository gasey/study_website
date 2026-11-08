/** Visual identity only. Source membership and answer states stay authoritative. */
export function examPresentation(id:string){
 const identities:Record<string,{tone:string;short:string;category:string}>={
  udc:{tone:'teal',short:'UDC',category:'Clerical preparation'},
  ldc:{tone:'blue',short:'LDC',category:'Clerical preparation'},
  assistant:{tone:'violet',short:'AST',category:'Clerical preparation'},
  'combined-prelims':{tone:'indigo',short:'MCS',category:'Civil services'},
  'group-b-gazetted':{tone:'violet',short:'GB',category:'Gazetted preparation'},
  'group-b-non-gazetted':{tone:'teal',short:'GB',category:'Non-Gazetted preparation'},
  'iti-instructor-2026':{tone:'amber',short:'ITI',category:'Technical preparation'},
 }
 return identities[id]||{tone:'indigo',short:'EX',category:'Exam preparation'}
}
export function examCatalogLayout(value:string|null){return value==='list'?'list':'cards'}
