# Relatórios locais

A Etapa 3 fornece uma estrutura JSON comum para resultados da inteligência pública e exportação local sanitizada.

## Formato

Cada relatório inclui `schema_version`, `generated_at` (UTC), `source`, `record_count` e `results`.

## Exportação

Use `--export-json nome.json` junto de `--nvd-search` ou `--nvd-cve`. O arquivo é gravado em `reports/`. Apenas arquivos `.json` dentro desse diretório são aceitos; caminhos que saem dele são rejeitados. A gravação usa arquivo temporário e substituição atômica.

## Sanitização e limites

Campos cujos nomes indicam senhas, tokens, chaves, cookies, sessões ou credenciais são mascarados. Padrões comuns de segredos em texto também são mascarados. Isso reduz exposição acidental, mas não garante que dados arbitrários estejam totalmente livres de informações sensíveis. Revise os relatórios antes de compartilhá-los e mantenha-os fora da raiz pública de servidores web.

Os arquivos locais dentro de `reports/` são ignorados pelo Git. Não inclua relatórios reais em commits ou tickets públicos.
