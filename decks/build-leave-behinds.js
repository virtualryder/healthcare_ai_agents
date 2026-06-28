// One-page leave-behinds (print-ready). One per agent + a suite one-pager. Same palette.
// Run: NODE_PATH=/tmp/decktools/node_modules node build-leave-behinds.js
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const AGENTS = require("./deck-data.js");
const ORANGE="FF9900", INK="232F3E", TEAL="01A88D", SLATE="5A6B7B", BODY="1A232E", WHITE="FFFFFF", PANEL="F4F7FA", AMBER="B26A00", FT="Calibri", FTL="Calibri Light";
const AWS_LOGO="assets/aws-logo.png";

function mark(s){ if(fs.existsSync(AWS_LOGO)){s.addImage({path:AWS_LOGO,x:11.7,y:0.3,w:1.2,h:0.72});return;}
  s.addText("aws",{x:11.55,y:0.28,w:1.35,h:0.45,fontSize:26,bold:true,color:ORANGE,fontFace:FT,align:"right"});
  s.addText("Built on AWS",{x:10.9,y:0.74,w:2.0,h:0.25,fontSize:9,color:SLATE,fontFace:FT,align:"right"}); }

function onePager(a){
  const pptx=new pptxgen(); pptx.defineLayout({name:"W",width:13.333,height:7.5}); pptx.layout="W";
  const s=pptx.addSlide(); s.background={color:WHITE};
  s.addShape("rect",{x:0,y:0,w:13.333,h:0.16,fill:{color:ORANGE}});
  s.addText(a.code,{x:0.6,y:0.36,w:9,h:0.4,fontSize:14,bold:true,color:ORANGE,fontFace:FT});
  s.addText(a.name,{x:0.6,y:0.72,w:10.5,h:0.7,fontSize:28,bold:true,color:INK,fontFace:FTL});
  s.addText(a.sub,{x:0.6,y:1.5,w:11.5,h:0.5,fontSize:13,color:SLATE,fontFace:FT}); mark(s);
  // three stat cards
  const w=3.85,gap=0.35,y=2.25,h=1.5;
  a.stats.forEach((st,i)=>{const x=0.6+i*(w+gap);
    s.addShape("roundRect",{x,y,w,h,rectRadius:0.06,fill:{color:INK}});
    s.addText(st.num,{x:x+0.15,y:y+0.18,w:w-0.3,h:0.6,fontSize:26,bold:true,color:ORANGE,fontFace:FTL,align:"center"});
    s.addText(st.cap,{x:x+0.2,y:y+0.78,w:w-0.4,h:0.65,fontSize:10.5,color:"C9D3DC",fontFace:FT,align:"center",valign:"top"});});
  // how we solve + bright line
  s.addText("How we solve it",{x:0.6,y:4.05,w:6,h:0.35,fontSize:14,bold:true,color:TEAL,fontFace:FT});
  s.addText((a.steps||[]).join("  →  ")+"  →  ["+a.gate+" gate]  →  finalize",
    {x:0.6,y:4.45,w:12,h:0.4,fontSize:12,color:BODY,fontFace:FT});
  s.addText("Outcomes",{x:0.6,y:5.0,w:6,h:0.35,fontSize:14,bold:true,color:TEAL,fontFace:FT});
  s.addText((a.outcome||[]).map(t=>({text:t,options:{bullet:{code:"2022"},fontSize:12,color:BODY,fontFace:FT,paraSpaceAfter:3}})),
    {x:0.7,y:5.4,w:7.0,h:1.4,valign:"top"});
  s.addShape("roundRect",{x:8.0,y:5.35,w:4.75,h:1.5,rectRadius:0.06,fill:{color:PANEL},line:{color:"E2E8EF",width:1}});
  s.addShape("rect",{x:8.0,y:5.35,w:0.12,h:1.5,fill:{color:AMBER}});
  s.addText("The bright line",{x:8.25,y:5.5,w:4.4,h:0.35,fontSize:12,bold:true,color:AMBER,fontFace:FT});
  s.addText(a.bright,{x:8.25,y:5.85,w:4.4,h:0.95,fontSize:11,color:BODY,fontFace:FT,valign:"top"});
  s.addText("HPP AI Agent Suite · Health Providers & Plans · Governed AI on AWS · "+a.statsrc,
    {x:0.6,y:7.05,w:12.3,h:0.3,fontSize:9,italic:true,color:SLATE,fontFace:FT});
  return pptx.writeFile({fileName:`leave-behinds/${a.file}-ONEPAGER.pptx`});
}

(async()=>{ for(const a of AGENTS){ await onePager(a); console.log("wrote",a.file+"-ONEPAGER"); } })();
