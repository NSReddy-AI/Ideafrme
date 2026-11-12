// Scene interpretation only. No rendering, shaping, schema mutation or drag engine.
export function sourcePoint(clientX,clientY,rect,view){
 if(!Number.isFinite(clientX)||!Number.isFinite(clientY)||rect.width<=0||rect.height<=0)return null;
 const x=(clientX-rect.left)/rect.width*view.width,y=(clientY-rect.top)/rect.height*view.height;
 return x>=0&&x<=view.width&&y>=0&&y<=view.height?{x,y}:null;
}
export function hitLayers(elements,point){
 if(!point)return [];
 return [...elements].reverse().filter(e=>{
  if(point.x<e.x||point.x>e.x+e.width||point.y<e.y||point.y>e.y+e.height)return false;
  if(e.type==='shape'&&e.style.shape==='ellipse')return ((point.x-e.x-e.width/2)/(e.width/2))**2+((point.y-e.y-e.height/2)/(e.height/2))**2<=1;
  return true; // Text selection deliberately uses the declared editable layout box.
 }).map(e=>e.id);
}
export function nextHit(hits,selected,cycle){return hits.length?hits[cycle?(hits.indexOf(selected)+1)%hits.length:0]:null;}
export function clippedBox(e,view){
 if(!e)return null;
 const x=Math.max(0,e.x),y=Math.max(0,e.y),right=Math.min(view.width,e.x+e.width),bottom=Math.min(view.height,e.y+e.height);
 return right>x&&bottom>y?{left:100*x/view.width,top:100*y/view.height,width:100*(right-x)/view.width,height:100*(bottom-y)/view.height}:null;
}
export function alignPosition(e,view,kind,margin=32){
 if(!Number.isInteger(margin)||margin<0||margin>540)throw Error('Use an integer margin between 0 and 540 pixels.');
 const horizontal=['left','center-x','right'].includes(kind),vertical=['top','center-y','bottom'].includes(kind);
 if(!horizontal&&!vertical)throw Error('Unsupported alignment.');
 if(horizontal&&e.width>view.width-2*margin||vertical&&e.height>view.height-2*margin)throw Error('Layer does not fit inside the selected margins.');
 let {x,y}=e;
 if(kind==='left')x=margin;if(kind==='right')x=view.width-margin-e.width;if(kind==='center-x')x=Math.round((view.width-e.width)/2);
 if(kind==='top')y=margin;if(kind==='bottom')y=view.height-margin-e.height;if(kind==='center-y')y=Math.round((view.height-e.height)/2);
 return {x,y};
}

export function shellQuote(value){return "'"+String(value).split("'").join("'\"'\"'")+"'";}
