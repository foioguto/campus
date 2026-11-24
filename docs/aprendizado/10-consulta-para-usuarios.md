# 10. O balcão de consulta ganhou organização 🧭

Em 23/11/2026, adaptamos o painel para quem precisa encontrar projetos sem conhecer
a estrutura técnica do ETL. Nenhum dado do banco foi alterado nesta etapa.

## Da tabela física para uma tela de trabalho

A consulta começa com ano, identificador, projeto/evento, demandante, setor, unidade
regional e situação. Os cabeçalhos usam nomes legíveis. O usuário pode escolher
outros campos de negócio em **Personalizar colunas da tabela** e abrir a ficha
completa em **Ver detalhes de um projeto**.

Arquivo, aba, linha de origem, lote e instante de carga não entram nessa consulta,
nem no CSV. A aplicação seleciona explicitamente campos de negócio no SQL: não
se limita a esconder metadados visualmente. A área **Auditoria** preserva o histórico
e o acompanhamento de cargas para quem precisar investigar a ingestão.
Essa separação é navegação, não autorização: ela não substitui autenticação ou
perfis de acesso numa implantação em rede.

## Como combinar filtros

- **Anos:** uma ou várias opções; nenhum ano selecionado pede nova seleção.
- **Busca geral:** texto em identificador, número da CI, demandante, projeto,
  demanda ou setor.
- **Filtrar por colunas:** escolha os campos desejados. Setor, unidade regional e
  situação aparecem inicialmente. Campos categóricos oferecem listas; outros
  campos permitem pesquisar um trecho de texto.
- **Não informado:** seleciona valores NULL, vazios ou formados por espaços.
- **Limpar filtros:** restaura todos os anos, busca vazia e filtros iniciais sem restrição.

Dentro da mesma lista, valores são alternativas (OU). Entre listas, as condições
são combinadas (E). Exemplo: anos 2024/2025 + setor Tecnologia + busca DEMO encontra
5 projetos da demonstração.

As opções de cada lista são obtidas de todos os projetos dos anos selecionados,
sem o limite de exibição da tabela e independentemente dos outros filtros.
Se trocar os anos, seleções indisponíveis são removidas.
Unidades regionais compostas permanecem como no Excel; não foi criada uma regra
para separar ou ratear múltiplas unidades. Datas e valores ainda são textos e seus
filtros são por trecho, não intervalos tipados ou comparações numéricas.

## Totais e exportação coerentes

**Projetos encontrados** considera todos os filtros no banco, antes do limite de
5.000 linhas. A tela avisa quando a tabela contém apenas parte dos resultados.
O CSV usa as linhas exibidas e as colunas escolhidas, com os mesmos cabeçalhos.
Ausências são apresentadas como “Não informado”, sem alterar o valor armazenado.
Se nenhuma coluna estiver selecionada, o painel pede uma seleção antes de exportar.

## Implementação

`presentation.py` mantém os nomes e campos permitidos; `queries.py` monta as
condições com identificadores de uma lista permitida e valores parametrizados.
Isso permite filtrar uma coluna sem concatenar entrada do usuário em SQL.
Caracteres `%`, `_` e barra invertida na busca são tratados literalmente.
`painel.py` coordena os filtros, a tabela, o resumo e a ficha de detalhes.

O identificador da ficha combina ano e CI, evitando confundir projetos de anos
diferentes ou manter o detalhe de outra linha quando o resultado da pesquisa muda.

## Verificações realizadas

- 14 testes locais passaram; 5 testes que exigem banco descartável foram ignorados.
- AppTest verificou filtros combinados, busca vazia, limpeza, colunas escolhidas,
  detalhe e ausência de metadados na consulta.
- Testes de SQL verificaram parâmetros, valores não informados e rejeição de
  colunas técnicas como filtro.
- Com consultas somente leitura na base do projeto, AppTest confirmou 139 projetos
  no total, 5 projetos DEMO de Tecnologia em 2024/2025 e 6 registros com setor não
  informado em 2026.
- Não houve inspeção visual em navegador; as interações foram verificadas pelo
  runtime oficial de testes do Streamlit.

Referências: [multiselect](https://docs.streamlit.io/develop/api-reference/widgets/st.multiselect)
e [dataframe](https://docs.streamlit.io/develop/api-reference/data/st.dataframe).
