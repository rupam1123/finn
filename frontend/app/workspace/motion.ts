// One observer per route; no scroll handler, hidden content, or perpetual animation.
const tiles='.filing-card,.holding-card,.quarter-card,.research-card,.return-tile,.health-grid>article,.launch-companies>a,.research-jumps>a,.signal-mix,.return-map';
const targets=`[data-motion="reveal"],[data-motion="plot"],${tiles}`;
export function observeMotion(root:HTMLElement,scope:Window=window){
 const media=scope.matchMedia?.('(prefers-reduced-motion: reduce)');
 if(media?.matches||typeof IntersectionObserver==='undefined')return()=>{};
 const seen=new WeakSet<Element>(),played=new WeakSet<Element>(),animations=new Set<Animation>();
 function play(element:Element,frames:Keyframe[],options:KeyframeAnimationOptions){
  const animation=element.animate?.(frames,options);if(!animation)return;
  animations.add(animation);animation.finished.then(()=>animations.delete(animation),()=>animations.delete(animation));
 }
 const observer=new IntersectionObserver(entries=>{
  for(const entry of entries){
   if(!entry.isIntersecting||played.has(entry.target))continue;
   observer.unobserve(entry.target);played.add(entry.target);if(media?.matches)continue;
   const element=entry.target;
   if(element.matches('[data-motion="plot"]')){
    element.querySelectorAll('[data-draw]').forEach(part=>{
     const kind=part.getAttribute('data-draw');
     const frames:Keyframe[]=kind==='line'?[{strokeDasharray:'1 1',strokeDashoffset:1},{strokeDasharray:'1 1',strokeDashoffset:0}]:kind==='grow'?[{transform:'scaleY(.02)',opacity:.4},{transform:'scaleY(1)',opacity:1}]:[{opacity:.15},{opacity:1}];
     play(part,frames,{duration:kind==='line'?240:180,easing:'cubic-bezier(.2,.8,.2,1)'});
    });
   }else{
    play(element,[{opacity:.55,transform:'translateY(16px) scale(.965)'},{opacity:1,transform:'translateY(0) scale(1)'}],{duration:150,easing:'cubic-bezier(.16,1,.3,1)'});
   }
  }
 },{threshold:.06,rootMargin:'0px 0px -12px 0px'});
 function register(node:Element){
  if(node.matches(targets)&&!seen.has(node)){seen.add(node);observer.observe(node)}
  node.querySelectorAll(targets).forEach(child=>{if(!seen.has(child)){seen.add(child);observer.observe(child)}});
 }
 register(root);
 const mutations=new MutationObserver(records=>{for(const record of records)record.addedNodes.forEach(node=>{if(node.nodeType===1)register(node as Element)})});
 mutations.observe(root,{childList:true,subtree:true});
 function stop(){animations.forEach(a=>a.cancel());animations.clear()}
 media?.addEventListener('change',stop);
 return()=>{observer.disconnect();mutations.disconnect();stop();media?.removeEventListener('change',stop)};
}
