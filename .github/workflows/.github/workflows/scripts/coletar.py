"""Coleta vagas de estágio (Gupy e, se houver chave, Adzuna) e grava vagas.json."""
import datetime, json, os, re, sys, urllib.parse, urllib.request

HOJE = datetime.date.today().isoformat()
MODELOS = {"remoto": "remote", "hibrido": "hybrid", "presencial": "on-site"}
VOLTA = {"remote": "remoto", "hybrid": "hibrido", "on-site": "presencial"}
ESTAGIO = re.compile(r"est[aá]gi|internship", re.I)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 buscador-de-estagios", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def gupy(b):
    saida, off = [], 0
    for _ in range(5):
        p = {"jobName": ("estágio " + b["termo"]).strip(), "limit": 20, "offset": off}
        if b.get("cidade"):
            p["city"] = b["cidade"]
        if b.get("modelo") in MODELOS:
            p["workplaceType"] = MODELOS[b["modelo"]]
        itens = get("https://portal.api.gupy.io/api/v1/jobs?" + urllib.parse.urlencode(p)).get("data") or []
        if not itens:
            break
        off += len(itens)
        for v in itens:
            if not (ESTAGIO.search(v.get("type") or "") or ESTAGIO.search(v.get("name") or "")):
                continue
            wt = VOLTA.get(v.get("workplaceType"), "")
            saida.append({
                "id": "gupy:" + str(v.get("id")),
                "titulo": v.get("name") or "",
                "empresa": v.get("careerPageName") or "",
                "cidade": v.get("city") or "",
                "estado": v.get("state") or "",
                "modelo": "remoto" if v.get("isRemoteWork") else wt,
                "publicada": (v.get("publishedDate") or "")[:10],
                "prazo": (v.get("applicationDeadline") or "")[:10],
                "url": v.get("jobUrl") or "",
                "fonte": "Gupy",
            })
    return saida


def adzuna(b):
    app_id, app_key = os.environ.get("ADZUNA_APP_ID"), os.environ.get("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        return []
    saida = []
    for pag in (1, 2):
        p = {"app_id": app_id, "app_key": app_key, "results_per_page": 50,
             "what": ("estagio " + b["termo"]).strip(), "content-type": "application/json"}
        if b.get("cidade"):
            p["where"] = b["cidade"]
        url = f"https://api.adzuna.com/v1/api/jobs/br/search/{pag}?" + urllib.parse.urlencode(p)
        for v in get(url).get("results") or []:
            titulo = re.sub(r"<[^>]+>", "", v.get("title") or "")
            if not ESTAGIO.search(titulo):
                continue
            saida.append({
                "id": "adzuna:" + str(v.get("id")),
                "titulo": titulo,
                "empresa": (v.get("company") or {}).get("display_name", ""),
                "cidade": (v.get("location") or {}).get("display_name", ""),
                "estado": "",
                "modelo": "",
                "publicada": (v.get("created") or "")[:10],
                "prazo": "",
                "url": v.get("redirect_url") or "",
                "fonte": "Adzuna",
            })
    return saida


def main():
    buscas = json.load(open("config.json", encoding="utf-8"))["buscas"]
    try:
        antigo = json.load(open("vagas.json", encoding="utf-8"))
        visto = {v["id"]: v.get("visto", HOJE) for v in antigo.get("vagas", [])}
        primeira_vez = False
    except (OSError, ValueError):
        visto, primeira_vez = {}, True

    achadas, erros = {}, 0
    for b in buscas:
        for fonte in (gupy, adzuna):
            try:
                for v in fonte(b):
                    achadas.setdefault(v["id"], v)
            except Exception as e:
                erros += 1
                print(f"Falha em {fonte.__name__} {b}: {e}", file=sys.stderr)

    if not achadas and erros:
        sys.exit("Nenhuma vaga coletada e houve erros; vagas.json não foi alterado.")

    vistas_chave, vagas = set(), []
    for v in achadas.values():
        if v["prazo"] and v["prazo"] < HOJE:
            continue
        chave = (v["titulo"].lower(), v["empresa"].lower(), v["cidade"].lower())
        if chave in vistas_chave:
            continue
        vistas_chave.add(chave)
        v["visto"] = visto.get(v["id"], HOJE)
        vagas.append(v)
    vagas.sort(key=lambda v: v["publicada"], reverse=True)

    json.dump({"atualizado": HOJE, "vagas": vagas}, open("vagas.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    novas = [v for v in vagas if v["visto"] == HOJE]
    if novas and not primeira_vez:
        linhas = [f"- [{v['titulo']}]({v['url']}) - {v['empresa']}, {v['cidade']} ({v['fonte']})" for v in novas[:40]]
        open("novas.md", "w", encoding="utf-8").write(f"{len(novas)} vagas novas encontradas:\n\n" + "\n".join(linhas) + "\n")
    print(f"{len(vagas)} vagas, {len(novas)} novas, {erros} erros")


main()
