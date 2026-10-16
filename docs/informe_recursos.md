# Informe de Recursos y Análisis de Duplicados

Este informe detalla el inventario de archivos en `guardados/` y `docs/ejemplos/`, identificando referencias en proyectos JSON, archivos sin uso y grupos de duplicados por hash SHA-256.

## 1. Resumen Ejecutivo

| Métrica | Valor |
|---|---|
| **Total de archivos analizados** | 380 |
| **Espacio total ocupado** | 4.45 MB (4,667,876 bytes) |
| **Espacio duplicado** | 2.96 MB (3,103,490 bytes) |
| **Archivos referenciados por proyectos** | 4 (0.04 MB) |
| **Archivos sin uso (no referenciados)** | 376 (4.41 MB) |
| **Grupos de archivos con contenido idéntico (SHA-256)** | 16 |

### Proyectos JSON analizados
- **`docs/ejemplos/disenos/ejemplo_espejo_12.json`**: 3 archivos referenciados en capas:
  - `flor_cantoya_7c0b5480.png` (presente en disco)
  - `medallon_d4da864b.svg` (presente en disco)
  - `mosaico_geometrico_04d6a76a.svg` (presente en disco)
- **`guardados/recursos_temp/prueba_imagen.json`**: 4 archivos referenciados en capas:
  - `WhatsApp_Image_2025-12-11_at_1_62029b24.jpeg` (no encontrado en recursos locales)
  - `_prueba_usuario_f1786920.svg` (no encontrado en recursos locales)
  - `descargar_26d3006a.jpg` (presente en disco)
  - `descargar__1__c02f4fab.jpg` (no encontrado en recursos locales)

## 2. Grupos de Archivos Duplicados (Mismo SHA-256)

A continuación se listan los grupos donde 2 o más archivos tienen exactamente el mismo hash SHA-256:

### Grupo 1: SHA-256 `f39774a2267d881b...` (6 copias, 213,987 bytes c/u, desperdicio: 1,069,935 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/_bench_180kb.png` | No | - |
| `guardados/recursos_temp/_bench_180kb_2bb3fb39.png` | No | - |
| `guardados/recursos_temp/_bench_180kb_5b7cb752.png` | No | - |
| `guardados/recursos_temp/_bench_180kb_a88234bd.png` | No | - |
| `guardados/recursos_temp/_bench_180kb_ab0e7e0a.png` | No | - |
| `guardados/recursos_temp/_bench_180kb_d7cc7817.png` | No | - |

### Grupo 2: SHA-256 `051dc60f85fd742b...` (8 copias, 127,512 bytes c/u, desperdicio: 892,584 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/malla_densa_20b3e7cc.svg` | No | - |
| `guardados/recursos_temp/malla_densa_2db5af03.svg` | No | - |
| `guardados/recursos_temp/malla_densa_404604c4.svg` | No | - |
| `guardados/recursos_temp/malla_densa_6c5c8099.svg` | No | - |
| `guardados/recursos_temp/malla_densa_72bf79c2.svg` | No | - |
| `guardados/recursos_temp/malla_densa_d5027d3a.svg` | No | - |
| `guardados/recursos_temp/malla_densa_ef83c4b1.svg` | No | - |
| `guardados/recursos_temp/malla_densa_f826333a.svg` | No | - |

### Grupo 3: SHA-256 `0a89c95889546076...` (8 copias, 56,255 bytes c/u, desperdicio: 393,785 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/textura_4k_0c405740.png` | No | - |
| `guardados/recursos_temp/textura_4k_1e4bf0f9.png` | No | - |
| `guardados/recursos_temp/textura_4k_44368855.png` | No | - |
| `guardados/recursos_temp/textura_4k_50fa1dd1.png` | No | - |
| `guardados/recursos_temp/textura_4k_53db712f.png` | No | - |
| `guardados/recursos_temp/textura_4k_54835c4f.png` | No | - |
| `guardados/recursos_temp/textura_4k_888e74b8.png` | No | - |
| `guardados/recursos_temp/textura_4k_89a55486.png` | No | - |

### Grupo 4: SHA-256 `bc16d4b1bdf8ee7f...` (3 copias, 157,194 bytes c/u, desperdicio: 314,388 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/Gemini_Generated_Image_oxoxud_557c40ec.jpg` | No | - |
| `guardados/recursos_temp/Gemini_Generated_Image_oxoxud_c39e767f.jpg` | No | - |
| `guardados/recursos_temp/Gemini_Generated_Image_oxoxud_eff8472f.jpg` | No | - |

### Grupo 5: SHA-256 `b0b593efb9b064e4...` (3 copias, 116,990 bytes c/u, desperdicio: 233,980 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/WhatsApp_Image_2026-10-08_at_8_bef569b3.jpeg` | No | - |
| `guardados/recursos_temp/WhatsApp_Image_2026-10-08_at_8_c4523fa5.jpeg` | No | - |
| `guardados/recursos_temp/WhatsApp_Image_2026-10-08_at_8_c72deaa1.jpeg` | No | - |

### Grupo 6: SHA-256 `af099b1ebc4c79b7...` (191 copias, 591 bytes c/u, desperdicio: 112,290 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/cuadrado_06e8346b.png` | No | - |
| `guardados/recursos_temp/cuadrado_078bdb62.png` | No | - |
| `guardados/recursos_temp/cuadrado_0b908583.png` | No | - |
| `guardados/recursos_temp/cuadrado_0c3f8096.png` | No | - |
| `guardados/recursos_temp/cuadrado_0eb5364d.png` | No | - |
| `guardados/recursos_temp/cuadrado_0ff63b73.png` | No | - |
| `guardados/recursos_temp/cuadrado_103d03bb.png` | No | - |
| `guardados/recursos_temp/cuadrado_12418b12.png` | No | - |
| `guardados/recursos_temp/cuadrado_12a00c8c.png` | No | - |
| `guardados/recursos_temp/cuadrado_1349b9e1.png` | No | - |
| `guardados/recursos_temp/cuadrado_13aab70b.png` | No | - |
| `guardados/recursos_temp/cuadrado_13b53411.png` | No | - |
| `guardados/recursos_temp/cuadrado_155a5861.png` | No | - |
| `guardados/recursos_temp/cuadrado_160d55c3.png` | No | - |
| `guardados/recursos_temp/cuadrado_170cb887.png` | No | - |
| `guardados/recursos_temp/cuadrado_17dc25bb.png` | No | - |
| `guardados/recursos_temp/cuadrado_193711dc.png` | No | - |
| `guardados/recursos_temp/cuadrado_19ca3273.png` | No | - |
| `guardados/recursos_temp/cuadrado_1aac79a5.png` | No | - |
| `guardados/recursos_temp/cuadrado_1ac7e707.png` | No | - |
| `guardados/recursos_temp/cuadrado_1b0ed508.png` | No | - |
| `guardados/recursos_temp/cuadrado_1d453bf0.png` | No | - |
| `guardados/recursos_temp/cuadrado_1e3f5053.png` | No | - |
| `guardados/recursos_temp/cuadrado_1e6b0baf.png` | No | - |
| `guardados/recursos_temp/cuadrado_1ecb9067.png` | No | - |
| `guardados/recursos_temp/cuadrado_215a95af.png` | No | - |
| `guardados/recursos_temp/cuadrado_21e47709.png` | No | - |
| `guardados/recursos_temp/cuadrado_2349c1eb.png` | No | - |
| `guardados/recursos_temp/cuadrado_23a9efd4.png` | No | - |
| `guardados/recursos_temp/cuadrado_24e7835c.png` | No | - |
| `guardados/recursos_temp/cuadrado_27a5be71.png` | No | - |
| `guardados/recursos_temp/cuadrado_27f26613.png` | No | - |
| `guardados/recursos_temp/cuadrado_2cc4d458.png` | No | - |
| `guardados/recursos_temp/cuadrado_2cd47a89.png` | No | - |
| `guardados/recursos_temp/cuadrado_2e23ab04.png` | No | - |
| `guardados/recursos_temp/cuadrado_2ebdc5a1.png` | No | - |
| `guardados/recursos_temp/cuadrado_30d550af.png` | No | - |
| `guardados/recursos_temp/cuadrado_34135428.png` | No | - |
| `guardados/recursos_temp/cuadrado_34748146.png` | No | - |
| `guardados/recursos_temp/cuadrado_3651e440.png` | No | - |
| `guardados/recursos_temp/cuadrado_3797fb3d.png` | No | - |
| `guardados/recursos_temp/cuadrado_37f6aeea.png` | No | - |
| `guardados/recursos_temp/cuadrado_38a2e546.png` | No | - |
| `guardados/recursos_temp/cuadrado_39715312.png` | No | - |
| `guardados/recursos_temp/cuadrado_39990bdc.png` | No | - |
| `guardados/recursos_temp/cuadrado_3ab43ba4.png` | No | - |
| `guardados/recursos_temp/cuadrado_3d075e73.png` | No | - |
| `guardados/recursos_temp/cuadrado_3d236c96.png` | No | - |
| `guardados/recursos_temp/cuadrado_3ecd8694.png` | No | - |
| `guardados/recursos_temp/cuadrado_43011577.png` | No | - |
| `guardados/recursos_temp/cuadrado_43314ed7.png` | No | - |
| `guardados/recursos_temp/cuadrado_43505861.png` | No | - |
| `guardados/recursos_temp/cuadrado_46b1378d.png` | No | - |
| `guardados/recursos_temp/cuadrado_49f1d131.png` | No | - |
| `guardados/recursos_temp/cuadrado_4d2af052.png` | No | - |
| `guardados/recursos_temp/cuadrado_4d74a623.png` | No | - |
| `guardados/recursos_temp/cuadrado_4e0bc9b9.png` | No | - |
| `guardados/recursos_temp/cuadrado_4ea14039.png` | No | - |
| `guardados/recursos_temp/cuadrado_4eb407fd.png` | No | - |
| `guardados/recursos_temp/cuadrado_4f13f5d5.png` | No | - |
| `guardados/recursos_temp/cuadrado_4f64e9d0.png` | No | - |
| `guardados/recursos_temp/cuadrado_4f99f9c1.png` | No | - |
| `guardados/recursos_temp/cuadrado_4fa81f5b.png` | No | - |
| `guardados/recursos_temp/cuadrado_504aaaf9.png` | No | - |
| `guardados/recursos_temp/cuadrado_5168ce97.png` | No | - |
| `guardados/recursos_temp/cuadrado_52010c40.png` | No | - |
| `guardados/recursos_temp/cuadrado_529a1225.png` | No | - |
| `guardados/recursos_temp/cuadrado_5344fbaa.png` | No | - |
| `guardados/recursos_temp/cuadrado_53b1d40a.png` | No | - |
| `guardados/recursos_temp/cuadrado_55056a35.png` | No | - |
| `guardados/recursos_temp/cuadrado_5728f396.png` | No | - |
| `guardados/recursos_temp/cuadrado_58292e55.png` | No | - |
| `guardados/recursos_temp/cuadrado_58b87c99.png` | No | - |
| `guardados/recursos_temp/cuadrado_5aa24590.png` | No | - |
| `guardados/recursos_temp/cuadrado_5ad497aa.png` | No | - |
| `guardados/recursos_temp/cuadrado_5cd27959.png` | No | - |
| `guardados/recursos_temp/cuadrado_5e26c63e.png` | No | - |
| `guardados/recursos_temp/cuadrado_609e056e.png` | No | - |
| `guardados/recursos_temp/cuadrado_611ab771.png` | No | - |
| `guardados/recursos_temp/cuadrado_63f881f9.png` | No | - |
| `guardados/recursos_temp/cuadrado_65e3ff44.png` | No | - |
| `guardados/recursos_temp/cuadrado_65f9ef18.png` | No | - |
| `guardados/recursos_temp/cuadrado_68a19bf3.png` | No | - |
| `guardados/recursos_temp/cuadrado_69373c65.png` | No | - |
| `guardados/recursos_temp/cuadrado_699291d4.png` | No | - |
| `guardados/recursos_temp/cuadrado_6c4d86c4.png` | No | - |
| `guardados/recursos_temp/cuadrado_6cdb9b8e.png` | No | - |
| `guardados/recursos_temp/cuadrado_706460de.png` | No | - |
| `guardados/recursos_temp/cuadrado_7522df99.png` | No | - |
| `guardados/recursos_temp/cuadrado_753a9123.png` | No | - |
| `guardados/recursos_temp/cuadrado_764c88cd.png` | No | - |
| `guardados/recursos_temp/cuadrado_7809f057.png` | No | - |
| `guardados/recursos_temp/cuadrado_79b62daa.png` | No | - |
| `guardados/recursos_temp/cuadrado_7a0f078a.png` | No | - |
| `guardados/recursos_temp/cuadrado_7acb03b6.png` | No | - |
| `guardados/recursos_temp/cuadrado_7bc6e38e.png` | No | - |
| `guardados/recursos_temp/cuadrado_7c2896e1.png` | No | - |
| `guardados/recursos_temp/cuadrado_7c434e63.png` | No | - |
| `guardados/recursos_temp/cuadrado_7e32d584.png` | No | - |
| `guardados/recursos_temp/cuadrado_7f0fc93d.png` | No | - |
| `guardados/recursos_temp/cuadrado_7f8477e9.png` | No | - |
| `guardados/recursos_temp/cuadrado_80b30f4c.png` | No | - |
| `guardados/recursos_temp/cuadrado_8146b95d.png` | No | - |
| `guardados/recursos_temp/cuadrado_8154ef6f.png` | No | - |
| `guardados/recursos_temp/cuadrado_81ffa965.png` | No | - |
| `guardados/recursos_temp/cuadrado_83de55d8.png` | No | - |
| `guardados/recursos_temp/cuadrado_85ec6dde.png` | No | - |
| `guardados/recursos_temp/cuadrado_860afa0a.png` | No | - |
| `guardados/recursos_temp/cuadrado_8901e06d.png` | No | - |
| `guardados/recursos_temp/cuadrado_899e6e4c.png` | No | - |
| `guardados/recursos_temp/cuadrado_8ae447c3.png` | No | - |
| `guardados/recursos_temp/cuadrado_8b0c1171.png` | No | - |
| `guardados/recursos_temp/cuadrado_8fb05945.png` | No | - |
| `guardados/recursos_temp/cuadrado_8fbc3812.png` | No | - |
| `guardados/recursos_temp/cuadrado_90a7029c.png` | No | - |
| `guardados/recursos_temp/cuadrado_91e77f8d.png` | No | - |
| `guardados/recursos_temp/cuadrado_928968f6.png` | No | - |
| `guardados/recursos_temp/cuadrado_934ecd7e.png` | No | - |
| `guardados/recursos_temp/cuadrado_9390d6f6.png` | No | - |
| `guardados/recursos_temp/cuadrado_971ff5c3.png` | No | - |
| `guardados/recursos_temp/cuadrado_9775d84b.png` | No | - |
| `guardados/recursos_temp/cuadrado_97ee8976.png` | No | - |
| `guardados/recursos_temp/cuadrado_994274dc.png` | No | - |
| `guardados/recursos_temp/cuadrado_99b970a7.png` | No | - |
| `guardados/recursos_temp/cuadrado_9a39f477.png` | No | - |
| `guardados/recursos_temp/cuadrado_9b59e220.png` | No | - |
| `guardados/recursos_temp/cuadrado_9c64e0c6.png` | No | - |
| `guardados/recursos_temp/cuadrado_9d6bd62d.png` | No | - |
| `guardados/recursos_temp/cuadrado_9df5f36c.png` | No | - |
| `guardados/recursos_temp/cuadrado_9ec64008.png` | No | - |
| `guardados/recursos_temp/cuadrado_a07714a8.png` | No | - |
| `guardados/recursos_temp/cuadrado_a1c0e40c.png` | No | - |
| `guardados/recursos_temp/cuadrado_a42ee068.png` | No | - |
| `guardados/recursos_temp/cuadrado_a5dc8f23.png` | No | - |
| `guardados/recursos_temp/cuadrado_a924a2c7.png` | No | - |
| `guardados/recursos_temp/cuadrado_ab165edf.png` | No | - |
| `guardados/recursos_temp/cuadrado_adef54f0.png` | No | - |
| `guardados/recursos_temp/cuadrado_adfa3961.png` | No | - |
| `guardados/recursos_temp/cuadrado_af67ae0e.png` | No | - |
| `guardados/recursos_temp/cuadrado_b2b95332.png` | No | - |
| `guardados/recursos_temp/cuadrado_b91ceb52.png` | No | - |
| `guardados/recursos_temp/cuadrado_ba35d2f2.png` | No | - |
| `guardados/recursos_temp/cuadrado_bad0c51b.png` | No | - |
| `guardados/recursos_temp/cuadrado_bd12f8d2.png` | No | - |
| `guardados/recursos_temp/cuadrado_be61ec8d.png` | No | - |
| `guardados/recursos_temp/cuadrado_c0a2bc0c.png` | No | - |
| `guardados/recursos_temp/cuadrado_c2f393ba.png` | No | - |
| `guardados/recursos_temp/cuadrado_c344901c.png` | No | - |
| `guardados/recursos_temp/cuadrado_c7330840.png` | No | - |
| `guardados/recursos_temp/cuadrado_c8af9128.png` | No | - |
| `guardados/recursos_temp/cuadrado_cbe12d83.png` | No | - |
| `guardados/recursos_temp/cuadrado_cc04edf4.png` | No | - |
| `guardados/recursos_temp/cuadrado_cd8ce16a.png` | No | - |
| `guardados/recursos_temp/cuadrado_cdba8f61.png` | No | - |
| `guardados/recursos_temp/cuadrado_d1d9aa68.png` | No | - |
| `guardados/recursos_temp/cuadrado_d1f14f92.png` | No | - |
| `guardados/recursos_temp/cuadrado_d333a4e7.png` | No | - |
| `guardados/recursos_temp/cuadrado_d4644238.png` | No | - |
| `guardados/recursos_temp/cuadrado_d46a6739.png` | No | - |
| `guardados/recursos_temp/cuadrado_d952c916.png` | No | - |
| `guardados/recursos_temp/cuadrado_d9fd96db.png` | No | - |
| `guardados/recursos_temp/cuadrado_dbff74a5.png` | No | - |
| `guardados/recursos_temp/cuadrado_dc19fff9.png` | No | - |
| `guardados/recursos_temp/cuadrado_dc88df2a.png` | No | - |
| `guardados/recursos_temp/cuadrado_dcf8316e.png` | No | - |
| `guardados/recursos_temp/cuadrado_ddd816a1.png` | No | - |
| `guardados/recursos_temp/cuadrado_de4c47c8.png` | No | - |
| `guardados/recursos_temp/cuadrado_df552b4f.png` | No | - |
| `guardados/recursos_temp/cuadrado_e3fa8297.png` | No | - |
| `guardados/recursos_temp/cuadrado_e59b0def.png` | No | - |
| `guardados/recursos_temp/cuadrado_e9d7a2ed.png` | No | - |
| `guardados/recursos_temp/cuadrado_ea5dabf8.png` | No | - |
| `guardados/recursos_temp/cuadrado_eb3cbb8f.png` | No | - |
| `guardados/recursos_temp/cuadrado_ebd41164.png` | No | - |
| `guardados/recursos_temp/cuadrado_ebe7676a.png` | No | - |
| `guardados/recursos_temp/cuadrado_ed200114.png` | No | - |
| `guardados/recursos_temp/cuadrado_ef41d91a.png` | No | - |
| `guardados/recursos_temp/cuadrado_f021d156.png` | No | - |
| `guardados/recursos_temp/cuadrado_f16415d2.png` | No | - |
| `guardados/recursos_temp/cuadrado_f1ef572c.png` | No | - |
| `guardados/recursos_temp/cuadrado_f2af5220.png` | No | - |
| `guardados/recursos_temp/cuadrado_f33aa28e.png` | No | - |
| `guardados/recursos_temp/cuadrado_f3eba0dd.png` | No | - |
| `guardados/recursos_temp/cuadrado_f40402ca.png` | No | - |
| `guardados/recursos_temp/cuadrado_f454d7bb.png` | No | - |
| `guardados/recursos_temp/cuadrado_f53e22a8.png` | No | - |
| `guardados/recursos_temp/cuadrado_f9a86cf5.png` | No | - |
| `guardados/recursos_temp/cuadrado_f9cce6ba.png` | No | - |
| `guardados/recursos_temp/cuadrado_fdaa8b6e.png` | No | - |
| `guardados/recursos_temp/cuadrado_ffcc6378.png` | No | - |
| `guardados/recursos_temp/cuadrado_ffd206cd.png` | No | - |

### Grupo 7: SHA-256 `99e4ab2df590cfd4...` (2 copias, 35,895 bytes c/u, desperdicio: 35,895 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/descargar_26d3006a.jpg` | Sí | `guardados/recursos_temp/prueba_imagen.json` |
| `guardados/recursos_temp/descargar_f4a4de9c.jpg` | No | - |

### Grupo 8: SHA-256 `08268d377cf9a691...` (22 copias, 611 bytes c/u, desperdicio: 12,831 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/flor_prueba_1de14ff1.png` | No | - |
| `guardados/recursos_temp/flor_prueba_3544879b.png` | No | - |
| `guardados/recursos_temp/flor_prueba_5f0f2e04.png` | No | - |
| `guardados/recursos_temp/flor_prueba_61487a20.png` | No | - |
| `guardados/recursos_temp/flor_prueba_617a3d23.png` | No | - |
| `guardados/recursos_temp/flor_prueba_66d40c01.png` | No | - |
| `guardados/recursos_temp/flor_prueba_710b90ae.png` | No | - |
| `guardados/recursos_temp/flor_prueba_7a11c01c.png` | No | - |
| `guardados/recursos_temp/flor_prueba_7bb28b5b.png` | No | - |
| `guardados/recursos_temp/flor_prueba_904cca10.png` | No | - |
| `guardados/recursos_temp/flor_prueba_9577f5bf.png` | No | - |
| `guardados/recursos_temp/flor_prueba_aead0972.png` | No | - |
| `guardados/recursos_temp/flor_prueba_b16e170c.png` | No | - |
| `guardados/recursos_temp/flor_prueba_be6aaf96.png` | No | - |
| `guardados/recursos_temp/flor_prueba_c5dbfbdb.png` | No | - |
| `guardados/recursos_temp/flor_prueba_ce0cb1bb.png` | No | - |
| `guardados/recursos_temp/flor_prueba_d0381b40.png` | No | - |
| `guardados/recursos_temp/flor_prueba_d1216d4d.png` | No | - |
| `guardados/recursos_temp/flor_prueba_dc9ac3b8.png` | No | - |
| `guardados/recursos_temp/flor_prueba_dd23ca6b.png` | No | - |
| `guardados/recursos_temp/flor_prueba_de68df63.png` | No | - |
| `guardados/recursos_temp/flor_prueba_eb8c8fd3.png` | No | - |

### Grupo 9: SHA-256 `4afc77d78056ad76...` (40 copias, 313 bytes c/u, desperdicio: 12,207 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/figura_0022ab20.png` | No | - |
| `guardados/recursos_temp/figura_0199e821.png` | No | - |
| `guardados/recursos_temp/figura_090a3df9.png` | No | - |
| `guardados/recursos_temp/figura_1657292f.png` | No | - |
| `guardados/recursos_temp/figura_182f656d.png` | No | - |
| `guardados/recursos_temp/figura_1e065fa2.png` | No | - |
| `guardados/recursos_temp/figura_30a7edc9.png` | No | - |
| `guardados/recursos_temp/figura_347d7776.png` | No | - |
| `guardados/recursos_temp/figura_39e6f730.png` | No | - |
| `guardados/recursos_temp/figura_487c67b3.png` | No | - |
| `guardados/recursos_temp/figura_4b66ae0a.png` | No | - |
| `guardados/recursos_temp/figura_4b922033.png` | No | - |
| `guardados/recursos_temp/figura_4e92e8ba.png` | No | - |
| `guardados/recursos_temp/figura_4fa66871.png` | No | - |
| `guardados/recursos_temp/figura_575188f3.png` | No | - |
| `guardados/recursos_temp/figura_84a90599.png` | No | - |
| `guardados/recursos_temp/figura_8547c396.png` | No | - |
| `guardados/recursos_temp/figura_865588d2.png` | No | - |
| `guardados/recursos_temp/figura_8bac368b.png` | No | - |
| `guardados/recursos_temp/figura_8e63fb99.png` | No | - |
| `guardados/recursos_temp/figura_914ea459.png` | No | - |
| `guardados/recursos_temp/figura_946318f6.png` | No | - |
| `guardados/recursos_temp/figura_9783090b.png` | No | - |
| `guardados/recursos_temp/figura_a78dd499.png` | No | - |
| `guardados/recursos_temp/figura_adee548b.png` | No | - |
| `guardados/recursos_temp/figura_b0d7ff5f.png` | No | - |
| `guardados/recursos_temp/figura_b3712ce2.png` | No | - |
| `guardados/recursos_temp/figura_c55cd7b4.png` | No | - |
| `guardados/recursos_temp/figura_ca3e02aa.png` | No | - |
| `guardados/recursos_temp/figura_d3f5d35a.png` | No | - |
| `guardados/recursos_temp/figura_d8039c91.png` | No | - |
| `guardados/recursos_temp/figura_dff9eff7.png` | No | - |
| `guardados/recursos_temp/figura_ea145df6.png` | No | - |
| `guardados/recursos_temp/figura_ec91ae64.png` | No | - |
| `guardados/recursos_temp/figura_f1356c3e.png` | No | - |
| `guardados/recursos_temp/figura_f31b6112.png` | No | - |
| `guardados/recursos_temp/figura_f778e799.png` | No | - |
| `guardados/recursos_temp/figura_f848c521.png` | No | - |
| `guardados/recursos_temp/figura_ff4bd52a.png` | No | - |
| `guardados/recursos_temp/figura_ff6bceec.png` | No | - |

### Grupo 10: SHA-256 `86f8b66e4d27ebc1...` (4 copias, 3,636 bytes c/u, desperdicio: 10,908 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/flor_cantoya_e96542ec.png` | No | - |
| `docs/ejemplos/disenos/flor_cantoya.png` | No | - |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/flor_cantoya_23891d12.png` | No | - |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/flor_cantoya_7c0b5480.png` | Sí | `docs/ejemplos/disenos/ejemplo_espejo_12.json` |

### Grupo 11: SHA-256 `7cbc8946681c36a6...` (8 copias, 1,061 bytes c/u, desperdicio: 7,427 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/medallon_2e680f58.svg` | No | - |
| `guardados/recursos_temp/medallon_5388d12f.svg` | No | - |
| `guardados/recursos_temp/medallon_6e46e873.svg` | No | - |
| `guardados/recursos_temp/medallon_6e6ff33e.svg` | No | - |
| `guardados/recursos_temp/medallon_812eee0e.svg` | No | - |
| `guardados/recursos_temp/medallon_dd88209a.svg` | No | - |
| `guardados/recursos_temp/medallon_df06b2a2.svg` | No | - |
| `guardados/recursos_temp/medallon_fdc6206f.svg` | No | - |

### Grupo 12: SHA-256 `4f2ca9dda6f185cb...` (3 copias, 1,092 bytes c/u, desperdicio: 2,184 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `docs/ejemplos/disenos/medallon.svg` | No | - |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/medallon_7b8d98e5.svg` | No | - |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/medallon_d4da864b.svg` | Sí | `docs/ejemplos/disenos/ejemplo_espejo_12.json` |

### Grupo 13: SHA-256 `ec8202bc75d11811...` (3 copias, 1,057 bytes c/u, desperdicio: 2,114 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `docs/ejemplos/disenos/mosaico_geometrico.svg` | No | - |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/mosaico_geometrico_04d6a76a.svg` | Sí | `docs/ejemplos/disenos/ejemplo_espejo_12.json` |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/mosaico_geometrico_4d2bbdb1.svg` | No | - |

### Grupo 14: SHA-256 `520f2290715922be...` (3 copias, 582 bytes c/u, desperdicio: 1,164 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/_franja_roja_mitad.png` | No | - |
| `guardados/recursos_temp/_franja_roja_mitad_06d01d70.png` | No | - |
| `guardados/recursos_temp/_franja_roja_mitad_3bf78bb9.png` | No | - |

### Grupo 15: SHA-256 `42ee8049e3303e5d...` (3 copias, 470 bytes c/u, desperdicio: 940 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/_bloque_azul_mitad.png` | No | - |
| `guardados/recursos_temp/_bloque_azul_mitad_3954a3ef.png` | No | - |
| `guardados/recursos_temp/_bloque_azul_mitad_e7b85351.png` | No | - |

### Grupo 16: SHA-256 `d08a07d0574b801e...` (7 copias, 143 bytes c/u, desperdicio: 858 bytes)
| Archivo | Referenciado | Proyectos que lo citan |
|---|---|---|
| `guardados/recursos_temp/figura_06f74931.svg` | No | - |
| `guardados/recursos_temp/figura_2763c577.svg` | No | - |
| `guardados/recursos_temp/figura_3ee0a6c1.svg` | No | - |
| `guardados/recursos_temp/figura_a518300f.svg` | No | - |
| `guardados/recursos_temp/figura_b1c1cf1d.svg` | No | - |
| `guardados/recursos_temp/figura_da882ecd.svg` | No | - |
| `guardados/recursos_temp/figura_e8cbd248.svg` | No | - |

## 3. Inventario Completo de Archivos

| Ruta Relativa | Tamaño (bytes) | SHA-256 | Referenciado |
|---|---|---|---|
| `docs/ejemplos/abanico_inf_carta.svg` | 25,933 | `4cbcbea2db64364b...` | No |
| `docs/ejemplos/abanico_pico_carta.svg` | 10,389 | `a3143987ca5b090b...` | No |
| `docs/ejemplos/abanico_sup_carta.svg` | 16,785 | `e13b5f8875d83901...` | No |
| `docs/ejemplos/cono_inferior_1_10.svg` | 7,660 | `57b21a7654893a59...` | No |
| `docs/ejemplos/cono_superior_1_10.svg` | 5,392 | `f4c6f92e054bf4e5...` | No |
| `docs/ejemplos/disenos/_prueba_usuario.jpg` | 108,754 | `4307cd2d18f284b3...` | No |
| `docs/ejemplos/disenos/_prueba_usuario.svg` | 83,449 | `0b3cc98f3ce2f188...` | No |
| `docs/ejemplos/disenos/ejemplo_espejo_12.json` | 5,231 | `044ef3e6b35c45e1...` | No |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/flor_cantoya_23891d12.png` | 3,636 | `86f8b66e4d27ebc1...` | No |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/flor_cantoya_7c0b5480.png` | 3,636 | `86f8b66e4d27ebc1...` | Sí |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/medallon_7b8d98e5.svg` | 1,092 | `4f2ca9dda6f185cb...` | No |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/medallon_d4da864b.svg` | 1,092 | `4f2ca9dda6f185cb...` | Sí |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/mosaico_geometrico_04d6a76a.svg` | 1,057 | `ec8202bc75d11811...` | Sí |
| `docs/ejemplos/disenos/ejemplo_espejo_12_recursos/mosaico_geometrico_4d2bbdb1.svg` | 1,057 | `ec8202bc75d11811...` | No |
| `docs/ejemplos/disenos/flor_cantoya.png` | 3,636 | `86f8b66e4d27ebc1...` | No |
| `docs/ejemplos/disenos/medallon.svg` | 1,092 | `4f2ca9dda6f185cb...` | No |
| `docs/ejemplos/disenos/mosaico_geometrico.svg` | 1,057 | `ec8202bc75d11811...` | No |
| `docs/ejemplos/hoja_inferior_central_espejo.svg` | 23,484 | `63a2a4278d21adcc...` | No |
| `docs/ejemplos/hoja_inferior_espejo_total.svg` | 15,804 | `be577c2e93024538...` | No |
| `docs/ejemplos/hoja_inferior_repeticion.svg` | 38,652 | `965a2837290aa2d8...` | No |
| `docs/ejemplos/pico_1_10.svg` | 4,049 | `49117abe242081f7...` | No |
| `guardados/_demo_recursos/mosaico_geometrico_256a9e4b.svg` | 994 | `bb2a21e35e1e1993...` | No |
| `guardados/_demo_recursos/mosaico_geometrico_39543adb.svg` | 994 | `7dd8cb0bfd995eca...` | No |
| `guardados/_demo_recursos/mosaico_geometrico_41a5a0e4.svg` | 994 | `8cc35b8f4dfa74f4...` | No |
| `guardados/_demo_recursos/mosaico_geometrico_4d5f80e4.svg` | 994 | `93daae7f613a2cf0...` | No |
| `guardados/_demo_recursos/mosaico_geometrico_52291198.svg` | 994 | `d4cc1c8cda54866a...` | No |
| `guardados/_demo_recursos/mosaico_geometrico_e47d227d.svg` | 994 | `e3e286421e0f5e4e...` | No |
| `guardados/_demo_recursos/mosaico_geometrico_e5401620.svg` | 994 | `163179148cca333d...` | No |
| `guardados/_demo_recursos/mosaico_geometrico_efa2bdd0.svg` | 994 | `d5e1116e5b30e229...` | No |
| `guardados/_demo_recursos/mosaico_geometrico_ff285b40.svg` | 994 | `189773a8a12288fa...` | No |
| `guardados/recursos_temp/Gemini_Generated_Image_oxoxud_557c40ec.jpg` | 157,194 | `bc16d4b1bdf8ee7f...` | No |
| `guardados/recursos_temp/Gemini_Generated_Image_oxoxud_c39e767f.jpg` | 157,194 | `bc16d4b1bdf8ee7f...` | No |
| `guardados/recursos_temp/Gemini_Generated_Image_oxoxud_eff8472f.jpg` | 157,194 | `bc16d4b1bdf8ee7f...` | No |
| `guardados/recursos_temp/WhatsApp_Image_2026-10-08_at_8_bef569b3.jpeg` | 116,990 | `b0b593efb9b064e4...` | No |
| `guardados/recursos_temp/WhatsApp_Image_2026-10-08_at_8_c4523fa5.jpeg` | 116,990 | `b0b593efb9b064e4...` | No |
| `guardados/recursos_temp/WhatsApp_Image_2026-10-08_at_8_c72deaa1.jpeg` | 116,990 | `b0b593efb9b064e4...` | No |
| `guardados/recursos_temp/_bench_180kb.png` | 213,987 | `f39774a2267d881b...` | No |
| `guardados/recursos_temp/_bench_180kb_2bb3fb39.png` | 213,987 | `f39774a2267d881b...` | No |
| `guardados/recursos_temp/_bench_180kb_5b7cb752.png` | 213,987 | `f39774a2267d881b...` | No |
| `guardados/recursos_temp/_bench_180kb_a88234bd.png` | 213,987 | `f39774a2267d881b...` | No |
| `guardados/recursos_temp/_bench_180kb_ab0e7e0a.png` | 213,987 | `f39774a2267d881b...` | No |
| `guardados/recursos_temp/_bench_180kb_d7cc7817.png` | 213,987 | `f39774a2267d881b...` | No |
| `guardados/recursos_temp/_bloque_azul_mitad.png` | 470 | `42ee8049e3303e5d...` | No |
| `guardados/recursos_temp/_bloque_azul_mitad_3954a3ef.png` | 470 | `42ee8049e3303e5d...` | No |
| `guardados/recursos_temp/_bloque_azul_mitad_e7b85351.png` | 470 | `42ee8049e3303e5d...` | No |
| `guardados/recursos_temp/_franja_roja_mitad.png` | 582 | `520f2290715922be...` | No |
| `guardados/recursos_temp/_franja_roja_mitad_06d01d70.png` | 582 | `520f2290715922be...` | No |
| `guardados/recursos_temp/_franja_roja_mitad_3bf78bb9.png` | 582 | `520f2290715922be...` | No |
| `guardados/recursos_temp/_prueba_usuario_0c8648e9.svg` | 83,108 | `a06fbf13cf7795ef...` | No |
| `guardados/recursos_temp/_prueba_usuario_39bafaf3.svg` | 83,108 | `06a02c1a79debaeb...` | No |
| `guardados/recursos_temp/_prueba_usuario_59deaee1.svg` | 83,108 | `f3ccff52c4ec6ac3...` | No |
| `guardados/recursos_temp/_prueba_usuario_5f971571.jpg` | 112,689 | `7d61c133e98212a4...` | No |
| `guardados/recursos_temp/_prueba_usuario_94c73647.svg` | 83,108 | `688106cc3d152553...` | No |
| `guardados/recursos_temp/cuadrado_06e8346b.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_078bdb62.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_0b908583.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_0c3f8096.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_0eb5364d.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_0ff63b73.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_103d03bb.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_12418b12.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_12a00c8c.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_1349b9e1.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_13aab70b.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_13b53411.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_155a5861.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_160d55c3.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_170cb887.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_17dc25bb.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_193711dc.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_19ca3273.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_1aac79a5.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_1ac7e707.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_1b0ed508.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_1d453bf0.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_1e3f5053.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_1e6b0baf.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_1ecb9067.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_215a95af.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_21e47709.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_2349c1eb.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_23a9efd4.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_24e7835c.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_27a5be71.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_27f26613.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_2cc4d458.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_2cd47a89.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_2e23ab04.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_2ebdc5a1.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_30d550af.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_34135428.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_34748146.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_3651e440.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_3797fb3d.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_37f6aeea.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_38a2e546.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_39715312.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_39990bdc.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_3ab43ba4.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_3d075e73.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_3d236c96.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_3ecd8694.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_43011577.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_43314ed7.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_43505861.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_46b1378d.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_49f1d131.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_4d2af052.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_4d74a623.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_4e0bc9b9.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_4ea14039.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_4eb407fd.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_4f13f5d5.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_4f64e9d0.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_4f99f9c1.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_4fa81f5b.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_504aaaf9.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_5168ce97.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_52010c40.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_529a1225.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_5344fbaa.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_53b1d40a.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_55056a35.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_5728f396.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_58292e55.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_58b87c99.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_5aa24590.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_5ad497aa.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_5cd27959.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_5e26c63e.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_609e056e.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_611ab771.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_63f881f9.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_65e3ff44.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_65f9ef18.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_68a19bf3.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_69373c65.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_699291d4.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_6c4d86c4.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_6cdb9b8e.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_706460de.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_7522df99.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_753a9123.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_764c88cd.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_7809f057.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_79b62daa.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_7a0f078a.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_7acb03b6.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_7bc6e38e.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_7c2896e1.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_7c434e63.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_7e32d584.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_7f0fc93d.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_7f8477e9.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_80b30f4c.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_8146b95d.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_8154ef6f.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_81ffa965.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_83de55d8.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_85ec6dde.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_860afa0a.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_8901e06d.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_899e6e4c.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_8ae447c3.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_8b0c1171.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_8fb05945.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_8fbc3812.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_90a7029c.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_91e77f8d.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_928968f6.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_934ecd7e.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_9390d6f6.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_971ff5c3.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_9775d84b.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_97ee8976.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_994274dc.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_99b970a7.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_9a39f477.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_9b59e220.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_9c64e0c6.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_9d6bd62d.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_9df5f36c.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_9ec64008.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_a07714a8.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_a1c0e40c.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_a42ee068.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_a5dc8f23.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_a924a2c7.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_ab165edf.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_adef54f0.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_adfa3961.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_af67ae0e.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_b2b95332.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_b91ceb52.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_ba35d2f2.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_bad0c51b.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_bd12f8d2.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_be61ec8d.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_c0a2bc0c.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_c2f393ba.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_c344901c.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_c7330840.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_c8af9128.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_cbe12d83.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_cc04edf4.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_cd8ce16a.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_cdba8f61.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_d1d9aa68.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_d1f14f92.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_d333a4e7.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_d4644238.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_d46a6739.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_d952c916.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_d9fd96db.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_dbff74a5.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_dc19fff9.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_dc88df2a.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_dcf8316e.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_ddd816a1.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_de4c47c8.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_df552b4f.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_e3fa8297.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_e59b0def.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_e9d7a2ed.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_ea5dabf8.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_eb3cbb8f.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_ebd41164.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_ebe7676a.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_ed200114.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_ef41d91a.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_f021d156.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_f16415d2.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_f1ef572c.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_f2af5220.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_f33aa28e.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_f3eba0dd.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_f40402ca.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_f454d7bb.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_f53e22a8.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_f9a86cf5.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_f9cce6ba.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_fdaa8b6e.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_ffcc6378.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/cuadrado_ffd206cd.png` | 591 | `af099b1ebc4c79b7...` | No |
| `guardados/recursos_temp/descargar_26d3006a.jpg` | 35,895 | `99e4ab2df590cfd4...` | Sí |
| `guardados/recursos_temp/descargar_f4a4de9c.jpg` | 35,895 | `99e4ab2df590cfd4...` | No |
| `guardados/recursos_temp/figura_0022ab20.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_0199e821.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_06f74931.svg` | 143 | `d08a07d0574b801e...` | No |
| `guardados/recursos_temp/figura_090a3df9.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_1657292f.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_182f656d.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_1e065fa2.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_2763c577.svg` | 143 | `d08a07d0574b801e...` | No |
| `guardados/recursos_temp/figura_30a7edc9.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_347d7776.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_39e6f730.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_3ee0a6c1.svg` | 143 | `d08a07d0574b801e...` | No |
| `guardados/recursos_temp/figura_487c67b3.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_4b66ae0a.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_4b922033.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_4e92e8ba.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_4fa66871.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_575188f3.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_84a90599.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_8547c396.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_865588d2.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_8bac368b.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_8e63fb99.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_914ea459.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_946318f6.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_9783090b.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_a518300f.svg` | 143 | `d08a07d0574b801e...` | No |
| `guardados/recursos_temp/figura_a78dd499.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_adee548b.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_b0d7ff5f.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_b1c1cf1d.svg` | 143 | `d08a07d0574b801e...` | No |
| `guardados/recursos_temp/figura_b3712ce2.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_c55cd7b4.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_ca3e02aa.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_d3f5d35a.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_d8039c91.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_da882ecd.svg` | 143 | `d08a07d0574b801e...` | No |
| `guardados/recursos_temp/figura_dff9eff7.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_e8cbd248.svg` | 143 | `d08a07d0574b801e...` | No |
| `guardados/recursos_temp/figura_ea145df6.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_ec91ae64.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_f1356c3e.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_f31b6112.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_f778e799.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_f848c521.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_ff4bd52a.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/figura_ff6bceec.png` | 313 | `4afc77d78056ad76...` | No |
| `guardados/recursos_temp/flor_cantoya_e96542ec.png` | 3,636 | `86f8b66e4d27ebc1...` | No |
| `guardados/recursos_temp/flor_prueba_1de14ff1.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_3544879b.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_5f0f2e04.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_61487a20.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_617a3d23.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_66d40c01.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_710b90ae.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_7a11c01c.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_7bb28b5b.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_904cca10.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_9577f5bf.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_aead0972.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_b16e170c.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_be6aaf96.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_c5dbfbdb.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_ce0cb1bb.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_d0381b40.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_d1216d4d.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_dc9ac3b8.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_dd23ca6b.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_de68df63.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/flor_prueba_eb8c8fd3.png` | 611 | `08268d377cf9a691...` | No |
| `guardados/recursos_temp/malla_densa_20b3e7cc.svg` | 127,512 | `051dc60f85fd742b...` | No |
| `guardados/recursos_temp/malla_densa_2db5af03.svg` | 127,512 | `051dc60f85fd742b...` | No |
| `guardados/recursos_temp/malla_densa_404604c4.svg` | 127,512 | `051dc60f85fd742b...` | No |
| `guardados/recursos_temp/malla_densa_6c5c8099.svg` | 127,512 | `051dc60f85fd742b...` | No |
| `guardados/recursos_temp/malla_densa_72bf79c2.svg` | 127,512 | `051dc60f85fd742b...` | No |
| `guardados/recursos_temp/malla_densa_d5027d3a.svg` | 127,512 | `051dc60f85fd742b...` | No |
| `guardados/recursos_temp/malla_densa_ef83c4b1.svg` | 127,512 | `051dc60f85fd742b...` | No |
| `guardados/recursos_temp/malla_densa_f826333a.svg` | 127,512 | `051dc60f85fd742b...` | No |
| `guardados/recursos_temp/medallon_2e680f58.svg` | 1,061 | `7cbc8946681c36a6...` | No |
| `guardados/recursos_temp/medallon_5388d12f.svg` | 1,061 | `7cbc8946681c36a6...` | No |
| `guardados/recursos_temp/medallon_6e46e873.svg` | 1,061 | `7cbc8946681c36a6...` | No |
| `guardados/recursos_temp/medallon_6e6ff33e.svg` | 1,061 | `7cbc8946681c36a6...` | No |
| `guardados/recursos_temp/medallon_812eee0e.svg` | 1,061 | `7cbc8946681c36a6...` | No |
| `guardados/recursos_temp/medallon_dd88209a.svg` | 1,061 | `7cbc8946681c36a6...` | No |
| `guardados/recursos_temp/medallon_df06b2a2.svg` | 1,061 | `7cbc8946681c36a6...` | No |
| `guardados/recursos_temp/medallon_fdc6206f.svg` | 1,061 | `7cbc8946681c36a6...` | No |
| `guardados/recursos_temp/mosaico_geometrico_003136d1.svg` | 994 | `957367165257e141...` | No |
| `guardados/recursos_temp/mosaico_geometrico_081c18e0.svg` | 994 | `eae983b498096136...` | No |
| `guardados/recursos_temp/mosaico_geometrico_1059fd87.svg` | 994 | `3d6a0a7a0bbcc346...` | No |
| `guardados/recursos_temp/mosaico_geometrico_1550d3c0.svg` | 994 | `48fc67e8dbc2ae7b...` | No |
| `guardados/recursos_temp/mosaico_geometrico_171259bc.svg` | 994 | `6c4d2283d7bb5e1f...` | No |
| `guardados/recursos_temp/mosaico_geometrico_19d9e169.svg` | 994 | `5134e50718531e9f...` | No |
| `guardados/recursos_temp/mosaico_geometrico_1a3ec20d.svg` | 994 | `965b5412c0f35d53...` | No |
| `guardados/recursos_temp/mosaico_geometrico_21676b7d.svg` | 994 | `82c820eb20434b0a...` | No |
| `guardados/recursos_temp/mosaico_geometrico_2e795338.svg` | 994 | `4090160c6fa496dd...` | No |
| `guardados/recursos_temp/mosaico_geometrico_4db205bb.svg` | 994 | `7f3a9877a6efae43...` | No |
| `guardados/recursos_temp/mosaico_geometrico_514e560f.svg` | 994 | `581a40fc01377239...` | No |
| `guardados/recursos_temp/mosaico_geometrico_52aa635b.svg` | 994 | `624a15f936b67b9f...` | No |
| `guardados/recursos_temp/mosaico_geometrico_605f4a96.svg` | 994 | `6c0b6f3f188c8c7a...` | No |
| `guardados/recursos_temp/mosaico_geometrico_62b05895.svg` | 994 | `9b9e3b1381ab9e29...` | No |
| `guardados/recursos_temp/mosaico_geometrico_6937e752.svg` | 994 | `55be40697f4e1f8f...` | No |
| `guardados/recursos_temp/mosaico_geometrico_6a63428d.svg` | 994 | `3477b7c22a24a837...` | No |
| `guardados/recursos_temp/mosaico_geometrico_6ad9d037.svg` | 994 | `6008e9b4b700fbe6...` | No |
| `guardados/recursos_temp/mosaico_geometrico_73e8438f.svg` | 994 | `5a638b6e880a8fb4...` | No |
| `guardados/recursos_temp/mosaico_geometrico_7506e89f.svg` | 994 | `5085500d4cff35cf...` | No |
| `guardados/recursos_temp/mosaico_geometrico_792e22cd.svg` | 994 | `4ea4e561fde2471b...` | No |
| `guardados/recursos_temp/mosaico_geometrico_7b60ac9f.svg` | 994 | `3f22b3bbd96484a0...` | No |
| `guardados/recursos_temp/mosaico_geometrico_8127492b.svg` | 994 | `c6a51d9f83966926...` | No |
| `guardados/recursos_temp/mosaico_geometrico_82b3bc02.svg` | 994 | `744e2399b241566f...` | No |
| `guardados/recursos_temp/mosaico_geometrico_909228d0.svg` | 994 | `d0cb947c00aef995...` | No |
| `guardados/recursos_temp/mosaico_geometrico_9301ff6f.svg` | 994 | `82e3efe3ca7a74b5...` | No |
| `guardados/recursos_temp/mosaico_geometrico_934570b6.svg` | 994 | `6f4b3afbeafb1c32...` | No |
| `guardados/recursos_temp/mosaico_geometrico_9b76b3ec.svg` | 994 | `3ccefb12691d99ed...` | No |
| `guardados/recursos_temp/mosaico_geometrico_a02e1a77.svg` | 994 | `ad64d4595fb01e6f...` | No |
| `guardados/recursos_temp/mosaico_geometrico_a4f3d19c.svg` | 994 | `f9c2c527cd463afe...` | No |
| `guardados/recursos_temp/mosaico_geometrico_a6878124.svg` | 994 | `e9f7acba5f26ffe5...` | No |
| `guardados/recursos_temp/mosaico_geometrico_b50ccf45.svg` | 994 | `2a5988cddc6452e1...` | No |
| `guardados/recursos_temp/mosaico_geometrico_b63daf1c.svg` | 994 | `50dea61723d6acb3...` | No |
| `guardados/recursos_temp/mosaico_geometrico_bb8d9cbf.svg` | 994 | `a827ad9c7b7a69ee...` | No |
| `guardados/recursos_temp/mosaico_geometrico_bdc29013.svg` | 994 | `4ca3851c965b0c45...` | No |
| `guardados/recursos_temp/mosaico_geometrico_c8c6893d.svg` | 994 | `bd9aa0648d52fa6e...` | No |
| `guardados/recursos_temp/mosaico_geometrico_d2e05486.svg` | 994 | `5959856878d8533e...` | No |
| `guardados/recursos_temp/mosaico_geometrico_e598196d.svg` | 994 | `65c7b84f6034d0f4...` | No |
| `guardados/recursos_temp/mosaico_geometrico_e8008f26.svg` | 994 | `78e4187baa11cda3...` | No |
| `guardados/recursos_temp/mosaico_geometrico_f7abd272.svg` | 994 | `9008525a4de03680...` | No |
| `guardados/recursos_temp/prueba_imagen.json` | 8,582 | `ac44319447e3f60f...` | No |
| `guardados/recursos_temp/textura_4k_0c405740.png` | 56,255 | `0a89c95889546076...` | No |
| `guardados/recursos_temp/textura_4k_1e4bf0f9.png` | 56,255 | `0a89c95889546076...` | No |
| `guardados/recursos_temp/textura_4k_44368855.png` | 56,255 | `0a89c95889546076...` | No |
| `guardados/recursos_temp/textura_4k_50fa1dd1.png` | 56,255 | `0a89c95889546076...` | No |
| `guardados/recursos_temp/textura_4k_53db712f.png` | 56,255 | `0a89c95889546076...` | No |
| `guardados/recursos_temp/textura_4k_54835c4f.png` | 56,255 | `0a89c95889546076...` | No |
| `guardados/recursos_temp/textura_4k_888e74b8.png` | 56,255 | `0a89c95889546076...` | No |
| `guardados/recursos_temp/textura_4k_89a55486.png` | 56,255 | `0a89c95889546076...` | No |