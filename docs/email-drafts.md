# Etapa 8 — Rascunhos de e-mail com revisão manual

O Sentinela pode criar um arquivo Markdown editável a partir de uma tarefa concluída na fila. O recurso não envia e-mails, não conecta a servidores SMTP e não chama serviços de e-mail.

## Gerar pelo terminal

1. Consulte a fila e encontre o ID de uma tarefa concluída:

```bash
python -m sentinela.queue_cli status
```

2. Gere o rascunho:

```bash
python -m sentinela.email_drafts --job-id 12
```

Substitua `12` por um ID real. O arquivo será criado em `reports/email-drafts/job-12.md`. Somente tarefas concluídas de consulta NVD, auditoria passiva ou verificação ativa limitada são aceitas. Gerar novamente o mesmo ID substitui o arquivo atomicamente.

## Revisão antes de compartilhar

- Preencha e confirme os destinatários manualmente.
- Revise o assunto, o contexto e os resultados antes de copiar para um cliente de e-mail.
- Para NVD/CVE, o texto avisa que inteligência pública não confirma que um ativo esteja vulnerável.
- Para auditoria passiva, o texto deixa claro que o resultado é limitado e não equivale a teste de exploração ou certificação completa.
- Os campos passam pela sanitização de relatórios; ainda assim, revise o conteúdo antes de compartilhar.
- Os rascunhos ficam em `reports/`, fora da raiz pública, e esse diretório é ignorado pelo Git.

## Limites

Não há envio automático, SMTP, anexos, destinatários inferidos, agenda ou integração com provedores. O arquivo é um ponto de partida para revisão humana, não um comunicado aprovado.
