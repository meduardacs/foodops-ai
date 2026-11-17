# Abrir no Windows sem se perder nos diretórios

1. Instale Python e Node.js. Extraia a pasta `foodops-ai` do ZIP.
2. Dê dois cliques em `iniciar-backend.bat`. Na primeira vez, ele cria um ambiente virtual, instala as bibliotecas Python e inicia a API. Deixe a janela aberta.
3. Dê dois cliques em `iniciar-frontend.bat`. Na primeira vez, ele instala dependências React; depois inicia a interface. Deixe a janela aberta.
4. Acesse `http://localhost:5173` no navegador.
5. Para encerrar, pressione `Ctrl+C` em cada terminal, ou feche as duas janelas.

Se preferir VS Code, abra a pasta raiz e use dois terminais Git Bash. Em um:

```bash
cd backend
py -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Em outro:

```bash
cd frontend
npm install
npm run dev
```

Se o `py` não existir, tente `python`. O modo padrão usa SQLite, não exige PostgreSQL e não exige chave OpenAI.

**Se aparecer erro de dependência:** confira internet, se você abriu o terminal na pasta correta e a versão do Python / Node. O frontend não funciona sem instalar os pacotes do `package.json`; o backend não funciona sem instalar `backend/requirements.txt`.
