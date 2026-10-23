"""Standalone command for the passive HTTPS audit: python -m sentinela.audit HOST."""
import argparse
import json
import sys

from sentinela.audit.passive import PassiveAuditError, audit_https
from sentinela.reports import ReportError, build_report, export_json_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Auditoria passiva HTTPS/TLS e cabeçalhos.")
    parser.add_argument("host", help="hostname autorizado; somente HTTPS na porta 443")
    parser.add_argument("--export-json", metavar="FILE", help="salva relatório sanitizado em reports/FILE")
    args = parser.parse_args(argv)
    try:
        result = audit_https(args.host)
        report = build_report([result], source="passive-https-audit")
        if args.export_json:
            path = export_json_report([result], args.export_json, source="passive-https-audit")
            print(f"Relatório JSON salvo em {path}", file=sys.stderr)
        print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    except (PassiveAuditError, ReportError, OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
