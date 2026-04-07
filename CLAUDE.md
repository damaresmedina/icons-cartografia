# ICONS — Cartografia do Contencioso Constitucional
## Instituto Constituição Aberta · PROJUS · Coord. Damares Medina

## QUEM É A USUÁRIA

**Damares Medina** — pesquisadora (15+ anos STF), advogada, professora IDP, Visiting Scholar Bicocca-Milano.
- Livros: Amicus Curiae (2010), Repercussão Geral no STF (2015, Saraiva), Manual do Contencioso Constitucional (em produção 2026)
- Papers: "The Extractive Litigating State", "Fiscal Risk Constitutionalism", "Circuitos de Enforcement"
- **NÃO é programadora**: executar e reportar RESULTADOS. NUNCA pedir para copiar/colar/recortar/anexar/rodar comandos. Fazer tudo direto.
- **Estilo**: direta, monitora de perto, quer resultados.
- **Voz autoral** para textos: frase densa, 1ª plural, dado → interpretação → implicação → ressalva
- **Rigor empírico**: nunca inferir além dos dados, nunca número sem contexto
- **Memórias globais**: `C:\Users\medin\.claude\projects\C--Users-medin\memory\`

## OBRIGATÓRIO A CADA INÍCIO DE SESSÃO

1. Leia este CLAUDE.md
2. Este projeto é **COMPLETAMENTE SEPARADO** do JudX. Nunca misturar dados, código ou infra.
3. Banco ICONS: `postgresql://postgres:RHuQvsf4shpsPRjP@db.hetuhkhhppxjliiaerlu.supabase.co:6543/postgres`
4. Protocolo ontológico vigente: v9 (9 entidades, 3 camadas)
5. CONSTITUICAO_ONTOLOGICA.md é a lei fundamental — toda implementação deriva dela
6. Nomenclatura obrigatória: registro_jurisprudencial, ancora_normativa, ancora_processual, etc.
7. Toda produção textual usa a voz autoral de Damares Medina (ver memórias)

## Projeto

O ICONS é a cartografia jurisprudencial da CF/88. A Constituição é SEMPRE o parâmetro. Decisões do STF são camada de anotação sobre ela.

- **Banco**: Supabase (hetuhkhhppxjliiaerlu)
- **Site**: icons.org.br (deploy via Vercel, repo damaresmedina/icons-cartografia)
- **Local**: C:\projetos\icons (código) + C:\projetos\icons-cartografia (deploy)
- **Ontologia**: 9 entidades (objeto, edge, bucket, etc.), 3 camadas (raw, semântica, analítica)

## Schema do Banco

- **objects** — id (uuid), slug, type_slug, payload (jsonb), court_id, recorded_at
- **edges** — edge_id, type_slug (ancora_normativa/ancora_processual/relator_de/produzido_por), source_id, target_id, payload
- Type slugs nos objects: registro_jurisprudencial, processo, artigo, inciso, paragrafo, alinea, tema_repetitivo_stj, divisor_editorial

## Dados Atuais

- 126.545 objects (registros jurisprudenciais, processos, dispositivos CF)
- 7.766 edges ancora_normativa (decisão → dispositivo CF)
- 213.258 edges ancora_processual
- 142.729 edges relator_de
- Art. 5º lidera com 1.049 decisões vinculadas

## Regras Absolutas

1. NUNCA mexer nos repos projus/icons no GitHub — sempre usar damaresmedina/icons-cartografia
2. Deploy só com confirmação explícita
3. Nunca criar nada sem perguntar antes
4. Conteúdo e rigor > design
5. JudX e ICONS nunca se misturam
