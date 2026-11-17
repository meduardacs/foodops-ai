import React from 'react';
import { AlertTriangle, RotateCcw, LoaderCircle } from 'lucide-react';
export const SectionTitle = ({title,description,aside}) => <div className="section-head"><div><h2>{title}</h2>{description&&<p>{description}</p>}</div>{aside}</div>;
export function Busy({message='Carregando dados...'}) {return <div className="loading-panel"><LoaderCircle size={25} className="spin"/><span>{message}</span></div>}
export function Failure({error,onRetry}) {return <div className="error-panel"><AlertTriangle size={22}/><div><b>Não foi possível carregar</b><p>{error?.message || 'Verifique se a API está iniciada.'}</p></div>{onRetry&&<button className="btn btn-secondary" onClick={onRetry}><RotateCcw size={15}/> Tentar novamente</button>}</div>}
export const Empty = ({children}) => <div className="empty-state">{children}</div>;
export function PageIntro({eyebrow,title,description,aside}) {return <div className="page-intro"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{aside}</div>}
