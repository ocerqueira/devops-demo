# devops-demo

Monorepo mínimo para testar o fluxo **GitHub → build de imagem → GHCR → Portainer → deploy automático**.

```
.
├── backend/            FastAPI com endpoint /api/status (checa o Postgres)
├── frontend/           HTML + nginx (console de status) — proxy /api -> backend
├── .github/workflows/  GitHub Actions: build/push das imagens + webhook do Portainer
└── docker-compose.yml  stack: db (Postgres) + backend + frontend
```

O endpoint `/api/status` devolve algo assim:

```json
{ "status": "ok", "service": "backend", "version": "1.0.0", "database": "connected", "timestamp": "..." }
```

O frontend consulta esse endpoint a cada 3s e mostra na tela. **A versão exibida vem da variável `APP_VERSION`** — é o que você vai mudar para provar que o deploy automático aconteceu.

---

## 1. Testar localmente (sem Portainer)

```bash
docker compose up --build
```

Abra http://localhost:8080 — o console deve ficar verde (OPERACIONAL) e mostrar `database: connected`.

---

## 2. Subir para o GitHub

```bash
git init
git add .
git commit -m "projeto de exemplo devops-demo"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/devops-demo.git
git push -u origin main
```

O workflow `.github/workflows/build.yml` roda a cada push na `main`:
1. Faz build das imagens `backend` e `frontend`.
2. Publica no **GHCR** (`ghcr.io/SEU_USUARIO/devops-demo-backend:latest` e `-frontend:latest`).
3. Dispara o webhook do Portainer (passo 4).

> **Deixe os pacotes do GHCR públicos** (na aba *Packages* do seu perfil → *Package settings* → *Change visibility* → Public). Assim o Portainer puxa as imagens sem precisar de login no registry. Se preferir mantê-los privados, adicione as credenciais do GHCR em *Registries* no Portainer.

---

## 3. Criar a stack no Portainer (a partir do Git)

No Portainer: **Stacks → Add stack → Repository**.

- **Repository URL**: `https://github.com/SEU_USUARIO/devops-demo`
- **Repository reference**: `refs/heads/main`
- **Compose path**: `docker-compose.yml`
- **Environment variables** (importante): adicione
  - `IMAGE_PREFIX` = `ghcr.io/SEU_USUARIO/devops-demo`
  
  Isso faz a stack puxar as imagens do GHCR em vez de tentar buildar.
- Ative **GitOps updates / Automatic updates** e escolha **Webhook**.

Copie a **webhook URL** que o Portainer gera.

---

## 4. Ligar o webhook ao GitHub

No repositório: **Settings → Secrets and variables → Actions → New repository secret**:

- Nome: `PORTAINER_WEBHOOK_URL`
- Valor: a URL de webhook do Portainer

Pronto. O último passo do workflow chama essa URL, e o Portainer redeploya a stack puxando as imagens novas.

> Alternativa ao webhook: em vez do secret, deixe o GitOps do Portainer no modo **Polling** (ex. a cada 5 min). Mas atenção — o polling olha o **repositório** (mudanças no compose), não o registry. Para refletir mudanças de código, o webhook disparado *depois* do build é o caminho confiável.

---

## 5. Testar o deploy automático ponta a ponta

1. Edite `docker-compose.yml` e troque `APP_VERSION: "1.0.0"` por `"1.1.0"`.
   (ou mude algo no `backend/app/main.py` / no HTML)
2. `git commit -am "v1.1.0" && git push`
3. Acompanhe a aba **Actions** no GitHub: build → push → webhook.
4. Recarregue http://SEU_SERVIDOR:8080 — a versão na tela vira **v1.1.0** sozinha.

Se a versão mudou sem você tocar no servidor, o fluxo inteiro está funcionando.

---

## Por que precisa do build + re-pull?

Atualizar só o compose pelo Git **não** atualiza o código da aplicação. Quem carrega o código novo é a **imagem** reconstruída pelo GitHub Actions e publicada no GHCR. O webhook então manda o Portainer fazer *re-pull* dessas imagens. Por isso o pipeline separa **build** (Actions) de **deploy** (Portainer).
