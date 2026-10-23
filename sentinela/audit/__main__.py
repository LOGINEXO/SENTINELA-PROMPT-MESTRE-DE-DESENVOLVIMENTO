"""Standalone command for a scoped passive HTTPS audit."""
import argparse
import json
import sys

from sentinela.audit.passive import PassiveAuditError, audit_https
from sentinela.reports import ReportError, build_report, export_json_report
from sentinela.scope import ScopeError, load_scope


def main(argv=None):
    parser = argparse.ArgumentParser(description="Auditoria passiva HTTPS/TLS limitada a escopo autorizado.")
    parser.add_argument("host", help="hostname autorizado; somente HTTPS na porta 443")
    parser.add_argument("--scope-file", default="config/authorized_targets.txt",
                        help="arquivo de allowlist explícita (padrão: config/authorized_targets.txt)")
    parser.add_argument("--export-json", metavar="FILE", help="salva relatório sanitizado em reports/FILE")
    args = parser.parse_args(argv)
    try:
        allowed_hosts = load_scope(args.scope_file)
        result = audit_https(args.host, allowed_hosts=allowed_hosts)
        report = build_report([result], source="passive-https-audit")
        if args.export_json:
            path = export_json_report([result], args.export_json, source="passive-https-audit")
            print(f"Relatório JSON salvo em {path}", file=sys.stderr)
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    except (PassiveAuditError, ScopeError, ReportError, OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
