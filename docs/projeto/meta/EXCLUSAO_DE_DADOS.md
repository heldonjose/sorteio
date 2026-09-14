# Instruções de Exclusão de Dados — [NOME_DO_PRODUTO]

> Página pública em `https://sorteio.repsys.com.br/exclusao-de-dados/`. A Meta exige esta URL **ou** um callback. Faremos **os dois**.

**Última atualização:** [DATA]

Você pode pedir a exclusão dos seus dados da plataforma [NOME_DO_PRODUTO] a qualquer momento, de três formas:

## Opção 1 — Pela plataforma
1. Entre em **sorteio.repsys.com.br** com sua conta do Instagram.
2. Acesse **Minha conta**.
3. Clique em **Excluir minha conta e meus dados** e confirme.

A exclusão é imediata para token de acesso, dados de perfil e comentários carregados.

## Opção 2 — Pelo Instagram
1. No Instagram, vá em **Configurações e privacidade → Permissões do site → Apps e sites**
   (ou acesse https://www.instagram.com/accounts/manage_access/ no navegador).
2. Em **Ativos**, encontre **[NOME_DO_PRODUTO]** e clique em **Remover**.
3. A Meta nos avisa automaticamente. Excluímos seus dados e geramos um **código de confirmação**, que você pode consultar em `https://sorteio.repsys.com.br/exclusao-de-dados/status/<código>/`.

## Opção 3 — Por e-mail
Envie um e-mail para **alinnequele@gmail.com** com o assunto "Exclusão de dados" informando o seu @ do Instagram. Respondemos em até 15 dias.

## O que é excluído
- Token de acesso ao Instagram
- Dados do perfil (@, nome, foto)
- Comentários carregados dos sorteios
- Histórico de sorteios e certificados públicos

## O que pode ser mantido (por obrigação legal)
- Registros de pedidos e pagamentos, **anonimizados**, por até 5 anos (obrigação fiscal)
- Registros de acesso (IP, data e hora) por 6 meses (Marco Civil da Internet)

## Pessoas que comentaram em um post sorteado
Se você comentou em uma publicação usada em sorteio e quer que seu comentário seja removido da nossa base, escreva para **alinnequele@gmail.com** informando o seu @ e o link da publicação.

---

## Nota técnica (não publicar): callback da Meta

`POST /meta/data-deletion/`: a Meta envia `signed_request` (form-urlencoded).

1. Separar `assinatura.payload` pelo ponto; decodificar os dois em base64url.
2. Validar `HMAC-SHA256(payload, INSTAGRAM_APP_SECRET) == assinatura` (comparação em tempo constante).
3. Ler `user_id` do payload JSON e agendar a exclusão (tarefa Celery).
4. Criar `DataDeletionRequest(confirmation_code, ig_user_id, status, created_at)`.
5. Responder:
   ```json
   { "url": "https://sorteio.repsys.com.br/exclusao-de-dados/status/ABC123/", "confirmation_code": "ABC123" }
   ```

`POST /meta/deauthorize/` segue a mesma validação: apagar o token e marcar `deauthorized_at`.
