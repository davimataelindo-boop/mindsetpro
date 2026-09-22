# Publicar o Mente Forte

## Opção recomendada: Render com o Blueprint

O arquivo `render.yaml` já descreve o serviço Docker, a rota de saúde e um disco persistente para manter o banco SQLite em `/app/data`.

1. Faça commit e push de todos os arquivos do projeto para a branch principal do repositório.
2. No Render, escolha a opção para criar um serviço a partir de um Blueprint.
3. Selecione o repositório e confirme o arquivo `render.yaml`.
4. Revise o nome do serviço e crie o serviço.
5. Aguarde o primeiro deploy e abra o endereço gerado pela plataforma.
6. Adicione no Render as variáveis `ADMIN_EMAIL` e `ADMIN_PASSWORD` definidas pelo responsável.
7. Crie uma conta de teste e valide login, pontuação, diário, plano e lembretes.
8. Abra `/admin.html` e teste a liberação manual de um plano premium.

O serviço expõe `/health`, que pode ser usado pela plataforma para verificar se o app está funcionando.

## Antes de abrir para usuários

- Use HTTPS e não compartilhe credenciais de teste.
- Faça um backup periódico do arquivo SQLite dentro do disco persistente.
- Defina uma política de privacidade e uma forma de contato.
- Teste a recuperação de senha antes de divulgar o cadastro.
- Para crescer para muitos usuários, migre o banco para PostgreSQL.

## Teste pós-deploy

Checklist mínimo:

- Cadastro com e-mail válido.
- Login e logout.
- Criação de cada tipo de plano.
- Conclusão de uma prática e atualização da pontuação.
- Criação de reflexão no diário.
- Ativação do lembrete com permissão do navegador.
- Reinício do serviço sem perder os dados.
