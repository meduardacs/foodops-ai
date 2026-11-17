import React,{useEffect,useState} from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { ShoppingBag, Wallet, ReceiptText, TrendingUp, TrendingDown, ArrowUpRight,
  Sparkles, ArrowRight, ChartColumnIncreasing, Package, Clock3, CalendarDays } from 'lucide-react';
import { get,money,number,shortDate } from '../lib/api';
import { Busy,Failure,PageIntro,SectionTitle } from '../components/Shared';

const CHART_COLORS = ['#214D3F','#418573','#88B4A5','#E5A564','#F3CC92'];

function StatCard({label,value,icon:Icon,foot,trend,decoration}){return <div className="stat-card">
  <div className="stat-top"><span>{label}</span><span className="stat-icon"><Icon size={20}/></span></div>
  <div className="stat-value">{value}</div>
  <div className="stat-foot">{typeof trend==='number'&&<span className={`trend-tag ${trend<0?'negative':''}`}>{trend>=0?<TrendingUp size={13}/>:<TrendingDown size={13}/>} {trend>0?'+':''}{trend}%</span>}<span>{foot}</span></div>
  {decoration&&<div className="stat-decoration"/>}
</div>}

export default function Dashboard({navigate}){
  const [days,setDays]=useState(7),[data,setData]=useState(null),[error,setError]=useState(null),[busy,setBusy]=useState(true),[version,setVersion]=useState(0);
  useEffect(()=>{let active=true;setBusy(true);setError(null);get(`/dashboard?days=${days}`).then(d=>{if(active){setData(d);setBusy(false)}}).catch(e=>{if(active){setError(e);setBusy(false)}});return()=>{active=false}},[days,version]);
  const s = data?.summary;
  return <>
    <PageIntro eyebrow="VISÃO GERAL DA OPERAÇÃO" title="Seu restaurante, em uma visão." description="Acompanhe suas vendas, entenda o movimento e tome decisões com confiança." aside={<div className="date-control"><CalendarDays size={17}/><select aria-label="Selecionar período" value={days} onChange={e=>setDays(Number(e.target.value))}><option value={7}>Últimos 7 dias</option><option value={14}>Últimos 14 dias</option><option value={30}>Últimos 30 dias</option></select></div>}/>
    <div className="notice-strip"><span className="notice-icon"><Sparkles size={17}/></span><div><strong>Bem-vindo ao FoodOps AI</strong><span>Este ambiente utiliza vendas fictícias para demonstrar análises e previsões.</span></div><button onClick={()=>navigate('assistant')}>Explorar copiloto <ArrowRight size={16}/></button></div>
    {busy ? <Busy/> : error ? <Failure error={error} onRetry={()=>setVersion(x=>x+1)}/> : <>
    <div className="stats-grid">
      <StatCard label="Faturamento" value={money(s.revenue)} icon={Wallet} foot="vs. período anterior" trend={s.revenue_growth_pct}/>
      <StatCard label="Pedidos concluídos" value={number(s.orders)} icon={ShoppingBag} foot={`${number(s.previous_orders)} no período anterior`}/>
      <StatCard label="Ticket médio" value={money(s.avg_ticket)} icon={ReceiptText} foot="por pedido concluído"/>
      <StatCard label="Produtos ativos" value={data.active_products} icon={Package} foot="cadastrados no cardápio" decoration/>
    </div>
    <div className="analytics-row">
      <div className="panel panel--wide"><SectionTitle title="Desempenho de vendas" description="Evolução do faturamento no período" aside={<span className="chart-legend"><span/> Receita (R$)</span>}/>
        <div className="chart-holder"><ResponsiveContainer width="100%" height="100%"><AreaChart data={data.daily_sales} margin={{top:8,right:4,left:-17,bottom:0}}>
        <defs><linearGradient id="salesFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3B8069" stopOpacity={.22}/><stop offset="97%" stopColor="#3B8069" stopOpacity={0}/></linearGradient></defs>
        <CartesianGrid stroke="#eff2ee" vertical={false}/><XAxis dataKey="date" tickFormatter={shortDate} axisLine={false} tickLine={false} tick={{fontSize:11,fill:'#89958E'}} dy={12} interval={days===30?4:days===14?2:0}/><YAxis tickFormatter={x=>x>=1000?`${(x/1000).toFixed(0)}k`:x} axisLine={false} tickLine={false} tick={{fontSize:11,fill:'#89958E'}}/>
        <Tooltip contentStyle={{borderRadius:12,border:'1px solid #e5ebe6',boxShadow:'0 12px 32px #182b2415'}} labelFormatter={shortDate} formatter={(v)=>[money(v),'Receita']}/>
        <Area type="monotone" dataKey="revenue" stroke="#2A745C" strokeWidth={2.5} fill="url(#salesFill)" activeDot={{r:5,strokeWidth:3,stroke:'#fff'}} />
        </AreaChart></ResponsiveContainer></div>
      </div>
      <div className="panel panel--narrow"><SectionTitle title="Receita por categoria" description="Distribuição do faturamento" />
        <div className="category-list">{data.categories.map((c,i)=><div key={c.name} className="category-item"><div className="cat-top"><span className="cat-name"><span className="cat-swatch" style={{background:CHART_COLORS[i%CHART_COLORS.length]}}/>{c.name}</span><b>{money(c.revenue)}</b></div><div className="cat-track"><div style={{width:`${c.revenue/(data.categories[0]?.revenue||1)*100}%`,background:CHART_COLORS[i%CHART_COLORS.length]}}/></div></div>)}</div>
      </div>
    </div>
    <div className="bottom-row">
      <div className="panel panel--products"><SectionTitle title="Produtos mais vendidos" description="Ranking por unidades vendidas" aside={<button className="text-action" onClick={()=>navigate('forecast')}>Ver previsões <ArrowUpRight size={15}/></button>}/>
      <div className="rank-list">{data.top_products.map((p,i)=><div className="rank-item" key={p.id}><span className={`rank-number rank-number--${i+1}`}>{String(i+1).padStart(2,'0')}</span><div className="rank-info"><strong>{p.name}</strong><small>{p.category}</small></div><div className="rank-units"><strong>{number(p.units)} un.</strong><small>{money(p.revenue)}</small></div><span className="rank-bar"><span style={{width:`${100*p.units/(data.top_products[0]?.units||1)}%`}}/></span></div>)}</div></div>
      <div className="right-column"><div className="ai-promo"><div className="promo-top"><span className="promo-spark"><Sparkles size={20}/></span><span>FOODOPS INTELLIGENCE</span></div><h3>Os números contam uma história. A IA te ajuda a ler.</h3><p>Pergunte sobre o movimento da semana, produtos populares ou quanto preparar amanhã.</p><button onClick={()=>navigate('assistant')}>Abrir copiloto <ArrowUpRight size={17}/></button><span className="promo-orbit promo-orbit-one"/><span className="promo-orbit promo-orbit-two"/></div>
      <div className="panel panel--recent"><SectionTitle title="Últimos pedidos" description="Registros mais recentes"/><div className="mini-orders">{data.recent_orders.slice(0,5).map(o=><div className="mini-order" key={o.id}><div className="order-id-box"><ShoppingBag size={16}/></div><div><strong>{o.id}</strong><small>{o.channel==='salao'?'Salão':o.channel==='balcao'?'Balcão':'Delivery'}</small></div><b>{money(o.total)}</b></div>)}</div></div></div>
    </div>
    </>}
  </>;
}
