import React, { useState } from 'react';
import Shell from './components/Shell';
import Dashboard from './pages/Dashboard';
import Assistant from './pages/Assistant';
import Forecast from './pages/Forecast';
import Knowledge from './pages/Knowledge';
import Evaluation from './pages/Evaluation';

export default function App(){
  const [page,setPage] = useState('dashboard');
  return <Shell page={page} setPage={setPage}>
    {page==='dashboard' && <Dashboard navigate={setPage}/>}
    {page==='assistant' && <Assistant/>}
    {page==='forecast' && <Forecast navigate={setPage}/>}
    {page==='knowledge' && <Knowledge/>}
    {page==='evaluation' && <Evaluation/>}
  </Shell>;
}
