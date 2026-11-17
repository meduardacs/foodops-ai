import React,{useState,useRef,useEffect} from 'react';
import ReactMarkdown from 'react-markdown';
import { Sparkles, Send, RotateCcw, Copy, Check, Database, BookText, BrainCircuit,
  ArrowUpRight, MessageSquareText, Lightbulb, ChevronRight, ShieldCheck, AlertCircle, LoaderCircle } from 'lucide-react';
import { post } from '../lib/api';
import { PageIntro } from '../components/Shared';
const STARTERS=[
  {title:'O que mais vendeu?',desc:'Veja o ranking desta semana',question:'Quais foram os 5 produtos mais vendidos esta semana?'},
  {title:'Quanto produzir amanhã?',desc:'Previsão de demanda por item',question:'Quanto devo preparar para amanhã? Mostre os produtos prioritários.'},
  {title:'Como reduzir perdas?',desc:'Consulte os manuais internos',question:'O que diz nosso manual sobre controle de desperdício e validade?'},
  {title:'Como está o faturamento?',desc:'Análise dos últimos 7 dias',question:'Quanto faturamos na última semana e qual foi o ticket médio?'}
];
const LABEL={get_sales_summary:'Vendas SQL',get_top_products:'Produtos SQL',get_demand_forecast:'Modelo de previsão',search_knowledge:'Base documental',get_recent_orders:'Pedidos SQL',get_sales_timeseries:'Série de vendas'};

export default function Assistant(){
  const [messages,setMessages]=useState([]),[input,setInput]=useState(''),[busy,setBusy]=useState(false),[mode,setMode]=useState('auto'),[copied,setCopied]=useState(-1);
  const endRef=useRef(null),inputRef=useRef(null);
  useEffect(()=>{endRef.current?.scrollIntoView({behavior:'smooth',block:'end'})},[messages,busy]);
  async function send(text=input){
    const question=text.trim();if(!question||busy)return;
    const history=messages.filter(x=>x.role!=='error').map(x=>({role:x.role,content:x.role==='assistant'?x.content.slice(0,2300):x.content})).slice(-6);
    setMessages(old=>[...old,{role:'user',content:question}]);setInput('');setBusy(true);
    try{const response=await post('/chat',{message:question,mode,history});setMessages(old=>[...old,{role:'assistant',content:response.answer,meta:response}]);}
    catch(e){setMessages(old=>[...old,{role:'error',content:e.message}]);}
    finally{setBusy(false);inputRef.current?.focus();}
  }
  async function copy(value,index){try{await navigator.clipboard.writeText(value);setCopied(index);setTimeout(()=>setCopied(-1),1500)}catch{}}
  return <>
    <PageIntro eyebrow="SEU ASSISTENTE DE OPERAÇÕES" title="Decisões começam com uma pergunta." description="Converse com seus dados. O copiloto consulta vendas, previsões e documentos para responder." aside={<span className="assistant-indicator"><span className="status-dot"/> {mode==='local'?'Modo local':'IA com ferramentas'}</span>}/>
    <div className="chat-frame"><div className="chat-head"><div className="chat-head-avatar"><Sparkles size={22}/></div><div><strong>Copiloto FoodOps</strong><span>Consultas confiáveis à operação</span></div><div className="chat-controls"><label htmlFor="agent-mode">Modo</label><select id="agent-mode" value={mode} onChange={e=>setMode(e.target.value)}><option value="auto">Automático</option><option value="local">Local / sem API</option></select><button className="icon-button" title="Nova conversa" aria-label="Limpar conversa" onClick={()=>setMessages([])}><RotateCcw size={18}/></button></div></div>
    <div className="chat-messages">{messages.length===0?<div className="chat-welcome"><span className="welcome-icon"><Sparkles size={29}/></span><div className="welcome-hello">Olá! Sou seu copiloto operacional.</div><h2>O que você gostaria de descobrir hoje?</h2><p>Faço buscas no histórico de vendas, calculo previsões e encontro informações em documentos. Tudo com fontes identificáveis.</p><div className="prompt-grid">{STARTERS.map(item=><button key={item.title} className="prompt-card" onClick={()=>send(item.question)}><div><strong>{item.title}</strong><span>{item.desc}</span></div><ArrowUpRight size={17}/></button>)}</div><span className="chat-note"><ShieldCheck size={14}/> Os valores são gerados a partir de dados fictícios, não de uma operação real.</span></div>:<div className="chat-thread">{messages.map((item,i)=><div key={i} className={`message-line message-line--${item.role}`}>
      {item.role==='assistant'&&<div className="message-avatar"><Sparkles size={18}/></div>}
      <div className="message-body">{item.role==='user'?<div className="user-bubble">{item.content}</div>:item.role==='error'?<div className="message-error"><AlertCircle size={17}/> {item.content}</div>:<><div className="assistant-bubble"><ReactMarkdown>{item.content}</ReactMarkdown></div><div className="response-meta"><div className="tool-pills">{item.meta?.tools_used.map((tool,ix)=><span className="tool-pill" key={ix}>{tool==='search_knowledge'?<BookText size={13}/>:tool==='get_demand_forecast'?<BrainCircuit size={13}/>:<Database size={13}/>} {LABEL[tool]||tool}</span>)}</div><button title="Copiar resposta" className="copy-answer" onClick={()=>copy(item.content,i)}>{copied===i?<Check size={15}/>:<Copy size={15}/>}</button></div>{item.meta?.sources?.length>0&&<div className="source-list"><strong>Fontes consultadas</strong>{item.meta.sources.map((s,j)=><span key={j}><BookText size={13}/> {s.source} · {s.section}</span>)}</div>}</>}
      </div></div>)}{busy&&<div className="message-line message-line--assistant"><div className="message-avatar"><Sparkles size={18}/></div><div className="assistant-thinking"><LoaderCircle className="spin" size={17}/> Consultando os dados...</div></div>}<div ref={endRef}/></div>}</div>
    <form className="chat-compose" onSubmit={e=>{e.preventDefault();send()}}><div className="compose-inner"><MessageSquareText size={20}/><input ref={inputRef} aria-label="Mensagem para o copiloto" value={input} onChange={e=>setInput(e.target.value)} placeholder="Pergunte sobre vendas, demanda, estoque, procedimentos..." disabled={busy}/><button className="send-button" type="submit" disabled={busy||!input.trim()} aria-label="Enviar mensagem"><Send size={18}/></button></div><small>O copiloto pode errar. Confira informações antes de decidir sobre a operação.</small></form></div>
  </>;
}
