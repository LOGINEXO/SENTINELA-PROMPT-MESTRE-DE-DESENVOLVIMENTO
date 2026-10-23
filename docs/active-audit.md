# Etapa 9 — Verificação ativa HTTPS limitada e autorizada

Esta etapa adiciona somente uma verificação ativa de baixa intensidade: **uma requisição GET para /** por HTTPS na porta 443, para hostname autorizado em arquivo de escopo ativo separado. Não é um scanner de vulnerabilidades nem um teste de penetração.

## Autorização explícita separada

1. Confirme autorização documentada do proprietário do ativo, incluindo hostname, finalidade e janela permitida.
2. Copie o modelo:

Linux/macOS:
```bash
cp config/authorized_active_targets.example.txt config/authorized_active_targets.txt
```

Windows PowerShell:
```powershell
Copy-Item config/authorized_active_targets.example.txt config/authorized_active_targets.txt
```

3. Edite `config/authorized_active_targets.txt` e adicione somente hostnames exatos autorizados para esse teste. O arquivo local é ignorado pelo Git. A allowlist passiva, sozinha, não autoriza teste ativo.

## Uso pelo terminal

```bash
python -m sentinela.queue_cli add-active-audit --host app.minha-empresa.example --confirm-authorized
python -m sentinela.queue_worker --once
python -m sentinela.queue_cli status
```

Substitua o hostname por um ativo autorizado presente em `config/authorized_active_targets.txt`. O argumento `--confirm-authorized` é obrigatório para expressar confirmação explícita, mas não substitui a autorização real. O worker repete a validação de escopo no momento da execução.

## Limites técnicos

- Exatamente uma requisição GET à raiz, HTTPS/443, sem seguir redirecionamentos.
- Hostname exato em arquivo de autorização ativa separado; sem curingas, IPs literais, portas alternativas ou caminhos.
- DNS validado e conectado por IP público fixado; certificados TLS continuam verificados.
- Timeout máximo de 15 segundos.
- O corpo não é armazenado; no máximo 8192 bytes são lidos para limitar a operação.
- Não envia formulários, credenciais, payloads de exploração, nem faz varredura de portas ou enumeração de diretórios.
- Respostas e códigos HTTP podem variar por CDN, proxy e aplicação. Resultado não prova ausência ou presença de vulnerabilidades.

Use apenas em ativos e períodos cobertos pela autorização. Para testes mais invasivos, faça uma avaliação de risco e autorização específica antes de implementar qualquer técnica adicional.
