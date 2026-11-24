# 8. Uma biblioteca com várias prateleiras 🗂️

Em 23/11/2026, adicionamos 56 projetos **fictícios** ao banco do projeto para testar
os filtros e pesquisas. Os 83 registros anteriores foram comparados antes e depois
e permaneceram intactos. A base agora tem 139 projetos em cinco anos.

| Ano | Projetos |
|---|---:|
| 2022 | 8 |
| 2023 | 12 |
| 2024 | 16 |
| 2025 | 20 |
| 2026 | 83 (preexistentes) |

## Por que essas escolhas?

Um gráfico com anos de tamanhos diferentes permite perceber o efeito do filtro.
Os mesmos cenários aparecem em anos distintos para testar buscas combinadas.
As chaves `DEMO-001`, `DEMO-002` etc. são reutilizadas entre anos para demonstrar
que a identidade do projeto inclui o ano. O prefixo `DEMO` nos identificadores,
eventos e demandantes e a observação de dado fictício distinguem a demonstração.

Foram criadas quatro planilhas com todos os cabeçalhos esperados em `data/demo/`.
Cada arquivo passou pela simulação e depois pelo ETL normal, gerando uma carga
bem-sucedida e uma versão inicial por projeto. Não houve inserção direta de linhas
na staging. O relatório de execução está em `reports/demo_20261123.json`.

## Roteiro manual

Clique em **Atualizar consultas** no painel e selecione explicitamente os anos
2022–2025 no filtro, caso uma sessão anterior ainda mantenha apenas 2026 selecionado.

| Ação (anos 2022–2025 selecionados) | Resultado verificado |
|---|---:|
| Buscar `DEMO` | 56 projetos |
| Buscar `Python` | 8 projetos |
| Buscar `Horizonte` | 8 projetos |
| Buscar `DEMO-001` | 4 projetos, um por ano |
| Buscar `termo_inexistente_987654` | 0 projetos |
| Selecionar só 2024 e 2025 e limpar a busca | 36 projetos |
| Selecionar só 2022 e limpar a busca | 8 projetos |

Buscas usam os campos CI, número da CI, demandante, evento, demanda e setor.
Status e UR estão disponíveis na tabela, mas não fazem parte da busca textual atual.
Os indicadores e o gráfico resumem os anos selecionados, antes do filtro textual.

Na aba **Histórico**, selecione 2023 e digite `DEMO-001`: deve existir uma versão
inicial. Esta carga não inventou atualizações posteriores. Na aba **Últimas cargas**,
confira as quatro novas execuções e suas respectivas contagens.

## Como reproduzir

Na raiz `data_mart_etl`:

```bash
python scripts/gerar_dados_demo.py
campus-etl --manifest config/sources.demo.json --dry-run
campus-etl --manifest config/sources.demo.json
```

O gerador somente cria arquivos; a última linha altera o banco configurado.
Recarregar conteúdo igual contabiliza registros inalterados, sem duplicar projetos
ou versões. Guarde o prefixo `DEMO-` para dados fictícios e não o use em projetos reais.
Datas, valores financeiros e nomes desta demonstração são ilustrativos.
