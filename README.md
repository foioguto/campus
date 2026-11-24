# Central de projetos internos

Planilhas anuais → PostgreSQL → painel de consulta. A primeira entrega reúne os anos,
permite buscar projetos e mantém versões quando uma planilha é corrigida.

## Preparar

Python 3.10+ e PostgreSQL 14+ (testes locais usam 18). Na raiz do projeto:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env     # Windows: Copy-Item .env.example .env
```

Preencha as conexões em `.env`. Não versionar senhas. `DATABASE_URL` tem precedência
sobre `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (compatibilidade).
`--dsn` tem precedência sobre ambos; prefira o ambiente para não expor senha no terminal.
O painel usa `QUERY_DATABASE_URL`, com fallback para a conexão principal.

Se mover o projeto, renomeie a `.venv` antiga e recrie o ambiente no novo
diretório. Reutilize o `.env` existente. Confira o [guia de mudança de diretório](docs/aprendizado/04-operacao-e-evolucao.md#mudar-o-projeto-de-diretório).

## Preparar o banco

Execute os arquivos com um cliente PostgreSQL na ordem abaixo, na base desejada:

1. `sql/01_schemas_staging_audit.sql` — base inicial, preservada.
2. `sql/03_integridade_historico_consultas.sql` — integridade, versões e views.
3. `sql/02_preflight.sql` — conferência, somente leitura.

Com `psql`, use `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/01_schemas_staging_audit.sql`
e depois o mesmo comando para `03_integridade_historico_consultas.sql`.
A variável deve estar exportada no shell; `psql` não carrega `.env` automaticamente.
Faça backup de uma base existente antes da migração. Os scripts são transacionais e
reexecutáveis; a migração 03 interrompe se houver chaves vazias ou duplicadas,
sem escolher arbitrariamente qual registro preservar. Não existe exclusão automática.

## Validar e carregar

```bash
python src/etl.py --file data/dados_mockados_treinamento.xlsx --year 2026 --sheet "PARECER EXTERNO 2026" --dry-run
python src/etl.py --file data/dados_mockados_treinamento.xlsx --year 2026 --sheet "PARECER EXTERNO 2026"
```

`--header-row 1` é o padrão: o cabeçalho está na segunda linha física do Excel.
O ano é explícito, nunca inferido de títulos da planilha.
A simulação não conecta nem exige o driver PostgreSQL.

- Chave: `(ano_origem, quant_ci)`, considerando `Quant. CI` um identificador textual estável.
- Novo projeto: insere. Projeto alterado: atualiza e registra nova versão.
- Repetição sem alteração: contabiliza como inalterada, sem gerar versão redundante.
- Projeto removido da planilha: permanece na base; exclusão exige regra de negócio futura.
- Erros de qualidade bloqueiam o lote inteiro. Nenhuma carga parcial silenciosa.
- Cabeçalhos desconhecidos e ausências bloqueiam a carga. Para um layout anual
  legitimamente reduzido, `--allow-missing-columns` permite ausências explicitamente.
  **Atenção:** na atualização, campos ausentes autorizados passam a NULL. Prefira
  homologar o layout completo e não usar essa opção em rotinas recorrentes.
- Valores monetários, datas e URs permanecem em texto de origem normalizado;
  ainda não existem totais financeiros nem rateio de URs sem regras homologadas.

Saída JSON: 0 = sucesso, incluindo reexecução sem alterações; 2 = lote inválido/falhou;
1 = configuração inválida. A auditoria registra cada tentativa que conseguiu abrir
conexão, inclusive erros de leitura. Sem conexão disponível, a saída JSON é a evidência.
Uma interrupção abrupta pode deixar `status=iniciada`; confira antes de reexecutar.

## Abrir a interface

```bash
streamlit run src/painel.py --server.address 127.0.0.1
```

Acesse `http://localhost:8501`. A consulta oferece filtros por ano e por colunas,
busca textual, escolha de colunas visíveis, detalhes do projeto e exportação CSV.
Os campos técnicos ficam fora da consulta; histórico e cargas estão na área Auditoria.
Exibe até 5.000 resultados por consulta e 100 cargas recentes, sem cache persistente.
O indicador de projetos considera todos os filtros, inclusive antes do limite da tabela.
O CSV contém as linhas exibidas e as colunas escolhidas.
Veja o [guia dos filtros](docs/aprendizado/10-consulta-para-usuarios.md).
O CSV protege textos que poderiam ser interpretados como fórmulas pelo Excel.

Para uso em rede, configure autenticação no proxy e uma conta de consulta com
`USAGE` nos schemas `mart`, `audit` e `SELECT` nas views `mart.projetos`,
`mart.resumo_anual` e tabelas `audit.demandas_versoes`, `audit.cargas`.
A aplicação força transações somente leitura; a conta dedicada reforça essa separação.
Esta entrega roda localmente, sem provisionar infraestrutura ou publicar dados.

## Vários anos e rotina

Copie `config/sources.example.json` para `config/sources.json` e cadastre cada origem.
Caminhos são relativos ao diretório do manifesto. Confira o ano e a aba de cada arquivo.

```bash
campus-etl --manifest config/sources.json --dry-run
campus-etl --manifest config/sources.json
```

O comando processa cada arquivo como uma transação independente e retorna erro se
qualquer origem falhar. Uma origem com erro não impede a tentativa das demais.
Exemplo de cron diário às 07h, usando o caminho absoluto do projeto:

```cron
0 7 * * * cd /caminho/data_mart_etl && .venv/bin/campus-etl --manifest config/sources.json >> /caminho/logs/campus-etl.log 2>&1
```

Crie o diretório de logs e ajuste caminhos, permissões e fuso do agendador.
O cron é um exemplo: **nenhuma tarefa foi instalada**. O processo deve receber os
arquivos prontos; sincronização com Drive/rede depende da origem a definir.
Veja [operação e evolução](docs/aprendizado/04-operacao-e-evolucao.md).

## Testar

```bash
python -m unittest discover -s tests -v
# Apenas em um banco DESCARTÁVEL: os testes de integração limpam as tabelas!
TEST_DATABASE_URL=postgresql://usuario:senha@localhost:5432/teste python -m unittest discover -s tests -v
```

Os testes de integração são ignorados se `TEST_DATABASE_URL` não estiver definida.
Não use a conexão principal do projeto nessa variável.

## Aprender com a refatoração

Comece por [docs/aprendizado/README.md](docs/aprendizado/README.md).
O material explica a arquitetura, a jornada dos dados, decisões, testes e próximos passos.

## Desenvolvimento com assistentes de IA

Leia o [guia codex.md](../codex.md) antes de alterar o projeto. Ele reúne o contexto,
as convenções de arquitetura, os contratos dos dados e os procedimentos de validação.
O [AGENTS.md](../AGENTS.md) da raiz aponta para esse guia.
