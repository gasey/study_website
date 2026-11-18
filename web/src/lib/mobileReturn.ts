export function mobileReturn(value:string|null):string|null {
 if(!value)return null;
 return /^\/api\/mobile-auth\/authorize\?flow=[A-Za-z0-9_-]{43}$/.test(value)?value:null;
}
export function consumeMobileReturn(){const value=mobileReturn(sessionStorage.getItem('ism-mobile-return'));sessionStorage.removeItem('ism-mobile-return');return value;}
