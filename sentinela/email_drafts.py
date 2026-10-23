"""Generate editable email drafts from completed jobs; never sends messages."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

from sentinela.queue import ROOT, QueueError, get_job
from sentinela.reports import sanitize

DEFAULT_OUTPUT_DIR = ROOT / "reports" / "email-drafts"
MAX_DRAFT_BYTES = 100_000


class EmailDraftError(ValueError):
    """Raised when a safe manual-review draft cannot be generated."""


def _plain(value: Any, *, limit: int = 1200) -> str:
    value = sanitize(value)
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    elif value is None:
        text = ""
    else:
        text = str(value)
    # Keep generated drafts readable and avoid control characters in copied mail.
    text = "".join(ch if ch in "\n\t" or ord(ch) >= 32 and ord(ch) != 127 else " " for ch in text)
    return text[:limit]


def _summarize_results(job: dict[str, Any]) -> str:
    result = job.get("result")
    if not isinstance(result, dict):
        return "O resultado estruturado não está disponível no histórico desta tarefa."
    results = result.get("results")
    if not isinstance(results, list):
        results = [result]
    if not results:
        return "A tarefa terminou sem registros de resultado."
    lines: list[str] = []
    for index, item in enumerate(results[:20], 1):
        if not isinstance(item, dict):
            lines.append(f"{index}. {_plain(item, limit=500)}")
            continue
        cve_id = item.get("cve_id")
        if isinstance(cve_id, str) and re.fullmatch(r"CVE-\d{4}-\d{4,}", cve_id, re.IGNORECASE):
            lines.append(f"{index}. **{cve_id.upper()}** — prioridade técnica: {_plain(item.get('technical_priority') or 'não informada', limit=80)}; CVSS: {_plain((item.get('cvss') or {}).get('base_score') if isinstance(item.get('cvss'), dict) else 'não informado', limit=80)}")
            description = _plain(item.get("description") or "Descrição não fornecida.", limit=600).replace("\n", " ")
            lines.append(f"   - Descrição pública: {description}")
            url = item.get("nvd_url")
            if isinstance(url, str) and url.startswith("https://nvd.nist.gov/vuln/detail/"):
                lines.append(f"   - Referência: {url}")
            lines.append("   - **Não significa que um ativo específico esteja vulnerável.**")
        else:
            lines.append(f"{index}. {_plain(item.get('host') or item.get('hostname') or item.get('target') or item.get('title') or f'Registro {index}', limit=200)}")
            for key in ("status", "tls_version", "certificate", "security_headers", "findings", "summary"):
                if key in item:
                    lines.append(f"   - {key.replace('_', ' ').capitalize()}: {_plain(item[key], limit=700).replace(chr(10), ' ')}")
            if len(lines) == 0:
                lines.append(f"{index}. Resultado disponível; revise o relatório original.")
    if len(results) > 20:
        lines.append(f"- Mais {len(results) - 20} registro(s) omitido(s) deste rascunho; consulte o histórico local.")
    return "\n".join(lines)


def render_email_draft(job: dict[str, Any]) -> str:
    if not isinstance(job, dict) or job.get("status") != "completed":
        raise EmailDraftError("Só é possível gerar rascunhos para tarefas concluídas.")
    job_id = job.get("id")
    if isinstance(job_id, bool) or not isinstance(job_id, int) or job_id < 1:
        raise EmailDraftError("Identificador de tarefa inválido.")
    task_type = job.get("task_type")
    if task_type == "nvd_search":
        subject = "Revisão necessária: informações públicas de vulnerabilidades NVD/CVE"
        context = f"Consulta pública NVD/CVE para a palavra-chave: {_plain(job.get('payload', {}).get('query', ''), limit=120)}."
        caveat = "Os registros abaixo são inteligência pública. Eles não confirmam exposição ou vulnerabilidade em qualquer ativo da organização."
    elif task_type == "passive_audit":
        host = _plain(job.get("payload", {}).get("host", ""), limit=253)
        subject = f"Revisão necessária: resultado de auditoria passiva HTTPS — {host}"
        context = f"Foi concluída uma auditoria passiva HTTPS para o hostname autorizado {host}."
        caveat = "Este resultado é uma observação passiva e limitada; não representa teste de exploração nem certificação completa de segurança."
    else:
        raise EmailDraftError("Tipo de tarefa não suportado para rascunho.")
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    body = _summarize_results(job)
    draft = f"""# Rascunho de e-mail — revisão manual obrigatória

**Estado:** RASCUNHO NÃO ENVIADO  
**Tarefa Sentinela:** {job_id}  
**Gerado em (UTC):** {generated}

**Para:** [preencher e revisar destinatários]  
**Assunto:** {subject}

---

Olá,

{context}

{caveat}

## Resumo dos resultados

{body}

## Próximos passos sugeridos

- Confirmar o contexto e a relevância dos resultados com a equipe responsável.
- Validar manualmente os dados e referências antes de tomar qualquer decisão.
- Não compartilhar informações sensíveis sem autorização e necessidade legítima.
- Ajustar o texto, destinatários e assunto antes de qualquer envio.

Atenciosamente,  
[Nome / equipe responsável]

---

**Aviso:** este arquivo é apenas um rascunho editável. O Sentinela não envia e-mails. Revise o conteúdo, os destinatários e a autorização manualmente antes de copiar para seu cliente de e-mail.
"""
    if len(draft.encode("utf-8")) > MAX_DRAFT_BYTES:
        raise EmailDraftError("O rascunho excede o tamanho máximo permitido.")
    return draft


def create_email_draft(job_id: int, *, output_dir: str | Path | None = None) -> Path:
    if isinstance(job_id, bool) or not isinstance(job_id, int) or job_id < 1:
        raise EmailDraftError("Informe um ID de tarefa positivo.")
    job = get_job(job_id)
    if job is None:
        raise EmailDraftError("Tarefa não encontrada.")
    content = render_email_draft(job)
    root = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve()
    target = (root / f"job-{job_id}.md").resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise EmailDraftError("Destino de rascunho inválido.") from exc
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=root,
                                         prefix=f".job-{job_id}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise EmailDraftError("Não foi possível gravar o rascunho local.") from exc
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera rascunho de e-mail para revisão manual; não envia mensagens.")
    parser.add_argument("--job-id", type=int, required=True, help="ID de uma tarefa concluída")
    args = parser.parse_args(argv)
    try:
        path = create_email_draft(args.job_id)
    except (EmailDraftError, QueueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"status": "draft_created_not_sent", "path": str(path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
