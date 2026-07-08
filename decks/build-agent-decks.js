// HPP deck generator — AWS-style decks mimicking the reference format & palette.
// Per-agent arc: Title · The Issue & Its Cost · What Customers Are Seeing (and how
// the market solves it) · How We Solve It (governed, human-decided) · AWS
// Architecture · Why It's Defensible. Plus an Executive Overview and a CISO/CMIO
// review. Figures trace to ../gtm/HPP-DECK-SOURCES.md.
// Run: NODE_PATH=/tmp/decktools/node_modules node build-agent-decks.js
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const AWS_LOGO = "assets/aws-logo.png";  // drop the official asset here to use it instead of the wordmark

const ORANGE="FF9900", INK="232F3E", INK2="2C3B4E", TEAL="01A88D", RED="C7361F",
      SLATE="5A6B7B", BODY="1A232E", LT="C9D3DC", WHITE="FFFFFF", PANEL="F4F7FA",
      PURPLE="8C4FFF", MAGENTA="C925D1", S3GREEN="7AA116", COMPUTE="ED7100", SECRED="DD344C";
const FT="Calibri", FTL="Calibri Light";

function awsMark(s, dark){
  // top-right brand mark. If the official logo asset is present, use it; otherwise
  // render a clean "aws" wordmark cue (not a reproduction of the trademarked logo).
  if (fs.existsSync(AWS_LOGO)) {
    s.addImage({ path: AWS_LOGO, x: 11.7, y: 0.42, w: 1.25, h: 0.75 });
    return;
  }
  const c = ORANGE, t = dark ? WHITE : INK;
  s.addText("aws", { x: 11.55, y: 0.42, w: 1.35, h: 0.5, fontSize: 30, bold: true,
    color: c, fontFace: FT, align: "right", charSpacing: 1 });
  s.addText("Built on AWS", { x: 10.9, y: 0.95, w: 2.0, h: 0.3, fontSize: 10,
    color: dark ? "9DC3E6" : SLATE, fontFace: FT, align: "right" });
}
function footer(s, code, light){
  const b = light ? INK : WHITE, g = light ? SLATE : "8FA1B3";
  s.addText([{text:"HPP AI Agent Suite",options:{bold:true,color:b}},
    {text:"   ·   Health Providers & Plans   ·   Governed AI on AWS   ·   "+code,options:{color:g}}],
    {x:0.5,y:7.05,w:12.3,h:0.3,fontSize:11,fontFace:FT});
}
function accentBar(s){ s.addShape("rect",{x:0,y:0,w:13.333,h:0.16,fill:{color:ORANGE}}); }

function titleSlide(pptx, code, title, sub){
  const s=pptx.addSlide(); s.background={color:INK}; accentBar(s);
  s.addText(code,{x:0.6,y:0.7,w:9,h:0.5,fontSize:16,bold:true,color:ORANGE,fontFace:FT});
  awsMark(s, true);
  s.addText(title,{x:0.6,y:1.7,w:12.1,h:1.8,fontSize:42,bold:true,color:WHITE,fontFace:FTL});
  s.addText(sub,{x:0.6,y:3.7,w:11.8,h:1.2,fontSize:19,color:LT,fontFace:FT});
  s.addText("AI assists, drafts, assembles, flags, recommends — a licensed human decides every consequential action.",
    {x:0.6,y:5.5,w:11.8,h:0.6,fontSize:14,italic:true,color:ORANGE,fontFace:FT});
  footer(s,code); return s;
}
function headerLight(pptx,title){
  const s=pptx.addSlide(); s.background={color:WHITE}; accentBar(s);
  s.addText(title,{x:0.6,y:0.42,w:12.1,h:0.7,fontSize:28,bold:true,color:INK,fontFace:FTL});
  return s;
}
function statSlide(pptx, code, heading, issueLine, stats, src){
  const s=pptx.addSlide(); s.background={color:INK}; accentBar(s);
  s.addText(heading,{x:0.6,y:0.5,w:10,h:0.7,fontSize:30,bold:true,color:WHITE,fontFace:FTL});
  awsMark(s, true);
  s.addText(issueLine,{x:0.6,y:1.45,w:12.1,h:0.9,fontSize:17,color:LT,fontFace:FT});
  const w=3.85, gap=0.35, x0=0.6, y=2.7, h=2.7;
  stats.forEach((st,i)=>{
    const x=x0+i*(w+gap);
    s.addShape("roundRect",{x,y,w,h,rectRadius:0.08,fill:{color:INK2}});
    s.addText(st.num,{x:x+0.2,y:y+0.35,w:w-0.4,h:1.0,fontSize:38,bold:true,color:ORANGE,fontFace:FTL,align:"center"});
    s.addText(st.cap,{x:x+0.25,y:y+1.45,w:w-0.5,h:1.0,fontSize:13.5,color:LT,fontFace:FT,align:"center",valign:"top"});
  });
  if(src) s.addText(src,{x:0.6,y:5.7,w:12.1,h:0.6,fontSize:10.5,italic:true,color:"8FA1B3",fontFace:FT});
  footer(s,code); return s;
}
function card(s,x,y,w,h,label,labelColor,lines){
  s.addShape("roundRect",{x,y,w,h,rectRadius:0.06,fill:{color:WHITE},line:{color:"E2E8EF",width:1},shadow:{type:"outer",color:"BFC9D4",opacity:0.4,blur:6,offset:2,angle:90}});
  s.addShape("rect",{x,y,w:w,h:0.5,fill:{color:labelColor}});
  s.addText(label,{x:x+0.18,y:y+0.06,w:w-0.3,h:0.38,fontSize:13,bold:true,color:WHITE,fontFace:FT});
  s.addText(lines.map(t=>({text:t,options:{bullet:{code:"2022"},fontSize:12.5,color:BODY,paraSpaceAfter:6,fontFace:FT}})),
    {x:x+0.22,y:y+0.65,w:w-0.44,h:h-0.8,valign:"top"});
}
function problemSlide(pptx, code, situation, market, constraint, role){
  const s=headerLight(pptx,"What Customers Are Seeing");
  card(s,0.6,1.35,6.0,4.0,"THE SITUATION TODAY",INK,situation);
  card(s,6.85,1.35,5.9,4.0,"HOW THE MARKET IS SOLVING IT",TEAL,market);
  s.addShape("roundRect",{x:0.6,y:5.55,w:12.15,h:1.05,rectRadius:0.06,fill:{color:INK}});
  s.addText([{text:"The line that must hold:  ",options:{bold:true,color:ORANGE}},
    {text:constraint,options:{color:WHITE}}],
    {x:0.85,y:5.62,w:11.7,h:0.9,fontSize:15,fontFace:FT,valign:"middle"});
  footer(s,code,true); return s;
}
function solutionSlide(pptx, code, steps, gate, features){
  const s=headerLight(pptx,"How We Solve It — Governed, Agentic, Human-Decided");
  s.addText("A LangGraph workflow on AWS: deterministic nodes + in-account Bedrock drafting, every system call through the deny-by-default MCP gateway, and a framework-enforced human gate before any consequential action.",
    {x:0.6,y:1.2,w:12.1,h:0.7,fontSize:13,color:SLATE,fontFace:FT});
  // numbered step chips
  const n=steps.length, y=2.1, h=0.62, x0=0.6, totalW=12.15, w=(totalW-(n-1)*0.18)/n;
  steps.forEach((st,i)=>{
    const x=x0+i*(w+0.18);
    s.addShape("roundRect",{x,y,w,h,rectRadius:0.05,fill:{color:INK}});
    s.addText(String(i+1),{x:x+0.08,y:y+0.06,w:0.4,h:0.5,fontSize:14,bold:true,color:ORANGE,fontFace:FT});
    s.addText(st,{x:x+0.45,y:y+0.04,w:w-0.5,h:0.55,fontSize:9.5,color:WHITE,fontFace:FT,valign:"middle"});
  });
  // human gate (red) full-width
  s.addShape("roundRect",{x:0.6,y:3.0,w:12.15,h:0.8,rectRadius:0.06,fill:{color:RED}});
  s.addText([{text:"HUMAN REVIEW GATE — "+gate+"  ",options:{bold:true,color:WHITE}},
    {text:"approves, edits, or rejects. High-risk writes cannot execute before this (LangGraph interrupt_before / Step Functions waitForTaskToken).",options:{color:"FFE2DB"}}],
    {x:0.85,y:3.06,w:11.7,h:0.68,fontSize:13,fontFace:FT,valign:"middle"});
  // three feature cards
  const fw=3.95, fy=4.05, fh=2.3;
  features.forEach((f,i)=>{
    const x=0.6+i*(fw+0.18);
    s.addShape("roundRect",{x,y:fy,w:fw,h:fh,rectRadius:0.06,fill:{color:PANEL},line:{color:"E2E8EF",width:1}});
    s.addShape("rect",{x,y:fy,w:0.12,h:fh,fill:{color:ORANGE}});
    s.addText(f.t,{x:x+0.28,y:fy+0.2,w:fw-0.45,h:0.5,fontSize:14,bold:true,color:INK,fontFace:FT});
    s.addText(f.d,{x:x+0.28,y:fy+0.75,w:fw-0.45,h:fh-0.9,fontSize:12,color:SLATE,fontFace:FT,valign:"top"});
  });
  footer(s,code,true); return s;
}
function archSlide(pptx, code, systems){
  const s=headerLight(pptx,"AWS Architecture & Traffic Flow");
  const rows=[
    {c:INK, t:"WORKFORCE  ·  Cognito / Identity Center (SAML/OIDC, MFA) → verified claims (custom:hpp_role)"},
    {c:COMPUTE, t:"AGENT  ·  ECS Fargate (LangGraph) or Step Functions (native, waitForTaskToken HITL)  +  Streamlit console"},
    {c:ORANGE, t:"MCP AUTHORIZATION GATEWAY  ·  deny-by-default + least-privilege intersection + scoped tokens + PHI-masked audit", dark:true},
    {c:TEAL, t:"MODEL  ·  Amazon Bedrock (in-account, HIPAA-eligible under BAA) + Guardrails (PHI filters)"},
    {c:SLATE, t:"CONNECTORS (governed Lambda)  →  "+systems},
    {c:MAGENTA, t:"DATA  ·  DynamoDB append-only audit (PITR, deny Update/Delete) · HITL table"},
    {c:S3GREEN, t:"S3 Object Lock (WORM) — finalized snapshots · KMS CMK throughout"},
  ];
  let y=1.25; const x=0.6, w=12.15, h=0.6;
  rows.forEach(r=>{
    s.addShape("roundRect",{x,y,w,h,rectRadius:0.05,fill:{color:r.c}});
    s.addText(r.t,{x:x+0.25,y:y+0.05,w:w-0.45,h:h-0.1,fontSize:12,bold:false,color:(r.dark?INK:WHITE),fontFace:FT,valign:"middle",bold:r.dark});
    y+=h+0.1;
  });
  s.addText("PHI never leaves the customer VPC: inference is in-account on Bedrock via a VPC endpoint; every tool call is authorized, scoped-token-minted, and PHI-masked-audited. CloudFormation + Terraform; native or container deploy.",
    {x:0.6,y:y+0.05,w:12.15,h:0.6,fontSize:11,italic:true,color:SLATE,fontFace:FT});
  footer(s,code,true); return s;
}
function resultsSlide(pptx, code, brightLine, why, outcome, src){
  const s=pptx.addSlide(); s.background={color:INK}; accentBar(s);
  s.addText("Why This Is Defensible",{x:0.6,y:0.5,w:10,h:0.7,fontSize:30,bold:true,color:WHITE,fontFace:FTL});
  awsMark(s, true);
  // bright line strip
  s.addShape("roundRect",{x:0.6,y:1.4,w:12.15,h:0.95,rectRadius:0.06,fill:{color:INK2}});
  s.addText([{text:"The bright line:  ",options:{bold:true,color:ORANGE}},{text:brightLine,options:{color:WHITE}}],
    {x:0.85,y:1.48,w:11.7,h:0.8,fontSize:15,fontFace:FT,valign:"middle"});
  // why bullets (left) + outcome card (right)
  s.addText(why.map(t=>({text:t,options:{bullet:{code:"2022"},fontSize:14,color:LT,paraSpaceAfter:9,fontFace:FT}})),
    {x:0.75,y:2.7,w:7.1,h:3.5,valign:"top"});
  s.addShape("roundRect",{x:8.1,y:2.7,w:4.65,h:3.4,rectRadius:0.08,fill:{color:INK2}});
  s.addText("WHAT GOOD LOOKS LIKE",{x:8.35,y:2.9,w:4.2,h:0.4,fontSize:13,bold:true,color:TEAL,fontFace:FT});
  s.addText(outcome.map(t=>({text:t,options:{bullet:{code:"2022"},fontSize:13,color:LT,paraSpaceAfter:8,fontFace:FT}})),
    {x:8.35,y:3.4,w:4.2,h:2.6,valign:"top"});
  if(src) s.addText(src,{x:0.6,y:6.55,w:12.1,h:0.4,fontSize:10,italic:true,color:"8FA1B3",fontFace:FT});
  footer(s,code); return s;
}

const AGENTS = require("./deck-data.js");

function buildAgentDeck(a){
  const pptx=new pptxgen(); pptx.defineLayout({name:"W",width:13.333,height:7.5}); pptx.layout="W";
  pptx.author="HPP AI Agent Suite";
  titleSlide(pptx,a.code,a.name,a.sub);
  statSlide(pptx,a.code,"The Issue & What It Costs",a.issue,a.stats,a.statsrc);
  problemSlide(pptx,a.code,a.situation,a.market,a.constraint,a.gate);
  solutionSlide(pptx,a.code,a.steps,a.gate,a.features);
  archSlide(pptx,a.code,a.systems);
  resultsSlide(pptx,a.code,a.bright,a.why,a.outcome,a.whysrc);
  return pptx.writeFile({fileName:a.file+".pptx"});
}

function buildExec(){
  const E=require("./deck-data.js");
  const pptx=new pptxgen(); pptx.defineLayout({name:"W",width:13.333,height:7.5}); pptx.layout="W";
  titleSlide(pptx,"Executive Overview","Governed AI Agents for Health Providers & Plans",
    "The agents are not the product. The governed platform that makes them deployable, auditable, and HIPAA-defensible is.");
  statSlide(pptx,"Executive Overview","The Stakes Across the Provider–Payer Arc",
    "Eight high-value workflows, one governed control plane. The cost of doing nothing, in three numbers:",
    [{num:"~$18B",cap:"U.S. hospital spend overturning denials in 2025 (of ~$43B on billing & collections)"},
     {num:"~13 hrs",cap:"physician time per week on ~39 prior authorizations; 94% say PA delays care"},
     {num:">80% / 70%",cap:"of health systems / health plans prioritizing agentic AI (Deloitte, Sep 2025)"}],
    "Sources: Experian State of Claims 2025; AMA 2024 PA survey; Deloitte Sep 2025 — gtm/HPP-DECK-SOURCES.md.");
  const s=headerLight(pptx,"The Eight-Agent Portfolio");
  card(s,0.6,1.35,6.0,4.55,"PROVIDER-SIDE",INK,[
    "01 Revenue-Cycle & Denial — drafts grounded appeals; a denials specialist submits",
    "03 Clinical-Administration — chart-grounded drafts; a clinician signs",
    "04 Patient Access — eligibility + deterministic Good Faith Estimate; a rep approves",
    "06 Payment Integrity & Coding — NCCI/MUE + upcoding flags; flags only, never recoups"]);
  card(s,6.85,1.35,5.9,4.55,"PAYER-SIDE",TEAL,[
    "02 Prior-Authorization — Da Vinci packet; a PA nurse submits; payer decides coverage",
    "05 Utilization Management — criteria + fairness screen; the medical director decides",
    "07 Care Management & Pop Health — gaps + HCC/RAF + SDOH; a care manager owns the plan",
    "08 Contact Center / Member Services — Amazon Connect; identity-gated answers; a rep approves"]);
  s.addText("All eight built to reference depth · 121 automated tests pass with no API key · CloudFormation + Terraform · cfn-lint clean.",
    {x:0.6,y:6.05,w:12.1,h:0.5,fontSize:13,bold:true,color:TEAL,fontFace:FT});
  footer(s,"Executive Overview",true);
  resultsSlide(pptx,"Executive Overview",
    "No agent submits a claim or issues a coverage determination autonomously. AI assists; a licensed human decides.",
    ["Deny-by-default MCP gateway — an agent can never exceed the human (agent grant ∩ user entitlement).",
     "Framework-enforced human gate on every high-risk write; PHI-masked append-only audit.",
     "HIPAA-eligible Amazon Bedrock under the AWS BAA, reached via PrivateLink — no PHI egress to external AI APIs; Guardrails on every call.",
     "Governance spine in CI: grounding, prompt registry, red team, four-fifths fairness, accessibility."],
    ["Land with denials (cleanest CFO ROI)","Expand 02+04, then payer 05+08","Each agent reuses the platform",
     "Marginal compliance cost falls per agent","Demonstrated + Deployable-by-design today"],
    "Maturity: production-readiness (CSV/CSA, IdP, live-connector validation, pen test, HITRUST) is the engagement.");
  return pptx.writeFile({fileName:"HPP-Agentic-AI-Suite-Executive-Overview.pptx"});
}

function buildCiso(){
  const pptx=new pptxgen(); pptx.defineLayout({name:"W",width:13.333,height:7.5}); pptx.layout="W";
  titleSlide(pptx,"CISO / CMIO Adoption Review","Why a Security & Clinical Leader Can Say Yes",
    "The controls are enforced in the gateway, outside the model — a prompt cannot disable them.");
  const s=headerLight(pptx,"Six Gateway Controls");
  const ctrls=[["1  Identity verification","Fail-closed on a missing verified subject (verified IdP claims)."],
    ["2  Deny-by-default authorization","Least-privilege intersection — agent grant ∩ user entitlement."],
    ["3  Human-approval gate","High-risk writes block until a verified reviewer is bound in (tested)."],
    ["4  Short-lived scoped tokens","Per-call, per-tool; no standing service accounts."],
    ["5  PHI-masked append-only audit","Every attempt logged with lineage to the system reached."],
    ["6  Fail-closed on error","Any execution error denies and audits — never silently proceeds."]];
  let i=0; for(let r=0;r<3;r++){for(let c=0;c<2;c++){const x=0.6+c*6.15,y=1.3+r*1.7;
    s.addShape("roundRect",{x,y,w:5.95,h:1.5,rectRadius:0.06,fill:{color:PANEL},line:{color:"E2E8EF",width:1}});
    s.addShape("rect",{x,y,w:0.12,h:1.5,fill:{color:ORANGE}});
    s.addText(ctrls[i][0],{x:x+0.28,y:y+0.14,w:5.5,h:0.4,fontSize:15,bold:true,color:INK,fontFace:FT});
    s.addText(ctrls[i][1],{x:x+0.28,y:y+0.6,w:5.5,h:0.8,fontSize:12.5,color:SLATE,fontFace:FT,valign:"top"}); i++; }}
  footer(s,"CISO / CMIO Adoption Review",true);
  resultsSlide(pptx,"CISO / CMIO Adoption Review",
    "issue_determination is withheld from EVERY agent; submit_claim from every agent. An adverse UM recommendation is forwarded for a human determination — never auto-denied.",
    ["AI assists, drafts, flags, recommends; a licensed/credentialed human decides.",
     "Each withheld authority is enforced in code and verified by a passing test.",
     "PHI residency: in-account Bedrock under BAA; Guardrails block SSN/bank/card, anonymize PII.",
     "Tamper-evident: append-only DynamoDB (deny Update/Delete) + S3 Object Lock COMPLIANCE."],
    ["Phase 1: assessment + platform + denials wedge","Phase 2: expand + CSV/CSA + pen test",
     "Phase 3: run-ops + HITRUST roadmap","Go/no-go gate at each phase",
     "Nothing consequential is automated end-to-end"],
    "Full division of duties: docs/SHARED-RESPONSIBILITY-MATRIX.md.");
  return pptx.writeFile({fileName:"HPP-CIO-Adoption-Review.pptx"});
}


function buildPlatform(){
  const pptx=new pptxgen(); pptx.defineLayout({name:"W",width:13.333,height:7.5}); pptx.layout="W";
  titleSlide(pptx,"Care & Claims Platform","Care & Claims Orchestration Platform",
    "Coordinates the eight agents across a patient/member journey — without widening authority.");
  statSlide(pptx,"Care & Claims Platform","Why Orchestrate — Journeys Span Agents",
    "A denial becomes an appeal and a member call; an admission becomes a discharge draft, a care-plan update, and a follow-up. The platform sequences governed actions and compensates cleanly when a system fails.",
    [{num:"1 \u2192 4",cap:"agents a single denial \u2192 appeal \u2192 notify journey spans"},
     {num:"0",cap:"new authority granted \u2014 every step authorizes through the same MCP gateway"},
     {num:"100%",cap:"steps emit a PHI-masked, hash-chained compliance event"}],
    "Reference: care_platform/hpp_care_platform/ \u00b7 runnable with no API key.");
  problemSlide(pptx,"Care & Claims Platform",
    ["Journeys are fragmented across agents and systems of record; handoffs are manual and lose context.",
     "A half-finished journey (appeal filed, member never notified) is an operational and compliance risk.",
     "Sensitive data (42 CFR Part 2) crosses agency lines and needs a consent record, not just a per-tool check."],
    ["A durable saga with compensation \u2014 if a step fails, completed steps roll back in reverse.",
     "An AAL-gated consent ledger checked before any sensitive disclosure; escalate without consent.",
     "A compliance event bus \u2014 a tamper-evident, step-by-step evidence trail for the whole journey."],
    "The platform never widens authority \u2014 every step calls the same gateway with the same acting-user claims; a withheld tool stays denied.","");
  solutionSlide(pptx,"Care & Claims Platform",
    ["govern","canonical","consent","saga","events"],"the agents' own human gates",
    [{t:"Saga + compensation",d:"No half-finished journeys: a downstream failure compensates completed steps in reverse, all audited."},
     {t:"Consent ledger",d:"AAL2-gated; 42 CFR Part 2 scopes require an explicit grant or the journey escalates."},
     {t:"Authority never widens",d:"A test asserts a journey step calling a withheld tool (issue_determination) is denied by the same gateway."}]);
  archSlide(pptx,"Care & Claims Platform","each step \u2192 the owning agent's tools, through the gateway");
  resultsSlide(pptx,"Care & Claims Platform",
    "Orchestration is sequencing + compensation + evidence \u2014 never a new privilege. The human gates and withheld authorities of each agent apply unchanged.",
    ["AWS-native form: a Step Functions state machine (Catch \u2192 compensate; waitForTaskToken gate).",
     "Every forward and compensating step emits a hash-chained compliance event (verify_chain).",
     "Consent (42 CFR Part 2) is recorded at the journey level and enforced per-tool at the gateway.",
     "Adopt agent by agent \u2014 the same agents become saga steps unchanged."],
    ["Denial \u2192 resolution journey","Admission \u2192 follow-up journey","New-member onboarding","No half-finished journeys","Full evidence trail per journey"],
    "Platform story: ENTERPRISE-PLATFORM.md \u00b7 run: aws-native-reference/care-platform/local_runner.py");
  return pptx.writeFile({fileName:"HPP-Care-Claims-Orchestration-Platform.pptx"});
}

(async()=>{
  for(const a of AGENTS){ await buildAgentDeck(a); console.log("wrote",a.file+".pptx"); }
  await buildExec(); console.log("wrote Executive Overview");
  await buildCiso(); console.log("wrote CISO/CMIO Review");
  await buildPlatform(); console.log("wrote Care & Claims Platform");
})();
