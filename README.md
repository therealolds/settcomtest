# Settimana comunitaria – La responsabilità

Sito statico con uno spunto al giorno: ogni giorno si apre solo alla sua data.

## Come si usa

1. Scrivi gli spunti in `G1.md`, `G2.md`, … (la prima riga `# Titolo` è il titolo del giorno).
   - Un blocco in corsivo su più righe (`_..._`) viene impaginato come poesia.
   - L'attività della giornata va in un file a parte: `G1a.md` per `G1.md`, `G2a.md` per `G2.md`, … Compare in una scheda separata sotto lo spunto, senza intestazione (se ne vuoi una, metti `# Titolo` in cima al file). Lì le righe in corsivo `_..._` sono impaginate come citazioni.
   - Un'immagine con lo stesso nome (`G1.jpg`, oppure `.png` / `.webp`) compare in cima allo spunto. Resta nascosta fino all'apertura del giorno, come il testo.
2. In `config.json` metti la data di apertura di ogni giorno (`"2026-10-12"`). Si apre all'ora indicata in `"ora_apertura"` (ora `"06:00"`); per un giorno con un orario diverso scrivi data e ora, es. `"2026-10-12 07:30"`.
3. Genera il sito:

   ```sh
   python3 build.py
   ```

4. Prova in locale:

   ```sh
   python3 -m http.server 17995 --bind 0.0.0.0 -d docs
   ```

   e apri <http://localhost:17995/?oggi=2026-10-12> per simulare un giorno qualsiasi
   (anche con l'ora: `?oggi=2026-10-12T23:59`). Dal telefono, collegato allo stesso Wi-Fi,
   usa l'indirizzo del computer (lo trovi con `hostname -I`), es. `http://192.168.1.104:17995/?oggi=2026-10-13`
   (uso la porta 17995 perché è l'unica aperta nel firewall di questo computer).
   `?oggi=` funziona solo in prova, sul sito pubblicato viene ignorato.

## Copia sbloccata per i capi

```sh
python3 build.py --capi
```

crea `capi.html` con tutti i giorni già aperti: un unico file da mandare come allegato.
Il sito in `docs/` non viene toccato. Non caricare `capi.html` su GitHub.

## Pubblicazione su GitHub Pages

Carica la cartella su un repository GitHub, poi vai in *Settings → Pages* e scegli
*Deploy from a branch*, branch `main`, cartella `/docs`. Ogni volta che modifichi uno spunto: `python3 build.py`, commit e push.
