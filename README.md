# mindsetpro

Aplicação full-stack de treinamento semanal de mentalidade, feita com Python puro + SQLite + HTML/CSS/JavaScript.

## Inclui

- Cadastro, login, sessão por cookie HttpOnly e logout
- Pontuação: +25 por sessão concluída, +10 por reflexão e bônus por sequência
- Sequência de dias e progresso do plano
- Diário de pensamentos com humor e histórico
- Sistema semanal com 7 práticas: foco, confiança, resiliência e visão
- Troca de foco e práticas diárias
- Página de atividades por tópico em `/atividades.html`
- PWA instalável
- Lembrete diário via Notification API + Service Worker neste dispositivo
- Catálogo de planos premium focados em estudos, com intenções de foco, memória, provas e rotina
- Endpoint `/api/study-offers` para catálogo premium e `/health` para monitoramento

## Rodar localmente

Requer Python 3.10+; não precisa instalar pacotes externos.

```bash
cd apps/mente-forte
python3 server.py
```

Abra `http://localhost:8000`.

Para mudar a porta:

```bash
PORT=8080 python3 server.py
```

## Deploy

A aplicação pode ser executada em qualquer serviço que aceite um processo Python. O `Dockerfile` já está incluído. Em produção:

1. Use HTTPS (necessário para notificações e boas práticas de sessão).
2. Defina `PORT` conforme o provedor.
3. Monte um volume persistente em `/app/data` para preservar o SQLite.
4. Para vários processos/instâncias, troque SQLite por PostgreSQL e coloque um proxy HTTPS na frente.
5. O lembrete atual funciona quando o usuário abre o app nesse dispositivo. Para push em segundo plano mesmo com o app fechado, conecte um provedor Web Push/VAPID e um job agendado no servidor. Os planos premium de estudos estão apresentados como pré-lançamento; o checkout ainda não está integrado.

## Segurança antes de produção

Trocar SQLite por PostgreSQL em escala, ativar HTTPS, configurar política de origem, adicionar rate limiting, rotação/limpeza de sessões, backup e recuperação de banco, além de logs e monitoramento.
