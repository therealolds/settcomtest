#!/usr/bin/env python3
"""Genera docs/index.html a partire da G1.md, G2.md, ... e da config.json.
Se accanto a G1.md c'è G1.jpg (o .png, .webp) diventa l'immagine del giorno,
se c'è G1a.md diventa la sezione con l'attività da fare durante la giornata.

Il testo e l'immagine di ogni giorno vengono offuscati, così non si legge aprendo il
sorgente della pagina: il browser lo decodifica solo dopo la data di apertura.
"""
import base64
import html
import json
import re
import secrets
import sys
from datetime import datetime
from pathlib import Path

RADICE = Path(__file__).resolve().parent
IMMAGINI = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
USCITA = RADICE / "docs" / "index.html"
# python3 build.py --capi: copia con tutti i giorni già aperti, da mandare agli altri capi.
# Va in un file a parte, così il sito pubblicato in docs/ resta bloccato.
USCITA_CAPI = RADICE / "capi" / "index.html"


def inline(testo):
    t = html.escape(testo, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"<em>\1</em>", t)
    return t


def md_to_html(testo, citazioni=False):
    """Markdown essenziale: ogni riga è un paragrafo, un blocco _..._ su più
    righe è una poesia, `## Titolo` apre un riquadro (es. la sfida del giorno),
    le righe che iniziano con `- ` sono un elenco.
    Con citazioni=True i blocchi in corsivo sono brani citati, non poesie."""
    titolo, out, poesia, lista, sezione = None, [], None, [], False

    def chiudi_lista():
        if lista:
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in lista) + "</ul>")
            lista.clear()

    def chiudi_poesia(versi):
        versi = "\n".join(versi).strip("_").split("\n")
        if citazioni:
            out.append("<blockquote>" + "".join(f"<p>{inline(v)}</p>" for v in versi) + "</blockquote>")
            return
        out.append('<p class="poesia">' + "".join(f"<span>{inline(v)}</span>" for v in versi) + "</p>")

    for riga in testo.splitlines():
        r = riga.strip()
        if poesia is not None:
            if r:
                poesia.append(r)
            if r.endswith("_"):
                chiudi_poesia(poesia)
                poesia = None
            continue
        if r.startswith(("- ", "* ")):
            lista.append(r[2:])
            continue
        chiudi_lista()
        if not r:
            continue
        if r.startswith("_") and not (len(r) > 1 and r.endswith("_")):
            poesia = [r]
            continue
        if citazioni and re.fullmatch(r"_[^_]+_", r):
            chiudi_poesia([r])
            continue
        m = re.match(r"(#{1,3})\s+(.*)", r)
        if m and len(m.group(1)) == 1 and titolo is None:
            titolo = inline(m.group(2))
        elif m and len(m.group(1)) == 2:
            if sezione:
                out.append("</section>")
            out.append(f'<section class="sfida"><h3>{inline(m.group(2))}</h3>')
            sezione = True
        elif m:
            out.append(f"<h4>{inline(m.group(2))}</h4>")
        else:
            out.append(f"<p>{inline(r)}</p>")

    if poesia is not None:
        chiudi_poesia(poesia)
    chiudi_lista()
    if sezione:
        out.append("</section>")
    return titolo, "\n".join(out)


def flusso(seme, lunghezza):
    """Sequenza pseudocasuale (mulberry32), identica a quella della pagina."""
    M = 0xFFFFFFFF
    out = bytearray()
    while len(out) < lunghezza:
        seme = (seme + 0x6D2B79F5) & M
        t = ((seme ^ (seme >> 15)) * (1 | seme)) & M
        t = ((t + (((t ^ (t >> 7)) * (61 | t)) & M)) & M) ^ t
        out += ((t ^ (t >> 14)) & M).to_bytes(4, "little")
    return out


def offusca(testo, chiave):
    dati = testo.encode()
    seme = int.from_bytes(chiave, "little")
    return base64.b64encode(bytes(a ^ b for a, b in zip(dati, flusso(seme, len(dati))))).decode()


def main():
    config = json.loads((RADICE / "config.json").read_text(encoding="utf-8"))
    aperture = config["apertura"]

    file_giorni = sorted(
        (int(m.group(1)), p)
        for p in RADICE.glob("G*.md")
        if (m := re.fullmatch(r"G(\d+)\.md", p.name))
    )
    if not file_giorni:
        sys.exit("Nessun file G1.md, G2.md, ... trovato.")

    giorni = []
    for n, percorso in file_giorni:
        nome = f"G{n}"
        if nome not in aperture:
            sys.exit(f"Manca la data di apertura di {nome} in config.json")
        data = aperture[nome].strip()
        if len(data) == 10:  # solo la data: si apre all'ora_apertura (00:00 se non indicata)
            data += " " + config.get("ora_apertura", "00:00")
        try:
            quando = datetime.fromisoformat(data)
        except ValueError:
            sys.exit(f"Data non valida per {nome}: {data!r} (usa 2026-10-12 oppure 2026-10-12 07:00)")

        titolo, corpo = md_to_html(percorso.read_text(encoding="utf-8"))
        if titolo is None:
            print(f"Attenzione: {percorso.name} non ha un titolo '# ...', uso 'Giorno {n}'")
            titolo = f"Giorno {n}"

        attivita = percorso.with_name(f"G{n}a.md")
        testo_attivita = ""
        if attivita.exists():
            titolo_attivita, testo_attivita = md_to_html(attivita.read_text(encoding="utf-8"), citazioni=True)
            if titolo_attivita:
                testo_attivita = f"<h3>{titolo_attivita}</h3>{testo_attivita}"
        else:
            print(f"Attenzione: manca {attivita.name}, il giorno {n} non ha l'attività")

        chiave = secrets.token_bytes(4)
        immagine = ""
        for estensione, tipo in IMMAGINI.items():
            foto = percorso.with_suffix(estensione)
            if foto.exists():
                immagine = f"data:{tipo};base64," + base64.b64encode(foto.read_bytes()).decode()
                break
        contenuto = json.dumps({"titolo": titolo, "html": corpo, "img": immagine, "attivita": testo_attivita}, ensure_ascii=False)
        giorni.append({
            "n": n,
            "apertura": quando.strftime("%Y-%m-%dT%H:%M"),
            "k": base64.b64encode(chiave).decode(),
            "c": offusca(contenuto, chiave),
        })
        print(f"{percorso.name}: «{html.unescape(re.sub('<[^>]+>', '', titolo))}» si apre il {quando:%d/%m/%Y %H:%M}")

    for nome in aperture:
        if not (RADICE / f"{nome}.md").exists():
            print(f"Attenzione: in config.json c'è {nome} ma il file {nome}.md non esiste")

    pagina = (RADICE / "template.html").read_text(encoding="utf-8")
    pagina = (pagina
              .replace("__TITOLO__", html.escape(config["titolo"]))
              .replace("__SOTTOTITOLO__", html.escape(config.get("sottotitolo", "")).replace(" · ", "&nbsp;· "))
              .replace("/*__DATI__*/[]", json.dumps(giorni)))
    uscita = USCITA
    if "--capi" in sys.argv[1:]:
        pagina = pagina.replace("const TUTTO_APERTO = false;", "const TUTTO_APERTO = true;")
        uscita = USCITA_CAPI
    uscita.parent.mkdir(exist_ok=True)
    uscita.write_text(pagina, encoding="utf-8")
    print(f"Creato {uscita.relative_to(RADICE)}" + (" (tutti i giorni aperti)" if uscita == USCITA_CAPI else ""))


if __name__ == "__main__":
    main()
