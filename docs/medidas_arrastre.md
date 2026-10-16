# Medidas de rendimiento de arrastre en modo Editar capa

Mediciones tomadas con `scripts/medir_arrastre_web.py` (Flet Web + Playwright Chromium headless).

## Medición: ANTES

| Capa | Gesto | Eventos Python | Proc. media (ms) | Proc. máx (ms) | `update()` / ev | Mensajes WS / ev | Bytes WS / ev | Retraso final (ms) | Error pos. (cm) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| PNG (~180 KB) | cuerpo_lento (60p/1.5s) | 60 | 1.80 | 2.98 | 17.1 (1026) | 12.1 | 602 B | 11.9 | 0.00 |
| PNG (~180 KB) | cuerpo_normal (30p/0.6s) | 30 | 2.73 | 6.32 | 17.2 (516) | 11.9 | 615 B | 15.8 | 0.00 |
| PNG (~180 KB) | cuerpo_brusco (6p/0.1s) | 6 | 0.65 | 3.91 | 3.8 (23) | 5.5 | 615 B | 7.0 | 79.36 |
| PNG (~180 KB) | tirador_br (30p/0.6s) | 29 | 2.15 | 4.44 | 16.0 (465) | 12.8 | 621 B | 6.4 | 3.35 |
| SVG | cuerpo_lento (60p/1.5s) | 60 | 2.21 | 4.46 | 17.1 (1026) | 12.1 | 897 B | 11.0 | 0.00 |
| SVG | cuerpo_normal (30p/0.6s) | 26 | 2.67 | 4.99 | 17.2 (448) | 12.2 | 634 B | 13.5 | 3.17 |
| SVG | cuerpo_brusco (6p/0.1s) | 5 | 0.92 | 2.40 | 8.0 (40) | 7.0 | 702 B | 10.7 | 63.49 |
| SVG | tirador_br (30p/0.6s) | 26 | 2.71 | 6.15 | 17.2 (448) | 13.7 | 656 B | 14.0 | 0.00 |




## Medición: DESPUES

| Capa | Gesto | Eventos Python | Proc. media (ms) | Proc. máx (ms) | `update()` / ev | Mensajes WS / ev | Bytes WS / ev | Retraso final (ms) | Error pos. (cm) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| PNG (~180 KB) | cuerpo_lento (60p/1.5s) | 60 | 3.08 | 6.13 | 1.0 (60) | 1.1 | 65 B | 27.8 | 0.00 |
| PNG (~180 KB) | cuerpo_normal (30p/0.6s) | 30 | 3.57 | 5.52 | 1.0 (30) | 1.1 | 85 B | 21.1 | 0.00 |
| PNG (~180 KB) | cuerpo_brusco (6p/0.1s) | 6 | 3.08 | 3.81 | 1.0 (6) | 1.7 | 216 B | 20.5 | 0.00 |
| PNG (~180 KB) | tirador_br (30p/0.6s) | 30 | 7.46 | 32.53 | 1.0 (30) | 1.2 | 508 B | 30.6 | 0.00 |
| SVG | cuerpo_lento (60p/1.5s) | 60 | 4.95 | 21.04 | 1.0 (59) | 1.1 | 362 B | 113.7 | 0.00 |
| SVG | cuerpo_normal (30p/0.6s) | 30 | 3.78 | 12.04 | 1.0 (30) | 1.2 | 88 B | 24.4 | 0.00 |
| SVG | cuerpo_brusco (6p/0.1s) | 6 | 7.09 | 11.89 | 1.0 (6) | 1.7 | 216 B | 19.1 | 0.00 |
| SVG | tirador_br (30p/0.6s) | 30 | 5.82 | 17.20 | 1.0 (30) | 1.1 | 492 B | 17.1 | 0.00 |
