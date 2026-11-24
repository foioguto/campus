# 3. Diário da oficina 🔧

## O ponto de partida

Havia um script que lia Excel e inseria staging, três testes pequenos e SQL inicial.
A simulação da planilha de treinamento já reconhecia os 83 registros e os 22 campos.
A revisão identificou ausência de unicidade no banco, linha física incorreta,
configuração divergente do README e lacunas de auditoria.

## As intervenções

| Ação | Motivo | O que observar no código |
|---|---|---|
| Separar módulos | Reduzir acoplamento entre arquivo, SQL e terminal | `src/campus_etl/` |
| Preservar entrada antiga | Não quebrar comandos usuais | `src/etl.py` delega à nova CLI |
| Resolver conexão na execução | Evitar efeitos colaterais ao importar | `config.database_url` |
| Usar parser de conexão do driver | Senhas podem conter `@`, espaço ou `/` | `make_conninfo` |
| Ler cabeçalhos sem renomeação automática | Detectar títulos repetidos em vez de ocultá-los | `header=None` |
| Desabilitar NA automático | `NA` pode ser um identificador legítimo | `keep_default_na=False` |
| Guardar linha física | Viabilizar correção na origem | Índice original + 1 |
| Bloquear lote inválido | Impedir “sucesso” com informação descartada | `QualityError` |
| Atualizar com histórico | Atender correções das planilhas anuais | `ON CONFLICT` e trigger |
| Não versionar reexecução igual | Evitar ruído no histórico | Comparação de campos de negócio |
| Auditar antes da leitura | Registrar arquivo ausente ou inválido | `Repository.start` |
| Criar contrato de consulta | Desacoplar consumidor da tabela física | Views no schema `mart` |
| Criar painel | Centralizar acesso para usuários sem SQL | Filtros, histórico e CSV |
| Adicionar manifesto | Preparar múltiplos anos e execução agendada | `config/sources.example.json` |
| Adotar pacote instalável | Tornar caminhos e comandos previsíveis | `pyproject.toml` |
| Usar unittest | Testar sem dependência de framework adicional | `tests/test_pipeline.py` |

As dependências diretas passam a ser declaradas em `pyproject.toml`; removemos pins
manuais de dependências transitivas. As faixas de versão facilitam instalação,
mas **não são um lock reproduzível**. Antes de implantar em produção, gere e revise
um lock no ambiente Python alvo, com política de atualização.

## Decisões de negócio recebidas

O usuário confirmou atualização de registros existentes, inclusão de novos e
preservação do histórico. Também confirmou necessidade de interface visual.
Essas escolhas orientaram a implementação. Não presumimos rateio de unidades,
normalização financeira, exclusão ou regras de datas ambíguas.

## Fronteiras conscientes

Datas e valores continuam textuais. É melhor mostrar um valor original do que
somar algo interpretado incorretamente. Dados canônicos tipados, dimensões e
indicadores financeiros exigem um contrato adicional com o negócio.

A entrega não modifica o `.env`, não migra a base principal do projeto, não configura cron
nem publica o painel. Os comandos de operação estão no README.
