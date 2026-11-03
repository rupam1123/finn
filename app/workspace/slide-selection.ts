// Delegated pointer gestures: preview in one animation frame, commit once on
// release. Normal taps, native scrolling and keyboard activation stay native.
const groups='.mobile-nav,.window-pills,.quick-categories,.feed-tabs,.segmented,.chart-mode,.research-nav,.company-context nav,.radar-summary,.showcase-pills';
const choices=':scope > a[href],:scope > button[aria-pressed]';
type Choice={element:HTMLElement;rect:DOMRect};
type Gesture={id:number;group:HTMLElement;items:Choice[];x:number;y:number;startX:number;startY:number;bounds:DOMRect;active:boolean;preview:HTMLElement|null};
export function installSlideSelection(root:HTMLElement,scope:Window=window){
 let gesture:Gesture|null=null,frame:number|null=null,suppress:HTMLElement|null=null,committing=false;
 const raf=(fn:FrameRequestCallback)=>scope.requestAnimationFrame(fn);
 function clear(){
  if(frame!==null){scope.cancelAnimationFrame(frame);frame=null;}
  const old=gesture;gesture=null;
  if(old){delete old.group.dataset.slideActive;delete old.preview?.dataset.slidePreview;try{if(old.group.hasPointerCapture?.(old.id))old.group.releasePointerCapture(old.id);}catch{}}
 }
 function pick(g:Gesture){
  if(g.y<g.bounds.top-20||g.y>g.bounds.bottom+20||g.x<g.bounds.left-24||g.x>g.bounds.right+24)return null;
  const sameRow=g.items.filter(({rect})=>g.startY>=rect.top-4&&g.startY<=rect.bottom+4);
  const items=sameRow.length?sameRow:g.items;
  return items.reduce<Choice|null>((closest,item)=>{const distance=Math.abs(g.x-(item.rect.left+item.rect.right)/2);return !closest||distance<Math.abs(g.x-(closest.rect.left+closest.rect.right)/2)?item:closest;},null)?.element??null;
 }
 function paint(){frame=null;const g=gesture;if(!g?.active)return;const next=pick(g);if(next===g.preview)return;if(g.preview)delete g.preview.dataset.slidePreview;g.preview=next;if(next)next.dataset.slidePreview='true';}
 function start(event:PointerEvent){
  if(event.isPrimary===false||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
  const target=event.target instanceof Element?event.target:null,group=target?.closest<HTMLElement>(groups);
  if(!group||!root.contains(group))return;
  const items=Array.from(group.querySelectorAll<HTMLElement>(choices)).filter(el=>!el.matches(':disabled,[aria-disabled=true]')).map(element=>({element,rect:element.getBoundingClientRect()})).filter(x=>x.rect.width>0&&x.rect.height>0);
  if(items.length<2||!items.some(x=>x.element===target||x.element.contains(target)))return;
  clear();suppress=null;gesture={id:event.pointerId,group,items,x:event.clientX,y:event.clientY,startX:event.clientX,startY:event.clientY,bounds:group.getBoundingClientRect(),active:false,preview:null};
 }
 function move(event:PointerEvent){
  const g=gesture;if(!g||event.pointerId!==g.id)return;g.x=event.clientX;g.y=event.clientY;
  if(!g.active){const dx=Math.abs(g.x-g.startX),dy=Math.abs(g.y-g.startY);if(dy>8&&dy>dx){clear();return;}if(dx<7||dx<dy*1.15)return;g.active=true;g.group.dataset.slideActive='true';try{g.group.setPointerCapture?.(g.id);}catch{}}
  if(frame===null)frame=raf(paint);
 }
 function finish(event:PointerEvent){
  const g=gesture;if(!g||event.pointerId!==g.id)return;
  if(!g.active){clear();return;}
  g.x=event.clientX;g.y=event.clientY;const selected=pick(g);suppress=g.group;event.preventDefault();clear();
  if(selected?.isConnected&&!selected.matches(':disabled,[aria-disabled=true],[aria-current=page],[aria-pressed=true]')){committing=true;try{selected.click();}finally{committing=false;}}
 }
 function cancel(event:PointerEvent){if(gesture?.id===event.pointerId)clear();}
 function click(event:MouseEvent){if(!committing&&suppress&&event.detail!==0&&event.target instanceof Node&&suppress.contains(event.target)){event.preventDefault();event.stopPropagation();suppress=null;}}
 function context(event:Event){if(gesture){event.preventDefault();}}
 root.addEventListener('pointerdown',start);
 scope.addEventListener('pointermove',move,{passive:true});scope.addEventListener('pointerup',finish);scope.addEventListener('pointercancel',cancel);scope.addEventListener('blur',clear);
 root.addEventListener('click',click,true);root.addEventListener('contextmenu',context);root.addEventListener('dragstart',context);
 return()=>{clear();root.removeEventListener('pointerdown',start);scope.removeEventListener('pointermove',move);scope.removeEventListener('pointerup',finish);scope.removeEventListener('pointercancel',cancel);scope.removeEventListener('blur',clear);root.removeEventListener('click',click,true);root.removeEventListener('contextmenu',context);root.removeEventListener('dragstart',context);};
}
