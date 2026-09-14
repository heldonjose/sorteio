# Meta — Checklist para Produção e Análise do App

Objetivo: obter **Acesso Avançado** para:

- `instagram_business_basic`
- `instagram_business_manage_comments`

Sem isso, a API devolve os comentários **filtrados/vazios** para contas que não têm função no app (confirmado no protótipo).

---

## 1. Pré-requisitos

- [ ] Site em produção com **HTTPS** e domínio próprio (`docs/DEPLOY.md`)
- [ ] Login com Instagram funcionando de ponta a ponta no domínio
- [ ] Páginas públicas no ar:
  - [ ] `/privacidade/` (ver `POLITICA_DE_PRIVACIDADE.md`)
  - [ ] `/termos/` (ver `TERMOS_DE_USO.md`)
  - [ ] `/exclusao-de-dados/` (ver `EXCLUSAO_DE_DADOS.md`)
- [ ] Callbacks implementados e respondendo:
  - [ ] `POST /meta/deauthorize/`
  - [ ] `POST /meta/data-deletion/` (retorna `url` + `confirmation_code`)
- [ ] Nome do app **sem** "Insta", "Instagram", "Gram", "Facebook", "Meta"
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

### 4.1 Texto — `instagram_business_basic`

> [NOME_DO_PRODUTO] é uma plataforma para criadores e empresas realizarem sorteios transparentes com base nos comentários de suas próprias publicações no Instagram. Usamos instagram_business_basic para identificar a conta profissional que fez login (ID, nome de usuário, nome e foto de perfil) e listar as publicações da própria conta (miniatura, legenda, data, link e quantidade de comentários), permitindo que o usuário escolha qual publicação será usada no sorteio. Os dados são exibidos apenas para o próprio usuário autenticado e não são compartilhados com terceiros.

### 4.2 Texto — `instagram_business_manage_comments`

> Usamos instagram_business_manage_comments exclusivamente para LER os comentários (texto, nome de usuário, data e respostas) da publicação escolhida pelo próprio dono da conta. A partir desses comentários, o usuário aplica regras (uma participação por pessoa, palavra-chave obrigatória, número mínimo de marcações, exclusão de usuários) e realiza um sorteio aleatório dos ganhadores. Não publicamos, respondemos, ocultamos nem excluímos comentários. Os comentários ficam armazenados por no máximo 90 dias para que o usuário possa auditar o resultado, e são excluídos antes disso se o usuário apagar a conta ou revogar o acesso.

### 4.3 Roteiro do vídeo (screencast, 2–4 min, em inglês ou com legendas em inglês)

A Meta recomenda mostrar **o fluxo completo de login da Meta** e **onde cada dado aparece**.

1. Abrir `https://sorteio.repsys.com.br` (mostrar a URL na barra).
2. Clicar em **"Entrar com Instagram"**.
3. Mostrar a **tela de login/consentimento do Instagram** com as permissões listadas, e autorizar.
4. Voltar ao painel: destacar **@username e foto** → *instagram_business_basic*.
5. Clicar em **Novo sorteio**: mostrar a **grade de posts** → *instagram_business_basic*.
6. Escolher um post e mostrar o **carregamento dos comentários** e a **lista de comentários** → *instagram_business_manage_comments*.
7. Configurar regras e clicar em **Sortear**: mostrar ganhador(es).
8. Mostrar **Histórico** e **Minha conta → Excluir conta/desconectar**.
9. (Opcional) Mostrar as páginas de Privacidade e Exclusão de dados.

Dicas: resolução legível (1080p), sem cortes nas etapas de login, cursor visível, legendas curtas explicando cada passo.

### 4.4 Instruções de teste para o revisor

> 1. Access https://sorteio.repsys.com.br and click "Log in with Instagram".
> 2. Use the test Instagram professional account: username `[CONTA_TESTE]`, password `[SENHA_TESTE]`. (Two-factor authentication is disabled for this account.)
> 3. After login, click "New raffle", select any post with comments, wait for comments to load, keep default rules and click "Draw".
> 4. The winner is displayed along with the list of eligible comments. History is available under "My raffles".

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
