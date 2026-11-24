# 6. Caderno de evidências ✅

Data: 17/11/2026. Ambiente: Python 3.14, PostgreSQL 18 descartável em `/tmp`.
O banco principal do projeto e o `.env` existente não foram alterados.

**Resultado final: 17 testes passaram**, incluindo integração com PostgreSQL e painel.

Foram exercitados:

- Planilha de treinamento: 83 registros válidos e 22 colunas mapeadas.
- Entrada legada e CLI instalável com manifesto.
- Migrações em banco novo e reexecução das migrações no mesmo banco.
- Inclusão, correção, repetição sem alteração e coexistência de anos.
- Histórico: uma versão na inclusão e outra quando o conteúdo muda.
- Falha no segundo registro: rollback do primeiro e de todas as versões do lote.
- Duas cargas simultâneas do mesmo ano: um estado e uma versão.
- Arquivo ausente: tentativa auditada como falha.
- Cabeçalhos repetidos, ausentes e desconhecidos, duplicatas e planilha vazia.
- Preservação de `NA`, zeros à esquerda em texto e números de linhas físicas.
- Senha com caracteres especiais na configuração legada `DB_*`.
- Painel pelo `streamlit.testing.v1.AppTest`: carregamento, 83 projetos, busca sem
  resultados, histórico da CI 1 e seleção vazia de anos.
- Consistência das dependências com `pip check`.

O teste do painel encontrou uma promoção automática de identificadores numéricos
para float durante a remoção de vazios. A correção filtra as linhas sem mudar seus
tipos e ganhou regressão com `001`, `NA` e o número `1`. Um bom teste atravessa
fronteiras e encontra problemas que o teste de uma função isolada não percebe.

Limites: AppTest valida o runtime e as interações, sem inspeção visual em navegador.
Não foram homologados arquivos reais de outros anos, autenticação em rede, backup,
volume elevado ou o agendador. Para grandes volumes, substituir consultas por linha
por carga em lote (`COPY` para tabela temporária e merge) após medir a necessidade.
