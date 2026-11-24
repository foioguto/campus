# 7. A biblioteca ganhou catálogo e memória 📚

Em 22/11/2026, as migrações foram aplicadas ao PostgreSQL configurado no projeto,
na base `dm_demandas`. Este é um projeto desenvolvido em contexto freelancer;
a base do projeto não é o banco corporativo da empresa em que o autor trabalha.

## Antes de trocar as estantes

Conferimos a conexão e o estado existente: 83 projetos na staging e 5 tentativas
na auditoria. As tabelas de histórico e as views ainda não existiam.
Foi criado um backup em formato custom do PostgreSQL, com acesso restrito ao usuário:

`reports/backups/pre_migracao_20261122T204822Z.dump`

O arquivo foi conferido com `pg_restore --list`. Isso verifica a leitura do catálogo
do backup; não substitui um teste completo de restauração em outro banco.
Backups e relatórios ficam ignorados pelo Git para evitar versionar dados internos.

## O que foi executado

1. `01_schemas_staging_audit.sql`: reaplicado de forma idempotente, preservando as estruturas existentes.
2. `03_integridade_historico_consultas.sql`: aplicado para criar unicidade, contadores,
   histórico por versão e as views `mart.projetos` e `mart.resumo_anual`.

Os arquivos 02 e 04 contêm consultas de conferência/exemplos, não migrações.
As verificações foram feitas diretamente com consultas equivalentes.

## Depois da mudança

| Verificação | Resultado |
|---|---|
| Projetos antes e depois | 83 → 83 |
| Cargas auditadas antes e depois | 5 → 5 |
| Versões iniciais registradas | 83 |
| Projetos sem versão de referência | 0 |
| Índice único anual | Válido |
| Trigger de histórico | Ativo |
| View de consulta | 83 projetos do ano 2026 |

O relatório técnico com hashes SHA-256 dos scripts está em
`reports/migracoes_20261122T204822Z.json`.

**Analogia:** a migração não reescreveu as fichas. Ela colocou um cadeado que impede
identificadores duplicados, fotografou o estado atual para iniciar o histórico e
abriu um balcão único de consulta. As 83 fotografias iniciais não recuperam mudanças
anteriores à implantação: elas mostram o estado existente no momento da migração.

As informações históricas deste diretório sobre a entrega de 17/11 descrevem aquele
momento, quando a base principal ainda não havia sido migrada. Esta entrada registra
a etapa posterior. Nenhuma ingestão nova nem agendamento foi executado nesta etapa.
