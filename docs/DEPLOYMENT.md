# Publicacao da demonstracao

O frontend pode ser servido sob `/cases/simpar/`; o FastAPI continua recebendo
as rotas internamente na raiz. A publicacao sugerida usa Render para a API e
PostgreSQL e um Cloudflare Worker versionado no repositorio NeoFlip para
encaminhar somente esse caminho. O site NeoFlip pode continuar no GitHub Pages.

## Render

1. Crie um PostgreSQL gerenciado e um Web Service a partir deste repositorio,
   usando o `Dockerfile` existente.
2. Configure `DATABASE_URL` com a URL interna do PostgreSQL. O backend aceita
   URLs `postgres://` e `postgresql://` do provedor.
3. Configure `REQUIRE_AUTH=true`, `APP_USERNAME` e `APP_PASSWORD` com
   valores fortes. A aplicacao responde com erro se a autenticacao estiver
   habilitada, mas as credenciais nao estiverem definidas.
4. Configure `SECRET_KEY` com uma chave Fernet estavel. Gere uma com:

   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

5. O container compila o frontend com `VITE_BASE_PATH=/cases/simpar/` e carrega
   os dados ficticios apenas quando ainda nao existe o schema. O comando de
   seed apaga e recria o schema; nao o execute manualmente num banco com dados
   que queira preservar.
6. Anote a URL HTTPS publica do Web Service, por exemplo
   `https://<servico>.onrender.com`.

A aplicacao e os dados do seed sao uma demonstracao. A autenticacao HTTP Basic
serve apenas como barreira para a demonstracao; nao use conectores com
credenciais reais ou dados operacionais sem implementar SSO/RBAC, protecao
contra CSRF, auditoria e uma revisao de seguranca.

## Cloudflare e Registro.br

O DNS nao encaminha por caminho. Para conservar
`https://www.neoflip.com.br/cases/simpar`, o dominio precisa passar pelo
Cloudflare e o Worker do repositorio NeoFlip deve ser associado aos caminhos
`/cases/simpar*` do dominio raiz e de `www`.

1. Adicione `neoflip.com.br` ao Cloudflare. Revise os registros importados e
   copie todos os registros atuais do Registro.br, incluindo os usados pelo
   GitHub Pages, antes de trocar os nameservers. A troca de nameservers exige
   uma alteracao no painel do Registro.br e pode interromper o site se os
   registros nao forem reproduzidos corretamente.
2. Aguarde o Cloudflare confirmar a zona ativa. Mantenha os registros que
   atendem o GitHub Pages e confirme que o site principal continua abrindo em
   HTTPS.
3. Configure o Worker `neoflip-simpar-path` com a variavel `SIMPAR_ORIGIN`,
   usando a URL Render da etapa anterior, sem barra final.
4. No clone do repositorio `joaoppr/neoflip`, com Node.js instalado, autentique
   o Wrangler, defina a origem e publique:

   ```bash
   npx wrangler login
   npx wrangler secret put SIMPAR_ORIGIN
   npx wrangler deploy
   ```

5. Teste `/cases/simpar`, recarregue uma rota interna como
   `/cases/simpar/executivo` e confirme que o site principal continua
   funcionando.

O Worker remove `/cases/simpar` antes de encaminhar a requisicao; o frontend
inclui esse prefixo nos assets, nas chamadas da API e na navegacao interna.
As credenciais HTTP Basic do Render tambem protegem o acesso pelo Worker.
