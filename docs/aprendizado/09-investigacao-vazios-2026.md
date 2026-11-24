# 9. A ficha vazia: origem incompleta ou perda na carga? 🔎

Investigação realizada em 23/11/2026, somente com leituras no banco `dm_demandas`.
Nenhum registro foi corrigido, excluído ou reprocessado nesta investigação.

## Como investigamos

Comparamos os 83 projetos de 2026 no banco, na view de consulta e na planilha
`data/dados_mockados_treinamento.xlsx`, aba `PARECER EXTERNO 2026`.
A comparação usou a chave `quant_ci`, os 22 campos de negócio e a linha física.
Também verificamos auditoria, fórmulas e células mescladas.

Todas as chaves do banco foram encontradas na planilha. O leitor atual reconhece
os 22 cabeçalhos, sem ausências nem colunas desconhecidas. Não há fórmulas na aba;
as células mescladas ficam apenas na linha de título, fora dos dados.

## Resultado: há duas causas diferentes

### 1. Valores presentes no Excel e ausentes no banco

| Campo | Vazios no banco | Vazios na planilha | Valores recuperáveis |
|---|---:|---:|---:|
| `contrapartida_apenas_valores` | 83 | 12 | 71 |
| `evento_ja_realizado_no_ultimo_ano` | 83 | 18 | 65 |

São **136 células em 74 projetos distintos**. Nas outras 20 colunas de negócio,
os valores do banco coincidem com a extração atual da planilha.

Exemplo: CI `1`, linha física 3 do Excel, tem contrapartida `25306.89` e resposta
`não` ao evento realizado no último ano. Ambos estão NULL no banco.

A auditoria mostra que a carga inicial ocorreu em 16/11/2026, antes da refatoração.
As quatro tentativas seguintes rejeitaram os 83 registros por já existirem; não
atualizaram os campos. Não há nova carga de 2026 com o fluxo de atualização atual.
Portanto, as melhorias no código e na estrutura não corrigiram retroativamente os dados.

O padrão de duas colunas inteiramente NULL, embora contenham valores na origem,
é compatível com cabeçalhos não reconhecidos pelo mapeamento antigo. Essa explicação
é uma inferência: não temos a versão exata executada em 16/11 nem hash do arquivo
registrado naquela carga para provar toda a cadeia histórica. O que foi comprovado
é a divergência entre o banco e o arquivo disponível, e a capacidade do leitor atual
de recuperar esses valores.

### 2. Campos já vazios na planilha

Existem **419 células de negócio vazias na origem**, distribuídas por campos
opcionais e registros incompletos. Por exemplo, `previsto_pa` e `data_entrega_para_ur`
estão vazios em 68 registros cada; `observacao` em 56. Não preenchemos por suposição.

Seis registros contêm somente o identificador, tanto no banco quanto no Excel:

| Quant. CI | Linha física no Excel |
|---|---:|
| 149 | 155 |
| 150 | 156 |
| 151 | 157 |
| 152 | 158 |
| 153 | 159 |
| 154 | 160 |

O validador atual exige chave preenchida e única, mas não exige demandante, setor
ou evento. Por isso essas linhas são consideradas válidas estruturalmente.
Isso revela uma regra de qualidade ainda não definida: uma linha com CI reservada
já representa um projeto ou deveria ficar fora da central até ser preenchida?
Excluir essas linhas ou inventar conteúdo sem confirmar essa regra esconderia a origem.

## Outro achado: linha de origem antiga

Os 83 registros de 2026 ainda têm `linha_origem` divergente da linha física atual.
A carga anterior registrava o índice relativo em vez da posição real no Excel.
Exemplo: CI `1` aponta para linha 1 no banco, enquanto está na linha 3 do arquivo.
As linhas vazias intermediárias podem ampliar a diferença. A leitura atual preserva
a posição correta. No fluxo atual, metadados são atualizados quando há mudança de
conteúdo de negócio; registros sem mudança não têm seus metadados regravados.
Logo, um reprocessamento comum pode deixar metadados legados incorretos nas linhas
cujo conteúdo não mudou. Uma correção completa de rastreabilidade requer tratar
explicitamente também esse caso, preservando as versões anteriores.

## Próximo passo recomendado

Reprocessar o arquivo de 2026 pelo ETL atual recupera as 136 células em 74 registros,
com histórico e auditoria, desde que a base e o arquivo não mudem após esta análise.
Os nove registros sem divergências de negócio permaneceriam inalterados.
Isso não elimina os vazios já existentes na origem, inclusive as seis CIs reservadas.

Separadamente, definir com o responsável pelas planilhas quais campos mínimos
caracterizam um projeto e como apresentar CIs ainda sem cadastro no painel.
Não transformar ausências em zero, “Não” ou valores fictícios automaticamente.

**Lição:** passar na validação estrutural não significa ter dados completos.
Uma migração melhora a estrutura; um reprocessamento reconcilia o conteúdo.
São operações diferentes e precisam ser verificadas separadamente.

Relatório detalhado, com cada diferença, linhas e auditoria:
`reports/investigacao_vazios_2026_20261123.json` (ignorado pelo Git).
