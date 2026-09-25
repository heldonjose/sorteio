# Meta — Checklist para Produção e Análise do App

Objetivo: obter **Acesso Avançado** para:

- `instagram_business_basic`
- `instagram_business_manage_comments`

Sem isso, a API devolve os comentários **filtrados/vazios** para contas que não têm função no app (confirmado no protótipo).

---

## 1. Pré-requisitos

- [ ] Site em produção com **HTTPS** e domínio próprio (`docs/DEPLOY.md`)
- [ ] Login com Instagram funcionando de ponta a ponta no domínio
- [x] Páginas públicas implementadas (falta publicar em produção):
  - [x] `/privacidade/` — LGPD completa
  - [x] `/termos/` — 12 cláusulas
  - [x] `/exclusao-de-dados/` — 3 formas de exclusão
  - [x] `/exclusao-de-dados/status/<code>/` — página de confirmação para o revisor
- [x] Callbacks implementados:
  - [x] `POST /meta/deauthorize/` — apaga token, registra `deauthorized_at`
  - [x] `POST /meta/data-deletion/` — apaga token + comentários, retorna `url` + `confirmation_code`
- [ ] **ATENÇÃO**: Nome do app **sem** "Insta", "Instagram", "Gram", "Facebook", "Meta" — o nome de produto "Sorteio Insta" precisa ser trocado antes de submeter. Sugestões: "Sorteio Pro", "SorteioBR", "Sorteamos"
- [ ] Chave secreta do app **redefinida** (a antiga apareceu em print)

## 2. Verificação da empresa

Meta Business Suite → **Configurações → Central de segurança → Verificação da empresa**

- [ ] Nome jurídico **exatamente** como no cartão CNPJ: `ALINE QUELE DA ROCHA DANTAS 05455124412` (empresário individual; nome fantasia "Soluções e Sistemas"). O portfólio empresarial da Meta deve usar esse nome
- [ ] Endereço do cartão CNPJ: R. Cabo José Benício, 102, Maternidade, Patos/PB, CEP 58701-384
- [ ] Documento (cartão CNPJ, contrato social ou conta de consumo no nome da empresa)
- [ ] Endereço e telefone que batem com o documento
- [ ] Domínio verificado (Configurações da empresa → Segurança da marca → Domínios: meta-tag ou TXT no DNS)
- [ ] E-mail com o domínio da empresa (ajuda a aprovar mais rápido)

Pode levar de alguns dias a 2 semanas. Dá para iniciar em paralelo ao desenvolvimento.

## 3. Configurações básicas do app

**Configurações do app → Básico**

- [ ] Nome de exibição: `[NOME_DO_PRODUTO]`
- [ ] E-mail de contato: `alinnequele@gmail.com`
- [ ] Domínios do app: `sorteio.repsys.com.br`
- [ ] URL da Política de Privacidade
- [ ] URL dos Termos de Serviço
- [ ] URL de instruções de exclusão de dados
- [ ] Ícone 1024 × 1024 px (sem logo do Instagram)
- [ ] Categoria: *Utilidades* / *Negócios e páginas*
- [ ] Empresa vinculada (a verificada)

**Instagram → Configuração da API com login do Instagram → Configure o login da empresa**

- [ ] URI de redirecionamento: `https://sorteio.repsys.com.br/auth/instagram/callback/`
- [ ] Callback de desautorização: `https://sorteio.repsys.com.br/meta/deauthorize/`
- [ ] Solicitação de exclusão de dados: `https://sorteio.repsys.com.br/meta/data-deletion/`

**Não é necessário:** webhooks, "Facebook Login for Business" nem `public_profile` avançado. Aquele aviso da tela do Login do Facebook pode ser ignorado.

## 4. Pedido de permissões

**Análise do app → Permissões e recursos** → "Solicitar acesso avançado" nas duas permissões. Para cada uma, a Meta pede uma descrição de uso, um vídeo e instruções de teste.

### 4.1 Texto — `instagram_business_basic` (enviar em inglês)

> Sorteio Pro lets Instagram professional accounts run transparent giveaways using comments on their own posts. We use instagram_business_basic to identify the logged-in account (ID, username, name and profile picture) and to list the account's own posts (thumbnail, caption, date, permalink and comment count), so the user can choose which post to use in the giveaway. This data is shown only to the authenticated user and is never shared with third parties.

### 4.2 Texto — `instagram_business_manage_comments` (enviar em inglês)

> We use instagram_business_manage_comments only to READ the comments (text, username, timestamp and replies) of the post selected by the account owner. The user then applies rules (one entry per person, required keyword, minimum number of mentions, excluded users) and a random winner is drawn from the eligible comments. We never publish, reply to, hide or delete comments. Comments are stored for up to 90 days so the user can audit the result, and are deleted earlier if the user deletes their account or revokes access.

**Observação para o revisor** (campo de notas do envio):

> This is not a server-to-server app: users authenticate through the front-end Instagram Login flow shown in the screencast. The app UI is in English by default (EN/PT switch in the top bar).

### 4.3 Roteiro do vídeo (screencast)

**1º envio rejeitado (23/09/2026)** por "screencast não alinhado com detalhes do caso de uso". A Meta exige: login completo da Meta, tela de consentimento com o usuário concedendo acesso, caso de uso completo, **interface em inglês** e legendas explicando telas e botões.

Um único vídeo, de 2 a 4 minutos, enviado nas duas permissões. As legendas prontas estão em `docs/projeto/meta/screencast_legendas.srt`; importe no editor e ajuste os tempos.

#### Antes de gravar

- [ ] Deploy da versão bilíngue, com `DEFAULT_LANGUAGE=en` no `.env` do servidor e o site abrindo em inglês
- [ ] **Remover a autorização antiga**, senão a tela de consentimento não aparece. No Instagram da conta de teste: Configurações → Permissões do site → Apps e sites → Ativos → Sorteio Pro → Remover
- [ ] No admin do Sorteio Pro, apagar o usuário da conta de teste para gravar um primeiro acesso limpo
- [ ] Navegador em inglês e anônimo, para as telas do Instagram também saírem em inglês: `google-chrome --lang=en-US --incognito`
- [ ] Post da conta de teste com 15 a 30 comentários de contas **Testador do Instagram**, com @menções. Em modo desenvolvimento, comentários de outras contas não aparecem
- [ ] Gravador (OBS ou `Ctrl+Shift+Alt+R` no GNOME) em 1080p, janela maximizada, **barra de endereço visível**, sem favoritos nem extensões. Áudio não é necessário

#### Cenas

| # | Na tela | Legenda (inglês) |
|---|---|---|
| 1 | Abrir `https://sorteio.repsys.com.br` e rolar a landing devagar | Sorteio Pro is a web app for Instagram professional accounts to run transparent giveaways based on comments on their own posts. |
| 2 | Mostrar o seletor **EN \| PT** na barra | The interface is in English (EN/PT switch in the top bar). |
| 3 | Clicar em **Log in with Instagram** | The user clicks "Log in with Instagram" to start the Meta login flow. |
| 4 | Login do Instagram: usuário e senha, **sem cortes** | Instagram Login: the user signs in with their Instagram professional account. |
| 5 | **Tela de consentimento**: parar 3 a 4 s na lista de permissões e clicar em **Allow** | The user grants Sorteio Pro access to instagram_business_basic and instagram_business_manage_comments. |
| 6 | **Dashboard**: destacar @usuário e saldo | instagram_business_basic: we display the logged-in account's username and profile to identify the user. |
| 7 | **New giveaway**: grade de posts | instagram_business_basic: we list the user's own posts (thumbnail, caption, comment count) so they can choose one for the giveaway. |
| 8 | Selecionar o post e clicar em **Use this post** | The user selects the post whose comments will be used. |
| 9 | Carregamento: contagem de comentários subindo | instagram_business_manage_comments: we read the comments (text, username, timestamp, replies) of the selected post. Read-only: we never post, reply to, hide or delete comments. |
| 10 | **Rules**: alterar uma regra (ex.: 1 menção) e ver a contagem mudar | The user applies rules to the loaded comments: one entry per person, required keyword, minimum mentions, excluded users. |
| 11 | **Draw now** e ganhador na tela | A random winner is drawn from the eligible comments. |
| 12 | Abrir o **Public certificate** | A public certificate with a SHA-256 hash lets participants verify the result. |
| 13 | No Dashboard, **See full history**; depois **My account** (clicar no @usuário): mostrar **Delete my account**, **sem clicar** | Users can view past giveaways and disconnect or delete their account and data at any time. |
| 14 | Rodapé → **Privacy** e **Data deletion** | Privacy Policy and Data Deletion instructions are publicly available. |

#### Dicas

- Mover o cursor devagar e parar 2 a 3 s em cada tela importante, para dar tempo de ler a legenda
- Só cortar esperas longas; **nunca cortar entre as cenas 3 e 6** (login + consentimento inteiros)
- Destacar com retângulo ou seta onde cada permissão aparece (cenas 6, 7 e 9). Kdenlive ou Clipchamp resolvem isso e as legendas
- Borrar senha ou código 2FA se aparecerem

### 4.4 Instruções de teste para o revisor

> 0. The interface is in English by default (EN/PT switch in the top bar).
> 1. Access https://sorteio.repsys.com.br and click "Log in with Instagram".
> 2. Use the test Instagram professional account: username `[CONTA_TESTE]`, password `[SENHA_TESTE]`. (Two-factor authentication is disabled for this account.)
> 3. After login, on the Dashboard click "New giveaway", select any post with comments and click "Use this post". Wait for the comments to load, keep the default rules and click "Draw now".
> 4. The winner is displayed along with the list of eligible comments. Past giveaways are listed under "History".

- [ ] Conta de teste: **Instagram institucional da empresa** (profissional, tipo Empresa), compartilhado entre os produtos. Criar **semanas antes** da análise e usar normalmente (foto, bio, e-mail e telefone confirmados, posts), para evitar bloqueio por "atividade suspeita" quando o revisor entrar de outro país
- [ ] Conteúdo mínimo: 3 a 5 posts (1 Reels) e um post com 15 a 30 comentários de **várias contas Testador do Instagram**, com @marcações e hashtag. Em modo desenvolvimento, comentários de contas sem função no app **não aparecem**
- [ ] Adicionar essa conta como **Testador do Instagram** no app
- [ ] Na véspera: desativar 2FA. Durante a análise: acompanhar e-mail e WhatsApp para códigos de verificação
- [ ] Depois da análise: **trocar a senha e reativar 2FA** (a senha foi entregue ao revisor)

## 5. Depois da aprovação

- [ ] Alternar **Modo do aplicativo → Ao vivo**
- [ ] Testar com uma conta **sem** função no app: os comentários devem aparecer
- [ ] Monitorar e-mails e "Ações necessárias" da Meta (verificações anuais de uso de dados)
- [ ] Manter as URLs legais sempre no ar (se caírem, o app pode ser restringido)

## 6. Motivos comuns de reprovação

- Vídeo não mostra o login da Meta ou onde a permissão é usada
- Revisor não consegue logar (conta com 2FA, credenciais erradas, site fora do ar)
- Política de privacidade genérica, sem citar dados do Instagram, retenção e exclusão
- Nome/ícone usando marca do Instagram
- Pedir permissões que o app não usa
