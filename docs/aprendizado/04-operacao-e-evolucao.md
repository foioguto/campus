# 4. A biblioteca abre todo dia ⏰

Um programa automatizável é diferente de um programa já automatizado.
A entrega fornece o primeiro: comando estável, manifesto, retorno ao agendador,
auditoria e reexecução sem duplicação. Falta conectar a operação real.

## Procedimento de operação

1. Receba a versão final do arquivo em uma pasta controlada. Quem disponibiliza deve
   gravar temporariamente e renomear ao concluir, evitando leitura de arquivo incompleto.
2. Confira arquivo/aba/ano no manifesto e faça `--dry-run`.
3. Execute a carga; confira JSON, status e contagens no painel.
4. Reexecução do mesmo conteúdo deve contabilizar registros inalterados.
5. Em caso de falha, confira `audit.cargas.detalhes`, corrija a origem e execute outra vez.
   Uma nova tentativa tem novo lote. Nunca apague a auditoria para “limpar” o erro.

Contagem esperada em um lote concluído:
`linhas_lidas = linhas_carregadas + linhas_atualizadas + linhas_inalteradas`.
“Linhas carregadas” conta inserções novas; atualizações aparecem em contador separado.

A aplicação não tenta conexões indefinidamente. Um agendador pode repetir uma
execução após falha temporária; as regras de carga tornam essa repetição segura.
Uma conexão indisponível impede auditoria no banco: preserve o log JSON externo.
Processos mortos podem deixar lotes iniciados. Investigue o processo e o horário,
confirme que não está ativo e registre a intervenção antes de repetir a carga.

## Mudar o projeto de diretório

Os manifestos resolvem as planilhas em relação ao próprio arquivo JSON. Ao mover
`config/` e `data/` juntos, as entradas relativas continuam funcionando. O ETL e o
painel leem o `.env` da raiz do projeto. Revise caminhos absolutos de planilhas e
de agendamentos que você tenha configurado.

Os comandos instalados na `.venv` apontam para o caminho absoluto do Python. Uma
instalação editável também aponta para o diretório do código. Em uma próxima
mudança, renomeie a `.venv` antiga, abra um terminal na nova raiz e execute:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
campus-etl --manifest config/sources.example.json --dry-run
streamlit --version
```

O `--dry-run` valida a leitura da planilha de exemplo sem conectar ao PostgreSQL.
Use o `.env` que já contém as conexões do projeto.

## Próximos portões da evolução

| Etapa | Critério para avançar |
|---|---|
| Homologar anos reais | Validar layouts e estabilidade de `Quant. CI` em todos os anos |
| Publicar internamente | Definir servidor, autenticação, HTTPS e usuários de consulta |
| Automatizar recebimento | Confirmar se a origem é pasta de rede, Drive ou outro sistema |
| Agendar | Definir frequência, horário, responsável e tratamento de falhas |
| Observar | Alertar execução ausente, lote iniciado antigo, mudança de volume e rejeições |
| Proteger recuperação | Definir backup, retenção do histórico e arquivos originais |
| Modelar Data Mart | Definir grão da fato, dimensões, datas e métricas com o negócio |

Antes de somar recursos, confirme formatos monetários e moedas. Antes de contar
projetos por UR, confirme delimitadores, múltiplas unidades e eventual regra de rateio.
Antes de usar valores para decisão, defina como tratar correções retroativas.

## Segurança operacional

Use uma conta de ingestão com permissões necessárias de escrita e outra de leitura.
Não conceda DDL ao processo diário. A migração deve ser uma operação controlada.
O painel local não inclui autenticação própria; acesso em rede exige proteção externa.
Os logs e históricos podem conter dados internos e precisam de acesso e retenção definidos.
