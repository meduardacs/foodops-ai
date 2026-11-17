export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, options);
  let data;
  try { data = await response.json(); }
  catch { throw new Error('Resposta inválida do servidor.'); }
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : `Erro ${response.status} ao consultar API.`);
  }
  return data;
}
export const get = path => api(path);
export const post = (path, body) => api(path, {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
});
export const money = n => new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(n || 0);
export const number = n => new Intl.NumberFormat('pt-BR').format(n || 0);
export const shortDate = value => {
  if (!value) return '—';
  const date = new Date(value.slice(0, 10) + 'T12:00:00');
  return new Intl.DateTimeFormat('pt-BR', {day:'2-digit',month:'short'}).format(date);
};
export const fullDate = value => {
  if (!value) return '—';
  const date = new Date(value.slice(0, 10) + 'T12:00:00');
  return new Intl.DateTimeFormat('pt-BR',{day:'numeric',month:'long',year:'numeric'}).format(date);
};
