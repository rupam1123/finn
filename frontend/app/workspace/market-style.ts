export type Direction='up'|'down'|'flat'|'missing';
export function returnDirection(value:unknown):Direction{
 if(value===null||value===undefined||value===''||!Number.isFinite(Number(value)))return 'missing';
 return Number(value)>0?'up':Number(value)<0?'down':'flat';
}
export function seriesDirection(first:number,last:number):Direction{
 return Number.isFinite(first)&&Number.isFinite(last)?last>first?'up':last<first?'down':'flat':'missing';
}
