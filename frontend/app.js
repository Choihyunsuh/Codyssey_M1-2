const API = (window.API_BASE_URL || "").replace(/\/$/, "");
let conversationId = null;
const $ = (id) => document.getElementById(id);
const fmt = (n) => Number(n).toLocaleString("ko-KR", {maximumFractionDigits:2});
async function api(path, options={}) {
  const response = await fetch(API + path, {headers:{"Content-Type":"application/json", ...(options.headers||{})}, ...options});
  if (!response.ok) { const detail = await response.text(); throw new Error(detail || response.statusText); }
  return response.json();
}
function showMessage(role, text) { const el=document.createElement("div"); el.className="bubble "+role; el.textContent=text; $("messages").append(el); $("messages").scrollTop=$("messages").scrollHeight; }
async function refreshData() {
  try {
    const [s, rows] = await Promise.all([api("/api/data/summary"),api("/api/data")]);
    $("api-status").textContent="API 연결됨"; $("period").textContent=s.period||"데이터 없음"; $("count").textContent=s.count;
    $("average").textContent=s.metrics.average ? fmt(s.metrics.average)+"원" : "—"; $("trend").textContent=s.trend||"—";
    $("data-rows").replaceChildren();
    [...rows].reverse().slice(0,100).forEach(r=>{const tr=document.createElement("tr"); tr.innerHTML="<td></td><td></td><td></td><td></td>"; tr.children[0].textContent=r.date; tr.children[1].textContent=fmt(r.value); tr.children[2].textContent=r.memo||""; const b=document.createElement("button");b.textContent="삭제";b.onclick=async()=>{if(confirm(r.date+" 기록을 삭제할까요?")){try{await api("/api/data/"+r.id,{method:"DELETE"});refreshData()}catch(e){alert(e.message)}}};tr.children[3].append(b);$("data-rows").append(tr);});
  } catch(e) {$("api-status").textContent="API 연결 필요"; $("period").textContent="백엔드 주소를 설정하세요"; console.error(e);}
}
async function refreshHistory(){try{const items=await api("/api/conversations");$("conversations").replaceChildren();items.forEach(c=>{const b=document.createElement("button");b.className="conversation";b.textContent=(c.messages?.find(m=>m.role==="user")?.content||"대화").slice(0,45);b.onclick=async()=>{try{const full=await api("/api/conversations/"+c.id);conversationId=full.id;$("messages").replaceChildren();full.messages.forEach(m=>showMessage(m.role==="assistant"?"assistant":"user",m.content));}catch(e){alert(e.message)}};$("conversations").append(b);});}catch(e){console.error(e)}}
$("chat-form").onsubmit=async(e)=>{e.preventDefault();const input=$("prompt");const message=input.value.trim();if(!message)return;showMessage("user",message);input.value="";$("send").disabled=true;$("send").textContent="답변 중…";try{const out=await api("/api/chat",{method:"POST",body:JSON.stringify({message,conversation_id:conversationId})});conversationId=out.conversation_id;showMessage("assistant",out.answer);refreshHistory();}catch(err){showMessage("assistant","요청에 실패했습니다. API 설정과 백엔드 로그를 확인해 주세요.");console.error(err)}finally{$("send").disabled=false;$("send").textContent="보내기";}};
$("data-form").onsubmit=async(e)=>{e.preventDefault();try{await api("/api/data",{method:"POST",body:JSON.stringify({date:$("date").value,value:Number($("value").value),memo:$("memo").value})});e.target.reset();refreshData()}catch(err){alert(err.message)}};
$("refresh").onclick=refreshData;$("load-history").onclick=refreshHistory;$("new-chat").onclick=()=>{conversationId=null;$("messages").replaceChildren();showMessage("assistant","새 대화를 시작했어요. 환율 데이터에 관해 질문해 주세요.")};
refreshData();refreshHistory();