<?php
declare(strict_types=1);

/**
 * Sentinela web interface (Stage 6).
 * Configure the web server document root to this /web directory and keep the
 * repository root, local allowlist, environment files and reports outside it.
 */
session_start();

const APP_ROOT = __DIR__ . '/..';
const MAX_OUTPUT_BYTES = 200000;

header('Content-Type: text/html; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: no-referrer');
header('Cache-Control: no-store');
header("Content-Security-Policy: default-src 'self'; style-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'");

if (!isset($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}

function e(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function run_cli(array $arguments): array
{
    if (!function_exists('proc_open')) {
        return [1, '', 'A função proc_open está desabilitada no PHP.'];
    }

    $python = getenv('SENTINELA_PYTHON') ?: 'python';
    $command = array_merge([$python], $arguments);
    $descriptors = [
        0 => ['pipe', 'r'],
        1 => ['pipe', 'w'],
        2 => ['pipe', 'w'],
    ];
    $process = @proc_open($command, $descriptors, $pipes, APP_ROOT, null, ['bypass_shell' => true]);
    if (!is_resource($process)) {
        return [1, '', 'Não foi possível iniciar o processo Python.'];
    }

    fclose($pipes[0]);
    stream_set_blocking($pipes[1], true);
    stream_set_blocking($pipes[2], true);
    $stdout = stream_get_contents($pipes[1], MAX_OUTPUT_BYTES + 1);
    $stderr = stream_get_contents($pipes[2], MAX_OUTPUT_BYTES + 1);
    fclose($pipes[1]);
    fclose($pipes[2]);
    $exitCode = proc_close($process);

    if (strlen($stdout) > MAX_OUTPUT_BYTES || strlen($stderr) > MAX_OUTPUT_BYTES) {
        return [1, '', 'A saída ultrapassou o limite permitido e foi descartada.'];
    }
    return [$exitCode, $stdout === false ? '' : $stdout, $stderr === false ? '' : $stderr];
}

function allowed_host(string $host): bool
{
    $scopePath = APP_ROOT . '/config/authorized_targets.txt';
    if (!is_file($scopePath) || !is_readable($scopePath)) {
        return false;
    }
    $entries = file($scopePath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    if ($entries === false) {
        return false;
    }
    foreach ($entries as $entry) {
        $entry = strtolower(trim(explode('#', $entry, 2)[0]));
        if ($entry !== '' && hash_equals($entry, strtolower($host))) {
            return true;
        }
    }
    return false;
}

$result = null;
$error = '';
$action = '';
$query = '';
$host = '';
$limit = '10';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $postedToken = is_string($_POST['csrf_token'] ?? null) ? $_POST['csrf_token'] : '';
    if (!hash_equals($_SESSION['csrf_token'], $postedToken)) {
        http_response_code(403);
        $error = 'Sessão inválida. Atualize a página e tente novamente.';
    } else {
        $action = is_string($_POST['action'] ?? null) ? $_POST['action'] : '';
        if ($action === 'nvd') {
            $query = trim(is_string($_POST['query'] ?? null) ? $_POST['query'] : '');
            $limit = is_string($_POST['limit'] ?? null) ? $_POST['limit'] : '10';
            if ($query === '' || strlen($query) > 120 || preg_match('/[\x00-\x1F\x7F]/', $query)) {
                $error = 'Informe uma palavra-chave válida (até 120 caracteres).';
            } elseif (!ctype_digit($limit) || (int)$limit < 1 || (int)$limit > 100) {
                $error = 'O limite deve ser um número entre 1 e 100.';
            } else {
                [$code, $stdout, $stderr] = run_cli(['-m', 'sentinela.cli', '--nvd-search', $query, '--limit', (string)(int)$limit]);
                if ($code !== 0) {
                    $error = 'A consulta NVD falhou. ' . trim($stderr);
                } else {
                    $result = $stdout;
                }
            }
        } elseif ($action === 'audit') {
            $host = strtolower(trim(is_string($_POST['host'] ?? null) ? $_POST['host'] : ''));
            if ($host === '' || strlen($host) > 253 || !preg_match('/^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)(?:\.(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?))*$/D', $host)) {
                $error = 'Informe apenas um hostname DNS, sem URL, porta ou caminho.';
            } elseif (!allowed_host($host)) {
                $error = 'Hostname não consta na allowlist local. Nenhuma auditoria foi iniciada.';
            } else {
                [$code, $stdout, $stderr] = run_cli(['-m', 'sentinela.audit', $host]);
                if ($code !== 0) {
                    $error = 'A auditoria não foi concluída. ' . trim($stderr);
                } else {
                    $result = $stdout;
                }
            }
        } else {
            $error = 'Ação inválida.';
        }
    }
}
?>
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sentinela — painel</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#121d30;--line:#273750;--text:#e8eef8;--muted:#a9b8ce;--accent:#60a5fa;--danger:#fecaca}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1000px;margin:0 auto;padding:32px 18px 60px}header{margin-bottom:26px}.eyebrow{color:var(--accent);font-size:.8rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase}h1{font-size:clamp(2rem,5vw,3rem);margin:.25rem 0}h2{margin-top:0}p{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:18px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:22px}
label{display:block;font-weight:650;margin:14px 0 6px}input,select,button{width:100%;font:inherit;border-radius:9px;padding:11px 12px}input,select{color:var(--text);background:#0b1424;border:1px solid #3a4b65}button{margin-top:18px;background:var(--accent);border:0;color:#061326;font-weight:750;cursor:pointer}button:focus-visible,input:focus-visible{outline:3px solid #bfdbfe;outline-offset:2px}.notice{padding:14px;border-radius:10px;margin:18px 0;overflow-wrap:anywhere}.error{background:#451a1a;border:1px solid #7f1d1d;color:var(--danger)}.success{background:#102b27;border:1px solid #23675b}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#07101d;border:1px solid var(--line);border-radius:10px;padding:16px;max-height:520px;overflow:auto;color:#dbeafe}.small{font-size:.9rem}footer{margin-top:22px;color:var(--muted);font-size:.88rem}
</style>
</head>
<body>
<main>
<header>
<div class="eyebrow">Painel defensivo</div>
<h1>Sentinela</h1>
<p>Inteligência pública NVD/CVE e auditoria passiva HTTPS/TLS com escopo autorizado.</p>
</header>

<?php if ($error !== ''): ?>
<div class="notice error" role="alert"><strong>Não concluído:</strong> <?= e($error) ?></div>
<?php endif; ?>

<div class="grid">
<section class="panel">
<h2>Inteligência NVD / CVE</h2>
<p>Consulta dados públicos da NVD. Um CVE encontrado não prova que um ativo esteja vulnerável.</p>
<form method="post">
<input type="hidden" name="csrf_token" value="<?= e($_SESSION['csrf_token']) ?>">
<input type="hidden" name="action" value="nvd">
<label for="query">Produto, tecnologia ou palavra-chave</label>
<input id="query" name="query" maxlength="120" required value="<?= e($action === 'nvd' ? $query : '') ?>" placeholder="Ex.: OpenSSH">
<label for="limit">Máximo de resultados</label>
<select id="limit" name="limit">
<?php foreach ([5,10,20,50,100] as $option): ?>
<option value="<?= $option ?>" <?= (int)$limit === $option ? 'selected' : '' ?>><?= $option ?></option>
<?php endforeach; ?>
</select>
<button type="submit">Consultar NVD</button>
</form>
</section>

<section class="panel">
<h2>Auditoria passiva HTTPS</h2>
<p>Verifica TLS e cabeçalhos de segurança. Somente hostnames exatos presentes em <code>config/authorized_targets.txt</code> são aceitos.</p>
<form method="post">
<input type="hidden" name="csrf_token" value="<?= e($_SESSION['csrf_token']) ?>">
<input type="hidden" name="action" value="audit">
<label for="host">Hostname autorizado</label>
<input id="host" name="host" maxlength="253" required pattern="(?i)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*" value="<?= e($action === 'audit' ? $host : '') ?>" placeholder="app.minha-empresa.com">
<button type="submit">Executar auditoria passiva</button>
</form>
</section>
</div>

<?php if ($result !== null): ?>
<section class="panel" style="margin-top:18px">
<h2>Resultado</h2>
<div class="notice success">Processo concluído. Revise o resultado antes de compartilhar.</div>
<pre><?= e(trim($result)) ?></pre>
</section>
<?php endif; ?>

<footer>
<strong>Segurança:</strong> use apenas sistemas com autorização documentada. Esta interface executa uma ação por envio; fila, pausa e cancelamento pertencem à etapa 7. Não exponha o diretório raiz do projeto nem os relatórios ao público.
</footer>
</main>
</body>
</html>
