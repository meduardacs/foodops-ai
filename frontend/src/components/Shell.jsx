import React, { useEffect, useState } from 'react';
import { LayoutDashboard, Sparkles, ChartNoAxesCombined, BookOpenText, FlaskConical,
  ChefHat, ChevronRight, ChevronDown, ArrowUpRight, PanelLeftClose, Menu, X,
  CircleHelp, Database, ShieldCheck, Server } from 'lucide-react';
import { get } from '../lib/api';

const NAV = [
  {id:'dashboard',label:'Visão geral',icon:LayoutDashboard},
  {id:'assistant',label:'Copiloto IA',icon:Sparkles},
  {id:'forecast',label:'Previsões',icon:ChartNoAxesCombined},
  {id:'knowledge',label:'Documentos',icon:BookOpenText},
  {id:'evaluation',label:'Avaliação técnica',icon:FlaskConical},
];

export default function Shell({page,setPage,children}) {
  const [menuOpen,setMenuOpen] = useState(false);
  const [health,setHealth] = useState(null);
  useEffect(() => { get('/health').then(setHealth).catch(() => setHealth(null)); },[]);
  const current = NAV.find(x=>x.id===page) || NAV[0];
  const navigate = id => {setPage(id);setMenuOpen(false);window.scrollTo({top:0,behavior:'smooth'});};
  return <div className="app-layout">
    {menuOpen && <div className="mobile-overlay" onClick={()=>setMenuOpen(false)} />}
    <aside className={`sidebar ${menuOpen ? 'sidebar--open':''}`}>
      <div className="brand" role="button" tabIndex={0} onClick={()=>navigate('dashboard')} onKeyDown={e=>e.key==='Enter'&&navigate('dashboard')}>
        <span className="brand-symbol"><ChefHat size={24} strokeWidth={2.1}/></span>
        <span className="brand-text">foodops<span className="brand-dot">.</span><span className="brand-ai">ai</span><small>INTELLIGENCE PLATFORM</small></span>
        <button className="sidebar-close" onClick={e=>{e.stopPropagation();setMenuOpen(false);}} aria-label="Fechar menu"><X size={18}/></button>
      </div>
      <div className="sidebar-menu">
        <div className="side-section-label">WORKSPACE</div>
        {NAV.map(item=><button key={item.id} className={`nav-item ${page===item.id?'active':''}`} onClick={()=>navigate(item.id)}>
          <item.icon size={19} strokeWidth={1.9}/><span>{item.label}</span>{page===item.id&&<span className="nav-active-dot"/>}
        </button>)}
        <div className="side-section-label side-section-label--space">AMBIENTE</div>
        <div className="side-status"><Database size={17} /><span>Dados demonstrativos</span><span className="green-dot"/></div>
        <div className="side-status"><Server size={17}/><span>{health?.database === 'postgresql'?'PostgreSQL':'SQLite local'}</span></div>
      </div>
      <div className="side-bottom">
        <div className="side-tip"><span className="side-tip-icon"><Sparkles size={17}/></span><strong>Uma operação mais inteligente</strong><p>Transforme dados em decisões com o seu copiloto.</p><button onClick={()=>navigate('assistant')}>Conversar com a IA <ArrowUpRight size={15}/></button></div>
        <div className="side-footer"><div className="avatar">FO</div><span><strong>Restaurante Demo</strong><small>Ambiente de demonstração</small></span><ChevronDown size={16}/></div>
      </div>
    </aside>
    <div className="main-wrapper">
      <header className="topbar">
        <div className="topbar-left"><button className="mobile-menu" onClick={()=>setMenuOpen(true)} aria-label="Abrir menu"><Menu size={22}/></button>
          <span className="crumb">Workspace</span><ChevronRight size={15} className="crumb-arrow"/><strong>{current.label}</strong></div>
        <div className="topbar-right"><span className="server-status"><span className={`status-dot ${health?'':'status-dot--off'}`}/>{health?'Sistema operacional':'API desconectada'}</span><span className="topbar-divider"/><span className="demo-badge"><ShieldCheck size={14}/> Modo demonstração</span><span className="top-avatar">FO</span></div>
      </header>
      <main className="main-content">{children}<footer className="footer-line">FoodOps AI · Projeto demonstrativo com dados sintéticos <span>Feito para decisões mais inteligentes, não para adivinhações.</span></footer></main>
    </div>
  </div>;
}
